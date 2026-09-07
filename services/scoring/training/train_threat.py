"""
Train the threat / intimidation signal (MuRIL, binary NOT_THREAT / THREAT).

  PYTHONPATH=. python training/train_threat.py                                  # cross-entropy (V7 recipe)
  PYTHONPATH=. python training/train_threat.py --objective contrastive \
      --output models/threat_contrastive_v1                                    # CE + supervised-contrastive

--objective contrastive adds a SupCon term on the [CLS] embedding: positives are
same-label pairs in the batch (coercion with coercion), so the encoder is pushed
to separate "I'm sad" (generic distress, label 0) from "I'm being threatened into
silence" (label 1) in embedding space, not only at the logit. The classifier head
still exports threat_flag + prob; calibrate afterwards with training/calibrate.py.
"""
import argparse
import glob
import json
import math
import os
import shutil
import sys
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from datasets import Dataset
from sklearn.metrics import (accuracy_score, confusion_matrix, precision_recall_fscore_support,
                             roc_auc_score)
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          EarlyStoppingCallback, Trainer, TrainingArguments, set_seed)
from transformers.modeling_outputs import SequenceClassifierOutput

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.config import MODELS_DIR, THREAT_LABELS  # noqa: E402
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402

LABELS = THREAT_LABELS


class ContrastiveTrainer(Trainer):
    """Cross-entropy + supervised contrastive loss (Khosla et al. 2020) on the [CLS] vector."""

    def __init__(self, *a, supcon_weight=0.5, supcon_temperature=0.1, **kw):
        super().__init__(*a, **kw)
        self.supcon_weight = supcon_weight
        self.supcon_temperature = supcon_temperature

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        inputs = dict(inputs)
        labels = inputs.pop("labels")
        outputs = model(**inputs, output_hidden_states=True)
        ce = F.cross_entropy(outputs.logits, labels)
        z = F.normalize(outputs.hidden_states[-1][:, 0], dim=1)
        sim = z @ z.T / self.supcon_temperature
        eye = torch.eye(len(z), dtype=torch.bool, device=z.device)
        sim = sim.masked_fill(eye, -1e9)
        pos = (labels[:, None] == labels[None, :]) & ~eye
        log_prob = sim - torch.logsumexp(sim, dim=1, keepdim=True)
        n_pos = pos.sum(1)
        per_anchor = -(log_prob * pos).sum(1) / n_pos.clamp(min=1)
        supcon = per_anchor[n_pos > 0].mean() if bool((n_pos > 0).any()) else torch.zeros((), device=z.device)
        loss = ce + self.supcon_weight * supcon
        # return a clean output (no hidden_states) so Trainer.predict can stack logits during eval
        clean = SequenceClassifierOutput(loss=loss, logits=outputs.logits)
        return (loss, clean) if return_outputs else loss


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--train", default="training/data/threat_v7_train.csv")
    p.add_argument("--val", default="training/data/threat_v7_val.csv")
    p.add_argument("--test", default="training/data/threat_v7_test.csv")
    p.add_argument("--challenge", default="training/data/threat_challenge_v1.csv")
    p.add_argument("--output", default=str(MODELS_DIR / "threat_v7"))
    p.add_argument("--model", default="google/muril-base-cased")
    p.add_argument("--objective", choices=["ce", "contrastive"], default="ce")
    p.add_argument("--supcon-weight", type=float, default=0.5)
    p.add_argument("--supcon-temperature", type=float, default=0.1)
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--max-length", type=int, default=128)
    p.add_argument("--warmup-ratio", type=float, default=0.06)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--patience", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--run-name", default=None)
    p.add_argument("--no-mlflow", action="store_true")
    return p.parse_args()


def binary_metrics(logits, labels):
    preds = np.argmax(logits, axis=1)
    prob = torch.softmax(torch.tensor(logits), dim=1)[:, 1].numpy()
    p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
    out = {"accuracy": float(accuracy_score(labels, preds)), "precision": float(p), "recall": float(r), "f1": float(f1)}
    if len(np.unique(labels)) == 2:
        out["roc_auc"] = float(roc_auc_score(labels, prob))
    return out


def compute_metrics(eval_pred):
    return binary_metrics(*eval_pred)


