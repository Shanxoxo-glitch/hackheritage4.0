import os
import base64
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid 32-byte base64-encoded Fernet default key (44 chars)
DEFAULT_FERNET_KEY = base64.urlsafe_b64encode(b"sih2026_distress_monitoring_key!").decode()

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH 2026 PS 26094 Distress & Legal Support Engine"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-sih-2026-distress-engine-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Environment
    ENV: str = os.getenv("ENV", "dev")

    # Database — uses PostgreSQL in Docker, SQLite fallback for plain local dev
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./sql_app.db"
    )

    # Redis URL — used by APScheduler background worker
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # PII Encryption Key (AES-256 Fernet base64 key, 44 chars)
    FERNET_KEY: str = os.getenv("FERNET_KEY", DEFAULT_FERNET_KEY)

    # Quick-Exit Redirect Target URL
    QUICK_EXIT_REDIRECT_URL: str = "https://weather.com"

    # Twilio / Telephony Gateway Credentials
    TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID", None)
    TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN", None)
    TWILIO_PHONE_NUMBER: str | None = os.getenv("TWILIO_PHONE_NUMBER", None)
    TWILIO_MOCK_MODE: bool = os.getenv("TWILIO_MOCK_MODE", "true").lower() == "true"

    # Background worker interval (in minutes)
    CHECKIN_WORKER_INTERVAL_MINUTES: int = int(os.getenv("CHECKIN_WORKER_INTERVAL_MINUTES", "60"))

    # Groq API key fallback for local AI responses when VM is offline
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY", "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")

    # Azure VM Orchestrator settings
    ORCHESTRATOR_URL: str = os.getenv("ORCHESTRATOR_URL", "http://localhost:8500")
    ORCHESTRATOR_API_KEY: str = os.getenv("ORCHESTRATOR_API_KEY", "")

    # CORS Origins (Explicit list for allow_credentials=True compatibility)
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173"
    ]

    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

settings = Settings()
