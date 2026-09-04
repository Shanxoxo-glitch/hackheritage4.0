# SIH 2026 — PS 26094 Backend Engine

**AI-Powered Dynamic Mental Health Monitoring and Distress Prediction System**
for victims under the SC/ST Prevention of Atrocities (PoA) Act.

Built by **Shaan** | Backend & DevOps Lead

---

## What Is This?

This is the core backend API server powering the distress monitoring platform. It handles:

- **Victim onboarding** with AES-256 encrypted PII (name, phone, email never stored in plain text)
- **Legal case file tracking** across milestones: FIR → Chargesheet → Trial → Compensation
- **Daily check-in engine** (Tier 0 to Tier 4 escalation ladder)
- **IVRS missed-call webhook** — victim gives a missed call = zero-data check-in ✅
- **Twilio SMS & voice dispatch** for neutral reminders and wellness checks
- **SHA-256 hash-chained audit ledger** for court-admissible tamper-evident alert logs
- **Counsellor triage queue** ranked by `Composite Risk × Confidence × Hours Elapsed`
- **Quick-Exit API** — single tap purges session and redirects to weather.com 🔒

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entrypoint, CORS, startup
│   ├── config.py                # All environment settings & secrets
│   ├── database.py              # Async SQLAlchemy engine & session
│   │
│   ├── models/                  # PostgreSQL / SQLite database entities
│   │   ├── victim.py            # Victim profile (AES-256 encrypted PII)
│   │   ├── consent.py           # DPDP Act consent ledger (SAFE_PAUSE here)
│   │   ├── case.py              # Legal case file (FIR stage etc.)
│   │   ├── interaction.py       # PWA / SMS / IVRS interaction logs
│   │   ├── distress.py          # Multimodal distress scores from AI models
│   │   ├── alert.py             # Risk alerts (SHA-256 hash-chained)
│   │   └── intervention.py      # Official counsellor action records
│   │
│   ├── schemas/                 # Pydantic v2 request/response validators
│   │   ├── victim.py
│   │   ├── checkin.py
│   │   ├── perception.py
│   │   └── alert.py
│   │
│   ├── services/                # Core business logic
│   │   ├── encryption.py        # AES-256 Fernet PII encrypt/decrypt
│   │   ├── audit_ledger.py      # SHA-256 cryptographic hash chain engine
│   │   ├── scheduler.py         # Tier 0–4 check-in state machine
│   │   └── ivrs_gateway.py      # Twilio SMS & Voice IVRS integration
│   │
│   └── api/v1/                  # REST API endpoints
│       ├── auth.py              # Session auth + Quick-Exit /purge
│       ├── cases.py             # Victim onboarding & case management
│       ├── checkin.py           # Check-in telemetry submission
│       ├── telephony.py         # IVRS missed-call & SMS webhooks
│       ├── perception.py        # ML scoring model gateway proxy
│       └── escalate.py          # Risk alert router & triage queue
│
├── tests/
│   ├── test_encryption.py       # AES-256 encrypt/decrypt unit tests
│   ├── test_audit_ledger.py     # SHA-256 hash chain integrity tests
│   └── test_api_endpoints.py    # Full end-to-end integration tests
│
├── Dockerfile                   # Production multi-stage Docker build
├── docker-compose.yml           # One-command local container setup
└── requirements.txt             # All Python dependencies
```

---

## API Endpoints

| Method | Endpoint | What it does |
|--------|----------|-------------|
| `GET` | `/` | Health check & system info |
| `POST` | `/api/v1/auth/session` | Create covert HttpOnly cookie session |
| `GET/POST` | `/api/v1/auth/purge` | **Quick-Exit** — wipes session & redirects to weather.com |
| `POST` | `/api/v1/cases/victims` | Onboard a new victim (PII encrypted) |
| `POST` | `/api/v1/cases/files` | Register a legal case file |
| `GET` | `/api/v1/cases/files/{case_id}` | Fetch case file details |
| `POST` | `/api/v1/checkin/submit` | Submit a daily check-in (PWA/SMS/IVRS) |
| `GET` | `/api/v1/checkin/status/{case_id}` | Get current check-in Tier (0–4) |
| `POST` | `/api/v1/telephony/missed-call` | IVRS webhook — missed call = check-in |
| `POST` | `/api/v1/perception/score` | Store AI model distress scores |
| `POST` | `/api/v1/escalate/alerts` | Create a hash-chained risk alert |
| `GET` | `/api/v1/escalate/triage-queue` | Get counsellor triage queue (ranked) |

Interactive full docs: **http://127.0.0.1:8000/docs**

---

## Check-in Escalation Ladder

| Tier | Trigger | Action |
|------|---------|--------|
| Tier 0 | < 24h since last contact | Normal — scheduled prompt |
| Tier 1 | 24h – 72h missed | Sends neutral reminder SMS |
| Tier 2 | 72h – 120h missed | Sends wellness check SMS |
| Tier 3 | 120h – 168h missed | Triggers IVRS voice call to counsellor |
| Tier 4 | 7+ days **AND** (risk ≥ 0.70 **OR** threat detected) | District Protection Officer alert |

> ⚠️ **Tier 4 NEVER fires on silence alone.** The combined condition rule prevents false police raids if an abuser confiscates the victim's phone.

> ✅ **SAFE_PAUSE**: Victim can freeze check-in alerts anytime (travel, hospital) with zero penalty.

---

## Running Locally (Python)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the development server
```bash
python -m uvicorn app.main:app --reload
```

Server starts at: **http://127.0.0.1:8000**
Swagger docs at: **http://127.0.0.1:8000/docs**

> The SQLite database (`sql_app.db`) is auto-created on first run. No setup needed.

---

## Running with Docker

### 1. Make sure Docker Desktop is running

### 2. Build and start the container
```bash
docker compose up --build
```

Server starts at: **http://127.0.0.1:8000**

### 3. Stop and remove container + image (save space)
```bash
docker compose down --rmi all --volumes
```

### 4. Just stop (keep image for fast restart)
```bash
docker compose down
```

---

## Environment Variables (Optional)

Create a `.env` file in `backend/` to override defaults:

```env
# Twilio (leave blank for mock/dev mode)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_MOCK_MODE=false          # Set true to log SMS/calls locally (no charges)

