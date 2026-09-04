from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.victim import Victim
from app.models.case import CaseFile
from app.models.interaction import Interaction
from app.schemas.checkin import MissedCallWebhook
from app.services.encryption import decrypt_pii

router = APIRouter(prefix="/telephony", tags=["IVRS & SMS Telephony Gateway"])

@router.post("/missed-call")
async def handle_missed_call_webhook(payload: MissedCallWebhook, db: AsyncSession = Depends(get_db)):
    """
    WEBHOOK: Called by Twilio / Exotel IVRS when a victim gives a missed call.
    Decrypts victim records to match phone number, logs interaction, and resets timer!
    Zero data cost for victim.
    """
    # Fetch all victims and decrypt contact to match (In production, use indexed hashed contact)
    stmt = select(Victim)
    res = await db.execute(stmt)
    victims = res.scalars().all()

    matched_victim = None
    for v in victims:
        decrypted_phone = decrypt_pii(v.contact_encrypted)
        if decrypted_phone and payload.caller_phone.endswith(decrypted_phone[-10:]):
            matched_victim = v
            break

    if not matched_victim:
        return {"status": "UNMATCHED", "message": "Caller phone number not registered to an active victim case."}

    # Get active case file
    case_stmt = select(CaseFile).where(CaseFile.victim_id == matched_victim.id)
    case_res = await db.execute(case_stmt)
    case_file = case_res.scalar_one_or_none()

    if not case_file:
        return {"status": "NO_CASE_FILE", "message": "Victim found but no open legal case file."}

    # Log missed call interaction
    interaction = Interaction(
        case_id=case_file.id,
        channel="IVRS",
        language=matched_victim.preferred_language,
        transcript="[IVRS MISSED CALL CHECK-IN]"
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)

    return {
        "status": "MISSED_CALL_CHECKIN_REGISTERED",
        "case_id": case_file.id,
        "interaction_id": interaction.id,
        "message": "Missed call successfully registered as daily check-in. Timer reset."
    }
