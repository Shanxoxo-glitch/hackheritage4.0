"""
Three module-level lazy singletons: get_sentiment(), get_threat(), get_voice().

Heavy imports (torch / transformers / librosa) happen inside the loaders, so
`app.main` imports with only fastapi + numpy present (CI runs the contract
tests with mocked models and no model download). First call warms the model;
later calls are ~20-60 ms on CPU for short texts.
"""
import logging
import threading
import time
from pathlib import Path

from . import config as C

log = logging.getLogger("scoring.models")

_lock = threading.RLock()
_cache = {}
_errors = {}            # name -> (exception, unix_time); retried after _RETRY_SECONDS
_RETRY_SECONDS = 30


def _ensure_local(path: Path, subpath: str) -> Path:
    if path.exists():
        return path
    if C.HF_AUTO_DOWNLOAD:
        from huggingface_hub import snapshot_download
        log.info("downloading %s from %s", subpath, C.HF_REPO)
        snapshot_download(repo_id=C.HF_REPO, allow_patterns=[subpath, f"{subpath}/*"],
                          local_dir=str(C.MODELS_DIR))
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Mount ./models:/models or set SCORING_HF_AUTO_DOWNLOAD=1 "
            f"with HF_TOKEN (repo {C.HF_REPO}).")
    return path


def _get(name, loader):
    with _lock:
        if name in _cache:
            return _cache[name]
        err = _errors.get(name)
        if err and time.time() - err[1] < _RETRY_SECONDS:
            raise err[0]
        try:
            t0 = time.time()
            obj = loader()
            _cache[name] = obj
            _errors.pop(name, None)
            log.info("loaded %s in %.1fs", name, time.time() - t0)
            return obj
        except Exception as e:
            _errors[name] = (e, time.time())
            log.warning("failed to load %s: %s: %s", name, type(e).__name__, e)
            raise


def get_sentiment():
    def load():
        from .text_models import TextClassifier
        return TextClassifier(_ensure_local(C.SENTIMENT_MODEL_DIR, C.SENTIMENT_MODEL_DIR.name),
                              C.SENTIMENT_LABELS, name=C.SENTIMENT_MODEL_DIR.name,
                              device=C.DEVICE, dtype=C.DTYPE)
    return _get("sentiment", load)


def get_threat():
    def load():
        from .text_models import TextClassifier
        return TextClassifier(_ensure_local(C.THREAT_MODEL_DIR, C.THREAT_MODEL_DIR.name),
                              C.THREAT_LABELS, name=C.THREAT_MODEL_DIR.name,
                              device=C.DEVICE, dtype=C.DTYPE)
    return _get("threat", load)


def get_voice():
    def load():
        from .voice_model import VoiceStressScorer
        return VoiceStressScorer(_ensure_local(C.VOICE_MODEL_PATH, C.VOICE_MODEL_PATH.name))
    return _get("voice", load)


_LOADERS = {"sentiment": get_sentiment, "threat": get_threat, "voice": get_voice}
_PATHS = {"sentiment": C.SENTIMENT_MODEL_DIR, "threat": C.THREAT_MODEL_DIR, "voice": C.VOICE_MODEL_PATH}


def warm_all():
    out = {}
    for name, fn in _LOADERS.items():
        try:
            fn()
            out[name] = True
        except Exception:
            out[name] = False
    return out


def status():
    return {name: {"loaded": name in _cache, "path": str(_PATHS[name]),
                   "version": getattr(_cache.get(name), "name", None),
                   "error": (f"{type(_errors[name][0]).__name__}: {_errors[name][0]}"[:300]
                             if name in _errors else None)}
            for name in _LOADERS}


def reset():
    with _lock:
        _cache.clear()
        _errors.clear()
