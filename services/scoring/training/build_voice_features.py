"""
Build the voice-stress feature table.

  python src/voice/build_voice_dataset.py --source synthetic   # smoke test
  python src/voice/build_voice_dataset.py --source ravdess     # after download_ravdess.sh

RAVDESS filename: 03-01-EE-II-SS-RR-AA.wav
  EE emotion 01 neutral 02 calm 03 happy 04 sad 05 angry 06 fearful 07 disgust 08 surprised
  II intensity (01 normal, 02 strong), AA actor 01-24
Stress label: NOT_STRESSED = neutral/calm/happy, STRESSED = sad/angry/fearful.
disgust & surprised are dropped (ambiguous arousal). Split is BY ACTOR
(speaker-independent): 1-18 train, 19-21 val, 22-24 test.

Output: training/data/voice_features_<source>.csv
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.voice_features import SR, extract_features, load_audio  # noqa: E402

EMOTION = {"01": "neutral", "02": "calm", "03": "happy", "04": "sad",
           "05": "angry", "06": "fearful", "07": "disgust", "08": "surprised"}
STRESS = {"neutral": 0, "calm": 0, "happy": 0, "sad": 1, "angry": 1, "fearful": 1}


def ravdess_items(root):
    items = []
    for wav in sorted(Path(root).rglob("*.wav")):
        parts = wav.stem.split("-")
        if len(parts) != 7 or parts[0] != "03" or parts[1] != "01":
            continue
        emotion = EMOTION.get(parts[2])
        if emotion not in STRESS:
            continue
        actor = int(parts[6])
        split = "train" if actor <= 18 else ("val" if actor <= 21 else "test")
        items.append({"file": str(wav), "actor": actor, "emotion": emotion,
                      "intensity": int(parts[3]), "label": STRESS[emotion], "split": split})
    return items


def synthetic_items(root):
    df = pd.read_csv(Path(root) / "labels.csv")
    trv, te = train_test_split(df, test_size=0.15, random_state=42, stratify=df["label"])
    tr, va = train_test_split(trv, test_size=0.1765, random_state=42, stratify=trv["label"])
    items = []
    for split, part in (("train", tr), ("val", va), ("test", te)):
        for _, r in part.iterrows():
            items.append({"file": str(Path(root) / r["file"]), "actor": -1, "emotion": r["label_name"].lower(),
                          "intensity": 0, "label": int(r["label"]), "split": split})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["ravdess", "synthetic"], required=True)
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    root = args.root or {"ravdess": "training/data/raw/ravdess", "synthetic": "training/data/raw/voice_synthetic"}[args.source]
    items = ravdess_items(root) if args.source == "ravdess" else synthetic_items(root)
    if not items:
        sys.exit(f"No audio found under {root}. "
                 + ("Run: bash training/download_ravdess.sh" if args.source == "ravdess"
                    else "Run: python training/make_synthetic_smoke_set.py"))
    print(f"{len(items)} clips from {root}")

    rows = []
    for it in tqdm(items, desc="features"):
        try:
            feats = extract_features(load_audio(it["file"], SR), SR)
        except Exception as e:
            print("skip", it["file"], e)
            continue
        rows.append({**it, "label_name": "STRESSED" if it["label"] else "NOT_STRESSED", **feats})
    df = pd.DataFrame(rows)
    out = f"training/data/voice_features_{args.source}.csv"
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(out, index=False)
    print("\nrows:", len(df), " features:", len(df.columns) - 7)
    print(pd.crosstab(df["split"], df["label_name"]))
    if args.source == "ravdess":
        print(pd.crosstab(df["emotion"], df["split"]))
    print("Saved:", out)


if __name__ == "__main__":
    main()
