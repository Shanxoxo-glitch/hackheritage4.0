"""PS-26094 Risk Engine -- the contract. FIELD NAMES ARE LAW.
v2: only OPTIONAL fields were added (observed_at, p10/p90, ...).
Existing posters keep working unchanged."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Sentiment(BaseModel):
    score: float = Field(..., ge=0, le=1)
    observed_at: Optional[datetime] = None    # v2: enables time-decay


class Threat(BaseModel):
    prob: float = Field(..., ge=0, le=1)
    observed_at: Optional[datetime] = None


class VoiceStress(BaseModel):
    score: float = Field(..., ge=0, le=1)
    observed_at: Optional[datetime] = None


class Engagement(BaseModel):
    messages_last_7d: Optional[int] = None
    avg_reply_latency_min: Optional[float] = None
    observed_at: Optional[datetime] = None


class FusionRequest(BaseModel):
    case_id: Optional[str] = None             # v2: for tracing (optional)
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
    # v2 additions:
    case_id: Optional[str] = None
    posterior_std: Optional[float] = None
    conflict_chi2: Optional[float] = None
    conflict: bool = False
    weights: dict = Field(default_factory=dict)
    stale: List[str] = Field(default_factory=list)


class ForecastRequest(BaseModel):
    case_id: str
    score_history: List[float] = Field(default_factory=list)
    legal_stage: Optional[str] = None


class ForecastResult(BaseModel):
    p_escalation: float = Field(..., ge=0, le=1)
    horizon_days: int = 7
    model_version: str = "heuristic-v0"
    p10: Optional[float] = None               # v2: ensemble interval
    p90: Optional[float] = None
    drivers: List[str] = Field(default_factory=list)
