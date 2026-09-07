"""
PS26094 Scoring Service (Sohon)  -  port 8100

  GET  /healthz                    model status (add ?warm=1 to force-load)
  POST /v1/signals/text            contract #1: sentiment + threat from text
  POST /v1/signals/voice           contract #2: voice stress from audio
  POST /v1/signals/threat          contract #3: threat_flag + prob from text

Every signal call is wrapped in the same try/except: if a model cannot be
loaded the route returns HTTP 503 {"error": "model_unavailable", "signal": ...}
so the orchestrator's breaker can degrade instead of failing the case.
"""
import base64
import io
import logging
import time
import uuid
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config as C
from . import models
from .models import get_sentiment, get_threat, get_voice
from .schemas import (HealthResponse, ModelUnavailable, TextSignalRequest, TextSignalResponse,
                      ThreatSignalRequest, ThreatSignalResponse, VoiceSignalRequest, VoiceSignalResponse)

log = logging.getLogger("scoring.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if C.WARM_ON_START:
        log.info("warming models: %s", models.warm_all())
    yield


app = FastAPI(title="PS26094 Scoring Service", version=C.SERVICE_VERSION, lifespan=lifespan,
              description="Perception signals (sentiment / threat / voice stress) for SIH 2026 PS 26094.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_503 = {503: {"model": ModelUnavailable}}


def model_unavailable(signal: str, exc: Exception) -> JSONResponse:
    log.warning("signal %s unavailable: %s: %s", signal, type(exc).__name__, exc)
    return JSONResponse(status_code=503, content={"error": "model_unavailable", "signal": signal,
                                                  "detail": f"{type(exc).__name__}: {exc}"[:300]})


# ----------------------------------------------------------------- signal builders
def _sentiment_signal(p: dict) -> dict:
    k = len(C.SENTIMENT_LABELS)
    expected = sum(p["probs"][n] * i for i, n in enumerate(C.SENTIMENT_LABELS)) / (k - 1)
    return {"label": p["label"], "level": p["label_id"], "sentiment_score": float(expected),
            "probs": p["probs"], "confidence": p["confidence"], "entropy": p["entropy"],
            "calibrated": p["calibrated"], "model_version": p["model"]}


def _threat_signal(p: dict) -> dict:
    prob = p["probs"]["THREAT"]
    return {"threat_flag": bool(prob >= C.THREAT_FLAG_THRESHOLD), "prob": prob,
            "raw_prob": p["raw_probs"]["THREAT"], "confidence": p["confidence"], "entropy": p["entropy"],
            "calibrated": p["calibrated"], "model_version": p["model"]}


def _flags(sent=None, thr=None, voice=None):
    flags = []
    if thr and sent and thr["threat_flag"] and sent["level"] == 0:
        flags.append("threat_without_expressed_distress")       # possible 'threatened into silence'
    if (sent and sent["confidence"] < C.CONFIDENCE_GATE) or (thr and thr["confidence"] < C.CONFIDENCE_GATE) \
            or (voice and voice["confidence"] < C.CONFIDENCE_GATE):
        flags.append("below_confidence_gate")
        flags.append("human_review_recommended")
    if voice and voice["trained_on"].startswith("synthetic"):
        flags.append("voice_model_trained_on_synthetic_smoke_data")
    return flags


def _ms(t0):
    return int((time.perf_counter() - t0) * 1000)


# ----------------------------------------------------------------- audio decoding
def decode_audio_bytes(raw: bytes):
    import soundfile as sf
    import librosa
    try:
        data, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
    except Exception as e:
        raise HTTPException(400, f"could not decode audio (send WAV/FLAC/OGG): {e}")
    y = data.mean(axis=1)
    if y.size < C.MIN_AUDIO_SECONDS * sr:
        raise HTTPException(400, f"audio too short (< {C.MIN_AUDIO_SECONDS} s)")
    if y.size > C.MAX_AUDIO_SECONDS * sr:
        raise HTTPException(400, f"audio too long (> {C.MAX_AUDIO_SECONDS} s)")
    if sr != C.AUDIO_SR:
        y, sr = librosa.resample(y, orig_sr=sr, target_sr=C.AUDIO_SR), C.AUDIO_SR
    return y.astype(np.float32), sr


def decode_audio_b64(b64: str):
    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception as e:
        raise HTTPException(400, f"invalid base64: {e}")
    return decode_audio_bytes(raw)


def load_audio(req: VoiceSignalRequest):
    if req.audio_base64:
        return decode_audio_b64(req.audio_base64)
    if req.audio_url:
        if not C.ALLOW_AUDIO_URL:
            raise HTTPException(400, "audio_url disabled (set SCORING_ALLOW_AUDIO_URL=1); send audio_base64")
        import httpx
        try:
            r = httpx.get(req.audio_url, timeout=20, follow_redirects=True)
            r.raise_for_status()
        except Exception as e:
            raise HTTPException(400, f"could not fetch audio_url: {e}")
        return decode_audio_bytes(r.content)
    raise HTTPException(400, "provide audio_base64 or audio_url")


# ----------------------------------------------------------------- routes
@app.get("/healthz", response_model=HealthResponse)
def healthz(warm: bool = False):
    if warm:
        models.warm_all()
    st = models.status()
    loaded = sum(1 for s in st.values() if s["loaded"])
    status = "ok" if loaded == len(st) else ("degraded" if loaded else "loading")
    return {"status": status, "service": C.SERVICE_NAME, "version": C.SERVICE_VERSION,
            "schema_version": C.SCHEMA_VERSION, "models": st}


@app.post("/v1/signals/text", response_model=TextSignalResponse, responses=_503)
def signals_text(req: TextSignalRequest):
    t0 = time.perf_counter()
    try:
        s = get_sentiment().predict([req.text])[0]
    except Exception as e:
        return model_unavailable("sentiment", e)
    try:
        t = get_threat().predict([req.text])[0]
    except Exception as e:
        return model_unavailable("threat", e)
    sent, thr = _sentiment_signal(s), _threat_signal(t)
    return TextSignalResponse(schema_version=C.SCHEMA_VERSION, request_id=req.request_id or str(uuid.uuid4()),
                              interaction_id=req.interaction_id, sentiment=sent, threat=thr,
                              flags=_flags(sent, thr), latency_ms=_ms(t0))


@app.post("/v1/signals/threat", response_model=ThreatSignalResponse, responses=_503)
def signals_threat(req: ThreatSignalRequest):
    t0 = time.perf_counter()
    try:
        t = get_threat().predict([req.text])[0]
    except Exception as e:
        return model_unavailable("threat", e)
    thr = _threat_signal(t)
    return ThreatSignalResponse(schema_version=C.SCHEMA_VERSION, request_id=req.request_id or str(uuid.uuid4()),
                                interaction_id=req.interaction_id, threat=thr, flags=_flags(thr=thr),
                                latency_ms=_ms(t0))


@app.post("/v1/signals/voice", response_model=VoiceSignalResponse, responses=_503)
def signals_voice(req: VoiceSignalRequest):
    t0 = time.perf_counter()
    y, sr = load_audio(req)                      # 400 on bad input
    try:
        v = get_voice().score_array(y, sr)
    except Exception as e:
        return model_unavailable("voice", e)
    voice = {"label": v["label"], "voice_stress_score": v["score"], "confidence": v["confidence"],
             "audio_seconds": v["audio_seconds"], "features_summary": v["features_summary"],
             "model_version": v["model"], "trained_on": v["trained_on"]}
    return VoiceSignalResponse(schema_version=C.SCHEMA_VERSION, request_id=req.request_id or str(uuid.uuid4()),
                               interaction_id=req.interaction_id, voice=voice, flags=_flags(voice=voice),
                               latency_ms=_ms(t0))
