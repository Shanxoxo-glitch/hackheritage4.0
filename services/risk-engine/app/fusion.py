"""Weighted fusion with HONEST confidence: rises with more signals,
falls when they disagree. Threat force rule: prob >= 0.90 floors score at 0.80."""
import numpy as np

from app.schemas import FusionRequest, FusionResult

W = {"sentiment": 0.30, "threat": 0.45, "voice_stress": 0.25}
THREAT_FORCE_AT = 0.90
THREAT_FORCE_FLOOR = 0.80
SPREAD_SENSITIVITY = 1.4


def _engagement_score(eng) -> float | None:
    if eng is None or (eng.messages_last_7d is None
                       and eng.avg_reply_latency_min is None):
        return None
    quiet = 1.0 - min((eng.messages_last_7d or 20) / 40.0, 1.0)
    slow = min((eng.avg_reply_latency_min or 120.0) / 480.0, 1.0)
    return round(0.6 * quiet + 0.4 * slow, 3)


def fuse(req: FusionRequest) -> FusionResult:
    present: dict[str, float] = {}
    if req.sentiment is not None:
        present["sentiment"] = float(req.sentiment.score)
    if req.threat is not None:
        present["threat"] = float(req.threat.prob)
    if req.voice_stress is not None:
        present["voice_stress"] = float(req.voice_stress.score)

    if not present:
        return FusionResult(composite_score=0.5, confidence=0.0,
                            top_signals=[], label="LOW",
                            triggers=["no_signals"], contributions={},
                            degraded=True)

    wsum = sum(W[k] for k in present)
    composite = sum(W[k] * v for k, v in present.items()) / wsum
    contributions = {k: round(W[k] * v / wsum, 3) for k, v in present.items()}

    vals = np.array(list(present.values()))
    spread = float(vals.max() - vals.min())
    agreement = max(0.0, 1.0 - SPREAD_SENSITIVITY * spread)
    coverage = len(present) / 3.0
    confidence = round(coverage * (0.35 + 0.65 * agreement), 3)

    eng = _engagement_score(req.engagement)
    if eng is not None:
        composite = 0.92 * composite + 0.08 * eng
        confidence = round(min(1.0, confidence + 0.05), 3)
        contributions["engagement"] = round(0.08 * eng, 3)

    triggers: list[str] = []
    if present.get("threat", 0.0) >= THREAT_FORCE_AT:
        triggers.append("threat_force")
        composite = max(composite, THREAT_FORCE_FLOOR)
        confidence = max(confidence, 0.60)

    top_signals = sorted(contributions, key=contributions.get, reverse=True)[:3]
    label = ("CRITICAL" if composite >= 0.8 or "threat_force" in triggers
             else "HIGH" if composite >= 0.6
             else "ELEVATED" if composite >= 0.4 else "LOW")

    return FusionResult(composite_score=round(float(composite), 3),
                        confidence=confidence, top_signals=top_signals,
                        label=label, triggers=triggers,
                        contributions=contributions, degraded=False)
