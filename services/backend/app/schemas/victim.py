from pydantic import BaseModel, ConfigDict
from datetime import datetime, date

class VictimCreate(BaseModel):
    name: str
    contact: str
    email: str | None = None
    vulnerability_category: str = "SC/ST_PoA_Sec3"
    preferred_language: str = "hi"

class VictimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vulnerability_category: str
    preferred_language: str
    created_at: datetime
    # Note: Decrypted fields are returned securely when requested by authorized roles
    name: str | None = None
    contact: str | None = None
    email: str | None = None

class CaseFileCreate(BaseModel):
    victim_id: str
    fir_number: str
    act_section: str = "SC/ST PoA Act 1989"
    case_stage: str = "FIR"
    registered_on: date
    next_hearing_date: date | None = None

class CaseFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    victim_id: str
    fir_number: str
    act_section: str
    case_stage: str
    registered_on: date
    next_hearing_date: date | None = None
    created_at: datetime
