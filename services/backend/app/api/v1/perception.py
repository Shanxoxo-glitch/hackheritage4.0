from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.distress import DistressScore
from app.schemas.perception import ScoreInput, ScoreResponse

router = APIRouter(prefix="/perception", tags=["Perception & Emotion AI Gateway"])

@router.post("/score", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def score_interaction(payload: ScoreInput, db: AsyncSession = Depends(get_db)):
    """
    Gateway endpoint for Sohon's Perception ML models.
    Persists computed sentiment score, voice stress score, threat flag, and composite risk.
    """
    # Simple deterministic fallback scoring engine until Sohon's microservice container connects
    text = payload.text or ""
    
    # Keyword threat heuristics (e.g. court, threat, force, silent, harm)
    threat_keywords = ["court", "threat", "force", "dont go", "silent", "harm", "kill", "dhamki"]
    is_threat = any(kw in text.lower() for kw in threat_keywords)

    sentiment_val = 0.85 if is_threat else 0.30
    voice_stress_val = 0.65 if payload.audio_url else 0.10

    # Composite weighted fusion score
    composite = (0.50 * sentiment_val) + (0.30 * voice_stress_val) + (0.20 * (1.0 if is_threat else 0.0))
    trend = "ESCALATING" if composite >= 0.60 else "STABLE"

    score_record = DistressScore(
        interaction_id=payload.interaction_id,
        sentiment_score=round(sentiment_val, 2),
        voice_stress_score=round(voice_stress_val, 2),
        threat_flag=is_threat,
        composite_score=round(composite, 2),
        confidence=0.92,
        trend_flag=trend
    )
    db.add(score_record)
    await db.commit()
    await db.refresh(score_record)

    return ScoreResponse.model_validate(score_record)
