# Frozen API Contracts Specification

| Path | Method | Source | Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| /v1/signals/text | POST | Web / IVRS / Backend | Scoring | Contract #1: sentiment (distress level) + threat from text |
| /v1/signals/voice | POST | Web / IVRS / Backend | Scoring | Contract #2: voice-stress score from an audio clip |
| /v1/signals/threat | POST | Orchestrator | Scoring | Contract #3: threat_flag + calibrated prob from text |
| /v1/fusion | POST | Orchestrator | Risk Engine | Evidential signal fusion -> composite distress score |
| /v1/case/{id}/context | GET | Orchestrator | Backend | Fetch victim case context & legal stage |
| /v1/alerts | POST | Risk Engine | Backend | Append tamper-evident hash-chained alert |


## Scoring service contracts (#1–3) — `services/scoring`, port 8100

Frozen field names. The backend row `distress_scores` stores `sentiment_score`, `voice_stress_score`,
`threat_flag` and `confidence` verbatim from these responses; the risk engine consumes the full objects.
Pydantic source of truth: `services/scoring/app/schemas.py`; shape tests: `services/scoring/tests/test_signals.py`.

Scales: every score is in [0, 1]. `sentiment_score` = expected distress level / 2 (LOW≈0, MODERATE≈0.5, HIGH≈1).
`prob` and `voice_stress_score` are calibrated / model probabilities, not real-world probabilities of danger.
`confidence` < 0.60 (decision-policy Confidence Calibration Gate) adds the flags `below_confidence_gate`
and `human_review_recommended`; `threat_flag` = `prob >= 0.5`.

### Contract #1 — `POST /v1/signals/text`
Request  `{"text": str(1..4000), "interaction_id"?: str, "language_hint"?: str, "request_id"?: str}`
```json
{
  "schema_version": "1.0", "request_id": "…", "interaction_id": "…",
  "sentiment": {"label": "HIGH", "level": 2, "sentiment_score": 0.93,
                "probs": {"LOW": 0.02, "MODERATE": 0.10, "HIGH": 0.88},
                "confidence": 0.88, "entropy": 0.21, "calibrated": true, "model_version": "distress_v3"},
  "threat":    {"threat_flag": true, "prob": 0.99, "raw_prob": 0.66, "confidence": 0.99, "entropy": 0.05,
                "calibrated": true, "model_version": "threat_contrastive_v1"},
  "flags": ["threat_without_expressed_distress"], "latency_ms": 23
}
```

### Contract #2 — `POST /v1/signals/voice`
Three accepted encodings of the same clip (WAV / FLAC / OGG, mono or stereo, any sample rate, 0.2–120 s, ≤ 25 MB):

| Content-Type | Body | interaction_id / request_id |
| :--- | :--- | :--- |
| `application/json` | `{"audio_base64": str, "audio_url"?: str}` | JSON fields |
| `multipart/form-data` | file part named `file` (or `audio`) | form fields |
| `audio/*`, `application/octet-stream` | raw audio bytes | query params |

All three return the identical body below. `audio_url` is fetched server-side only when
`SCORING_ALLOW_AUDIO_URL=1` (off by default: SSRF); otherwise send `audio_base64` or a file part.
Errors: `400` undecodable / too short / too long / no audio, `413` over 25 MB, `422` malformed body
(the response never echoes the audio bytes back).
```json
{
  "schema_version": "1.0", "request_id": "…", "interaction_id": "…",
  "voice": {"label": "STRESSED", "voice_stress_score": 0.76, "confidence": 0.76, "audio_seconds": 2.5,
            "features_summary": {"f0_mean": 214.1, "f0_cv": 0.18, "jitter": 0.021, "rms_mean": 0.21, "pause_ratio": 0.12},
            "model_version": "voice_stress_ravdess", "trained_on": "ravdess_all_24_actors"},
  "flags": [], "latency_ms": 140
}
```

### Contract #3 — `POST /v1/signals/threat`
Request  `{"text": str(1..4000), "interaction_id"?: str, "language_hint"?: str, "request_id"?: str}`
Response `{"schema_version", "request_id", "interaction_id", "threat": <same object as #1>, "flags", "latency_ms"}`

### Backend gateway (`services/backend`, `POST /api/v1/perception/score`)
The backend calls contracts #1–2 through `app/services/scoring_client.py` and stores the result on the
`distress_scores` row (`sentiment_score`, `voice_stress_score`, `threat_flag`, `composite_score`, `confidence`).
The response adds three non-breaking provenance fields: `signal_source`
(`scoring_service` | `partial` | `heuristic_fallback`), `model_versions`, `degraded_signals`.
A scoring outage never fails the case — the gateway degrades to its keyword heuristic and says so.
`GET /api/v1/perception/health` reports whether the scoring service is reachable and which models it loaded.

### Degradation (all three routes)
`HTTP 503 {"error": "model_unavailable", "signal": "sentiment" | "threat" | "voice", "detail": "…"}` — the
orchestrator's circuit breaker treats this as signal-down and degrades; it is never a 500.
`GET /healthz` → `{"status": "ok"|"degraded"|"loading", "service", "version", "schema_version", "models": {...}}`.

Flags: `threat_without_expressed_distress` (threat_flag with LOW sentiment — the "threatened into silence" pattern),
`below_confidence_gate`, `human_review_recommended`, `voice_model_trained_on_synthetic_smoke_data`.
