"""PS-26094 Risk Engine -- the contract. FIELD NAMES ARE LAW.
v3: only OPTIONAL constraints tightened on v2-added fields; v1 fields are NOT
bounds-validated (a poster sending 1.7 keeps working -- we sanitize server-side
instead of 422ing them). No renames, no new required fields."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Sentiment(BaseModel):
    score: float = Field(..., ge=0, le=1)
    observed_at: Optional[datetime] = None


class Threat(BaseModel):
    prob: float = Field(..., ge=0, le=1)
    observed_at: Optional[datetime] = None


class VoiceStress(BaseModel):
    score: float = Field(..., ge=0, le=1)
    observed_at: Optional[datetime] = None


class Engagement(BaseModel):
    messages_last_7d: Optional[int] = Field(None, ge=0)
    avg_reply_latency_min: Optional[float] = Field(None, ge=0)
    observed_at: Optional[datetime] = None


class FusionRequest(BaseModel):
    case_id: Optional[str] = None
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
    contributions: Dict[str, float] = Field(default_factory=dict)
    degraded: bool = False
    case_id: Optional[str] = None
    posterior_std: Optional[float] = None
    conflict_chi2: Optional[float] = None
    conflict: bool = False
    weights: Dict[str, float] = Field(default_factory=dict)
    stale: List[str] = Field(default_factory=list)


class ForecastRequest(BaseModel):
    case_id: str
    score_history: List[float] = Field(default_factory=list)  # sanitized in forecast()
    legal_stage: Optional[str] = None


class ForecastResult(BaseModel):
    p_escalation: float = Field(..., ge=0, le=1)
    horizon_days: int = Field(7, ge=1)
    model_version: str = "heuristic-v0"
    p10: Optional[float] = Field(None, ge=0, le=1)
    p90: Optional[float] = Field(None, ge=0, le=1)
    drivers: List[str] = Field(default_factory=list)
