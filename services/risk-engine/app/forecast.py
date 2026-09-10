"""p(escalation within 7 days). v1: logistic model + heuristic fallback."""
from pathlib import Path

import joblib
import numpy as np

from app.schemas import ForecastRequest, ForecastResult

MODEL = None
MODEL_VERSION = "heuristic-v0"
BASE_RATE = 0.10
ARTIFACT = Path(__file__).resolve().parents[1] / "artifacts" / "forecaster.pkl"
STAGE_MULTIPLIER = {"intake": 1.0, "fir_filed": 1.15, "investigation": 1.10,
                    "chargesheet": 1.25, "trial": 1.20, "judgment": 0.80}


def load_model() -> bool:
    global MODEL, MODEL_VERSION
    if ARTIFACT.exists():
        MODEL = joblib.load(ARTIFACT)
        MODEL_VERSION = "logreg-v1"
        return True
    return False


def _features(history: list[float]) -> np.ndarray:
    h = np.array(history[-14:], dtype=np.float32)
    if len(h) == 0:
        h = np.array([0.5], dtype=np.float32)
    pad = np.full(14 - len(h), h[0], dtype=np.float32)
    w = np.concatenate([pad, h])
    slope = w[-3:].mean() - w[:3].mean() if len(w) >= 6 else 0.0
    return np.array([w[-1], w.mean(), slope,
                     w.max() - w.min(), (w > 0.75).mean()], dtype=np.float32)


def forecast(req: ForecastRequest) -> ForecastResult:
    if len(req.score_history) < 2:
        return ForecastResult(p_escalation=BASE_RATE, horizon_days=7,
                              model_version=MODEL_VERSION)
    f = _features(req.score_history)
    if MODEL is not None:
        p = float(MODEL.predict_proba(f.reshape(1, -1))[0][1])
    else:
        p = float(np.clip(BASE_RATE + f[2] * 0.5 + f[4] * 0.35, 0.02, 0.97))
    p *= STAGE_MULTIPLIER.get(req.legal_stage or "", 1.0)
    return ForecastResult(p_escalation=round(min(p, 0.97), 3), horizon_days=7,
                          model_version=MODEL_VERSION)
