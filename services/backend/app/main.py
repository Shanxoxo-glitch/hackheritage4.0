from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.v1 import api_v1_router
from app.routes.case import router as case_contract_router
from app.routes.alerts import router as alerts_contract_router
from app.routes.consent import router as consent_contract_router
from app.api.v1.checkin import router as checkin_router
from app.workers.checkin_worker import build_scheduler
# Import models to ensure registered with Base
import app.models  # noqa: F401
import logging

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    # 1. Create all database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables initialised.")

    # 2. Start background check-in sweep worker (APScheduler + Redis)
    scheduler = build_scheduler()
    scheduler.start()
    logger.info(
        f"✅ Background check-in worker started. "
        f"Sweep interval: every {settings.CHECKIN_WORKER_INTERVAL_MINUTES} minute(s)."
    )

    yield  # Server is running

    # ── Shutdown ──────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logger.info("🛑 Background worker stopped.")
    await engine.dispose()
    logger.info("🛑 Database engine disposed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API engine for SIH 2026 PS 26094 (Distress & Legal Support System)",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS with explicit allowed origins (F9 Fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Mount contract routes directly at root (/v1/...)
app.include_router(case_contract_router)
app.include_router(alerts_contract_router)
app.include_router(consent_contract_router)

# 2. Mount checkin status at root (/checkin/status/{id}) as required by verdict test
app.include_router(checkin_router)

# 3. Mount full API v1 routers (/api/v1/...)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(api_v1_router, prefix="/v1")  # Alias /v1 prefix for backwards compatibility

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "quick_exit_purge_url": f"{settings.API_V1_STR}/auth/purge"
    }
