"""v1 forecaster: logreg over the SAME 5 features the service uses.
Run:  python -m training.train_forecaster
Gate: holdout AUC >= 0.75."""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from app.forecast import _features

N, HORIZON = 30_000, 7
rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parents[1] / "artifacts"

X, y = [], []
for _ in range(N):
    escalating = rng.random() < 0.30
    start = rng.uniform(0.1, 0.5)
    drift = rng.uniform(0.02, 0.09) if escalating else rng.uniform(-0.03, 0.02)
    L = int(rng.integers(6, 28))
    hist = np.clip(start + np.cumsum(rng.normal(drift, 0.05, L)), 0.02, 0.98).tolist()
    future = np.clip(hist[-1] + np.cumsum(rng.normal(drift, 0.05, HORIZON)), 0.02, 0.98)
    X.append(_features(hist).tolist())
    y.append(1 if future.max() >= 0.8 else 0)

X, y = np.array(X), np.array(y)
cut = int(0.8 * N)
model = LogisticRegression(max_iter=2000).fit(X[:cut], y[:cut])
auc = float(roc_auc_score(y[cut:], model.predict_proba(X[cut:])[:, 1]))

OUT.mkdir(exist_ok=True)
joblib.dump(model, OUT / "forecaster.pkl")
(OUT / "forecaster_meta.json").write_text(json.dumps({
    "model": "logreg-v1", "features": 5, "horizon_days": HORIZON,
    "train_n": cut, "holdout_auc": round(auc, 4),
    "gate": "holdout_auc >= 0.75", "passed": auc >= 0.75,
    "trained_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"holdout AUC = {auc:.3f}  ({'PASS' if auc >= 0.75 else 'FAIL'})")
print(f"saved -> {OUT / 'forecaster.pkl'}")
