"""
Pydantic models for scoring contracts #1-3 (contracts/api-contracts.md, section "Scoring service").
Field names are frozen: the backend's DistressScore row stores sentiment_score,
voice_stress_score, threat_flag and confidence verbatim from these responses.
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------- shared
class ThreatSignal(BaseModel):
    threat_flag: bool = Field(..., description="prob >= threshold (default 0.5)")
    prob: float = Field(..., ge=0, le=1, description="calibrated P(threat)")
    raw_prob: float = Field(..., ge=0, le=1, description="uncalibrated softmax P(threat)")
    confidence: float = Field(..., ge=0, le=1)
    entropy: float = Field(..., ge=0, le=1, description="normalised entropy; 0 = certain, 1 = uniform")
    calibrated: bool
    model_version: str


class ModelUnavailable(BaseModel):
    """HTTP 503 body. Avik's circuit breaker treats this as signal-down and degrades."""
    error: Literal["model_unavailable"] = "model_unavailable"
    signal: Literal["sentiment", "threat", "voice"]
    detail: Optional[str] = None


# ---------------------------------------------------------------- contract #1  POST /v1/signals/text
class TextSignalRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000,
                      examples=["Case wapas le lo warna tumhare bhai ko uthwa lenge."])
    interaction_id: Optional[str] = Field(None, description="backend interactions.id, echoed back")
    language_hint: Optional[str] = Field(None, examples=["hinglish"])
    request_id: Optional[str] = None


class SentimentSignal(BaseModel):
    label: Literal["LOW", "MODERATE", "HIGH"]
    level: int = Field(..., ge=0, le=2)
    sentiment_score: float = Field(..., ge=0, le=1,
                                   description="expected distress level / 2 -> LOW~0, MODERATE~0.5, HIGH~1")
    probs: Dict[str, float]
    confidence: float = Field(..., ge=0, le=1)
    entropy: float = Field(..., ge=0, le=1)
    calibrated: bool
    model_version: str


class TextSignalResponse(BaseModel):
    schema_version: str
    request_id: str
    interaction_id: Optional[str] = None
    sentiment: SentimentSignal
    threat: ThreatSignal
    flags: List[str] = []
    latency_ms: int


# ---------------------------------------------------------------- contract #2  POST /v1/signals/voice
class VoiceSignalRequest(BaseModel):
    audio_base64: Optional[str] = Field(None, description="base64 WAV/FLAC/OGG, mono or stereo, any rate")
    audio_url: Optional[str] = Field(None, description="fetched server-side only when SCORING_ALLOW_AUDIO_URL=1")
    interaction_id: Optional[str] = None
    request_id: Optional[str] = None


class VoiceSignal(BaseModel):
    label: Literal["NOT_STRESSED", "STRESSED"]
    voice_stress_score: float = Field(..., ge=0, le=1, description="P(stressed)")
    confidence: float = Field(..., ge=0, le=1)
    audio_seconds: float
    features_summary: Dict[str, float]
    model_version: str
    trained_on: str


class VoiceSignalResponse(BaseModel):
    schema_version: str
    request_id: str
    interaction_id: Optional[str] = None
    voice: VoiceSignal
    flags: List[str] = []
    latency_ms: int


# ---------------------------------------------------------------- contract #3  POST /v1/signals/threat
class ThreatSignalRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    interaction_id: Optional[str] = None
    language_hint: Optional[str] = None
    request_id: Optional[str] = None


class ThreatSignalResponse(BaseModel):
    schema_version: str
    request_id: str
    interaction_id: Optional[str] = None
    threat: ThreatSignal
    flags: List[str] = []
    latency_ms: int


# ---------------------------------------------------------------- GET /healthz
class ModelStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    loaded: bool
    path: str
    version: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "loading"]
    service: str
    version: str
    schema_version: str
    models: Dict[str, ModelStatus]
