"""v2 forecaster trainer: 25-model bootstrap ensemble + Platt calibration
+ linear attribution. Holdout gates: AUC >= 0.75 raw and calibrated.
Run:  python -m training.train_forecaster
Out:  artifacts/forecaster.pkl + artifacts/forecaster_meta.json"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from app.forecast import FEATURES, _features

N, HORIZON, B = 30_000, 7, 25
rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parents[1] / "artifacts"

# ---- synthetic data: escalating vs stable regimes --------------------------
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
    X.append([_features(hist)[k] for k in FEATURES])
    y.append(1 if future.max() >= 0.8 else 0)

X, y = np.array(X), np.array(y, dtype=int)
assert len(X) == len(y), "feature/label mismatch"

# ---- splits: train (bootstrap) / calibration (Platt) / holdout (gates) -----
idx = rng.permutation(N)
tr, ca, ho = (idx[:int(.6 * N)], idx[int(.6 * N):int(.8 * N)],
              idx[int(.8 * N):])

# ---- FIXED: one bootstrap draw, used for BOTH X and y ----------------------
models = []
for _ in range(B):
    boot = rng.choice(tr, size=len(tr), replace=True)
    models.append(LogisticRegression(max_iter=2000).fit(X[boot], y[boot]))
# -----------------------------------------------------------------------------


def ens_probs(rows: np.ndarray) -> np.ndarray:
    """Mean probability across the ensemble. rows = 2D feature matrix."""
    return np.column_stack([m.predict_proba(rows)[:, 1]
                            for m in models]).mean(axis=1)


# ---- Platt calibration on the cal split (makes p a real probability) --------
p_cal = ens_probs(X[ca])
calibrator = LogisticRegression(max_iter=2000).fit(p_cal.reshape(-1, 1), y[ca])

# ---- linear attribution model (what drives predictions, on average) ---------
attr = LogisticRegression(max_iter=2000).fit(X[tr], y[tr])
coefs = {k: float(c) for k, c in zip(FEATURES, attr.coef_[0])}
feature_means = {k: float(v) for k, v in zip(FEATURES, X[tr].mean(axis=0))}

# ---- holdout gates -----------------------------------------------------------
p_raw = ens_probs(X[ho])
p_cal_ho = calibrator.predict_proba(p_raw.reshape(-1, 1))[:, 1]
auc_raw = float(roc_auc_score(y[ho], p_raw))
auc_cal = float(roc_auc_score(y[ho], p_cal_ho))
brier = float(brier_score_loss(y[ho], p_cal_ho))

OUT.mkdir(exist_ok=True)
joblib.dump({"version": "ens25-cal-v2", "models": models,
             "calibrator": calibrator, "feature_names": FEATURES,
             "feature_means": feature_means, "coefs": coefs},
            OUT / "forecaster.pkl")
(OUT / "forecaster_meta.json").write_text(json.dumps({
    "model": "ens25-cal-v2", "ensemble_size": B, "features": FEATURES,
    "horizon_days": HORIZON,
    "train_n": int(len(tr)), "cal_n": int(len(ca)),
    "holdout_n": int(len(ho)),
    "holdout_auc_raw": round(auc_raw, 4),
    "holdout_auc_calibrated": round(auc_cal, 4),
    "holdout_brier": round(brier, 4),
    "gate": "holdout_auc >= 0.75", "passed": auc_cal >= 0.75,
    "trained_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"holdout AUC raw={auc_raw:.3f} calibrated={auc_cal:.3f} "
      f"brier={brier:.3f} ({'PASS' if auc_cal >= 0.75 else 'FAIL'})")
print(f"saved -> {OUT / 'forecaster.pkl'}")
