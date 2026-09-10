"""
Speaker-robustness experiment for the RAVDESS voice-stress model.

The fixed 3-actor test split is high-variance and showed a speaker shift
(59 % acc, over-predicting STRESSED). Here every actor is a held-out test
speaker exactly once (GroupKFold by actor, 6 folds x 4 actors) and we compare:
  feature sets : all | speaker_robust (no absolute pitch, no MFCC means) | dynamics_only
  params       : default | regularized (shallower trees, fewer features per tree)
  normalisation: none | per_speaker_z (z-score each feature within the speaker's own clips
                 = 'compare against the victim's own baseline', which the longitudinal
                 product design allows; not available for a single cold-start clip)

  python src/voice/experiment_speaker_robust.py
"""
import json
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from training.mlflow_utils import log_dict, log_metrics, mlflow_run  # noqa: E402

META = {"file", "actor", "emotion", "intensity", "label", "split", "label_name"}
ABS_PITCH = {"f0_mean", "f0_min", "f0_max", "f0_median", "f0_range", "f0_std"}
MFCC_MEAN = {f"mfcc{i}_mean" for i in range(20)}

PARAM_SETS = {
    "default": dict(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=10,
                    subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                    class_weight="balanced", random_state=42, verbose=-1),
    "regularized": dict(n_estimators=300, learning_rate=0.05, num_leaves=7, min_child_samples=30,
                        subsample=0.8, subsample_freq=1, colsample_bytree=0.5, reg_lambda=5.0,
                        class_weight="balanced", random_state=42, verbose=-1),
}


def add_derived(df):
    if "f0_cv" not in df.columns:
        df["f0_cv"] = df["f0_std"] / (df["f0_mean"] + 1e-8)
    if "f0_range_rel" not in df.columns:
        df["f0_range_rel"] = df["f0_range"] / (df["f0_mean"] + 1e-8)
    return df


def feature_sets(df):
    all_feats = [c for c in df.columns if c not in META]
    robust = [f for f in all_feats if f not in ABS_PITCH and f not in MFCC_MEAN]
    dynamics = [f for f in robust if not f.startswith("mfcc")]
    return {"all": all_feats, "speaker_robust": robust, "dynamics_only": dynamics}


def per_speaker_z(df, cols):
    return df.groupby("actor")[cols].transform(lambda s: (s - s.mean()) / (s.std() + 1e-8)).values


def main():
    df = add_derived(pd.read_csv("training/data/voice_features_ravdess.csv"))
    y, groups = df["label"].values.astype(int), df["actor"].values
    gkf = GroupKFold(n_splits=6)
    rows = []
    for fs_name, cols in feature_sets(df).items():
        for norm in ("none", "per_speaker_z"):
            X = df[cols].values if norm == "none" else per_speaker_z(df, cols)
            for p_name, params in PARAM_SETS.items():
                prob = np.zeros(len(df))
                fold_bal = []
                for tr, te in gkf.split(X, y, groups):
                    m = lgb.LGBMClassifier(**params).fit(X[tr], y[tr])
                    prob[te] = m.predict_proba(X[te])[:, 1]
                    fold_bal.append(balanced_accuracy_score(y[te], (prob[te] >= 0.5).astype(int)))
                pred = (prob >= 0.5).astype(int)
                emo = df.assign(pred=pred).groupby("emotion").apply(
                    lambda g: float((g["pred"] == g["label"]).mean()), include_groups=False).to_dict()
                row = {"features": fs_name, "n_features": len(cols), "norm": norm, "params": p_name,
                       "accuracy": accuracy_score(y, pred), "balanced_accuracy": balanced_accuracy_score(y, pred),
                       "bal_acc_fold_std": float(np.std(fold_bal)), "f1": f1_score(y, pred),
                       "roc_auc": roc_auc_score(y, prob), "per_emotion": emo}
                rows.append(row)
                print(f"{fs_name:15s} n={len(cols):3d} {norm:13s} {p_name:11s} "
                      f"acc={row['accuracy']:.3f} bal={row['balanced_accuracy']:.3f}±{row['bal_acc_fold_std']:.3f} "
                      f"f1={row['f1']:.3f} auc={row['roc_auc']:.3f}  "
                      + " ".join(f"{k[:4]}={v:.2f}" for k, v in emo.items()))

    rows.sort(key=lambda r: -r["balanced_accuracy"])
    print("\nRANKED by balanced accuracy (24 actors, leave-4-actors-out CV):")
    for r in rows:
        print(f"  {r['balanced_accuracy']:.3f}  auc={r['roc_auc']:.3f}  {r['features']}/{r['norm']}/{r['params']}")
    os.makedirs("evaluation", exist_ok=True)
    json.dump(rows, open("evaluation/voice_speaker_robustness.json", "w"), indent=2)

    with mlflow_run("voice_stress", "experiment_speaker_robust_cv",
                    params={"cv": "GroupKFold(6) by actor", "n_clips": len(df), "n_configs": len(rows)},
                    tags={"task": "voice_stress", "stage": "experiment"}):
        for r in rows:
            key = f"{r['features']}__{r['norm']}__{r['params']}"
            log_metrics({f"{key}_bal_acc": r["balanced_accuracy"], f"{key}_auc": r["roc_auc"]})
        log_dict(rows, "voice_speaker_robustness.json")
    print("\nSaved evaluation/voice_speaker_robustness.json")


if __name__ == "__main__":
    main()
