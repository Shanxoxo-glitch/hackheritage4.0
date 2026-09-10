"""
Held-out evaluation of all three perception signals -> ONE machine-readable JSON.

  PYTHONPATH=. python evals/eval_signals.py                 # -> <repo>/artifacts/signal_eval.json
  PYTHONPATH=. python evals/eval_signals.py --markdown      # + human-readable summary on stdout

Uses the exact model objects the API serves (app.models singletons), so these are the
numbers the running service produces - not a separate evaluation path.

Reported per signal
  sentiment (3-class)  accuracy, macro precision/recall/F1, per-class P/R/F1/support,
                       confusion matrix, per-language, calibration (T, ECE/NLL before->after),
                       held-out test + adversarial challenge set
  threat (binary)      accuracy, precision, recall, F1, ROC-AUC, confusion matrix,
                       per-language (EN / Hinglish), per-category incl. hard negatives,
                       hard-negative subset summary, calibration, test + adversarial challenge
  voice (binary)       accuracy, balanced accuracy, precision, recall, F1, ROC-AUC on the fixed
                       by-actor split AND the speaker-independent GroupKFold-by-actor CV
                       (every actor held out once) recorded at training time
Also writes artifacts/signal_sentiment_f1.json (per-language sentiment F1, pitch artifact).
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

# categories that carry threat-like vocabulary but are NOT threats: the cases a keyword
# baseline gets wrong. Names as they appear in the V5/V6/V7 generators + challenge sets.
HARD_NEGATIVE_CATEGORIES = {
    "hard_negative", "negation", "case_negation", "hinglish_negation", "explicit_denial_of_being_threatened",
    "fear", "hinglish_fear", "fear_without_threat", "fear_without_an_actual_threat",
    "non_threat_advice", "ambiguous_non_threat", "ambiguous_context_dependent",
    "other_person_threat", "mention_of_threats_to_other_people", "legal_stress",
}


def _prf(y, yhat, average, labels=None):
    p, r, f1, _ = precision_recall_fscore_support(y, yhat, average=average, labels=labels, zero_division=0)
    return float(p), float(r), float(f1)


def _calibration(clf):
    """Temperature + the before/after calibration metrics recorded by training/calibrate.py."""
    cal = {"calibrated": bool(clf.calibrated), "temperature": float(clf.temperature)}
    raw = getattr(clf, "calibration", None) or {}
    for split in ("val", "test"):
        before, after = (raw.get("before") or {}).get(split), (raw.get("after") or {}).get(split)
        if before and after:
            cal[f"{split}_ece_before"] = round(float(before["ece"]), 4)
            cal[f"{split}_ece_after"] = round(float(after["ece"]), 4)
            cal[f"{split}_nll_before"] = round(float(before["nll"]), 4)
            cal[f"{split}_nll_after"] = round(float(after["nll"]), 4)
    if raw.get("fitted_on"):
        cal["fitted_on"] = os.path.basename(str(raw["fitted_on"]))
        cal["n_val"] = raw.get("n_val")
    cal["note"] = ("Temperature scaling on the validation set. A calibrated score is still a model score, "
                   "not a real-world probability of danger.")
    return cal


def text_eval(clf, df, labels, binary):
    preds = clf.predict(df["text"].tolist())
    yhat = np.array([p["label_id"] for p in preds])
    y = df["label"].values.astype(int)
    conf = np.array([p["confidence"] for p in preds])
    avg = "binary" if binary else "macro"
    p, r, f1 = _prf(y, yhat, avg)

    out = {"n": int(len(df)), "accuracy": float(accuracy_score(y, yhat)),
           "balanced_accuracy": float(balanced_accuracy_score(y, yhat)),
           ("precision" if binary else "macro_precision"): p,
           ("recall" if binary else "macro_recall"): r,
           ("f1" if binary else "macro_f1"): f1,
           "confusion_matrix": confusion_matrix(y, yhat, labels=list(range(len(labels)))).tolist(),
           "confusion_matrix_labels": list(labels),
           "mean_confidence": float(conf.mean()),
           "mean_confidence_correct": float(conf[y == yhat].mean()) if (y == yhat).any() else None,
           "mean_confidence_wrong": float(conf[y != yhat].mean()) if (y != yhat).any() else None}

    if binary:
        prob = np.array([q["probs"][labels[1]] for q in preds])
        out["roc_auc"] = float(roc_auc_score(y, prob)) if len(np.unique(y)) == 2 else None

    pc, rc, fc, sup = precision_recall_fscore_support(y, yhat, labels=list(range(len(labels))), zero_division=0)
    out["per_class"] = {n: {"precision": float(pc[i]), "recall": float(rc[i]), "f1": float(fc[i]), "support": int(sup[i])}
                        for i, n in enumerate(labels)}

    d = df.assign(pred=yhat, correct=(yhat == y))
    if "language" in df.columns:
        out["per_language"] = {}
        for lang, g in d.groupby("language"):
            lp, lr, lf = _prf(g["label"], g["pred"], avg)
            out["per_language"][str(lang)] = {"n": int(len(g)), "accuracy": float(g["correct"].mean()),
                                              "precision": lp, "recall": lr, "f1": lf}
    if "category" in df.columns:
        out["per_category"] = {str(cat): {"n": int(len(g)), "correct": int(g["correct"].sum()),
                                          "accuracy": float(g["correct"].mean())}
                               for cat, g in d.groupby("category")}
        hn = d[d["category"].astype(str).isin(HARD_NEGATIVE_CATEGORIES)]
        if len(hn):
            out["hard_negatives"] = {
                "n": int(len(hn)), "accuracy": float(hn["correct"].mean()),
                "false_positive_rate": float((hn[hn["label"] == 0]["pred"] == 1).mean()) if (hn["label"] == 0).any() else None,
                "categories": sorted(hn["category"].astype(str).unique().tolist()),
                "note": "threat-like vocabulary that is NOT a threat (negation, fear, advice, third-party reports)"}
    out["errors"] = [{"text": str(row["text"])[:200], "expected": labels[int(row["label"])],
                      "predicted": labels[int(row["pred"])], "confidence": round(float(conf[i]), 4),
                      **({"category": str(row["category"])} if "category" in df.columns else {}),
                      **({"language": str(row["language"])} if "language" in df.columns else {})}
                     for i, (_, row) in enumerate(d.iterrows()) if not row["correct"]]
    return out


def voice_eval(scorer):
    path = os.path.join(DATA, "voice_features_ravdess.csv")
    if not os.path.exists(path):
        return {"skipped": "training/data/voice_features_ravdess.csv missing (run training/build_voice_features.py)"}
    df = pd.read_csv(path)
    if "f0_cv" not in df.columns:                       # derived features added after the table was built
        df["f0_cv"] = df["f0_std"] / (df["f0_mean"] + 1e-8)
        df["f0_range_rel"] = df["f0_range"] / (df["f0_mean"] + 1e-8)
    test = df[df["split"] == "test"]
    y = test["label"].values.astype(int)
    prob = scorer.score_features(test[scorer.feature_names].values)
    yhat = (prob >= 0.5).astype(int)
    p, r, f1 = _prf(y, yhat, "binary")
    fixed = {"n": int(len(test)), "actors": sorted(map(int, test["actor"].unique())),
             "accuracy": float(accuracy_score(y, yhat)), "balanced_accuracy": float(balanced_accuracy_score(y, yhat)),
             "precision": p, "recall": r, "f1": f1, "roc_auc": float(roc_auc_score(y, prob)),
             "confusion_matrix": confusion_matrix(y, yhat, labels=[0, 1]).tolist(),
             "confusion_matrix_labels": list(C.VOICE_LABELS),
             "per_emotion": {str(e): {"n": int(len(g)), "accuracy": float((g["pred"] == g["label"]).mean())}
                             for e, g in test.assign(pred=yhat).groupby("emotion")} if "emotion" in test.columns else {},
             "note": "the served model was re-fit on all 24 actors, so this split is in-sample; "
                     "speaker_independent_cv below is the honest number"}
    cv = (scorer.metrics or {}).get("cv_by_actor")
    return {"fixed_split_test": fixed,
            "speaker_independent_cv": ({**cv, "protocol": "GroupKFold by actor, every actor held out exactly once"}
                                       if cv else {"missing": "retrain with training/train_voice.py to record CV"}),
            "trained_on": scorer.trained_on, "n_features": len(scorer.feature_names),
            "calibration": {"calibrated": False,
                            "note": "LightGBM probabilities are used as-is; no temperature fitted for the voice signal"},
            "caveat": "RAVDESS is ACTED English speech. Prototype acoustic stress signal, not validated "
                      "real-world victim stress detection; Indian-accent adaptation is the known domain gap."}


def _md(report):
    lines = ["# Perception signal evaluation", "",
             f"generated {report['generated_at_utc']} · schema {report['schema_version']}", ""]
    for name, sig in report["signals"].items():
        if "error" in sig:
            lines += [f"## {name}", f"ERROR: {sig['error']}", ""]
            continue
        lines += [f"## {name}  (`{sig.get('model')}`)"]
        for split in ("test", "challenge"):
            s = sig.get(split)
            if isinstance(s, dict) and "n" in s:
                key = "f1" if "f1" in s else "macro_f1"
                extra = f", ROC-AUC {s['roc_auc']:.3f}" if s.get("roc_auc") else ""
                lines.append(f"- **{split}** (n={s['n']}): accuracy {s['accuracy']:.3f}, {key} {s[key]:.3f}{extra}")
                if s.get("hard_negatives"):
                    lines.append(f"  - hard negatives (n={s['hard_negatives']['n']}): "
                                 f"accuracy {s['hard_negatives']['accuracy']:.3f}")
                if s.get("per_language"):
                    lines.append("  - " + " · ".join(f"{l}: {v['accuracy']:.3f} (n={v['n']})"
                                                     for l, v in s["per_language"].items()))
        if sig.get("fixed_split_test"):
            f, cv = sig["fixed_split_test"], sig.get("speaker_independent_cv") or {}
            lines.append(f"- **fixed by-actor split** (n={f['n']}): accuracy {f['accuracy']:.3f}, ROC-AUC {f['roc_auc']:.3f}")
            if "accuracy" in cv:
                lines.append(f"- **speaker-independent CV**: accuracy {cv['accuracy']:.3f}, "
                             f"balanced {cv.get('balanced_accuracy', float('nan')):.3f}, ROC-AUC {cv.get('roc_auc', float('nan')):.3f}")
        cal = sig.get("calibration") or {}
        if cal.get("calibrated"):
            lines.append(f"- calibration: T={cal['temperature']:.3f}, test ECE "
                         f"{cal.get('test_ece_before', float('nan')):.3f} -> {cal.get('test_ece_after', float('nan')):.3f}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(C.REPO_ROOT / "artifacts" / "signal_eval.json"))
    ap.add_argument("--markdown", action="store_true", help="also print a human-readable summary")
    args = ap.parse_args()

    report = {"generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "schema_version": C.SCHEMA_VERSION,
              "note": "Synthetic/hand-written prototype corpora for text; acted speech (RAVDESS) for voice. "
                      "Held-out numbers on that data, not production validation.",
              "signals": {}}

    try:
        s = get_sentiment()
        report["signals"]["sentiment"] = {
            "model": s.name, "task": "3-class distress level", "labels": C.SENTIMENT_LABELS,
            "calibration": _calibration(s),
            "test": text_eval(s, pd.read_csv(os.path.join(DATA, "distress_v3_test.csv")), C.SENTIMENT_LABELS, False),
            "challenge": text_eval(s, pd.read_csv(os.path.join(DATA, "distress_challenge_v1.csv")), C.SENTIMENT_LABELS, False)}
    except Exception as e:
        report["signals"]["sentiment"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        t = get_threat()
        report["signals"]["threat"] = {
            "model": t.name, "task": "binary threat / intimidation", "labels": C.THREAT_LABELS,
            "calibration": _calibration(t),
            "test": text_eval(t, pd.read_csv(os.path.join(DATA, "threat_v7_test.csv")), C.THREAT_LABELS, True),
            "challenge": text_eval(t, pd.read_csv(os.path.join(DATA, "threat_challenge_v1.csv")), C.THREAT_LABELS, True)}
    except Exception as e:
        report["signals"]["threat"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        v = get_voice()
        report["signals"]["voice"] = {"model": v.name, "task": "binary acoustic stress",
                                      "labels": C.VOICE_LABELS, **voice_eval(v)}
    except Exception as e:
        report["signals"]["voice"] = {"error": f"{type(e).__name__}: {e}"}

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(report, open(args.out, "w"), indent=2)

    sent = report["signals"].get("sentiment", {})
    if "test" in sent:
        json.dump({"signal": "sentiment", "model": sent["model"],
                   "test": {k: sent["test"][k] for k in ("n", "accuracy", "macro_f1")},
                   "per_language": sent["test"].get("per_language", {}),
                   "per_class": sent["test"].get("per_class", {})},
                  open(os.path.join(os.path.dirname(args.out), "signal_sentiment_f1.json"), "w"), indent=2)

    summary = {}
    for k, v in report["signals"].items():
        if "error" in v:
            summary[k] = {"error": v["error"]}
            continue
        row = {"model": v.get("model")}
        for split in ("test", "challenge"):
            if isinstance(v.get(split), dict) and "n" in v[split]:
                row[split] = {m: round(v[split][m], 4) for m in ("n", "accuracy", "f1", "macro_f1", "roc_auc")
                              if v[split].get(m) is not None}
        if v.get("speaker_independent_cv", {}).get("accuracy"):
            row["speaker_independent_cv"] = {m: round(v["speaker_independent_cv"][m], 4)
                                             for m in ("accuracy", "balanced_accuracy", "f1", "roc_auc")
                                             if v["speaker_independent_cv"].get(m) is not None}
        summary[k] = row
    print(json.dumps(summary, indent=2))
    if args.markdown:
        print("\n" + _md(report))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
