# services/scoring — Perception signals (Sohon)

Turns victim text (English / Hindi / Hinglish) and short voice clips into calibrated perception
signals for the rest of PS 26094. FastAPI on **:8100**, CPU-only, self-hosted, no external API calls.

```
text  ──► MuRIL threat_contrastive_v1 ──► threat_flag + calibrated prob      ┐
text  ──► MuRIL distress_v3           ──► LOW / MODERATE / HIGH + score      ├─► JSON ─► backend :8400 ─► risk engine :8200
audio ──► librosa 89 features ─► LightGBM trees (numpy) ──► P(stressed)      ┘
```

| Signal | Model | Route | Held-out performance |
| :--- | :--- | :--- | :--- |
| **threat** (intimidation / coercion) | MuRIL `threat_contrastive_v1` (CE + SupCon) + temperature calibration; `threat_v7` fallback | `POST /v1/signals/text` (#1), `POST /v1/signals/threat` (#3) | F1 **0.974**, ROC-AUC 0.998, hard negatives 0.955; adversarial 50/51 |
| **sentiment** (distress level) | MuRIL `distress_v3` + temperature calibration | `POST /v1/signals/text` (#1) | macro-F1 **0.907**; adversarial 34/37 |
| **voice stress** | librosa → LightGBM, numpy tree inference | `POST /v1/signals/voice` (#2) | speaker-independent CV accuracy **0.752**, ROC-AUC 0.824 |

Full metrics, per-class / per-language / per-category breakdowns and calibration curves:
[`models/REGISTRY.md`](../../models/REGISTRY.md) and [`artifacts/signal_eval.json`](../../artifacts/signal_eval.json).

> Honest framing: the text corpora are hand-written / synthetic prototypes and the voice model is
> trained on **acted** English speech (RAVDESS). These are real held-out numbers on that data, not
> production validation. A calibrated score is a model score, never a clinical or forensic probability.

## Run it

```bash
# local (weights in ../../models)
PYTHONPATH=. python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
# container (weights bind-mounted)
docker build -t sih-scoring . && docker run -p 8100:8100 -v "$PWD/../../models:/models:ro" sih-scoring
# whole stack
make up            # docker compose: scoring on :8100 with ./models mounted
```

Docs at `http://localhost:8100/docs`. Weights are **not** in git — they come from the bind mount, or
from the private HF repo when `SCORING_HF_AUTO_DOWNLOAD=1` with `HF_TOKEN`.

## API

`GET /healthz` — per-model load status (`?warm=1` forces loading).

**`POST /v1/signals/text`** (contract #1) → `sentiment` + `threat`
```bash
curl -s localhost:8100/v1/signals/text -H 'content-type: application/json' \
  -d '{"text":"Case wapas le lo warna tumhare bhai ko uthwa lenge.","interaction_id":"int-1"}'
```
```json
{"schema_version":"1.0","request_id":"…","interaction_id":"int-1",
 "sentiment":{"label":"LOW","level":0,"sentiment_score":0.0096,"probs":{…},"confidence":0.985,
              "entropy":0.080,"calibrated":true,"model_version":"distress_v3"},
 "threat":{"threat_flag":true,"prob":0.988,"raw_prob":0.619,"confidence":0.988,"entropy":0.091,
           "calibrated":true,"model_version":"threat_contrastive_v1"},
 "flags":["threat_without_expressed_distress"],"latency_ms":73}
```

**`POST /v1/signals/threat`** (contract #3) → the `threat` object only.

**`POST /v1/signals/voice`** (contract #2) — the same clip in any of three encodings, identical response:
```bash
curl -s localhost:8100/v1/signals/voice -F "file=@clip.wav"                          # multipart
curl -s localhost:8100/v1/signals/voice --data-binary @clip.wav -H 'content-type: audio/wav'
curl -s localhost:8100/v1/signals/voice -H 'content-type: application/json' -d '{"audio_base64":"…"}'
```
```json
{"voice":{"label":"STRESSED","voice_stress_score":0.859,"confidence":0.859,"audio_seconds":1.728,
          "features_summary":{"f0_mean":147.5,"f0_cv":0.122,"jitter":0.022,"shimmer":0.173,…},
          "model_version":"voice_stress_ravdess","trained_on":"ravdess_all_24_actors"},
 "flags":[],"latency_ms":984}
```
WAV/FLAC/OGG, mono or stereo, any sample rate, 0.2–120 s, ≤ 25 MB. `audio_url` is fetched server-side
only when `SCORING_ALLOW_AUDIO_URL=1` (off by default: SSRF).

**Errors** — `400` undecodable / too short / too long / no audio · `413` over 25 MB · `422` malformed
body · `503 {"error":"model_unavailable","signal":"…"}` when a model cannot load, so the orchestrator's
breaker degrades instead of failing the case. Validation errors never echo the request body back.

## Layout

```
app/     main.py (routes + audio parsing) · schemas.py (frozen contracts) · models.py (lazy singletons)
         config.py · text_models.py · voice_model.py · voice_features.py · tree_eval.py (numpy LightGBM)
training/ train_sentiment.py · train_threat.py (--objective ce|contrastive) · train_voice.py
          calibrate.py · evaluate_text.py · build_voice_features.py · push_to_hub.py · mlflow_utils.py
          data/  corpora + splits (small CSVs, in git; raw audio and weights are not)
corpus/  threat_corpus_builder.py (Indian Kanoon + labelling + merge) · synthetic_* generators · split_*
evals/   eval_signals.py -> ../../artifacts/signal_eval.json
tests/   test_signals.py (46 contract tests, mocked models) · test_integration.py (real weights + RAVDESS)
```

## Reproduce the models

Weights already exist; these commands regenerate them. Everything logs to MLflow.

```bash
pip install -r requirements-train.txt

# sentiment (distress_v3)
PYTHONPATH=. python corpus/synthetic_distress_v3.py && python corpus/distress_challenge_v1.py && python corpus/split_distress_v3.py
PYTHONPATH=. python training/train_sentiment.py                       # lr 3e-5, batch 8, max_len 64, seed 42
PYTHONPATH=. python training/calibrate.py --task sentiment --model ../../models/distress_v3 \
    --val training/data/distress_v3_val.csv --test training/data/distress_v3_test.csv

# threat (contrastive = served; ce = the frozen V7 baseline recipe)
PYTHONPATH=. python corpus/synthetic_threat_v5.py && python corpus/synthetic_threat_v6.py \
    && python corpus/combine_threat_v7.py && python corpus/split_threat_v7.py
PYTHONPATH=. python training/train_threat.py --objective contrastive --output ../../models/threat_contrastive_v1
PYTHONPATH=. python training/calibrate.py --task threat --model ../../models/threat_contrastive_v1 \
    --val training/data/threat_v7_val.csv --test training/data/threat_v7_test.csv

# voice
bash training/download_ravdess.sh                                     # ~208 MB, Zenodo, CC BY-NC-SA
PYTHONPATH=. python training/build_voice_features.py --source ravdess # 1056 clips, split BY ACTOR
PYTHONPATH=. python training/train_voice.py --source ravdess          # + GroupKFold-by-actor CV

# evaluation + tracking + publish
PYTHONPATH=. python evals/eval_signals.py --markdown
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
PYTHONPATH=. python training/push_to_hub.py                           # -> Shota2811/ps26094-signals (private)
```

Datasets actually used: the corpora in `training/data/` and RAVDESS. IndicSentiment, IndicGLUE,
HingCorpus, ILDC, CREMA-D, IEMOCAP, Svarah and IndicVoices are **not** used by any current model;
`--extra-csv` / `--extra-features-csv` are the hooks for adding them later.

## Threat corpus

`corpus/threat_corpus_builder.py` — collect, label, validate, merge, audit.

```bash
export IK_API_TOKEN=…                                                  # never commit it
PYTHONPATH=. python corpus/threat_corpus_builder.py scrape --dry-run   # offline parser check, writes nothing
PYTHONPATH=. python corpus/threat_corpus_builder.py scrape --pages 5   # -> training/data/kanoon_candidates.csv
#   label the `label` column by hand (1 threat/coercion, 0 not), save as kanoon_labelled.csv
PYTHONPATH=. python corpus/threat_corpus_builder.py validate --labelled training/data/kanoon_labelled.csv
PYTHONPATH=. python corpus/threat_corpus_builder.py merge               # -> training/data/threat_corpus_v8.csv
PYTHONPATH=. python corpus/threat_corpus_builder.py stats               # taxonomy coverage, prints gaps
```

17-category taxonomy: 7 threat categories (direct, indirect, witness intimidation, forced silence,
financial coercion, third-party threat, case-withdrawal coercion) and 10 hard-negative categories
(fear / sadness / anger / legal stress without threat, negation, third-party statement, benign advice,
ambiguous, neutral legal, hard negative). Category names are label-aware: "they threatened my brother
if I testify" is a third-party **threat**, "I heard another family was threatened" is a third-party
**statement**. Current state: **840 rows** (synthetic + distress negatives), target ≥ 2,500;
`neutral_legal` is the one empty category and needs the Kanoon scrape. Nothing here fabricates data.

## Tests

```bash
PYTHONPATH=. python -m pytest tests/                        # 54: contract + real-model integration
PYTHONPATH=. python -m pytest tests/ -m "not integration"   # 46 contract tests (what CI runs, no torch)
```
`tests/test_signals.py` mocks the three model singletons but exercises real routing, validation, base64 /
multipart / raw-audio parsing and WAV decoding. `tests/test_integration.py` loads the real weights and a
real RAVDESS clip and skips itself when they are absent.

## Engineering notes (read before touching this)

* **torch + lightgbm in one process segfaults on macOS** (two OpenMP runtimes). Training uses LightGBM;
  inference walks the dumped trees in numpy (`app/tree_eval.py`) and `train_voice.py` asserts the two
  agree bit-exactly before saving. LightGBM is deliberately absent from the runtime image.
* **`/v1/signals/voice` used to 500** on multipart and raw-body uploads: FastAPI's default validation
  handler tried to UTF-8 decode the binary body while building the 422. The route now parses all three
  encodings itself and a custom handler redacts non-text input (`<N bytes>`). Regression-tested.
* **`REPO_ROOT` must tolerate the container layout**: the service is `/app` in the image, which has no
  grandparent — `parents[1]` raised `IndexError` and the container never booted. Regression-tested.
* MLflow ≥ 3.16 refuses the plain `./mlruns` file store; `training/mlflow_utils.py` uses
  `sqlite:///mlflow.db` and stamps every run with the git commit, branch, dirty flag and artifact path.
* Model directories come from `app/config.py`; override with `SCORING_SENTIMENT_MODEL`,
  `SCORING_THREAT_MODEL`, `SCORING_VOICE_MODEL`, `SCORING_MODELS_DIR`.
* The service is CPU-only by default (short texts, ~20–70 ms; ~1 s for a voice clip including feature
  extraction). Container memory sits near 1.4 GB against the 2.5 GB compose limit.

## Known weaknesses (say these before the judges do)

* Threat: one ambiguous false positive ("please think carefully before getting involved") and one soft
  financial-coercion miss. Differences between the two threat checkpoints are 1–2 sentences on a 78-row
  test set — the Indian Kanoon corpus is what would make them meaningful.
* Sentiment: MODERATE vs LOW when a sentence ends on a coping clause ("…but I'm managing").
* Calibration is fitted on 73–78 validation rows from the same synthetic distribution: a first-order
  correction, not a guarantee. `raw_prob` and `entropy` are exposed so the fusion layer can route on
  uncertainty rather than on the second decimal of a score.
* Voice: 75 % speaker-independent on acted English speech; sad (0.63) and happy (0.58) are the
  confusions. The domain gap to Indian field audio and phone-line quality is real and unmeasured.
