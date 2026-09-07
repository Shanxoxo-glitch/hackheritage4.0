"""Score one or more audio files:  python src/voice/predict_voice.py a.wav b.wav [--model path]"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.voice_model import VoiceStressScorer  # noqa: E402
from app.voice_features import SR, load_audio  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("--model", default=None)
args = ap.parse_args()
scorer = VoiceStressScorer(args.model)
print(f"model={scorer.name} trained_on={scorer.source}")
for f in args.files:
    r = scorer.score_array(load_audio(f, SR), SR)
    print(f"\n{f}\n  {r['label']}  P(stressed)={r['score']:.3f}\n  {json.dumps(r['features_summary'])}")
