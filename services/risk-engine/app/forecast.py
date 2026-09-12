"""p(escalation within horizon days). v3.

v2 -> v3:
- FEATURES exported (fixes trainer import crash; train/serve single source)
- artifact served through EnsembleForecaster (fixes dict.predict_proba crash)
- stage effect applied in LOG-ODDS space (values = ln of v1 multipliers):
  bounded by construction, no clamp distortion of calibrated probabilities
- p10/p90 + drivers populated (schema promised them, tests assert ordering)
- history sanitized (NaN/inf/out-of-range) instead of trusted
- case-insensitive legal_stage (v2 silently ignored "Trial" vs "trial")
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import structlog

from app.schemas import ForecastRequest, ForecastResult

log = structlog.get_logger(__name__)

# single source of truth for feature order -- trainer imports this
FEATURES = ("last", "mean14", "slope", "range14", "frac_high")
WINDOW = 14
MIN_HISTORY = 2
BASE_RATE = 0.10
P_CAP = 0.97
HORIZON_DAYS = 7
ARTIFACT = Path(__file__).resolve().parents[1] / "artifacts" / "forecaster.pkl"

# ln() of the v1 multipliers: same effect, but in calibrated space
STAGE_LOGODDS = {"intake": 0.0, "fir_filed": 0.140, "investigation": 0.095,
                 "chargesheet": 0.223, "trial": 0.182, "judgment": -0.223}

_EPS = 1e-6


def _logit(p: float) -> float:
    p = min(max(p, _EPS), 1.0 - _EPS)
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class EnsembleForecaster:
    """Serves the dict artifact written by training.train_forecaster.
    Exposes a sklearn-style predict_proba so call sites stay unchanged."""

    def __init__(self, artifact: dict):
        names = tuple(artifact["feature_names"])
        if names != FEATURES:
            raise ValueError(f"artifact/serving feature skew: {names} != {FEATURES}")
        self.version = str(artifact["version"])
        self.models = artifact["models"]
        self.calibrator = artifact["calibrator"]
        self.horizon_days = int(artifact.get("horizon_days", HORIZON_DAYS))
        coefs, means = artifact.get("coefs", {}), artifact.get("feature_means", {})
        self._coef = np.array([float(coefs.get(k, 0.0)) for k in FEATURES])
        self._mean = np.array([float(means.get(k, 0.0)) for k in FEATURES])

    def _member_raw(self, X) -> np.ndarray:                       # (n, B)
        X2 = np.atleast_2d(np.asarray(X, dtype=np.float64))
        return np.column_stack([m.predict_proba(X2)[:, 1] for m in self.models])

    def predict_proba(self, X) -> np.ndarray:                     # (n, 2)
        # point estimate = calibrator(mean raw member prob): EXACTLY what the
        # trainer computes -> no train/serve skew
        p = self.calibrator.predict_proba(
            self._member_raw(X).mean(axis=1).reshape(-1, 1))[:, 1]
        return np.column_stack([1.0 - p, p])

    def interval(self, X) -> tuple[float, float]:
        """p10/p90 from ensemble spread (single row)."""
        raw = self._member_raw(X)
        per_member = np.column_stack([
            self.calibrator.predict_proba(raw[:, [i]])[:, 1]
            for i in range(raw.shape[1])])
        q = np.quantile(per_member, [0.10, 0.90], axis=1)
        return float(q[0][0]), float(q[1][0])

    def drivers(self, x) -> list[str]:
        """Log-odds attribution: coef * (x - train_mean), top positive."""
        contrib = self._coef * (np.asarray(x, dtype=np.float64) - self._mean)
        ranked = sorted(zip(FEATURES, contrib), key=lambda kv: kv[1], reverse=True)
        return [k for k, c in ranked[:2] if c > 0] or ["baseline"]


MODEL: Optional[EnsembleForecaster] = None
MODEL_VERSION = "heuristic-v0"


def load_model() -> bool:
    """Load + validate artifact; ANY failure -> safe heuristic fallback."""
    global MODEL, MODEL_VERSION
    if not ARTIFACT.exists():
        log.warning("forecaster_artifact_missing", path=str(ARTIFACT))
        return False
    try:
        MODEL = EnsembleForecaster(joblib.load(ARTIFACT))
    except Exception as exc:                    # noqa: BLE001 - degrade, never crash
        log.error("forecaster_artifact_rejected", error=str(exc))
        MODEL = None
    if MODEL is None:
        MODEL_VERSION = "heuristic-v0"
        return False
    MODEL_VERSION = MODEL.version
    log.info("forecaster_loaded", version=MODEL_VERSION,
             horizon_days=MODEL.horizon_days, n_models=len(MODEL.models))
    return True


def _features(history: list[float]) -> np.ndarray:
    """Same vector as v2 (model compatibility), but NaN/inf/range-safe."""
    clean = [min(max(float(v), 0.0), 1.0)
             for v in history if math.isfinite(float(v))][-WINDOW:]
    if not clean:
        clean = [0.5]
    h = np.asarray(clean, dtype=np.float32)
    pad = np.full(WINDOW - len(h), h[0], dtype=np.float32)
    w = np.concatenate([pad, h])                # always length WINDOW
    slope = float(w[-3:].mean() - w[:3].mean())
    return np.array([w[-1], w.mean(), slope,
                     w.max() - w.min(), (w > 0.75).mean()], dtype=np.float32)


def forecast(req: ForecastRequest) -> ForecastResult:
    horizon = MODEL.horizon_days if MODEL is not None else HORIZON_DAYS
    if len(req.score_history) < MIN_HISTORY:
        return ForecastResult(p_escalation=BASE_RATE, horizon_days=horizon,
                              model_version=MODEL_VERSION,
                              drivers=["insufficient_history"])

    f = _features(req.score_history)
    stage = (req.legal_stage or "").strip().lower()
    stage_effect = STAGE_LOGODDS.get(stage, 0.0)
    if stage and stage not in STAGE_LOGODDS:
        log.info("unknown_legal_stage", stage=stage)   # v2 silently defaulted

    p10 = p90 = None
    if MODEL is not None:
        X = f.reshape(1, -1)
        p = float(MODEL.predict_proba(X)[0][1])
        p10, p90 = MODEL.interval(X)
        drivers = MODEL.drivers(f)
    else:
        p = float(np.clip(BASE_RATE + f[2] * 0.5 + f[4] * 0.35, 0.02, 0.97))
        drivers = ([n for n, hit in (("trend_up", f[2] > 0.05),
                                     ("high_scores", f[4] > 0.0)) if hit]
                   or ["baseline"])

    if stage_effect != 0.0:
        p = _sigmoid(_logit(p) + stage_effect)
        if p10 is not None:                      # shift the whole interval too
            p10 = _sigmoid(_logit(p10) + stage_effect)
            p90 = _sigmoid(_logit(p90) + stage_effect)
        drivers.append(f"legal_stage:{stage}")

    out = ForecastResult(
        p_escalation=round(min(p, P_CAP), 3), horizon_days=horizon,
        model_version=MODEL_VERSION,
        p10=round(min(p10, P_CAP), 3) if p10 is not None else None,
        p90=round(min(p90, P_CAP), 3) if p90 is not None else None,
        drivers=drivers[:3])
    log.info("forecast", case_id=req.case_id, p=out.p_escalation,
             p10=out.p10, p90=out.p90, stage=stage, drivers=out.drivers)
    return out
