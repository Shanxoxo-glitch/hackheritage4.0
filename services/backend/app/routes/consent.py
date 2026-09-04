"""POST /v1/consent (grant/revoke) -> consent_record"""
from fastapi import APIRouter

router = APIRouter(prefix="/v1/consent", tags=["consent"])
