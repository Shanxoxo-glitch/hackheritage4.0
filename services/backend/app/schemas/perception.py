from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ScoreInput(BaseModel):
    interaction_id: str
    text: str | None = None
    audio_url: str | None = None
    audio_base64: str | None = None   # required for a real voice-stress score (contract #2)

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

    # provenance (not persisted; defaults keep existing consumers working unchanged)
    signal_source: str = "scoring_service"        # scoring_service | partial | heuristic_fallback
    model_versions: dict[str, str] = {}
    degraded_signals: list[str] = []
