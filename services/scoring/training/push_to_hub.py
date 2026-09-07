"""
Upload the served weights to the private HF repo (models/REGISTRY.md).

  huggingface-cli login                          # once
  PYTHONPATH=. python training/push_to_hub.py    # uploads $SCORING_MODELS_DIR -> Shota2811/ps26094-signals (private)

Layout on the hub mirrors SCORING_MODELS_DIR:
  threat_v7/ distress_v3/ voice_stress_ravdess.joblib voice_metrics_ravdess.json
The Dockerfile / app.models pull the same layout with snapshot_download.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.config import HF_REPO, MODELS_DIR  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=HF_REPO)
ap.add_argument("--models-dir", default=str(MODELS_DIR))
ap.add_argument("--public", action="store_true")
args = ap.parse_args()

from huggingface_hub import HfApi  # noqa: E402

api = HfApi()
api.create_repo(args.repo, private=not args.public, exist_ok=True)
api.upload_folder(repo_id=args.repo, folder_path=args.models_dir,
                  allow_patterns=["threat_v7/*", "distress_v3/*", "voice_stress_ravdess.joblib",
                                  "voice_metrics_ravdess.json", "voice_feature_order_ravdess.json"],
                  ignore_patterns=["**/checkpoint-*", "**/training_args.bin"],
                  commit_message="scoring weights: threat_v7, distress_v3, voice_stress_ravdess")
print(f"uploaded {args.models_dir} -> https://huggingface.co/{args.repo}")
