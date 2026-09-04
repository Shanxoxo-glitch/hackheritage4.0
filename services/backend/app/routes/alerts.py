"""POST /v1/alerts + hash-chained append"""
from fastapi import APIRouter
from app.api.v1.escalate import router as alerts_router

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])
