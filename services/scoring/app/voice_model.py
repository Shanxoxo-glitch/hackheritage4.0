"""
Voice-stress scorer: audio -> librosa features -> dumped LightGBM trees (numpy) -> P(stressed).

LightGBM is never imported at inference: torch and lightgbm in one process
segfault on macOS (two OpenMP runtimes). Training dumps the trees and
verifies app.tree_eval reproduces predict_proba before the bundle is saved.
"""
from pathlib import Path

import joblib
import librosa
import numpy as np

from .config import AUDIO_SR, VOICE_LABELS
from .tree_eval import predict_proba as np_predict_proba
from .voice_features import SUMMARY_FEATURES, extract_features


class VoiceStressScorer:
    def __init__(self, path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"voice model not found: {path}")
        bundle = joblib.load(path)
        if "model_dump" not in bundle:
            raise ValueError(f"{path} is an old-format bundle (contains a LightGBM object); retrain with training/train_voice.py")
        self.path, self.name = path, path.stem
        self.dump = bundle["model_dump"]
        self.feature_names = list(bundle["feature_names"])
        self.label_names = list(bundle.get("label_names", VOICE_LABELS))
        self.source = bundle.get("source", "unknown")
        self.trained_on = bundle.get("trained_on", self.source)
        self.metrics = bundle.get("metrics", {})
        self.sr = int(bundle.get("sr", AUDIO_SR))

    def features(self, y, sr):
        y = np.asarray(y, dtype=np.float32)
        if sr != self.sr:
            y = librosa.resample(y, orig_sr=sr, target_sr=self.sr)
        return extract_features(y, self.sr)

    def score_features(self, X):
        """X: array [n, len(feature_names)] in feature_names order -> P(stressed) [n]."""
        return np_predict_proba(self.dump, np.asarray(X, dtype=float))[:, 1]

    def score_array(self, y, sr):
        feats = self.features(y, sr)
        X = np.array([[feats.get(f, 0.0) for f in self.feature_names]], dtype=float)
        p = float(self.score_features(X)[0])
        idx = 1 if p >= 0.5 else 0
        return {
            "label": self.label_names[idx], "score": p, "confidence": float(max(p, 1.0 - p)),
            "model": self.name, "trained_on": self.trained_on, "meaningful": self.source == "ravdess",
            "audio_seconds": round(feats.get("duration_s", 0.0), 3),
            "features_summary": {k: round(feats[k], 4) for k in SUMMARY_FEATURES if k in feats},
        }

    def info(self):
        return {"name": self.name, "path": str(self.path), "labels": self.label_names,
                "trained_on": self.trained_on, "n_features": len(self.feature_names),
                "n_trees": len(self.dump.get("tree_info", [])), "sample_rate": self.sr,
                "inference": "numpy_tree_eval (lightgbm-free)", "metrics": self.metrics}
