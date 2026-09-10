"""
Temperature-scaling calibration for a MuRIL classifier.

Fits one scalar T on the VALIDATION logits (minimising NLL), reports
NLL / ECE / mean-confidence before vs after on val and test, and writes
<model>/calibration.json which TextClassifier picks up automatically.

  python src/calibrate_model.py --task threat   --model models/threat_v7 \
      --val training/data/threat_v7_val.csv --test training/data/threat_v7_test.csv
  python src/calibrate_model.py --task distress --model models/distress_v3 \
      --val training/data/distress_v3_val.csv --test training/data/distress_v3_test.csv
"""
import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import log_softmax, softmax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402
from app.config import SENTIMENT_LABELS as DISTRESS_LABELS, THREAT_LABELS  # noqa: E402
from app.text_models import TextClassifier  # noqa: E402

LABELS = {"threat": THREAT_LABELS, "distress": DISTRESS_LABELS}


def nll(logits, y, T):
    lp = log_softmax(logits / T, axis=1)
    return float(-lp[np.arange(len(y)), y].mean())


def ece(logits, y, T, bins=10):
    p = softmax(logits / T, axis=1)
    conf, pred = p.max(1), p.argmax(1)
    acc = (pred == y).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(acc[m].mean() - conf[m].mean())
    return float(total)


def summary(logits, y, T):
    p = softmax(logits / T, axis=1)
    return {"nll": nll(logits, y, T), "ece": ece(logits, y, T),
            "mean_confidence": float(p.max(1).mean()),
            "accuracy": float((p.argmax(1) == y).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=list(LABELS), required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--val", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--no-mlflow", action="store_true")
    args = ap.parse_args()

    clf = TextClassifier(args.model, LABELS[args.task])
    val, test = pd.read_csv(args.val), pd.read_csv(args.test)
    lv, yv = clf.logits(val["text"].tolist()), val["label"].values.astype(int)
    lt, yt = clf.logits(test["text"].tolist()), test["label"].values.astype(int)

    opt = minimize_scalar(lambda T: nll(lv, yv, T), bounds=(0.05, 10.0), method="bounded")
    T = float(opt.x)

    before = {"val": summary(lv, yv, 1.0), "test": summary(lt, yt, 1.0)}
    after = {"val": summary(lv, yv, T), "test": summary(lt, yt, T)}

    print("=" * 60); print(f"TEMPERATURE SCALING  {clf.name}"); print("=" * 60)
    print(f"fitted temperature T = {T:.4f}   (T>1 softens over-confident outputs, T<1 sharpens)")
    for split in ("val", "test"):
        b, a = before[split], after[split]
        print(f"\n{split.upper()}  (n={len(yv) if split == 'val' else len(yt)})")
        print(f"  NLL              {b['nll']:.4f} -> {a['nll']:.4f}")
        print(f"  ECE              {b['ece']:.4f} -> {a['ece']:.4f}")
        print(f"  mean confidence  {b['mean_confidence']:.4f} -> {a['mean_confidence']:.4f}   (accuracy {a['accuracy']:.4f})")

    cal = {"method": "temperature_scaling", "temperature": T, "fitted_on": args.val,
           "n_val": int(len(yv)), "n_test": int(len(yt)),
           "before": before, "after": after,
           "fitted_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "note": "Applied as softmax(logits / T). Fitted on a small validation set; treat as a first-order correction."}
    out = os.path.join(args.model, "calibration.json")
    with open(out, "w") as f:
        json.dump(cal, f, indent=2)
    print(f"\nSaved: {out}")

    enabled = not args.no_mlflow
    with mlflow_run(args.task, f"calibrate_{clf.name}", params={"model": args.model, "val": args.val},
                    tags={"task": args.task, "stage": "calibration"}, enabled=enabled):
        log_metrics({"temperature": T}, enabled=enabled)
        for split in ("val", "test"):
            log_metrics(before[split], prefix=f"{split}_before_", enabled=enabled)
            log_metrics(after[split], prefix=f"{split}_after_", enabled=enabled)
        log_dict(cal, "calibration.json", enabled=enabled)


if __name__ == "__main__":
    main()
