"""
PS26094 Scoring Service (Sohon)  -  port 8100

  GET  /healthz                    model status (add ?warm=1 to force-load)
  POST /v1/signals/text            contract #1: sentiment + threat from text
  POST /v1/signals/voice           contract #2: voice stress from audio
  POST /v1/signals/threat          contract #3: threat_flag + prob from text

/v1/signals/voice accepts three encodings of the same clip (WAV / FLAC / OGG, mono or stereo, any rate):
  application/json          {"audio_base64": "..."}  or  {"audio_url": "..."}   (contract #2, unchanged)
  multipart/form-data       file=<audio> [+ interaction_id, request_id form fields]
  audio/* | octet-stream    raw bytes body  (?interaction_id=&request_id= as query params)

Every signal call is wrapped in the same try/except: if a model cannot be
loaded the route returns HTTP 503 {"error": "model_unavailable", "signal": ...}
so the orchestrator's breaker can degrade instead of failing the case.
Validation errors never echo request bodies (a binary WAV in the default
handler's "input" field used to raise UnicodeDecodeError -> HTTP 500).
"""
import base64
import io
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import config as C
from . import models
from .models import get_sentiment, get_threat, get_voice
from .schemas import (HealthResponse, ModelUnavailable, TextSignalRequest, TextSignalResponse,
                      ThreatSignalRequest, ThreatSignalResponse, VoiceSignalRequest, VoiceSignalResponse)

log = logging.getLogger("scoring.api")

MAX_AUDIO_BYTES = 25 * 1024 * 1024        # 25 MB raw upload cap (413 above this)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if C.WARM_ON_START:
        log.info("warming models: %s", models.warm_all())
    yield


app = FastAPI(title="PS26094 Scoring Service", version=C.SERVICE_VERSION, lifespan=lifespan,
              description="Perception signals (sentiment / threat / voice stress) for SIH 2026 PS 26094.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_503 = {503: {"model": ModelUnavailable}}


# ----------------------------------------------------------------- safe validation errors
def _safe_error(err: dict) -> dict:
    """Strip anything from a pydantic error that is not JSON-safe or could be a request body."""
    err = dict(err)
    inp = err.get("input")
    if isinstance(inp, (bytes, bytearray)):
        err["input"] = f"<{len(inp)} bytes>"
    elif isinstance(inp, str):
        err["input"] = inp[:120] + ("..." if len(inp) > 120 else "")
    elif isinstance(inp, (int, float, bool)) or inp is None:
        pass
    else:
        err["input"] = f"<{type(inp).__name__}>"
    err.pop("url", None)
    err.pop("ctx", None)
    return err


def _validation_response(errors) -> JSONResponse:
    try:
        detail = jsonable_encoder([_safe_error(e) for e in errors])
    except Exception as e:                       # never let error reporting itself fail
        detail = [{"type": "validation_error", "msg": f"{type(e).__name__}"}]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return _validation_response(exc.errors())


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


def _voice_signal(v: dict) -> dict:
    return {"label": v["label"], "voice_stress_score": v["score"], "confidence": v["confidence"],
            "audio_seconds": v["audio_seconds"], "features_summary": v["features_summary"],
            "model_version": v["model"], "trained_on": v["trained_on"]}


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
    if not raw:
        raise HTTPException(400, "empty audio body")
    if len(raw) > MAX_AUDIO_BYTES:
        raise HTTPException(413, f"audio larger than {MAX_AUDIO_BYTES // (1024 * 1024)} MB")
    try:
        data, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
    except Exception as e:
        raise HTTPException(400, f"could not decode audio (send WAV/FLAC/OGG): {type(e).__name__}: {str(e)[:120]}")
    y = data.mean(axis=1)
    if y.size < C.MIN_AUDIO_SECONDS * sr:
        raise HTTPException(400, f"audio too short (< {C.MIN_AUDIO_SECONDS} s)")
    if y.size > C.MAX_AUDIO_SECONDS * sr:
        raise HTTPException(400, f"audio too long (> {C.MAX_AUDIO_SECONDS} s)")
    if sr != C.AUDIO_SR:
        import librosa                         # lazy: only needed for resampling
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
            raise HTTPException(400, f"could not fetch audio_url: {type(e).__name__}: {str(e)[:120]}")
        return decode_audio_bytes(r.content)
    raise HTTPException(400, "provide audio_base64 or audio_url")


async def read_voice_request(request: Request):
    """Parse the three accepted encodings -> (y, sr, interaction_id, request_id)."""
    ctype = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    interaction_id = request.query_params.get("interaction_id")
    request_id = request.query_params.get("request_id")

    if ctype.startswith("multipart/form-data"):
        try:
            form = await request.form()
        except Exception as e:
            raise HTTPException(422, f"could not parse multipart body: {type(e).__name__}: {str(e)[:120]}")
        part = form.get("file") or form.get("audio")
        if part is None or isinstance(part, str):
            raise HTTPException(422, "multipart body must contain an audio file part named 'file'")
        raw = await part.read()
        interaction_id = (form.get("interaction_id") or interaction_id) or None
        request_id = (form.get("request_id") or request_id) or None
        y, sr = decode_audio_bytes(raw)
        return y, sr, interaction_id, request_id

    if ctype.startswith("audio/") or ctype == "application/octet-stream":
        y, sr = decode_audio_bytes(await request.body())
        return y, sr, interaction_id, request_id

    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(422, "body must be JSON (application/json), multipart/form-data with a 'file' part, "
                                 "or raw audio bytes with an audio/* content-type")
    try:
        req = VoiceSignalRequest.model_validate(payload)
    except ValidationError as e:
        raise _VoiceValidation(e.errors())
    y, sr = load_audio(req)
    return y, sr, req.interaction_id or interaction_id, req.request_id or request_id


class _VoiceValidation(Exception):
    def __init__(self, errors):
        self.errors = errors


VOICE_OPENAPI_BODY = {"requestBody": {"required": True, "content": {
    "application/json": {"schema": VoiceSignalRequest.model_json_schema()},
    "multipart/form-data": {"schema": {"type": "object", "required": ["file"], "properties": {
        "file": {"type": "string", "format": "binary"},
        "interaction_id": {"type": "string"}, "request_id": {"type": "string"}}}},
    "audio/wav": {"schema": {"type": "string", "format": "binary"}},
    "application/octet-stream": {"schema": {"type": "string", "format": "binary"}},
}}}


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


@app.post("/v1/signals/voice", response_model=VoiceSignalResponse, responses=_503, openapi_extra=VOICE_OPENAPI_BODY)
async def signals_voice(request: Request):
    t0 = time.perf_counter()
    try:
        y, sr, interaction_id, request_id = await read_voice_request(request)     # 400 / 413 / 422 on bad input
    except _VoiceValidation as e:
        return _validation_response(e.errors)
    try:
        v = get_voice().score_array(y, sr)
    except Exception as e:
        return model_unavailable("voice", e)
    voice = _voice_signal(v)
    return VoiceSignalResponse(schema_version=C.SCHEMA_VERSION, request_id=request_id or str(uuid.uuid4()),
                               interaction_id=interaction_id, voice=voice, flags=_flags(voice=voice),
                               latency_ms=_ms(t0))