def main():
    args = parse_args()
    set_seed(args.seed)
    train_df, val_df, test_df = (pd.read_csv(p) for p in (args.train, args.val, args.test))
    print(f"objective={args.objective}  train={len(train_df)} val={len(val_df)} test={len(test_df)}")

    tokenizer = AutoTokenizer.from_pretrained(args.model)

    def to_ds(df):
        return Dataset.from_pandas(df[["text", "label"]], preserve_index=False).map(
            lambda b: tokenizer(b["text"], truncation=True, max_length=args.max_length), batched=True)

    train_ds, val_ds, test_ds = to_ds(train_df), to_ds(val_df), to_ds(test_df)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=2, id2label={0: LABELS[0], 1: LABELS[1]}, label2id={LABELS[0]: 0, LABELS[1]: 1})

    total_steps = math.ceil(len(train_df) / args.batch) * args.epochs
    targs = TrainingArguments(
        output_dir=args.output, num_train_epochs=args.epochs, per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=32, learning_rate=args.lr, warmup_steps=int(args.warmup_ratio * total_steps),
        weight_decay=args.weight_decay, eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="f1", greater_is_better=True, save_total_limit=1,
        logging_steps=10, report_to="none", seed=args.seed, dataloader_pin_memory=False)
    common = dict(model=model, args=targs, train_dataset=train_ds, eval_dataset=val_ds, processing_class=tokenizer,
                  data_collator=DataCollatorWithPadding(tokenizer), compute_metrics=compute_metrics,
                  callbacks=[EarlyStoppingCallback(early_stopping_patience=args.patience)])
    trainer = (ContrastiveTrainer(supcon_weight=args.supcon_weight, supcon_temperature=args.supcon_temperature, **common)
               if args.objective == "contrastive" else Trainer(**common))

    t0 = time.time()
    trainer.train()
    train_seconds = time.time() - t0

    val_res = trainer.evaluate(eval_dataset=val_ds)
    pred = trainer.predict(test_ds)
    test_metrics = binary_metrics(pred.predictions, pred.label_ids)
    cm = confusion_matrix(pred.label_ids, np.argmax(pred.predictions, 1), labels=[0, 1]).tolist()
    challenge = None
    if args.challenge and os.path.exists(args.challenge):
        ch_df = pd.read_csv(args.challenge)
        ch_pred = trainer.predict(to_ds(ch_df))
        challenge = binary_metrics(ch_pred.predictions, ch_pred.label_ids)

    print("\nVAL :", {k: round(float(v), 4) for k, v in val_res.items() if k.startswith("eval_") and "runtime" not in k})
    print("TEST:", {k: round(v, 4) for k, v in test_metrics.items()}, "confusion", cm)
    if challenge:
        print("CHALLENGE:", {k: round(v, 4) for k, v in challenge.items()})

    os.makedirs(args.output, exist_ok=True)
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    for ckpt in glob.glob(os.path.join(args.output, "checkpoint-*")):
        shutil.rmtree(ckpt, ignore_errors=True)

    metrics = {"signal": "threat", "objective": args.objective, "model_name": args.model,
               "dataset": os.path.basename(args.train), "train_size": len(train_df), "val_size": len(val_df),
               "test_size": len(test_df),
               "config": {"epochs": args.epochs, "lr": args.lr, "batch": args.batch, "max_length": args.max_length,
                          "warmup_ratio": args.warmup_ratio, "weight_decay": args.weight_decay,
                          "supcon_weight": args.supcon_weight if args.objective == "contrastive" else 0.0,
                          "supcon_temperature": args.supcon_temperature, "seed": args.seed},
               "epochs_run": int(round(trainer.state.epoch or 0)), "train_seconds": round(train_seconds, 1),
               "val": {k.replace("eval_", ""): float(v) for k, v in val_res.items() if k.startswith("eval_")},
               "test": test_metrics, "test_confusion_matrix": cm, "challenge": challenge,
               "export": {"threat_flag": "prob >= 0.5", "prob": "softmax(logits / T)[THREAT], T from calibration.json"},
               "history": [h for h in trainer.state.log_history if "eval_f1" in h]}
    json.dump(metrics, open(os.path.join(args.output, "metrics.json"), "w"), indent=2)

    run_name = args.run_name or f"train_threat_{args.objective}_{os.path.basename(args.output)}"
    with mlflow_run("threat", run_name, params={**metrics["config"], "objective": args.objective, "model": args.model,
                                                "train_size": len(train_df)},
                    tags={"signal": "threat", "stage": "train"}, enabled=not args.no_mlflow):
        for h in metrics["history"]:
            log_metrics({k.replace("eval_", "val_"): v for k, v in h.items() if k.startswith("eval_")},
                        step=int(round(h["epoch"])), enabled=not args.no_mlflow)
        log_metrics(metrics["val"], prefix="final_val_", enabled=not args.no_mlflow)
        log_metrics(test_metrics, prefix="test_", enabled=not args.no_mlflow)
        if challenge:
            log_metrics(challenge, prefix="challenge_", enabled=not args.no_mlflow)
        log_dict(metrics, "metrics.json", enabled=not args.no_mlflow)
    print(f"\nsaved {args.output}")


if __name__ == "__main__":
    main()
