import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH 2026 PS 26094 Distress & Legal Support Engine"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key-for-sih-2026-distress-engine-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database — uses PostgreSQL in Docker, SQLite fallback for plain local dev
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./sql_app.db"  # fallback for running without Docker
    )

    # Redis URL — used by APScheduler background worker
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # PII Encryption Key (AES-256 Fernet base64 key)
    FERNET_KEY: str = "c2loLTIwMjYtZGlzdHJlc3MtbW9uaXRvcmluZy1zZWN1cmUta2V5PQ=="

    # Quick-Exit Redirect Target URL
    QUICK_EXIT_REDIRECT_URL: str = "https://weather.com"

    # Twilio / Telephony Gateway Credentials
    TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID", None)
    TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN", None)
    TWILIO_PHONE_NUMBER: str | None = os.getenv("TWILIO_PHONE_NUMBER", None)
    TWILIO_MOCK_MODE: bool = os.getenv("TWILIO_MOCK_MODE", "true").lower() == "true"

    # Background worker interval (how often to scan all cases, in minutes)
    CHECKIN_WORKER_INTERVAL_MINUTES: int = int(os.getenv("CHECKIN_WORKER_INTERVAL_MINUTES", "60"))

    class ConfigDict:
        case_sensitive = True

settings = Settings()

