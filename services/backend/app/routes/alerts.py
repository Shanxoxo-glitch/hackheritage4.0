from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Alert, DistressScore, Interaction, CaseFile
from app.services.audit_ledger import compute_alert_hash, GENESIS_HASH

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])

class CreateAlertPayload(BaseModel):
    case_id: str | None = None
    score_id: str | None = None
    severity: str | None = None
    risk_level: str | None = None
    reasons: list[str] | None = []
    summary_text: str | None = None

@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_orchestrator_alert(payload: CreateAlertPayload, db: AsyncSession = Depends(get_db)):
    # 1. Resolve risk level / severity
    raw_severity = payload.severity or payload.risk_level or "HIGH"
    risk_level = raw_severity.upper()

    # 2. Resolve score_id
    score_id = payload.score_id
    if not score_id and payload.case_id:
        # Find latest DistressScore for this case
        latest_score = (await db.execute(
            select(DistressScore)
            .join(Interaction, DistressScore.interaction_id == Interaction.id)
            .where(Interaction.case_id == payload.case_id)
            .order_by(desc(DistressScore.created_at))
            .limit(1)
        )).scalar_one_or_none()

        if latest_score:
            score_id = latest_score.id
        else:
            # Create a synthetic interaction & distress score for the orchestrator alert
            case = (await db.execute(select(CaseFile).where(CaseFile.id == payload.case_id))).scalar_one_or_none()
            if not case:
                raise HTTPException(404, f"Case file {payload.case_id} not found")
            
            synth_interaction = Interaction(
                case_id=payload.case_id,
                channel="ORCHESTRATOR",
                transcript=payload.summary_text or "Orchestrator automated risk trigger"
            )
            db.add(synth_interaction)
            await db.flush()

            synth_score = DistressScore(
                interaction_id=synth_interaction.id,
                composite_score=0.85,
                confidence=0.90,
                trend_flag="ESCALATING"
            )
            db.add(synth_score)
            await db.flush()
            score_id = synth_score.id
    
    if not score_id:
        raise HTTPException(400, "Must provide either score_id or case_id")

    # 3. Hash-chaining setup
    latest_alert = (await db.execute(
        select(Alert).order_by(desc(Alert.raised_at)).limit(1)
    )).scalar_one_or_none()

    previous_hash = latest_alert.current_hash if latest_alert else GENESIS_HASH
    raised_at = datetime.now(timezone.utc)

    current_hash = compute_alert_hash(
        score_id=score_id,
        risk_level=risk_level,
        raised_at=raised_at,
        previous_hash=previous_hash
    )

    alert = Alert(
        score_id=score_id,
        risk_level=risk_level,
        raised_at=raised_at,
        status="PENDING",
        previous_hash=previous_hash,
        current_hash=current_hash
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return {
        "id": alert.id,
        "score_id": alert.score_id,
        "risk_level": alert.risk_level,
        "status": alert.status,
        "previous_hash": alert.previous_hash,
        "current_hash": alert.current_hash,
        "raised_at": alert.raised_at.isoformat()
    }
