# ML Model Registry

Weights are never committed. Served copies live in the private HF repo below (`services/scoring/training/push_to_hub.py`)
and are bind-mounted into the scoring container as `/models` (`docker-compose.yml`). Metrics: `artifacts/signal_eval.json`.

| Model Name | Base Architecture | Training Corpus | HF Repository | Promoted By |
| :--- | :--- | :--- | :--- | :--- |
| distress_v3 (sentiment signal) | MuRIL `google/muril-base-cased`, 3-class + temperature calibration | distress V3: 480 hand-written/templated EN + Hinglish rows, leak-aware split | Shota2811/ps26094-signals `distress_v3/` | Sohon |
| threat_contrastive_v1 (threat signal, served) | MuRIL, binary, CE + supervised-contrastive on [CLS], temperature calibration | threat V7 corpus: 520 EN + Hinglish rows (synthetic V5+V6, adversarial-tested) | Shota2811/ps26094-signals `threat_contrastive_v1/` | Sohon |
| threat_v7 (threat signal, fallback baseline) | MuRIL, binary cross-entropy + temperature calibration | same corpus | Shota2811/ps26094-signals `threat_v7/` | Sohon |
| voice_stress_ravdess (voice signal) | librosa 89-dim features → LightGBM (numpy tree inference) | RAVDESS speech, 1,056 clips, 24 actors, speaker-independent CV | Shota2811/ps26094-signals `voice_stress_ravdess.joblib` | Sohon |

Planned upgrades (tracked in `services/scoring/README.md`): threat corpus from Indian Kanoon (`training/corpus/threat_corpus_builder.py`,
target ≥ 2,500 rows) retrained with the contrastive objective (`training/train_threat.py --objective contrastive`); Indian-accent voice
adaptation rows (`training/train_voice.py --extra-features-csv`).
