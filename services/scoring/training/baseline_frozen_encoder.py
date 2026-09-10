"""
Frozen-encoder baseline for distress V3:
MuRIL mean-pooled embeddings (no fine-tuning) -> logistic regression.

Why: it ALWAYS learns (no plateau risk), trains in ~1 minute, and gives a
reference row in MLflow so the fine-tuned model has something to beat.
Saved to models/distress_v3_embed/ (not used by the API by default).
"""
from app.config import MODELS_DIR
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from transformers import AutoModel, AutoTokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402
from app.text_models import pick_device  # noqa: E402

MODEL_NAME = "google/muril-base-cased"
OUT_DIR = "models/distress_v3_embed"
LABELS = ["LOW", "MODERATE", "HIGH"]


@torch.no_grad()
def embed(texts, tok, model, device, bs=32):
    out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i + bs], padding=True, truncation=True, max_length=64, return_tensors="pt").to(device)
        h = model(**enc).last_hidden_state
        m = enc["attention_mask"].unsqueeze(-1).float()
        out.append(((h * m).sum(1) / m.sum(1)).float().cpu().numpy())
    return np.concatenate(out)


def metrics(y, yhat):
    p, r, f, _ = precision_recall_fscore_support(y, yhat, average="macro", zero_division=0)
    return {"accuracy": float(accuracy_score(y, yhat)), "macro_precision": float(p),
            "macro_recall": float(r), "macro_f1": float(f)}


def main():
    tr = pd.read_csv("training/data/distress_v3_train.csv")
    va = pd.read_csv("training/data/distress_v3_val.csv")
    te = pd.read_csv("training/data/distress_v3_test.csv")
    device = "cpu"   # tiny embedding pass; CPU avoids an MPS hang seen with AutoModel on torch 2.14
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    enc = AutoModel.from_pretrained(MODEL_NAME).to(device).eval()
    print(f"Embedding {len(tr)}/{len(va)}/{len(te)} texts on {device} ...")
    Xtr, Xva, Xte = (embed(d["text"].tolist(), tok, enc, device) for d in (tr, va, te))
    ytr, yva, yte = tr["label"].values, va["label"].values, te["label"].values

    best = None
    for C in (0.1, 0.3, 1.0, 3.0, 10.0):
        clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced").fit(Xtr, ytr)
        m = metrics(yva, clf.predict(Xva))
        print(f"  C={C:<5} val macro_f1={m['macro_f1']:.4f} acc={m['accuracy']:.4f}")
        if best is None or m["macro_f1"] > best[1]["macro_f1"]:
            best = (C, m, clf)
    C, val_m, clf = best
    test_m = metrics(yte, clf.predict(Xte))
    cm = confusion_matrix(yte, clf.predict(Xte), labels=[0, 1, 2]).tolist()
    print(f"\nBest C={C}\nVAL : {val_m}\nTEST: {test_m}\nconfusion: {cm}")

    os.makedirs(OUT_DIR, exist_ok=True)
    joblib.dump({"clf": clf, "encoder": MODEL_NAME, "labels": LABELS, "pooling": "mean", "max_length": 64},
                os.path.join(OUT_DIR, "model.joblib"))
    meta = {"C": C, "val": val_m, "test": test_m, "confusion": cm, "encoder": MODEL_NAME}
    json.dump(meta, open(os.path.join(OUT_DIR, "metrics.json"), "w"), indent=2)

    with mlflow_run("distress", "embed_baseline_distress_v3",
                    params={"encoder": MODEL_NAME, "head": "logreg", "C": C, "pooling": "mean",
                            "train_size": len(tr)}, tags={"task": "distress", "stage": "baseline"}):
        log_metrics(val_m, prefix="final_val_"); log_metrics(test_m, prefix="test_"); log_dict(meta, "metrics.json")
    print("Saved:", OUT_DIR)


if __name__ == "__main__":
    main()
