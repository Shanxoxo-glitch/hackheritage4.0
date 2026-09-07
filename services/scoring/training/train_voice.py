"""
Train the voice-stress signal: librosa features -> LightGBM.

  PYTHONPATH=. bash   training/download_ravdess.sh                       # ~208 MB, Zenodo, CC BY-NC-SA
  PYTHONPATH=. python training/build_voice_features.py --source ravdess  # 1056 clips, split BY ACTOR
  PYTHONPATH=. python training/train_voice.py --source ravdess
  PYTHONPATH=. python training/train_voice.py --source ravdess --extra-features-csv indic_adapt.csv

Protocol (RAVDESS)
  1. fixed by-actor split (1-18 / 19-21 / 22-24): early-stop on val, report test (transparency)
  2. GroupKFold(6) by actor over all clips = every actor held out once  (headline number)
  3. final served model = same config re-fit on all actors (+ any --extra-features-csv rows)

--extra-features-csv: additional labelled feature rows (same columns as build_voice_features.py
output, e.g. Indian-accent clips from AI4Bharat Svarah / IndicVoices labelled for stress) appended
to training. Western acted-speech corpora alone are a known domain gap; this is the adaptation hook.

Outputs (in SCORING_MODELS_DIR):
  voice_stress_<source>.joblib      lightgbm-free numpy bundle used by the API (trees + feature order)
  voice_lgbm_<source>.pkl           full sklearn LGBMClassifier (analysis only)
  voice_feature_order_<source>.json feature order the API must reproduce
  voice_metrics_<source>.json
"""
import argparse
import datetime as dt
import json
import os
import sys

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix,
                             precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import GroupKFold

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.config import MODELS_DIR, VOICE_LABELS  # noqa: E402
from app.tree_eval import predict_proba as np_predict_proba  # noqa: E402
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402

META = {"file", "actor", "emotion", "intensity", "label", "split", "label_name"}
PARAMS = dict(n_estimators=600, learning_rate=0.03, num_leaves=15, min_child_samples=10,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
              class_weight="balanced", random_state=42, verbose=-1)
N_FOLDS = 6


def add_derived(df):
    if "f0_cv" not in df.columns:
        df["f0_cv"] = df["f0_std"] / (df["f0_mean"] + 1e-8)
    if "f0_range_rel" not in df.columns:
        df["f0_range_rel"] = df["f0_range"] / (df["f0_mean"] + 1e-8)
    return df


def metrics(y, p):
    yhat = (p >= 0.5).astype(int)
    pr, rc, f1, _ = precision_recall_fscore_support(y, yhat, average="binary", zero_division=0)
    out = {"accuracy": float(accuracy_score(y, yhat)), "balanced_accuracy": float(balanced_accuracy_score(y, yhat)),
           "precision": float(pr), "recall": float(rc), "f1": float(f1)}
    if len(np.unique(y)) == 2:
        out["roc_auc"] = float(roc_auc_score(y, p))
    return out


