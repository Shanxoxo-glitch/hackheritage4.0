import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app import forecast as forecast_module
from app.forecast import forecast, load_model
from app.fusion import DEFAULT_NOISE, fuse, fusion_explain
from app.metrics import (metrics_snapshot, note_fusion, note_forecast,
                         note_latency, note_signal)
from app.schemas import (ForecastRequest, ForecastResult, FusionRequest,
                         FusionResult)

structlog.configure(processors=[structlog.processors.add_log_level,
                                structlog.processors.TimeStamper("iso"),
                                structlog.processors.JSONRenderer()])
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    loaded = load_model()
    log.info("startup", forecaster="loaded" if loaded else "heuristic-fallback")
    yield


app = FastAPI(title="PS-26094 Risk Engine", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def _time_and_tag(req: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    t0 = time.perf_counter()
    resp = await call_next(req)
    dt = time.perf_counter() - t0
    kind = ("fusion" if req.url.path.startswith("/v1/fusion")
            else "forecast" if req.url.path.startswith("/v1/forecast") else None)
    if kind:
        note_latency(kind, dt)
    resp.headers["X-Request-ID"] = rid
    log.info("http", rid=rid, path=req.url.path, ms=round(dt * 1000, 2),
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
    out = forecast(req)
    note_forecast()
    log.info("forecast", case=req.case_id, p=out.p_escalation)
    return out


@app.post("/v1/explain")
def explain_ep(req: FusionRequest):
    return fusion_explain(req)


@app.get("/metrics")
def metrics_ep():
    return PlainTextResponse(metrics_snapshot(DEFAULT_NOISE),
                             media_type="text/plain")


@app.get("/healthz")
def healthz():
    return {"ok": True, "model": forecast_module.MODEL_VERSION}
