from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import ConsentRecord, CaseFile, Victim

router = APIRouter(prefix="/v1/consent", tags=["consent"])

class ConsentTogglePayload(BaseModel):
    case_id: str | None = None
    victim_id: str | None = None
    scope: str = "DATA_SHARING"
    granted: bool = True

@router.post("", status_code=status.HTTP_200_OK)
@router.post("/", status_code=status.HTTP_200_OK)
async def toggle_consent(payload: ConsentTogglePayload, db: AsyncSession = Depends(get_db)):
    victim_id = payload.victim_id
    if not victim_id and payload.case_id:
        case = (await db.execute(select(CaseFile).where(CaseFile.id == payload.case_id))).scalar_one_or_none()
        if not case:
            raise HTTPException(404, f"Case {payload.case_id} not found")
        victim_id = case.victim_id

    if not victim_id:
        raise HTTPException(400, "Must provide victim_id or case_id")

    victim = await db.get(Victim, victim_id)
    if not victim:
        raise HTTPException(404, f"Victim {victim_id} not found")

    # Fetch existing consent record for this victim and scope
    stmt = select(ConsentRecord).where(
        ConsentRecord.victim_id == victim_id,
        ConsentRecord.scope == payload.scope
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()

    new_status = "GRANTED" if payload.granted else "REVOKED"
    now = datetime.now(timezone.utc)

    if existing:
        existing.status = new_status
        if not payload.granted:
            existing.revoked_at = now
        else:
            existing.revoked_at = None
        record = existing
    else:
        record = ConsentRecord(
            victim_id=victim_id,
            scope=payload.scope,
            status=new_status,
            granted_at=now,
            revoked_at=None if payload.granted else now
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)

    return {
        "id": record.id,
        "victim_id": record.victim_id,
        "scope": record.scope,
        "status": record.status,
        "granted_at": record.granted_at.isoformat() if record.granted_at else None,
        "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None
    }
