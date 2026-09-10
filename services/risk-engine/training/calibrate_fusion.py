"""Proves confidence is honest: error must FALL as confidence RISES.
Run:  python -m training.calibrate_fusion"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.fusion import fuse
from app.schemas import FusionRequest, Sentiment, Threat, VoiceStress

N = 20_000
rng = np.random.default_rng(42)
NOISE = {"sentiment": 0.15, "threat": 0.10, "voice_stress": 0.20}
OUT = Path(__file__).resolve().parents[1] / "artifacts" / "fusion_calibration.json"

rows = []
for _ in range(N):
    truth = float(rng.beta(2, 5))
    req = FusionRequest(
        sentiment=Sentiment(score=float(np.clip(truth + rng.normal(0, NOISE["sentiment"]), 0, 1))) if rng.random() < 0.85 else None,
        threat=Threat(prob=float(np.clip(truth + rng.normal(0, NOISE["threat"]), 0, 1))) if rng.random() < 0.70 else None,
        voice_stress=VoiceStress(score=float(np.clip(truth + rng.normal(0, NOISE["voice_stress"]), 0, 1))) if rng.random() < 0.50 else None)
    out = fuse(req)
    rows.append((out.confidence, abs(out.composite_score - truth)))

rows.sort(key=lambda r: r[0])
bins, k = [], max(50, N // 10)
for i in range(0, N, k):
    chunk = rows[i:i + k]
    bins.append({"confidence": round(sum(c for c, _ in chunk) / len(chunk), 3),
                 "mae": round(sum(e for _, e in chunk) / len(chunk), 4),
                 "n": len(chunk)})

maes = [b["mae"] for b in bins]
drops = sum(1 for a, b in zip(maes, maes[1:]) if b < a)
verdict = "CALIBRATED" if drops >= len(maes) - 3 else "UNCALIBRATED"

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({
    "n_cases": N, "verdict": verdict, "bins": bins,
    "rule": "error must fall as confidence rises",
    "generated_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"verdict={verdict}  mae by confidence: {maes}")
print(f"saved -> {OUT}")
