from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ScoreInput(BaseModel):
    interaction_id: str
    text: str | None = None
    audio_url: str | None = None

class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    interaction_id: str
    sentiment_score: float
    voice_stress_score: float
    threat_flag: bool
    composite_score: float
    confidence: float
    trend_flag: str
    created_at: datetime
