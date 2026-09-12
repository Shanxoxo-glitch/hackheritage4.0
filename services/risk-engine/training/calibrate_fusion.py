"""Calibration v3 -- proves confidence is honest, two ways:
1) error FALLS as confidence RISES (reliability curve; Spearman(conf, mae) <= -0.30)
2) the 95% credible interval covers ~85-99.5% of truth (coverage)
Also MEASURES per-detector noise -> artifacts/detector_noise.json.
v3 fixes: mkdir artifacts/ (v2 FileNotFoundError); fuse(..., noise=) is hermetic
(no feedback loop with the file this script writes); Spearman criterion replaces
the fragile 'monotone drops' count.
NOTE: measured_sigma here is the SIMULATION's generator sigma. Production
weights must come from residuals on labeled real cases.
Run:  python -m training.calibrate_fusion"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.fusion import DEFAULT_NOISE, fuse
from app.schemas import FusionRequest, Sentiment, Threat, VoiceStress

N = 20_000
TRUE_NOISE = {"sentiment": 0.15, "threat": 0.10, "voice_stress": 0.20}
PRESENCE = {"sentiment": 0.85, "threat": 0.70, "voice_stress": 0.50}
OUT = Path(__file__).resolve().parents[1] / "artifacts"


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


rng = np.random.default_rng(42)
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
    out = fuse(FusionRequest(**kwargs), noise=DEFAULT_NOISE)   # hermetic
    z = abs(out.composite_score - truth) / max(out.posterior_std, 1e-9)
    rows.append((out.confidence, abs(out.composite_score - truth), z))

OUT.mkdir(parents=True, exist_ok=True)

measured = {k: round(float(np.std(v)) if len(v) else TRUE_NOISE[k], 4)
            for k, v in err.items()}
(OUT / "detector_noise.json").write_text(json.dumps(
    {"n": N, "measured_sigma": measured, "generator_sigma": TRUE_NOISE,
     "note": "simulation-measured; replace with labeled production residuals",
     "generated_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"measured sigma: {measured}")

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

conf = np.array([r[0] for r in rows])
mae = np.array([r[1] for r in rows])
zs = [r[2] for r in rows]
spear = _spearman(conf, mae)
coverage = sum(1 for z in zs if z <= 1.96) / len(rows)
drops = sum(1 for a, b in zip(bins, bins[1:]) if b["mae"] < a["mae"])
verdict = ("CALIBRATED" if spear <= -0.30 and 0.85 <= coverage <= 0.995
           else "UNCALIBRATED")
suggest = (round(sorted(zs)[int(0.95 * len(zs))] / 1.96, 3)
           if verdict != "CALIBRATED" else None)

(OUT / "fusion_calibration.json").write_text(json.dumps(
    {"n_cases": N, "verdict": verdict,
     "spearman_conf_vs_mae": round(spear, 3),
     "monotone_drops": drops, "n_bins": len(bins),
     "overall_coverage_95": round(coverage, 4),
     "reliability": bins, "measured_sigma": measured,
     "rules": ["spearman(confidence, mae) <= -0.30",
               "95% interval covers 85-99.5% of truth"],
     "inflate_std_by_if_uncalibrated": suggest,
     "generated_at": datetime.now(timezone.utc).isoformat()}, indent=2))
print(f"verdict={verdict}  coverage={coverage:.3f}  spearman={spear:+.3f}")
print(f"mae by confidence: {[b['mae'] for b in bins]}")
print(f"saved -> {OUT / 'fusion_calibration.json'}")
