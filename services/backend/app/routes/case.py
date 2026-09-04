"""GET /v1/case/{id}/context"""
from fastapi import APIRouter
from app.api.v1.cases import router as cases_router

router = APIRouter(prefix="/v1/case", tags=["case"])
