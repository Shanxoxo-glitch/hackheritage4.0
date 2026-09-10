"""
Train the sentiment / distress-level signal (MuRIL, 3-class LOW / MODERATE / HIGH).

  PYTHONPATH=. python training/train_sentiment.py                       # distress V3 corpus (default)
  PYTHONPATH=. python training/train_sentiment.py --extra-csv more.csv  # mix in extra labelled rows

Recipe that fixed the V2 collapse (loss stuck at ln 3): 4x data with a leak-aware
split, lr 3e-5, 10 % warm-up, early stopping on macro-F1, id2label in config.
Reports per-language F1 -> <repo>/artifacts/signal_sentiment_f1.json. Logs to MLflow.

Public corpora (IndicSentiment / IndicGLUE sentiment / L3Cube Hinglish) can be mixed
in after converting them to text,label[,language] CSVs with label mapping
negative->HIGH(2) neutral->LOW(0); they are NOT distress-labelled, so keep the
hand-written distress test set as the reported metric.

Kaggle runner:  git clone <repo> && cd services/scoring && pip install -r requirements-train.txt
                && PYTHONPATH=. python training/train_sentiment.py --output /kaggle/working/distress_v3
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
from datasets import Dataset
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          EarlyStoppingCallback, Trainer, TrainingArguments, set_seed)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.config import MODELS_DIR, REPO_ROOT, SENTIMENT_LABELS  # noqa: E402
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402

LABELS = SENTIMENT_LABELS


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--train", default="training/data/distress_v3_train.csv")
    p.add_argument("--val", default="training/data/distress_v3_val.csv")
    p.add_argument("--test", default="training/data/distress_v3_test.csv")
    p.add_argument("--extra-csv", action="append", default=[], help="extra labelled rows appended to train")
    p.add_argument("--output", default=str(MODELS_DIR / "distress_v3"))
    p.add_argument("--model", default="google/muril-base-cased")
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--lr", type=float, default=3e-5)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--max-length", type=int, default=64)
    p.add_argument("--warmup-ratio", type=float, default=0.10)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--patience", type=int, default=4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--run-name", default="train_sentiment_distress_v3")
    p.add_argument("--no-mlflow", action="store_true")
    return p.parse_args()


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    return {"accuracy": accuracy_score(labels, preds), "macro_precision": p, "macro_recall": r, "macro_f1": f1}


def per_language_f1(df, preds):
    out = {}
    if "language" not in df.columns:
        return out
    for lang, g in df.assign(pred=preds).groupby("language"):
        p, r, f1, _ = precision_recall_fscore_support(g["label"], g["pred"], average="macro", zero_division=0)
        out[str(lang)] = {"n": int(len(g)), "accuracy": float((g["pred"] == g["label"]).mean()),
                          "macro_precision": float(p), "macro_recall": float(r), "macro_f1": float(f1)}
    return out


def main():
    args = parse_args()
    set_seed(args.seed)
    train_df = pd.concat([pd.read_csv(args.train)] + [pd.read_csv(p) for p in args.extra_csv], ignore_index=True)
    val_df, test_df = pd.read_csv(args.val), pd.read_csv(args.test)
    print(f"train={len(train_df)} (extra files: {len(args.extra_csv)})  val={len(val_df)}  test={len(test_df)}")
    print("train labels:", train_df["label"].value_counts().sort_index().to_dict())

    tokenizer = AutoTokenizer.from_pretrained(args.model)

    def to_ds(df):
        return Dataset.from_pandas(df[["text", "label"]], preserve_index=False).map(
            lambda b: tokenizer(b["text"], truncation=True, max_length=args.max_length), batched=True)

    train_ds, val_ds, test_ds = to_ds(train_df), to_ds(val_df), to_ds(test_df)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(LABELS),
        id2label={i: n for i, n in enumerate(LABELS)}, label2id={n: i for i, n in enumerate(LABELS)})

    total_steps = math.ceil(len(train_df) / args.batch) * args.epochs
    warmup_steps = int(args.warmup_ratio * total_steps)
    targs = TrainingArguments(
        output_dir=args.output, num_train_epochs=args.epochs, per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=32, learning_rate=args.lr, warmup_steps=warmup_steps,
        weight_decay=args.weight_decay, lr_scheduler_type="linear", eval_strategy="epoch",
        save_strategy="epoch", load_best_model_at_end=True, metric_for_best_model="macro_f1",
        greater_is_better=True, save_total_limit=1, logging_steps=10, report_to="none", seed=args.seed,
        dataloader_pin_memory=False)
    trainer = Trainer(model=model, args=targs, train_dataset=train_ds, eval_dataset=val_ds,
                      processing_class=tokenizer, data_collator=DataCollatorWithPadding(tokenizer),
                      compute_metrics=compute_metrics,
                      callbacks=[EarlyStoppingCallback(early_stopping_patience=args.patience)])
    t0 = time.time()
    trainer.train()
    train_seconds = time.time() - t0

    val_res = trainer.evaluate(eval_dataset=val_ds)
    pred = trainer.predict(test_ds)
    test_preds = np.argmax(pred.predictions, axis=1)
    test_metrics = {k: float(v) for k, v in compute_metrics((pred.predictions, pred.label_ids)).items()}
    report = classification_report(pred.label_ids, test_preds, target_names=LABELS, zero_division=0, output_dict=True)
    cm = confusion_matrix(pred.label_ids, test_preds, labels=list(range(len(LABELS)))).tolist()
    lang_f1 = per_language_f1(test_df, test_preds)

    print("\nVAL :", {k: round(float(v), 4) for k, v in val_res.items() if k.startswith("eval_") and "runtime" not in k})
    print("TEST:", {k: round(v, 4) for k, v in test_metrics.items()})
    print("confusion:", cm)
    for lang, m in lang_f1.items():
        print(f"  {lang:10s} n={m['n']:3d} acc={m['accuracy']:.3f} macro_f1={m['macro_f1']:.3f}")
    if test_metrics["macro_f1"] < 0.5:
        print("!! macro-F1 < 0.5: model may be collapsing; try --lr 5e-5 --epochs 15")

    os.makedirs(args.output, exist_ok=True)
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    for ckpt in glob.glob(os.path.join(args.output, "checkpoint-*")):
        shutil.rmtree(ckpt, ignore_errors=True)

    history = [h for h in trainer.state.log_history if "eval_macro_f1" in h]
    metrics = {"signal": "sentiment", "model_name": args.model, "dataset": os.path.basename(args.train),
               "train_size": len(train_df), "val_size": len(val_df), "test_size": len(test_df),
               "config": {"epochs": args.epochs, "lr": args.lr, "batch": args.batch, "max_length": args.max_length,
                          "warmup_steps": warmup_steps, "weight_decay": args.weight_decay,
                          "patience": args.patience, "seed": args.seed},
               "epochs_run": int(round(trainer.state.epoch or 0)), "train_seconds": round(train_seconds, 1),
               "val": {k.replace("eval_", ""): float(v) for k, v in val_res.items() if k.startswith("eval_")},
               "test": test_metrics, "test_per_class": report, "test_confusion_matrix": cm,
               "per_language": lang_f1, "history": history}
    json.dump(metrics, open(os.path.join(args.output, "metrics.json"), "w"), indent=2)
    art = REPO_ROOT / "artifacts"
    art.mkdir(exist_ok=True)
    json.dump({"signal": "sentiment", "model": os.path.basename(args.output), "test": test_metrics,
               "per_language": lang_f1, "per_class": {k: report[k] for k in LABELS}},
              open(art / "signal_sentiment_f1.json", "w"), indent=2)

    with mlflow_run("sentiment", args.run_name, artifact_path=args.output,
                    params={**metrics["config"], "model": args.model, "train_size": len(train_df)},
                    tags={"signal": "sentiment", "stage": "train"}, enabled=not args.no_mlflow):
        for h in history:
            log_metrics({k.replace("eval_", "val_"): v for k, v in h.items() if k.startswith("eval_")},
                        step=int(round(h["epoch"])), enabled=not args.no_mlflow)
        log_metrics(metrics["val"], prefix="final_val_", enabled=not args.no_mlflow)
        log_metrics(test_metrics, prefix="test_", enabled=not args.no_mlflow)
        for lang, m in lang_f1.items():
            log_metrics({"macro_f1": m["macro_f1"]}, prefix=f"test_{lang}_", enabled=not args.no_mlflow)
        log_dict(metrics, "metrics.json", enabled=not args.no_mlflow)
    print(f"\nsaved {args.output}  |  artifacts/signal_sentiment_f1.json")


if __name__ == "__main__":
    main()
