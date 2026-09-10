from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.distress import DistressScore
from app.models.interaction import Interaction
from app.models.case import CaseFile
from app.models.victim import Victim
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertResponse, TriageQueueItem
from app.services.audit_ledger import compute_alert_hash, GENESIS_HASH

router = APIRouter(prefix="/escalate", tags=["Alert Escalation & Triage Queue"])

@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_risk_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new risk alert with SHA-256 cryptographic hash chaining for legal auditability.
    """
    latest_alert_stmt = select(Alert).order_by(desc(Alert.raised_at))
    latest_alert_res = await db.execute(latest_alert_stmt)
    latest_alert = latest_alert_res.scalars().first()


    prev_hash = latest_alert.current_hash if latest_alert else GENESIS_HASH
    now = datetime.now(timezone.utc)
    curr_hash = compute_alert_hash(
        score_id=payload.score_id,
        risk_level=payload.risk_level,
        raised_at=now,
        previous_hash=prev_hash
    )

    alert = Alert(
        score_id=payload.score_id,
        official_id=payload.official_id,
        risk_level=payload.risk_level,
        status="PENDING",
        raised_at=now,
        previous_hash=prev_hash,
        current_hash=curr_hash
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return AlertResponse.model_validate(alert)

@router.get("/triage-queue", response_model=list[TriageQueueItem])
async def get_counsellor_triage_queue(db: AsyncSession = Depends(get_db)):
    """
    AUTOMATED CASE PRIORITISATION QUEUE:
    Returns triage list for district counsellors ranked by:
    Triage Priority Score = Composite Score x Confidence x Hours Since Last Contact
    """
    stmt = (
        select(Alert, DistressScore, Interaction, CaseFile, Victim)
        .join(DistressScore, Alert.score_id == DistressScore.id)
        .join(Interaction, DistressScore.interaction_id == Interaction.id)
        .join(CaseFile, Interaction.case_id == CaseFile.id)
        .join(Victim, CaseFile.victim_id == Victim.id)
        .where(Alert.status == "PENDING")
    )
    res = await db.execute(stmt)
    rows = res.all()

    now = datetime.now(timezone.utc)
    queue = []
    for alert, score, interaction, case_file, victim in rows:
        occ_at = interaction.occurred_at
        if occ_at.tzinfo is None:
            occ_at = occ_at.replace(tzinfo=timezone.utc)
        hours_since = (now - occ_at).total_seconds() / 3600.0
        priority_score = score.composite_score * score.confidence * (1.0 + (hours_since / 24.0))

        queue.append(TriageQueueItem(
            alert_id=alert.id,
            case_id=case_file.id,
            victim_vulnerability=victim.vulnerability_category,
            risk_level=alert.risk_level,
            composite_score=score.composite_score,
            confidence=score.confidence,
            hours_since_last_contact=round(hours_since, 2),
            triage_priority_score=round(priority_score, 2),
            raised_at=alert.raised_at
        ))

    # Sort descending by priority score
    queue.sort(key=lambda x: x.triage_priority_score, reverse=True)
    return queue
