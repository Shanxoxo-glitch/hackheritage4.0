"""
Generic evaluator for the MuRIL text models (threat or distress).

Examples
  python src/evaluate_text_model.py --task threat   --model models/threat_v7 \
      --test training/data/threat_v7_test.csv
  python src/evaluate_text_model.py --task distress --model models/distress_v3 \
      --test training/data/distress_v3_test.csv --challenge training/data/distress_challenge_v1.csv

Prints overall / per-class / per-language / per-category metrics, the
confusion matrix and every wrong prediction; logs everything to MLflow.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402
from app.config import SENTIMENT_LABELS as DISTRESS_LABELS, THREAT_LABELS  # noqa: E402
from app.text_models import TextClassifier  # noqa: E402

LABELS = {"threat": THREAT_LABELS, "distress": DISTRESS_LABELS}


def evaluate_df(clf, df, title, label_names):
    preds = clf.predict(df["text"].tolist())
    df = df.copy()
    df["pred"] = [p["label_id"] for p in preds]
    df["confidence"] = [p["confidence"] for p in preds]
    df["p_top"] = [p["probs"][label_names[-1]] for p in preds]  # P(THREAT) or P(HIGH)
    df["correct"] = df["label"] == df["pred"]
    y, yhat = df["label"].values, df["pred"].values

    res = {"n": int(len(df)), "accuracy": float(accuracy_score(y, yhat))}
    mp, mr, mf, _ = precision_recall_fscore_support(y, yhat, average="macro", zero_division=0)
    res.update({"macro_precision": float(mp), "macro_recall": float(mr), "macro_f1": float(mf)})
    if len(label_names) == 2:
        bp, br, bf, _ = precision_recall_fscore_support(y, yhat, average="binary", zero_division=0)
        res.update({"precision": float(bp), "recall": float(br), "f1": float(bf)})
    res["per_class"] = classification_report(y, yhat, labels=list(range(len(label_names))),
                                             target_names=label_names, zero_division=0, output_dict=True)
    cm = confusion_matrix(y, yhat, labels=list(range(len(label_names))))
    res["confusion_matrix"] = cm.tolist()
    res["prediction_distribution"] = {n: int(c) for n, c in zip(label_names, np.bincount(yhat, minlength=len(label_names)))}

    print("\n" + "=" * 60); print(title); print("=" * 60)
    print(f"n={res['n']}  accuracy={res['accuracy']:.4f}  macro_f1={res['macro_f1']:.4f}", end="")
    if "f1" in res:
        print(f"  |  binary P={res['precision']:.4f} R={res['recall']:.4f} F1={res['f1']:.4f}", end="")
    print()
    print("\nPer class:")
    for n in label_names:
        r = res["per_class"][n]
        print(f"  {n:12s} P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1-score']:.3f} n={int(r['support'])}")
    print("\nConfusion (rows=actual, cols=pred):", label_names)
    for i, row in enumerate(cm):
        print(f"  {label_names[i]:12s} {row.tolist()}")

    for col in ("language", "category"):
        if col in df.columns:
            res[f"by_{col}"] = {}
            print(f"\nBy {col}:")
            for val in sorted(df[col].dropna().unique()):
                sub = df[df[col] == val]
                acc = float(sub["correct"].mean())
                res[f"by_{col}"][str(val)] = {"n": int(len(sub)), "accuracy": acc}
                print(f"  {str(val):28s} {int(sub['correct'].sum()):>3}/{len(sub):<3} acc={acc:.3f}")

    wrong = df[~df["correct"]]
    res["wrong"] = wrong[["text", "label", "pred", "confidence"]].to_dict("records")
    print(f"\nWrong predictions: {len(wrong)}")
    for _, r in wrong.iterrows():
        extra = "  ".join(f"{c}={r[c]}" for c in ("language", "category") if c in df.columns)
        print(f"  ✗ [{label_names[int(r['label'])]} -> {label_names[int(r['pred'])]} conf={r['confidence']:.2f}] {r['text']}  {extra}")
    print(f"\nMean confidence: {df['confidence'].mean():.3f}  "
          f"(correct {df.loc[df['correct'], 'confidence'].mean():.3f}"
          + (f", wrong {wrong['confidence'].mean():.3f})" if len(wrong) else ")"))
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", choices=list(LABELS), required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--test", required=True)
    p.add_argument("--challenge", default=None)
    p.add_argument("--run-name", default=None)
    p.add_argument("--no-mlflow", action="store_true")
    args = p.parse_args()

    label_names = LABELS[args.task]
    clf = TextClassifier(args.model, label_names)
    print(f"Loaded {clf.name} on {clf.device}  calibrated={clf.calibrated} T={clf.temperature:.3f}")

    report = {"model": args.model, "task": args.task}
    report["test"] = evaluate_df(clf, pd.read_csv(args.test), f"HELD-OUT TEST  ({args.test})", label_names)
    if args.challenge:
        report["challenge"] = evaluate_df(clf, pd.read_csv(args.challenge),
                                          f"ADVERSARIAL CHALLENGE  ({args.challenge})", label_names)

    enabled = not args.no_mlflow
    with mlflow_run(args.task, args.run_name or f"eval_{clf.name}",
                    params={"model": args.model, "test": args.test, "challenge": args.challenge or "",
                            "calibrated": clf.calibrated, "temperature": round(clf.temperature, 4)},
                    tags={"task": args.task, "stage": "eval"}, enabled=enabled):
        log_metrics(report["test"], prefix="test_", enabled=enabled)
        if "challenge" in report:
            log_metrics(report["challenge"], prefix="challenge_", enabled=enabled)
        log_dict(report, "evaluation_report.json", enabled=enabled)
    print("\nDone.")


if __name__ == "__main__":
    main()
