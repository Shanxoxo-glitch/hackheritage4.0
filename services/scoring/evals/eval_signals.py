"""
Held-out evaluation of all three signals -> ONE JSON in <repo>/artifacts/signal_eval.json  (pitch artifact #3)
plus artifacts/signal_sentiment_f1.json (per-language sentiment F1).

  PYTHONPATH=. python evals/eval_signals.py

Uses the exact model objects the API serves (app.models singletons), so the
numbers are the numbers the service produces. F1 per signal + ROC-AUC for threat.
"""
import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix,
                             precision_recall_fscore_support, roc_auc_score)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SCORING_WARM_ON_START", "0")
from app import config as C  # noqa: E402
from app.models import get_sentiment, get_threat, get_voice  # noqa: E402

DATA = os.path.join(ROOT, "training", "data")


def text_eval(clf, df, labels, binary):
    preds = clf.predict(df["text"].tolist())
    yhat = np.array([p["label_id"] for p in preds])
    y = df["label"].values.astype(int)
    avg = "binary" if binary else "macro"
    p, r, f1, _ = precision_recall_fscore_support(y, yhat, average=avg, zero_division=0)
    out = {"n": int(len(df)), "accuracy": float(accuracy_score(y, yhat)), "precision": float(p), "recall": float(r),
           "f1": float(f1), "confusion_matrix": confusion_matrix(y, yhat, labels=list(range(len(labels)))).tolist(),
           "mean_confidence": float(np.mean([q["confidence"] for q in preds]))}
    if binary:
        prob = np.array([q["probs"][labels[1]] for q in preds])
        out["roc_auc"] = float(roc_auc_score(y, prob)) if len(np.unique(y)) == 2 else None
    else:
        pc, rc, fc, sup = precision_recall_fscore_support(y, yhat, labels=list(range(len(labels))), zero_division=0)
        out["per_class"] = {n: {"precision": float(pc[i]), "recall": float(rc[i]), "f1": float(fc[i]), "n": int(sup[i])}
                            for i, n in enumerate(labels)}
    if "language" in df.columns:
        out["per_language"] = {}
        for lang, g in df.assign(pred=yhat).groupby("language"):
            lp, lr, lf, _ = precision_recall_fscore_support(g["label"], g["pred"], average=avg, zero_division=0)
            out["per_language"][str(lang)] = {"n": int(len(g)), "accuracy": float((g["pred"] == g["label"]).mean()),
                                              "f1": float(lf)}
    return out


def voice_eval(scorer):
    path = os.path.join(DATA, "voice_features_ravdess.csv")
    if not os.path.exists(path):
        return {"skipped": "training/data/voice_features_ravdess.csv missing"}
    df = pd.read_csv(path)
    if "f0_cv" not in df.columns:
        df["f0_cv"] = df["f0_std"] / (df["f0_mean"] + 1e-8)
        df["f0_range_rel"] = df["f0_range"] / (df["f0_mean"] + 1e-8)
    test = df[df["split"] == "test"]
    X = test[scorer.feature_names].values
    y = test["label"].values.astype(int)
    prob = scorer.score_features(X)
    yhat = (prob >= 0.5).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(y, yhat, average="binary", zero_division=0)
    out = {"fixed_split_test": {"n": int(len(test)), "actors": sorted(map(int, test["actor"].unique())),
                                "accuracy": float(accuracy_score(y, yhat)),
                                "balanced_accuracy": float(balanced_accuracy_score(y, yhat)),
                                "precision": float(p), "recall": float(r), "f1": float(f1),
                                "roc_auc": float(roc_auc_score(y, prob)),
                                "note": "final model was re-fit on all 24 actors, so this split is in-sample; "
                                        "cv_by_actor below is the honest speaker-independent number"},
           "cv_by_actor": (scorer.metrics or {}).get("cv_by_actor"), "trained_on": scorer.trained_on}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(C.REPO_ROOT / "artifacts" / "signal_eval.json"))
    args = ap.parse_args()
    report = {"generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "schema_version": C.SCHEMA_VERSION, "signals": {}}

    try:
        s = get_sentiment()
        report["signals"]["sentiment"] = {
            "model": s.name, "calibrated": s.calibrated, "temperature": s.temperature,
            "test": text_eval(s, pd.read_csv(os.path.join(DATA, "distress_v3_test.csv")), C.SENTIMENT_LABELS, False),
            "challenge": text_eval(s, pd.read_csv(os.path.join(DATA, "distress_challenge_v1.csv")), C.SENTIMENT_LABELS, False)}
    except Exception as e:
        report["signals"]["sentiment"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        t = get_threat()
        report["signals"]["threat"] = {
            "model": t.name, "calibrated": t.calibrated, "temperature": t.temperature,
            "test": text_eval(t, pd.read_csv(os.path.join(DATA, "threat_v7_test.csv")), C.THREAT_LABELS, True),
            "challenge": text_eval(t, pd.read_csv(os.path.join(DATA, "threat_challenge_v1.csv")), C.THREAT_LABELS, True)}
    except Exception as e:
        report["signals"]["threat"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        v = get_voice()
        report["signals"]["voice"] = {"model": v.name, **voice_eval(v)}
    except Exception as e:
        report["signals"]["voice"] = {"error": f"{type(e).__name__}: {e}"}

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(report, open(args.out, "w"), indent=2)
    sent = report["signals"].get("sentiment", {})
    if "test" in sent:
        json.dump({"signal": "sentiment", "model": sent["model"], "test": {k: sent["test"][k] for k in ("n", "accuracy", "f1")},
                   "per_language": sent["test"].get("per_language", {}), "per_class": sent["test"].get("per_class", {})},
                  open(os.path.join(os.path.dirname(args.out), "signal_sentiment_f1.json"), "w"), indent=2)

    print(json.dumps({k: {kk: (vv if not isinstance(vv, dict) else {m: vv[m] for m in vv if m in ("n", "accuracy", "f1", "roc_auc")})
                          for kk, vv in v.items() if kk in ("model", "test", "challenge", "cv_by_actor", "error")}
                      for k, v in report["signals"].items()}, indent=2))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
