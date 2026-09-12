"""Novelty 1 v3 -- Bayesian linear-Gaussian fusion (model unchanged; see v2
header). v2 -> v3:
- sensor registry kills the name/attr if-chains (_collect + explain share it)
- detector_noise.json cached with mtime check (v2 parsed it on EVERY request)
- chi^2 is now truly "prior excluded": computed around the SENSOR-ONLY mean
  (v2 used the posterior mean -- contradicting its own docstring -- and could
  flag conflict for a single sensor; a lone sensor now yields chi2=0)
- engagement is now reportable as stale (v2 forgot it in the stale list)
- fuse(..., noise=...) override makes calibration hermetic (no feedback loop
  with the file the calibration script writes)
- unreadable noise file logs a warning instead of a silent except: pass
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import structlog

from app.schemas import FusionRequest, FusionResult

log = structlog.get_logger(__name__)

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
NOISE_FILE = ARTIFACTS / "detector_noise.json"

PRIOR_MU = float(os.getenv("RISK_PRIOR_MU", "0.35"))
PRIOR_SIGMA = float(os.getenv("RISK_PRIOR_SIGMA", "0.45"))
DECAY_LAMBDA = float(os.getenv("RISK_DECAY_LAMBDA", "0.10"))
THREAT_FORCE_AT = float(os.getenv("RISK_THREAT_FORCE_AT", "0.90"))
THREAT_FORCE_FLOOR = 0.80
STALE_BELOW = float(os.getenv("RISK_STALE_BELOW", "0.50"))   # v2: not env-able

DEFAULT_NOISE = {"sentiment": 0.15, "threat": 0.10,
                 "voice_stress": 0.20, "engagement": 0.25}

CHI2_CRIT = {1: 3.84, 2: 5.99, 3: 7.81, 4: 9.49}

# registry: request attr -> value attr. one place to add a sensor.
DIRECT_SENSORS = {"sentiment": "score", "threat": "prob", "voice_stress": "score"}
SENSOR_ORDER = ("sentiment", "threat", "voice_stress", "engagement")

_noise_cache: Optional[tuple[float, dict]] = None      # (mtime, noise)


def _load_noise() -> dict:
    global _noise_cache
    try:
        mtime = NOISE_FILE.stat().st_mtime
    except OSError:
        return dict(DEFAULT_NOISE)
    if _noise_cache is not None and _noise_cache[0] == mtime:
        return dict(_noise_cache[1])
    noise = dict(DEFAULT_NOISE)
    try:
        measured = json.loads(NOISE_FILE.read_text()).get("measured_sigma", {})
        noise.update({k: float(v) for k, v in measured.items()
                      if k in DEFAULT_NOISE})
    except Exception as exc:                    # noqa: BLE001
        log.warning("detector_noise_unreadable", error=str(exc))
    _noise_cache = (mtime, noise)               # cache even the failure (no spam)
    return dict(noise)


def current_noise() -> dict:
    """For /metrics: measured noise if available, else defaults."""
    return _load_noise()


def _engagement_value(eng) -> Optional[float]:
    if eng is None or (eng.messages_last_7d is None
                       and eng.avg_reply_latency_min is None):
        return None
    msgs = max(eng.messages_last_7d or 20, 0)
    lat = max(eng.avg_reply_latency_min or 120.0, 0.0)
    return 0.6 * (1.0 - min(msgs / 40.0, 1.0)) + 0.4 * min(lat / 480.0, 1.0)


def _age_days(observed_at) -> float:
    if observed_at is None:
        return 0.0
    ts = observed_at if observed_at.tzinfo else observed_at.replace(
        tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0)


def _collect(req: FusionRequest, noise: dict):
    """-> {name: (value, decayed_precision)}, stale list."""
    obs, stale = {}, []
    for name, attr in DIRECT_SENSORS.items():
        sig = getattr(req, name, None)
        if sig is None:
            continue
        value = float(getattr(sig, attr))
        decay = math.exp(-DECAY_LAMBDA * _age_days(sig.observed_at))
        if decay < STALE_BELOW:
            stale.append(name)
        sigma = noise.get(name, DEFAULT_NOISE[name])
        obs[name] = (value, decay ** 2 / sigma ** 2)
    eng = _engagement_value(req.engagement)
    if eng is not None:
        decay = math.exp(-DECAY_LAMBDA * _age_days(req.engagement.observed_at))
        if decay < STALE_BELOW:
            stale.append("engagement")            # v2 bug: never reported
        sigma = noise.get("engagement", DEFAULT_NOISE["engagement"])
        obs["engagement"] = (eng, decay ** 2 / sigma ** 2)
    return obs, stale


def fuse(req: FusionRequest, noise: Optional[dict] = None) -> FusionResult:
    noise = noise if noise is not None else _load_noise()
    obs, stale = _collect(req, noise)

    if not obs:
        return FusionResult(
            case_id=req.case_id, composite_score=round(PRIOR_MU, 3),
            confidence=0.0, top_signals=[], label="LOW",
            triggers=["no_signals"], contributions={}, degraded=True,
            posterior_std=round(PRIOR_SIGMA, 4), conflict_chi2=0.0,
            conflict=False, weights={}, stale=[])

    # -- Bayesian update (inverse-variance weights + prior) ------------------
    prior_prec = 1.0 / PRIOR_SIGMA ** 2
    sensor_prec = sum(p for _, p in obs.values())
    total_prec = prior_prec + sensor_prec
    mu = (prior_prec * PRIOR_MU
          + sum(p * v for v, p in obs.values())) / total_prec
    std = 1.0 / math.sqrt(total_prec)

    # -- chi^2 conflict BETWEEN SENSORS ONLY (prior excluded, as documented) --
    if len(obs) > 1:
        sensor_mean = sum(p * v for v, p in obs.values()) / sensor_prec
        chi2 = sum(p * (v - sensor_mean) ** 2 for v, p in obs.values())
        df = len(obs) - 1
        crit = CHI2_CRIT.get(df, df + 2.8 * math.sqrt(2 * df))
        conflict = chi2 > crit
    else:
        chi2, conflict = 0.0, False
    if conflict:
        std *= math.sqrt(max(chi2 / df, 1.0))     # random-effects inflation

    composite = min(max(mu, 0.0), 1.0)
    confidence = min(1.0, max(0.0, 1.0 - 2.0 * std))

    weights = {k: round(p / sensor_prec, 3) for k, (v, p) in obs.items()}
    contributions = {k: round(p * v / sensor_prec, 3)
                     for k, (v, p) in obs.items()}

    # -- threat force rule (kept from v1; policy overrides statistics) --------
    triggers: list[str] = ["signal_conflict"] if conflict else []
    if req.threat is not None and float(req.threat.prob) >= THREAT_FORCE_AT:
        triggers.append("threat_force")
        composite = max(composite, THREAT_FORCE_FLOOR)
        confidence = max(confidence, 0.60)

    top_signals = sorted(contributions, key=contributions.get, reverse=True)[:3]
    label = ("CRITICAL" if composite >= 0.8 or "threat_force" in triggers
             else "HIGH" if composite >= 0.6
             else "ELEVATED" if composite >= 0.4 else "LOW")

    return FusionResult(
        case_id=req.case_id, composite_score=round(composite, 3),
        confidence=round(confidence, 4), top_signals=top_signals,
        label=label, triggers=triggers, contributions=contributions,
        degraded=False, posterior_std=round(std, 4),
        conflict_chi2=round(chi2, 2), conflict=conflict,
        weights=weights, stale=stale)


def fusion_explain(req: FusionRequest) -> dict:
    """Leave-one-out attribution for /v1/explain (feeds TraceView)."""
    base = fuse(req)
    noise = _load_noise()
    out = {"case_id": req.case_id, "composite_score": base.composite_score,
           "confidence": base.confidence, "posterior_std": base.posterior_std,
           "conflict_chi2": base.conflict_chi2, "conflict": base.conflict,
           "label": base.label, "triggers": base.triggers,
           "weights": base.weights, "stale": base.stale,
           "prior": {"mu": PRIOR_MU, "sigma": PRIOR_SIGMA}, "sensors": {}}
    for name in SENSOR_ORDER:
        sig = getattr(req, name, None)
        if name in DIRECT_SENSORS:
            if sig is None:
                continue
            val, observed_at = float(getattr(sig, DIRECT_SENSORS[name])), sig.observed_at
        else:                                     # engagement
            val = _engagement_value(sig)
            if val is None:
                continue
            observed_at = sig.observed_at
        loo = fuse(req.model_copy(update={name: None}))
        out["sensors"][name] = {
            "value": round(val, 3), "sigma": noise.get(name),
            "weight": base.weights.get(name),
            "age_days": round(_age_days(observed_at), 2),
            "contribution": base.contributions.get(name),
            "score_without_this": loo.composite_score}
    return out
