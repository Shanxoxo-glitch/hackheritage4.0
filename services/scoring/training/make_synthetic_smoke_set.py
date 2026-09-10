"""
Synthetic SMOKE-TEST audio (NOT real speech, NOT a real result).

Generates 60 'calm' + 60 'stressed' 2.5 s clips with numpy: harmonic tone
bursts at syllable rate, with pitch / jitter / tremor / rate / noise set
higher for 'stressed'. Purpose: prove the feature -> LightGBM -> API path
runs end-to-end before the real RAVDESS data is downloaded.

Output: training/data/voice_synthetic/*.wav + labels.csv
"""
import os

import numpy as np
import pandas as pd
import soundfile as sf

OUT_DIR = "training/data/raw/voice_synthetic"
SR = 16000
N_PER_CLASS = 60


def _smooth(x, w):
    w = max(int(w), 1)
    return np.convolve(x, np.ones(w) / w, mode="same")


def synthesize(stressed, rng, sr=SR, dur=2.5):
    n = int(sr * dur)
    t = np.arange(n) / sr
    if stressed:
        f0_base, jitter, rate = rng.uniform(190, 300), 0.03, rng.uniform(4.5, 6.5)
        tremor, noise, vib = 0.35, 0.05, 0.03
    else:
        f0_base, jitter, rate = rng.uniform(100, 160), 0.003, rng.uniform(2.5, 3.5)
        tremor, noise, vib = 0.05, 0.01, 0.01
    wobble = _smooth(rng.standard_normal(n), 400) * 20.0          # unit-variance slow noise
    f0 = f0_base * (1 + jitter * wobble) * (1 + vib * np.sin(2 * np.pi * 5.5 * t))
    phase = 2 * np.pi * np.cumsum(f0) / sr
    y = sum((0.55 ** h) * np.sin(h * phase) for h in range(1, 6))
    gate = (np.sin(2 * np.pi * rate * t) > -0.2).astype(float)      # syllable on/off
    env = _smooth(gate, 0.02 * sr) * (1 + tremor * np.sin(2 * np.pi * rng.uniform(6, 9) * t))
    y = y * env + noise * rng.standard_normal(n)
    y = y / (np.abs(y).max() + 1e-9) * rng.uniform(0.3, 0.8)
    return y.astype(np.float32)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rng = np.random.default_rng(42)
    rows = []
    for label, name in ((0, "calm"), (1, "stressed")):
        for i in range(N_PER_CLASS):
            fn = f"{name}_{i:03d}.wav"
            sf.write(os.path.join(OUT_DIR, fn), synthesize(bool(label), rng), SR)
            rows.append({"file": fn, "label": label, "label_name": "STRESSED" if label else "NOT_STRESSED"})
    pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, "labels.csv"), index=False)
    print(f"Wrote {len(rows)} synthetic clips to {OUT_DIR}  (SMOKE TEST ONLY)")


if __name__ == "__main__":
    main()
