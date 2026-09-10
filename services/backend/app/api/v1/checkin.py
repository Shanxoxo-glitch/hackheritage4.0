from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.interaction import Interaction
from app.schemas.checkin import CheckInRequest, CheckInResponse
from app.services.scheduler import CheckInSchedulerService

router = APIRouter(prefix="/checkin", tags=["Check-In & Telemetry"])

@router.post("/submit", response_model=CheckInResponse)
async def submit_checkin(payload: CheckInRequest, db: AsyncSession = Depends(get_db)):
    """
    Submits a daily check-in (from PWA, SMS, or IVRS). Logs the interaction and
    resets the check-in timer.
    """
    interaction = Interaction(
        case_id=payload.case_id,
        channel=payload.channel,
        language=payload.language,
        transcript=payload.transcript
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)

    # Evaluate updated state
    state = await CheckInSchedulerService.evaluate_case_checkin_state(db, payload.case_id)
    next_due = datetime.now(timezone.utc) + timedelta(hours=24)

    return CheckInResponse(
        status="CHECKIN_SUCCESSFUL",
        message=f"Check-in recorded via {payload.channel}. Timer reset.",
        interaction_id=interaction.id,
        hours_since_last_checkin=0.0,
        next_checkin_due=next_due
    )

@router.get("/status/{case_id}")
async def get_checkin_status(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Evaluates current check-in Tier (Tier 0 to Tier 4) and dispatches action.
    """
    return await CheckInSchedulerService.evaluate_case_checkin_state(db, case_id)
