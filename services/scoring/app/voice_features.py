"""
Acoustic feature extraction for voice-stress.

librosa-based features used by the trained RAVDESS LightGBM model.
"""

import librosa
import numpy as np

SR = 16000
HOP = 256
N_FFT = 1024
N_MFCC = 20

SUMMARY_FEATURES = [
    "duration_s",
    "f0_mean",
    "f0_std",
    "f0_cv",
    "f0_range",
    "jitter",
    "voiced_fraction",
    "rms_mean",
    "rms_std",
    "shimmer",
    "pause_ratio",
    "onset_rate",
    "spectral_centroid_mean",
]


def load_audio(path, sr=SR):
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y


def _stats(name, arr, feats, minmax=False):
    arr = np.asarray(arr, dtype=float).ravel()

    if arr.size == 0:
        arr = np.zeros(1)

    feats[f"{name}_mean"] = arr.mean()
    feats[f"{name}_std"] = arr.std()

    if minmax:
        feats[f"{name}_min"] = arr.min()
        feats[f"{name}_max"] = arr.max()


def extract_features(y, sr=SR):
    y = np.nan_to_num(
        np.asarray(y, dtype=np.float32).ravel()
    )

    if y.size == 0:
        y = np.zeros(int(0.5 * sr), dtype=np.float32)

    peak = float(np.abs(y).max())

    if peak > 0:
        y = y / peak * 0.9

    yt, _ = librosa.effects.trim(y, top_db=30)

    if yt.size >= int(0.2 * sr):
        y = yt

    min_len = int(0.5 * sr)

    if y.size < min_len:
        y = np.pad(
            y,
            (0, min_len - y.size),
        )

    feats = {}

    duration = y.size / sr
    feats["duration_s"] = duration

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=N_MFCC,
        n_fft=N_FFT,
        hop_length=HOP,
    )

    for i in range(N_MFCC):
        feats[f"mfcc{i}_mean"] = mfcc[i].mean()
        feats[f"mfcc{i}_std"] = mfcc[i].std()

    dm = librosa.feature.delta(mfcc)

    for i in range(N_MFCC):
        feats[f"dmfcc{i}_absmean"] = np.abs(dm[i]).mean()

    f0, _, _ = librosa.pyin(
        y,
        fmin=60,
        fmax=500,
        sr=sr,
        frame_length=2048,
        hop_length=HOP,
    )

    f0v = f0[np.isfinite(f0)]

    if f0v.size >= 2:
        feats["f0_mean"] = f0v.mean()
        feats["f0_std"] = f0v.std()
        feats["f0_min"] = f0v.min()
        feats["f0_max"] = f0v.max()
        feats["f0_median"] = np.median(f0v)
        feats["f0_range"] = f0v.max() - f0v.min()

        feats["jitter"] = (
            np.abs(np.diff(f0v)).mean()
            / (f0v.mean() + 1e-8)
        )

        feats["f0_cv"] = (
            f0v.std()
            / (f0v.mean() + 1e-8)
        )

        feats["f0_range_rel"] = (
            (f0v.max() - f0v.min())
            / (f0v.mean() + 1e-8)
        )

    else:
        for k in (
            "f0_mean",
            "f0_std",
            "f0_min",
            "f0_max",
            "f0_median",
            "f0_range",
            "jitter",
            "f0_cv",
            "f0_range_rel",
        ):
            feats[k] = 0.0

    feats["voiced_fraction"] = (
        f0v.size / max(f0.size, 1)
    )

    rms = librosa.feature.rms(
        y=y,
        frame_length=N_FFT,
        hop_length=HOP,
    )[0]

    _stats(
        "rms",
        rms,
        feats,
        minmax=True,
    )

    feats["rms_cv"] = (
        rms.std()
        / (rms.mean() + 1e-8)
    )

    feats["shimmer"] = (
        np.abs(np.diff(rms)).mean()
        / (rms.mean() + 1e-8)
        if rms.size > 1
        else 0.0
    )

    feats["pause_ratio"] = (
        float(
            (rms < 0.1 * rms.max()).mean()
        )
        if rms.max() > 0
        else 1.0
    )

    _stats(
        "zcr",
        librosa.feature.zero_crossing_rate(
            y,
            frame_length=N_FFT,
            hop_length=HOP,
        )[0],
        feats,
    )

    _stats(
        "spectral_centroid",
        librosa.feature.spectral_centroid(
            y=y,
            sr=sr,
            n_fft=N_FFT,
            hop_length=HOP,
        )[0],
        feats,
    )

    _stats(
        "spectral_bandwidth",
        librosa.feature.spectral_bandwidth(
            y=y,
            sr=sr,
            n_fft=N_FFT,
            hop_length=HOP,
        )[0],
        feats,
    )

    _stats(
        "spectral_rolloff",
        librosa.feature.spectral_rolloff(
            y=y,
            sr=sr,
            n_fft=N_FFT,
            hop_length=HOP,
        )[0],
        feats,
    )

    _stats(
        "spectral_flatness",
        librosa.feature.spectral_flatness(
            y=y,
            n_fft=N_FFT,
            hop_length=HOP,
        )[0],
        feats,
    )

    onsets = librosa.onset.onset_detect(
        y=y,
        sr=sr,
        hop_length=HOP,
    )

    feats["onset_rate"] = len(onsets) / duration

    return {
        k: float(np.nan_to_num(v))
        for k, v in feats.items()
    }


def feature_names():
    rng = np.random.default_rng(0)

    return list(
        extract_features(
            rng.standard_normal(SR).astype(np.float32) * 0.05,
            SR,
        ).keys()
    )
