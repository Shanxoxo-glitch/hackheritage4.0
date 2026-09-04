from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AlertCreate(BaseModel):
    score_id: str
    official_id: str | None = None
    risk_level: str # "LOW", "MODERATE", "HIGH", "CRITICAL"

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    score_id: str
    official_id: str | None = None
    risk_level: str
    status: str
    raised_at: datetime
    previous_hash: str
    current_hash: str

class TriageQueueItem(BaseModel):
    alert_id: str
    case_id: str
    victim_vulnerability: str
    risk_level: str
    composite_score: float
    confidence: float
    hours_since_last_contact: float
    triage_priority_score: float
    raised_at: datetime
