import os
import sys
from pathlib import Path

# never load real weights in the test suite
os.environ.setdefault("SCORING_WARM_ON_START", "0")
os.environ.setdefault("SCORING_HF_AUTO_DOWNLOAD", "0")

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
