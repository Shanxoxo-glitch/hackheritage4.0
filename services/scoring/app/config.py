"""
Scoring service configuration (every value env-overridable).

Model weights are NOT in git. At runtime they come from one of:
  * a bind mount           ./models -> /models          (docker-compose.yml, default)
  * HF Hub auto-download   SCORING_HF_AUTO_DOWNLOAD=1 + HF_TOKEN  (private repo Shota2811/ps26094-signals)
  * the monorepo ./models dir when running locally      (python -m uvicorn app.main:app --port 8100)
"""
import os
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]      # services/scoring in the repo, /app in the container
# monorepo root when running from a checkout; in the container /app has no such ancestor, so fall back
# to SERVICE_ROOT (models come from SCORING_MODELS_DIR=/models there anyway).
REPO_ROOT = SERVICE_ROOT.parents[1] if len(SERVICE_ROOT.parents) > 1 else SERVICE_ROOT

SERVICE_NAME = "scoring"
SERVICE_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"          # contracts #1-3 in contracts/api-contracts.md

MODELS_DIR = Path(os.environ.get("SCORING_MODELS_DIR", REPO_ROOT / "models"))
SENTIMENT_MODEL_DIR = Path(os.environ.get("SCORING_SENTIMENT_MODEL", MODELS_DIR / "distress_v3"))
_THREAT_CANDIDATES = [MODELS_DIR / "threat_contrastive_v1", MODELS_DIR / "threat_v7"]   # served, then fallback
THREAT_MODEL_DIR = Path(os.environ.get("SCORING_THREAT_MODEL") or
                        next((p for p in _THREAT_CANDIDATES if p.exists()), _THREAT_CANDIDATES[0]))
VOICE_MODEL_PATH = Path(os.environ.get("SCORING_VOICE_MODEL", MODELS_DIR / "voice_stress_ravdess.joblib"))

HF_REPO = os.environ.get("SCORING_HF_REPO", "Shota2811/ps26094-signals")
HF_AUTO_DOWNLOAD = os.environ.get("SCORING_HF_AUTO_DOWNLOAD", "0") == "1"

DEVICE = os.environ.get("SCORING_DEVICE", "cpu")                 # cpu | mps | cuda
DTYPE = os.environ.get("SCORING_DTYPE", "float32")               # float32 | bfloat16 (CPU-safe half precision)
WARM_ON_START = os.environ.get("SCORING_WARM_ON_START", "1") == "1"
ALLOW_AUDIO_URL = os.environ.get("SCORING_ALLOW_AUDIO_URL", "0") == "1"

SENTIMENT_LABELS = ["LOW", "MODERATE", "HIGH"]       # distress level; sentiment_score = expected level / 2
THREAT_LABELS = ["NOT_THREAT", "THREAT"]
VOICE_LABELS = ["NOT_STRESSED", "STRESSED"]

AUDIO_SR = 16000
MAX_TEXT_CHARS = 4000
MIN_AUDIO_SECONDS = 0.2
MAX_AUDIO_SECONDS = 120

THREAT_FLAG_THRESHOLD = float(os.environ.get("SCORING_THREAT_THRESHOLD", "0.5"))
CONFIDENCE_GATE = 0.60          # contracts/decision-policy.md: required confidence for automated intervention
