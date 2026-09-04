from pydantic import BaseModel
from datetime import datetime

class CheckInRequest(BaseModel):
    case_id: str
    channel: str = "PWA" # "PWA", "SMS", "IVRS"
    language: str = "hi"
    transcript: str | None = None

class MissedCallWebhook(BaseModel):
    caller_phone: str
    timestamp: datetime | None = None
    call_duration_seconds: int = 0

class CheckInResponse(BaseModel):
    status: str
    message: str
    interaction_id: str
    hours_since_last_checkin: float
    next_checkin_due: datetime
