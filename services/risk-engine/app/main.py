import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.forecast import forecast, load_model
from app.fusion import fuse
from app.schemas import (ForecastRequest, ForecastResult, FusionRequest,
                         FusionResult)

structlog.configure(processors=[structlog.processors.add_log_level,
                                structlog.processors.TimeStamper("iso"),
                                structlog.processors.JSONRenderer()])
log = structlog.get_logger()

app = FastAPI(title="PS-26094 Risk Engine", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
load_model()


@app.post("/v1/fusion", response_model=FusionResult)
def fusion_ep(req: FusionRequest) -> FusionResult:
    out = fuse(req)
    log.info("fusion", score=out.composite_score, conf=out.confidence,
             top=out.top_signals)
    return out


@app.post("/v1/forecast", response_model=ForecastResult)
def forecast_ep(req: ForecastRequest) -> ForecastResult:
    out = forecast(req)
    log.info("forecast", case=req.case_id, p=out.p_escalation)
    return out


@app.get("/healthz")
def healthz():
    return {"ok": True}
