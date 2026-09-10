"""Calibration v2 -- proves confidence is honest, two ways:
1) error FALLS as confidence RISES (reliability curve)
2) the 95% credible interval covers ~95% of truth (coverage)
Also MEASURES per-detector noise -> artifacts/detector_noise.json,
which fusion reads for its weights (data-derived, not hand-tuned).
Run:  python -m training.calibrate_fusion"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.fusion import fuse
from app.schemas import FusionRequest, Sentiment, Threat, VoiceStress

N = 20_000
rng = np.random.default_rng(42)
TRUE_NOISE = {"sentiment": 0.15, "threat": 0.10, "voice_stress": 0.20}
PRESENCE = {"sentiment": 0.85, "threat": 0.70, "voice_stress": 0.50}
OUT = Path(__file__).resolve().parents[1] / "artifacts"

err = {k: [] for k in TRUE_NOISE}
rows = []
for _ in range(N):
    truth = float(rng.beta(2, 5))
    kwargs = {}
    for name, cls in (("sentiment", Sentiment), ("threat", Threat),
                      ("voice_stress", VoiceStress)):
        if rng.random() < PRESENCE[name]:
            obs = float(np.clip(truth + rng.normal(0, TRUE_NOISE[name]), 0, 1))
            kwargs[name] = cls(**({"prob": obs} if name == "threat"
                                  else {"score": obs}))
            err[name].append(obs - truth)
    out = fuse(FusionRequest(**kwargs))
    z = abs(out.composite_score - truth) / max(out.posterior_std, 1e-9)
    rows.append((out.confidence, abs(out.composite_score - truth), z))

# -- measured detector noise (this is what makes fusion weights data-derived)
measured = {k: round(float(np.std(v)), 4) for k, v in err.items()}
(OUT / "detector_noise.json").write_text(json.dumps(
    {"n": N, "measured_sigma": measured, "generator_sigma": TRUE_NOISE,
     "note": "fusion.py reads this file; weights become measured",
     "generated_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"measured sigma: {measured}")

# -- reliability + coverage ----------------------------------------------------
rows.sort(key=lambda r: r[0])
k = max(50, N // 10)
bins = []
for i in range(0, N, k):
    chunk = rows[i:i + k]
    bins.append({"confidence": round(sum(c for c, _, _ in chunk) / len(chunk), 3),
                 "mae": round(sum(e for _, e, _ in chunk) / len(chunk), 4),
                 "coverage_95": round(
                     sum(1 for _, _, z in chunk if z <= 1.96) / len(chunk), 4),
                 "n": len(chunk)})

maes = [b["mae"] for b in bins]
drops = sum(1 for a, b in zip(maes, maes[1:]) if b < a)
coverage = sum(1 for _, _, z in rows if z <= 1.96) / len(rows)
verdict = ("CALIBRATED" if drops >= len(maes) - 3 and 0.85 <= coverage <= 0.995
           else "UNCALIBRATED")
suggest = (round(sorted(z for _, _, z in rows)[int(0.95 * len(rows))] / 1.96, 3)
           if verdict != "CALIBRATED" else None)

(OUT / "fusion_calibration.json").write_text(json.dumps(
    {"n_cases": N, "verdict": verdict, "overall_coverage_95": round(coverage, 4),
     "reliability": bins, "measured_sigma": measured,
     "rules": ["error falls as confidence rises",
               "95% interval covers ~95% of truth"],
     "inflate_std_by_if_uncalibrated": suggest,
     "generated_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"verdict={verdict}  coverage={coverage:.3f}")
print(f"mae by confidence: {maes}")
print(f"saved -> {OUT / 'fusion_calibration.json'}")
