"""v3 forecaster trainer: 25-model bootstrap ensemble + Platt calibration
+ linear attribution. Gates: holdout AUC >= 0.75 raw AND calibrated.
v3: the .pkl is written ONLY on pass (a failed gate can never be served);
artifact now carries horizon_days + feature names for the serving wrapper.
Run:  python -m training.train_forecaster
Out:  artifacts/forecaster.pkl (on pass) + artifacts/forecaster_meta.json"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from app.forecast import FEATURES, _features

N, HORIZON, B = 30_000, 7, 25
GATE = 0.75
rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parents[1] / "artifacts"
OUT.mkdir(parents=True, exist_ok=True)

# ---- synthetic data: escalating vs stable regimes ---------------------------
X, y = [], []
for _ in range(N):
    escalating = rng.random() < 0.30
    start = rng.uniform(0.1, 0.5)
    drift = rng.uniform(0.02, 0.09) if escalating else rng.uniform(-0.03, 0.02)
    L = int(rng.integers(6, 28))
    hist = np.clip(start + np.cumsum(rng.normal(drift, 0.05, L)),
                   0.02, 0.98).tolist()
    future = np.clip(hist[-1] + np.cumsum(rng.normal(drift, 0.05, HORIZON)),
                     0.02, 0.98)
    feats = list(_features(hist))               # positional (v2 string-index bug)
    assert len(feats) == len(FEATURES)
    X.append(feats)
    y.append(1 if future.max() >= 0.8 else 0)

X, y = np.array(X), np.array(y, dtype=int)

idx = rng.permutation(N)
tr, ca, ho = (idx[:int(.6 * N)], idx[int(.6 * N):int(.8 * N)],
              idx[int(.8 * N):])


def ens_probs(rows: np.ndarray) -> np.ndarray:
    """Mean raw member prob -- EXACTLY the serving point estimate."""
    return np.column_stack([m.predict_proba(rows)[:, 1]
                            for m in models]).mean(axis=1)


models = []
for _ in range(B):
    boot = rng.choice(tr, size=len(tr), replace=True)  # one draw, X and y together
    models.append(LogisticRegression(max_iter=2000).fit(X[boot], y[boot]))

p_cal = ens_probs(X[ca])
calibrator = LogisticRegression(max_iter=2000).fit(p_cal.reshape(-1, 1), y[ca])

attr = LogisticRegression(max_iter=2000).fit(X[tr], y[tr])
coefs = {k: float(c) for k, c in zip(FEATURES, attr.coef_[0])}
feature_means = {k: float(v) for k, v in zip(FEATURES, X[tr].mean(axis=0))}

# ---- holdout gates -----------------------------------------------------------
p_raw = ens_probs(X[ho])
p_cal_ho = calibrator.predict_proba(p_raw.reshape(-1, 1))[:, 1]
auc_raw = float(roc_auc_score(y[ho], p_raw))
auc_cal = float(roc_auc_score(y[ho], p_cal_ho))
brier = float(brier_score_loss(y[ho], p_cal_ho))
passed = auc_raw >= GATE and auc_cal >= GATE

if passed:                     # gate blocks serving: no pkl on failure
    joblib.dump({"version": "ens25-cal-v3", "models": models,
                 "calibrator": calibrator, "feature_names": list(FEATURES),
                 "feature_means": feature_means, "coefs": coefs,
                 "horizon_days": HORIZON}, OUT / "forecaster.pkl")

(OUT / "forecaster_meta.json").write_text(json.dumps({
    "model": "ens25-cal-v3", "ensemble_size": B, "features": list(FEATURES),
    "horizon_days": HORIZON, "positive_rate": round(float(y.mean()), 4),
    "train_n": int(len(tr)), "cal_n": int(len(ca)), "holdout_n": int(len(ho)),
    "holdout_auc_raw": round(auc_raw, 4),
    "holdout_auc_calibrated": round(auc_cal, 4),
    "holdout_brier": round(brier, 4),
    "gate": "holdout AUC >= 0.75 (raw AND calibrated)", "passed": passed,
    "artifact_written": passed,
    "trained_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"holdout AUC raw={auc_raw:.3f} calibrated={auc_cal:.3f} "
      f"brier={brier:.3f} ({'PASS' if passed else 'FAIL'})")
print(f"saved -> {OUT / 'forecaster_meta.json'}"
      + (f" + {OUT / 'forecaster.pkl'}" if passed else " (pkl withheld: gate failed)"))
sys.exit(0 if passed else 1)
