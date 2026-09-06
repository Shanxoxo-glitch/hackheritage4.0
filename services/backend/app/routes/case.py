from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import CaseFile, Victim, ConsentRecord, Interaction, DistressScore
from app.policy_constants import STAGE_CANONICAL

router = APIRouter(prefix="/v1/case", tags=["case"])

@router.get("/{case_id}/context")
async def case_context(case_id: str, db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(CaseFile).where(CaseFile.id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case file not found")
    
    victim = await db.get(Victim, case.victim_id)
    consents = (await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.victim_id == case.victim_id, 
            ConsentRecord.status == "GRANTED"
        )
    )).scalars().all()
    
    msgs = (await db.execute(
        select(Interaction)
        .where(Interaction.case_id == case_id)
        .order_by(desc(Interaction.occurred_at))
        .limit(6)
    )).scalars().all()
    
    scores = (await db.execute(
        select(DistressScore)
        .join(Interaction, DistressScore.interaction_id == Interaction.id)
        .where(Interaction.case_id == case_id)
        .order_by(desc(DistressScore.created_at))
        .limit(30)
    )).scalars().all()
    
    now = datetime.now(timezone.utc).date()
    
    return {
        "case_stage": STAGE_CANONICAL.get(case.case_stage.upper() if case.case_stage else "FIR", "FIR"),
        "days_to_next_hearing": ((case.next_hearing_date - now).days if case.next_hearing_date else None),
        "language": victim.preferred_language if victim else "hi",
        "consent_scopes": [c.scope for c in consents],
        "recent_checkins": [{"at": i.occurred_at.isoformat() if i.occurred_at else "", "channel": i.channel} for i in msgs],
        "recent_messages": [{"role": "user", "content": i.transcript if i.transcript else ""} for i in reversed(msgs)],
        "score_history": [s.composite_score for s in scores],
    }
