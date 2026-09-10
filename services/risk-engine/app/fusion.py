"""Novelty 1 v2 -- Bayesian linear-Gaussian fusion.

Each detector is a noisy observation of latent distress d:
    x_i = d + eps_i,   eps_i ~ N(0, sigma_i^2)
sigma_i comes from artifacts/detector_noise.json (MEASURED by the
calibration script), so weights are inverse-variance optimal, not tuned.

Honest uncertainty, statistically:
    posterior_std = 1 / sqrt(prior_prec + sum decay_i^2 / sigma_i^2)
    chi^2 test between sensors -> if they disagree more than their own
    noise explains, inflate std by sqrt(chi^2/df) (random-effects
    correction). confidence = 1 - 2*std -> widens exactly on conflict.

Threat force rule kept: threat.prob >= 0.90 floors score at 0.80.
Stale signals decay: weight *= exp(-lambda * age_days)^2.
"""
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import FusionRequest, FusionResult

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

# ---- tunables: env-overridable, retune without touching code --------------
PRIOR_MU = float(os.getenv("RISK_PRIOR_MU", "0.35"))
PRIOR_SIGMA = float(os.getenv("RISK_PRIOR_SIGMA", "0.45"))
DECAY_LAMBDA = float(os.getenv("RISK_DECAY_LAMBDA", "0.10"))    # per day
THREAT_FORCE_AT = float(os.getenv("RISK_THREAT_FORCE_AT", "0.90"))
THREAT_FORCE_FLOOR = 0.80
STALE_BELOW = 0.50           # decay factor under which a signal is "stale"

# fallback noise; replaced by calibration measurements when available
DEFAULT_NOISE = {"sentiment": 0.15, "threat": 0.10,
                 "voice_stress": 0.20, "engagement": 0.25}

# chi-square 95th percentiles df 1..4 (table lookup -- no scipy dependency)
CHI2_CRIT = {1: 3.84, 2: 5.99, 3: 7.81, 4: 9.49}


def _load_noise() -> dict:
    f = ARTIFACTS / "detector_noise.json"
    if f.exists():
        try:
            data = json.loads(f.read_text())
            if "measured_sigma" in data:
                return {**DEFAULT_NOISE,
                        **{k: float(v) for k, v in data["measured_sigma"].items()
                           if k in DEFAULT_NOISE}}
        except Exception:
            pass
    return dict(DEFAULT_NOISE)


def _engagement_value(eng) -> float | None:
    if eng is None or (eng.messages_last_7d is None
                       and eng.avg_reply_latency_min is None):
        return None
    quiet = 1.0 - min((eng.messages_last_7d or 20) / 40.0, 1.0)
    slow = min((eng.avg_reply_latency_min or 120.0) / 480.0, 1.0)
    return 0.6 * quiet + 0.4 * slow


def _age_days(observed_at) -> float:
    if observed_at is None:
        return 0.0
    ts = observed_at if observed_at.tzinfo else observed_at.replace(
        tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0)


def _collect(req: FusionRequest, noise: dict):
    """-> {name: (value, decayed_precision)}, stale list."""
    obs, stale = {}, []
    for name, sig in (("sentiment", req.sentiment), ("threat", req.threat),
                      ("voice_stress", req.voice_stress)):
        if sig is None:
            continue
        value = float(sig.prob if name == "threat" else sig.score)
        decay = math.exp(-DECAY_LAMBDA * _age_days(sig.observed_at))
        if decay < STALE_BELOW:
            stale.append(name)
        obs[name] = (value, decay ** 2 / noise[name] ** 2)
    eng = _engagement_value(req.engagement)
    if eng is not None:
        decay = math.exp(-DECAY_LAMBDA * _age_days(req.engagement.observed_at))
        obs["engagement"] = (eng, decay ** 2 / noise["engagement"] ** 2)
    return obs, stale


def fuse(req: FusionRequest) -> FusionResult:
    noise = _load_noise()
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
    total_prec = prior_prec + sum(p for _, p in obs.values())
    mu = (prior_prec * PRIOR_MU
          + sum(p * v for v, p in obs.values())) / total_prec
    std = 1.0 / math.sqrt(total_prec)

    # -- chi^2 conflict test between sensors (prior excluded) -----------------
    chi2 = sum(p * (v - mu) ** 2 for v, p in obs.values())
    df = max(len(obs) - 1, 1)
    crit = CHI2_CRIT.get(df, df + 2.8 * math.sqrt(2 * df))
    conflict = chi2 > crit
    if conflict:
        std *= math.sqrt(max(chi2 / df, 1.0))   # random-effects inflation

    composite = min(max(mu, 0.0), 1.0)
    confidence = min(1.0, max(0.0, 1.0 - 2.0 * std))

    sensor_prec = sum(p for _, p in obs.values())
    weights = {k: round(p / sensor_prec, 3) for k, (v, p) in obs.items()}
    contributions = {k: round(p * v / sensor_prec, 3)
                     for k, (v, p) in obs.items()}

    # -- threat force rule (kept from v1) --------------------------------------
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
    for name in ("sentiment", "threat", "voice_stress", "engagement"):
        sig = getattr(req, name, None)
        if sig is None:
            continue
        if name == "threat":
            val = float(sig.prob)
        elif name == "engagement":
            val = _engagement_value(sig)
            if val is None:
                continue
        else:
            val = float(sig.score)
        loo = fuse(req.model_copy(update={name: None}))
        out["sensors"][name] = {
            "value": round(val, 3), "sigma": noise.get(name),
            "weight": base.weights.get(name),
            "age_days": round(_age_days(sig.observed_at), 2),
            "contribution": base.contributions.get(name),
            "score_without_this": loo.composite_score}
    return out
