"""
Perception & Emotion AI gateway.

Calls Sohon's scoring service (services/scoring, port 8100, SCORING_URL) for the three
perception signals and persists them on the DistressScore row:

    sentiment_score      contract #1  POST /v1/signals/text    (distress level 0..1)
    threat_flag          contract #1/3 (calibrated P(threat) >= threshold)
    voice_stress_score   contract #2  POST /v1/signals/voice   (P(stressed), needs audio_base64)

If the scoring service is unreachable or reports a model as unavailable (HTTP 503), the
endpoint degrades to the previous deterministic keyword heuristic instead of failing the
case, and says so in `signal_source`. The persisted columns and the ScoreResponse shape
are unchanged.
"""
import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.distress import DistressScore
from app.schemas.perception import ScoreInput, ScoreResponse
from app.services.scoring_client import ScoringUnavailable, scoring_client

logger = logging.getLogger("perception")
router = APIRouter(prefix="/perception", tags=["Perception & Emotion AI Gateway"])

# Fallback heuristic (used only when the scoring service is unavailable)
THREAT_KEYWORDS = ["court", "threat", "force", "dont go", "silent", "harm", "kill", "dhamki"]

# Composite fusion weights (unchanged; the risk engine owns the real fusion)
W_SENTIMENT, W_VOICE, W_THREAT = 0.50, 0.30, 0.20
ESCALATING_AT = 0.60


def _heuristic(text: str, has_audio: bool) -> tuple[float, float, bool]:
    is_threat = any(kw in (text or "").lower() for kw in THREAT_KEYWORDS)
    return (0.85 if is_threat else 0.30), (0.65 if has_audio else 0.10), is_threat


@router.post("/score", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def score_interaction(payload: ScoreInput, db: AsyncSession = Depends(get_db)):
    """Score one interaction through the perception service and persist the result."""
    text = payload.text or ""
    has_audio = bool(payload.audio_base64 or payload.audio_url)

    sentiment_val, voice_stress_val, is_threat = _heuristic(text, has_audio)
    confidences: list[float] = []
    model_versions: dict[str, str] = {}
    degraded: list[str] = []
    source = "scoring_service"

    # ---- text signals (sentiment + threat) -------------------------------------------
    if text.strip():
        try:
            body = await scoring_client.score_text(text, payload.interaction_id)
            sentiment_val = float(body["sentiment"]["sentiment_score"])
            is_threat = bool(body["threat"]["threat_flag"])
            confidences += [float(body["sentiment"]["confidence"]), float(body["threat"]["confidence"])]
            model_versions["sentiment"] = body["sentiment"]["model_version"]
            model_versions["threat"] = body["threat"]["model_version"]
        except (ScoringUnavailable, KeyError, TypeError, ValueError) as exc:
            logger.warning("scoring service text signal unavailable, using heuristic: %s", exc)
            degraded.append("text")
    else:
        degraded.append("text_empty")

    # ---- voice signal ------------------------------------------------------------------
    if payload.audio_base64:
        try:
            body = await scoring_client.score_voice_base64(payload.audio_base64, payload.interaction_id)
            voice_stress_val = float(body["voice"]["voice_stress_score"])
            confidences.append(float(body["voice"]["confidence"]))
            model_versions["voice"] = body["voice"]["model_version"]
        except (ScoringUnavailable, KeyError, TypeError, ValueError) as exc:
            logger.warning("scoring service voice signal unavailable, using heuristic: %s", exc)
            degraded.append("voice")
    elif payload.audio_url:
        # server-side URL fetching is disabled on the scoring service by default (SSRF);
        # send audio_base64 to get a real voice score.
        degraded.append("voice_url_not_scored")
    else:
        degraded.append("voice_not_provided")       # no audio in this interaction: not a service failure

    failures = [d for d in degraded if d in {"text", "voice"}]
    if failures and not model_versions:
        source = "heuristic_fallback"
    elif failures or degraded:
        source = "partial"

    composite = (W_SENTIMENT * sentiment_val) + (W_VOICE * voice_stress_val) + (W_THREAT * (1.0 if is_threat else 0.0))
    confidence = min(confidences) if confidences else 0.50      # heuristic is not a confident signal

    score_record = DistressScore(
        interaction_id=payload.interaction_id,
        sentiment_score=round(sentiment_val, 4),
        voice_stress_score=round(voice_stress_val, 4),
        threat_flag=is_threat,
        composite_score=round(composite, 4),
        confidence=round(confidence, 4),
        trend_flag="ESCALATING" if composite >= ESCALATING_AT else "STABLE",
    )
    db.add(score_record)
    await db.commit()
    await db.refresh(score_record)

    response = ScoreResponse.model_validate(score_record)
    response.signal_source = source
    response.model_versions = model_versions
    response.degraded_signals = degraded
    return response


@router.get("/health", tags=["Perception & Emotion AI Gateway"])
async def perception_health():
    """Is the scoring service reachable, and which models has it loaded?"""
    try:
        return {"scoring_service": "up", "url": scoring_client.base_url, **(await scoring_client.health())}
    except ScoringUnavailable as exc:
        return {"scoring_service": "down", "url": scoring_client.base_url, "detail": str(exc),
                "note": "POST /perception/score still works and degrades to the keyword heuristic"}
