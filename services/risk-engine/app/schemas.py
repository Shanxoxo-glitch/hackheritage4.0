"""PS-26094 Risk Engine -- the contract. FIELD NAMES ARE LAW."""
from typing import List, Optional
from pydantic import BaseModel, Field


class Sentiment(BaseModel):
    score: float = Field(..., ge=0, le=1)


class Threat(BaseModel):
    prob: float = Field(..., ge=0, le=1)


class VoiceStress(BaseModel):
    score: float = Field(..., ge=0, le=1)


class Engagement(BaseModel):
    messages_last_7d: Optional[int] = None
    avg_reply_latency_min: Optional[float] = None


class FusionRequest(BaseModel):
    sentiment: Optional[Sentiment] = None
    threat: Optional[Threat] = None
    voice_stress: Optional[VoiceStress] = None
    engagement: Optional[Engagement] = None


class FusionResult(BaseModel):
    composite_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    top_signals: List[str] = Field(default_factory=list)
    label: str = "LOW"
    triggers: List[str] = Field(default_factory=list)
    contributions: dict = Field(default_factory=dict)
    degraded: bool = False


class ForecastRequest(BaseModel):
    case_id: str
    score_history: List[float] = Field(default_factory=list)
    legal_stage: Optional[str] = None


class ForecastResult(BaseModel):
    p_escalation: float = Field(..., ge=0, le=1)
    horizon_days: int = 7
    model_version: str = "heuristic-v0"
