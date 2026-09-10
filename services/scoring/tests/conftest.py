"""
Shared fixtures. Contract tests (test_signals.py) mock the three model singletons but
run the REAL request parsing + audio decoding on generated WAV bytes.
Integration tests (test_integration.py) load the real weights and a real RAVDESS clip;
they skip themselves when those files are absent (CI has neither).
"""
import io
import os
import sys
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("SCORING_WARM_ON_START", "0")      # never auto-load weights in the test process
os.environ.setdefault("SCORING_HF_AUTO_DOWNLOAD", "0")

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

RAVDESS_DIR = Path(os.environ.get("SCORING_RAVDESS_DIR", SERVICE_ROOT / "training" / "data" / "raw" / "ravdess"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: loads the real local models and a real RAVDESS clip (auto-skipped when absent)")


def make_wav_bytes(seconds=1.0, sr=16000, f0=180.0, channels=1, seed=0) -> bytes:
    """A real RIFF/WAV file (PCM_16) with a modulated tone; goes through the real decode path."""
    import soundfile as sf
    rng = np.random.default_rng(seed)
    t = np.arange(int(sr * seconds)) / sr
    y = 0.4 * np.sin(2 * np.pi * f0 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t)) + 0.02 * rng.standard_normal(t.size)
    data = np.stack([y] * channels, axis=1) if channels > 1 else y
    buf = io.BytesIO()
    sf.write(buf, data.astype(np.float32), sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture(scope="session")
def wav_bytes():
    return make_wav_bytes()


@pytest.fixture(scope="session")
def wav_bytes_48k_stereo():
    return make_wav_bytes(sr=48000, channels=2)


@pytest.fixture(scope="session")
def short_wav_bytes():
    return make_wav_bytes(seconds=0.05)


@pytest.fixture(scope="session")
def ravdess_wav():
    """One real RAVDESS clip (fearful, actor 1) if the dataset is present locally, else None."""
    if not RAVDESS_DIR.exists():
        return None
    files = sorted(RAVDESS_DIR.rglob("03-01-06-01-01-01-01.wav")) or sorted(RAVDESS_DIR.rglob("*.wav"))
    return files[0] if files else None
