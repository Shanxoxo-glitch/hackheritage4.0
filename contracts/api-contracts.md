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
                "calibrated": true, "model_version": "threat_v7"},
  "flags": ["threat_without_expressed_distress"], "latency_ms": 23
}
```

### Contract #2 — `POST /v1/signals/voice`
Request  `{"audio_base64": str (WAV/FLAC/OGG), "audio_url"?: str, "interaction_id"?: str, "request_id"?: str}`
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

### Degradation (all three routes)
`HTTP 503 {"error": "model_unavailable", "signal": "sentiment" | "threat" | "voice", "detail": "…"}` — the
orchestrator's circuit breaker treats this as signal-down and degrades; it is never a 500.
`GET /healthz` → `{"status": "ok"|"degraded"|"loading", "service", "version", "schema_version", "models": {...}}`.

Flags: `threat_without_expressed_distress` (threat_flag with LOW sentiment — the "threatened into silence" pattern),
`below_confidence_gate`, `human_review_recommended`, `voice_model_trained_on_synthetic_smoke_data`.
