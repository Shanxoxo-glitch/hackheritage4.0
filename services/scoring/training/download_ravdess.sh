#!/usr/bin/env bash
# RAVDESS speech-only archive (Livingstone & Russo, 2018), Zenodo record 1188976.
# File : Audio_Speech_Actors_01-24.zip   Size: ~208 MB   Licence: CC BY-NC-SA 4.0
# 1440 wav files, 24 actors, 8 emotions, 2 intensities. Speaker-independent
# split used by training/build_voice_features.py: actors 1-18 train, 19-21 val, 22-24 test.
set -euo pipefail
cd "$(dirname "$0")/.."
URL="https://zenodo.org/records/1188976/files/Audio_Speech_Actors_01-24.zip?download=1"
DEST="training/data/raw/ravdess"
ZIP="$DEST/Audio_Speech_Actors_01-24.zip"
mkdir -p "$DEST"
if [ ! -f "$ZIP" ]; then
  echo "Downloading RAVDESS speech (~208 MB) from Zenodo ..."
  curl -L --progress-bar -o "$ZIP" "$URL"
fi
unzip -q -o "$ZIP" -d "$DEST"
echo "wav files: $(find "$DEST" -name '*.wav' | wc -l | tr -d ' ')   (expected 1440)"