def fmt(d):
    return "  ".join(f"{k}={v:.4f}" for k, v in d.items() if isinstance(v, float))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["ravdess", "synthetic"], required=True)
    ap.add_argument("--features-csv", default=None)
    ap.add_argument("--extra-features-csv", action="append", default=[])
    ap.add_argument("--no-mlflow", action="store_true")
    args = ap.parse_args()

    df = add_derived(pd.read_csv(args.features_csv or f"training/data/voice_features_{args.source}.csv"))
    extra = pd.concat([add_derived(pd.read_csv(p)) for p in args.extra_features_csv], ignore_index=True) \
        if args.extra_features_csv else None
    feats = [c for c in df.columns if c not in META]
    parts = {s: df[df["split"] == s] for s in ("train", "val", "test")}
    X = {s: parts[s][feats].values for s in parts}
    y = {s: parts[s]["label"].values.astype(int) for s in parts}
    if extra is not None:
        X["train"] = np.vstack([X["train"], extra[feats].values])
        y["train"] = np.concatenate([y["train"], extra["label"].values.astype(int)])
    print(f"features={len(feats)}  train={len(y['train'])} val={len(y['val'])} test={len(y['test'])}"
          + (f"  (+{len(extra)} adaptation rows)" if extra is not None else ""))

    model = lgb.LGBMClassifier(**PARAMS)
    model.fit(X["train"], y["train"], eval_set=[(X["val"], y["val"])], eval_metric="binary_logloss",
              callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)])
    best_iter = int(model.best_iteration_ or PARAMS["n_estimators"])
    res = {s: metrics(y[s], model.predict_proba(X[s])[:, 1]) for s in ("val", "test")}
    cm = confusion_matrix(y["test"], (model.predict_proba(X["test"])[:, 1] >= 0.5).astype(int), labels=[0, 1])
    print(f"\n[1] FIXED SPLIT  best_iteration={best_iter}")
    for s in ("val", "test"):
        print(f"    {s.upper():5s} {fmt(res[s])}")
    per_emotion_split = {}
    if args.source == "ravdess":
        t = parts["test"].assign(pred=(model.predict_proba(X["test"])[:, 1] >= 0.5).astype(int))
        per_emotion_split = {e: float((g["pred"] == g["label"]).mean()) for e, g in t.groupby("emotion")}

    cv, trained_on, final = None, "train_split", model
    if args.source == "ravdess":
        Xall, yall, gall = df[feats].values, df["label"].values.astype(int), df["actor"].values
        cfg = dict(PARAMS, n_estimators=best_iter)
        prob, fold_bal = np.zeros(len(df)), []
        for tr, te in GroupKFold(n_splits=N_FOLDS).split(Xall, yall, gall):
            Xtr, ytr = Xall[tr], yall[tr]
            if extra is not None:
                Xtr, ytr = np.vstack([Xtr, extra[feats].values]), np.concatenate([ytr, extra["label"].values.astype(int)])
            m = lgb.LGBMClassifier(**cfg).fit(Xtr, ytr)
            prob[te] = m.predict_proba(Xall[te])[:, 1]
            fold_bal.append(balanced_accuracy_score(yall[te], (prob[te] >= 0.5).astype(int)))
        pred = (prob >= 0.5).astype(int)
        cv = {**metrics(yall, prob), "bal_acc_fold_std": float(np.std(fold_bal)), "n_folds": N_FOLDS,
              "n_clips": int(len(df)), "n_actors": int(df["actor"].nunique()),
              "per_emotion": {e: float((g["pred"] == g["label"]).mean()) for e, g in df.assign(pred=pred).groupby("emotion")},
              "confusion": confusion_matrix(yall, pred, labels=[0, 1]).tolist()}
        print(f"\n[2] SPEAKER-INDEPENDENT CV  GroupKFold({N_FOLDS}) by actor\n    {fmt(cv)}")
        print("    acc by emotion:", {k: round(v, 2) for k, v in cv["per_emotion"].items()})
        Xfin, yfin = Xall, yall
        if extra is not None:
            Xfin, yfin = np.vstack([Xall, extra[feats].values]), np.concatenate([yall, extra["label"].values.astype(int)])
        final = lgb.LGBMClassifier(**cfg).fit(Xfin, yfin)
        trained_on = "ravdess_all_24_actors" + ("+adaptation" if extra is not None else "")
        print(f"\n[3] final model re-fit on {len(yfin)} clips ({best_iter} trees)")

    imp = sorted(zip(feats, final.feature_importances_), key=lambda x: -x[1])[:15]
    print("\nTop features:", ", ".join(f"{f}({int(i)})" for f, i in imp))

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    out = MODELS_DIR / f"voice_stress_{args.source}.joblib"
    booster = final.booster_
    dump = booster.dump_model(num_iteration=best_iter)
    diff = float(np.abs(np_predict_proba(dump, X["test"])[:, 1] - final.predict_proba(X["test"])[:, 1]).max())
    print(f"numpy tree evaluator vs LightGBM: max |diff| = {diff:.2e}")
    assert diff < 1e-5, "numpy evaluator disagrees with LightGBM - refusing to save"
    all_metrics = {"fixed_split": res, "cv_by_actor": cv}
    joblib.dump({"model_dump": dump, "model_string": booster.model_to_string(num_iteration=best_iter),
                 "inference": "numpy_tree_eval", "feature_names": feats, "label_names": VOICE_LABELS,
                 "source": args.source, "trained_on": trained_on, "metrics": all_metrics, "sr": 16000,
                 "best_iteration": best_iter,
                 "trained_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}, out)
    joblib.dump(final, MODELS_DIR / f"voice_lgbm_{args.source}.pkl")
    json.dump({"feature_order": feats, "sr": 16000, "extractor": "app.voice_features.extract_features"},
              open(MODELS_DIR / f"voice_feature_order_{args.source}.json", "w"), indent=2)
    meta = {"signal": "voice", "source": args.source, "trained_on": trained_on, "params": PARAMS,
            "best_iteration": best_iter, "n_features": len(feats), "sizes": {s: int(len(y[s])) for s in y},
            "metrics": all_metrics, "test_confusion": cm.tolist(), "test_accuracy_by_emotion": per_emotion_split,
            "top_features": [[f, int(i)] for f, i in imp]}
    json.dump(meta, open(MODELS_DIR / f"voice_metrics_{args.source}.json", "w"), indent=2)

    enabled = not args.no_mlflow
    with mlflow_run("voice", f"train_voice_{args.source}",
                    params={**PARAMS, "source": args.source, "n_features": len(feats), "trained_on": trained_on,
                            "adaptation_rows": 0 if extra is None else len(extra)},
                    tags={"signal": "voice", "stage": "train", "synthetic": str(args.source == "synthetic")},
                    enabled=enabled):
        log_metrics(res["val"], prefix="final_val_", enabled=enabled)
        log_metrics(res["test"], prefix="test_", enabled=enabled)
        if cv:
            log_metrics(cv, prefix="cv_", enabled=enabled)
        log_dict(meta, "metrics.json", enabled=enabled)
    print("\nsaved", out)


if __name__ == "__main__":
    main()