# Security
SECRET_KEY=change-this-in-production
FERNET_KEY=your-32-byte-base64-fernet-key

# Quick-Exit redirect URL
QUICK_EXIT_REDIRECT_URL=https://weather.com
```

> In development, `TWILIO_MOCK_MODE=true` (default) — all SMS/calls are logged locally, no Twilio account needed.

---

## Running Tests

```bash
python -m pytest tests/
```

Expected output:
```
tests/test_api_endpoints.py ...     [ 42%]
tests/test_audit_ledger.py ..       [ 71%]
tests/test_encryption.py ..         [100%]

7 passed in 2.50s
```

---

## Team Integration Notes

This backend exposes the following integration points for teammates:

| Teammate | Their Work | Connects To |
|----------|-----------|-------------|
| **Sohon** | IndicBERT Sentiment + Threat + Voice-Stress models | `POST /api/v1/perception/score` |
| **Soham** | React PWA frontend + Counsellor Dashboard | `/api/v1/checkin/submit`, `/api/v1/auth/purge`, `/api/v1/escalate/triage-queue` |
| **Avik** | Sarvam-1 LangGraph dialogue agent | `/api/v1/chat/message` *(to be wired)* |

---

## Built By

**Shaan** — Backend Architecture, Database Design, Check-in Engine, Telephony Gateway, Cryptographic Audit Ledger, Docker & DevOps

*SIH 2026 — Team: Avik, Shaan, Sohon, Soham*
