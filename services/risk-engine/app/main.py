import os
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app import forecast as forecast_module
from app.forecast import forecast, load_model
from app.fusion import current_noise, fuse, fusion_explain
from app.metrics import (metrics_snapshot, note_fusion, note_forecast,
                         note_latency, note_signal)
from app.schemas import (ForecastRequest, ForecastResult, FusionRequest,
                         FusionResult)

structlog.configure(processors=[
    structlog.contextvars.merge_contextvars,   # v3: request_id in EVERY log line
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper("iso"),
    structlog.processors.JSONRenderer()])
log = structlog.get_logger()

# v2 shipped allow_origins=["*"] hardcoded; now ops-controllable
CORS_ORIGINS = [o.strip() for o in os.getenv("RISK_CORS_ORIGINS", "*").split(",")
                if o.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    loaded = load_model()
    log.info("startup", forecaster="loaded" if loaded else "heuristic-fallback",
             model_version=forecast_module.MODEL_VERSION)
    yield
    log.info("shutdown", model_version=forecast_module.MODEL_VERSION)


app = FastAPI(title="PS-26094 Risk Engine", version="0.3.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def _time_and_tag(req: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=rid)
    t0 = time.perf_counter()
    try:
        resp = await call_next(req)
    except Exception:                           # v2: unhandled -> bare 500, no log
        log.exception("unhandled", path=req.url.path)
        resp = JSONResponse(status_code=500,
                            content={"error": "internal_error", "request_id": rid})
    dt = time.perf_counter() - t0
    path = req.url.path
    kind = ("fusion" if path.startswith("/v1/fusion")
            else "forecast" if path.startswith("/v1/forecast") else None)
    if kind:
        note_latency(kind, dt)
    resp.headers["X-Request-ID"] = rid
    log.info("http", rid=rid, path=path, ms=round(dt * 1000, 2),
             status=resp.status_code)
    return resp


def _signal_values(req: FusionRequest) -> dict:
    v = {}
    if req.sentiment is not None:
        v["sentiment"] = float(req.sentiment.score)
    if req.threat is not None:
        v["threat"] = float(req.threat.prob)
    if req.voice_stress is not None:
        v["voice_stress"] = float(req.voice_stress.score)
    return v


@app.post("/v1/fusion", response_model=FusionResult)
def fusion_ep(req: FusionRequest) -> FusionResult:
    out = fuse(req)
    note_fusion(out.label, out.conflict, out.degraded)
    for name, v in _signal_values(req).items():
        note_signal(name, v)
    log.info("fusion", score=out.composite_score, conf=out.confidence,
             conflict=out.conflict, chi2=out.conflict_chi2,
             top=out.top_signals)
    return out


@app.post("/v1/forecast", response_model=ForecastResult)
def forecast_ep(req: ForecastRequest) -> ForecastResult:
    out = forecast(req)                # forecast() logs case_id/p/interval itself
    note_forecast()
    return out


@app.post("/v1/explain", summary="Leave-one-out attribution")
def explain_ep(req: FusionRequest):
    return fusion_explain(req)


@app.get("/metrics")
def metrics_ep():
    # v2 bug: always reported DEFAULT_NOISE even when measured noise existed
    return PlainTextResponse(metrics_snapshot(current_noise()),
                             media_type="text/plain")


@app.get("/healthz")
def healthz():
    return {"ok": True, "model": forecast_module.MODEL_VERSION,
            "horizon_days": (forecast_module.MODEL.horizon_days
                             if forecast_module.MODEL else 7)}
