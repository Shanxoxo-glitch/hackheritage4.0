from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.victim import Victim
from app.models.case import CaseFile
from app.models.consent import ConsentRecord
from app.schemas.victim import VictimCreate, VictimResponse, CaseFileCreate, CaseFileResponse
from app.services.encryption import encrypt_pii, decrypt_pii

router = APIRouter(prefix="/cases", tags=["Case & Victim Management"])

@router.post("/victims", response_model=VictimResponse, status_code=status.HTTP_201_CREATED)
async def onboard_victim(payload: VictimCreate, db: AsyncSession = Depends(get_db)):
    """
    Onboards a victim. Encrypts all PII (name, phone, email) using AES-256 Fernet
    before persisting to PostgreSQL database.
    """
    victim = Victim(
        name_encrypted=encrypt_pii(payload.name),
        contact_encrypted=encrypt_pii(payload.contact),
        email_encrypted=encrypt_pii(payload.email) if payload.email else None,
        vulnerability_category=payload.vulnerability_category,
        preferred_language=payload.preferred_language
    )
    db.add(victim)
    await db.commit()
    await db.refresh(victim)

    # Automatically grant default SMS check-in consent
    default_consent = ConsentRecord(
        victim_id=victim.id,
        scope="SMS_CHECKIN",
        status="GRANTED"
    )
    db.add(default_consent)
    await db.commit()

    return VictimResponse(
        id=victim.id,
        vulnerability_category=victim.vulnerability_category,
        preferred_language=victim.preferred_language,
        created_at=victim.created_at,
        name=payload.name,
        contact=payload.contact,
        email=payload.email
    )

@router.post("/files", response_model=CaseFileResponse, status_code=status.HTTP_201_CREATED)
async def create_case_file(payload: CaseFileCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a legal case file linked to a victim under the SC/ST PoA Act.
    """
    case_file = CaseFile(
        victim_id=payload.victim_id,
        fir_number=payload.fir_number,
        act_section=payload.act_section,
        case_stage=payload.case_stage,
        registered_on=payload.registered_on,
        next_hearing_date=payload.next_hearing_date
    )
    db.add(case_file)
    await db.commit()
    await db.refresh(case_file)

    return CaseFileResponse.model_validate(case_file)

@router.get("/files/{case_id}", response_model=CaseFileResponse)
async def get_case_file(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches legal case file details.
    """
    stmt = select(CaseFile).where(CaseFile.id == case_id)
    res = await db.execute(stmt)
    case_file = res.scalar_one_or_none()
    if not case_file:
        raise HTTPException(status_code=404, detail="Case file not found")
    return CaseFileResponse.model_validate(case_file)
