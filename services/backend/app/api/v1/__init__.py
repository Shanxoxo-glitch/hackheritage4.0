from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.cases import router as cases_router
from app.api.v1.checkin import router as checkin_router
from app.api.v1.telephony import router as telephony_router
from app.api.v1.perception import router as perception_router
from app.api.v1.escalate import router as escalate_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(checkin_router)
api_v1_router.include_router(telephony_router)
api_v1_router.include_router(perception_router)
api_v1_router.include_router(escalate_router)
