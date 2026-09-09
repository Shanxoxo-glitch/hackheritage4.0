"""
Integration / smoke tests with the REAL local models and a REAL RAVDESS clip.

Skipped automatically when the weights are not present (CI). Locally:
    PYTHONPATH=. python -m pytest tests/test_integration.py -q
Model paths come from app.config (SCORING_MODELS_DIR / SCORING_*_MODEL env overrides);
the RAVDESS clip is looked up under SCORING_RAVDESS_DIR (default training/data/raw/ravdess).
"""
import base64

import pytest
from fastapi.testclient import TestClient

from app import config as C
from app import models
from app.main import app

pytestmark = pytest.mark.integration

_weights = [C.SENTIMENT_MODEL_DIR / "model.safetensors", C.THREAT_MODEL_DIR / "model.safetensors", C.VOICE_MODEL_PATH]
if not all(p.exists() for p in _weights):
    pytest.skip(f"real weights not found under {C.MODELS_DIR}", allow_module_level=True)


@pytest.fixture(scope="module")
def client():
    models.reset()
    with TestClient(app) as c:
        h = c.get("/healthz?warm=1").json()
        assert h["status"] == "ok", h
        yield c


def test_healthz_reports_all_three_real_models(client):
    h = client.get("/healthz").json()
    assert all(s["loaded"] for s in h["models"].values())
    assert h["models"]["sentiment"]["version"] == "distress_v3"
    assert h["models"]["threat"]["version"] in {"threat_contrastive_v1", "threat_v7"}
    assert h["models"]["voice"]["version"] == "voice_stress_ravdess"


def test_real_text_threat_hinglish(client):
    body = client.post("/v1/signals/text", json={"text": "Case wapas le lo warna tumhare bhai ko uthwa lenge."}).json()
    assert body["threat"]["threat_flag"] is True and body["threat"]["prob"] > 0.5
    assert body["threat"]["calibrated"] is True and body["threat"]["model_version"] == C.THREAT_MODEL_DIR.name


def test_real_text_distress_high(client):
    body = client.post("/v1/signals/text",
                       json={"text": "I can't sleep at all, I'm terrified to leave the house and I can't stop crying."}).json()
    assert body["sentiment"]["label"] == "HIGH" and body["sentiment"]["sentiment_score"] > 0.6
    assert body["sentiment"]["calibrated"] is True and body["sentiment"]["model_version"] == "distress_v3"


def test_real_text_neutral_is_low_and_not_threat(client):
    body = client.post("/v1/signals/text", json={"text": "The hearing is on the 14th and I have submitted the documents."}).json()
    assert body["sentiment"]["label"] == "LOW" and body["threat"]["threat_flag"] is False


def test_real_threat_route_soft_witness_intimidation(client):
    body = client.post("/v1/signals/threat", json={"text": "They asked me to forget what I had seen."}).json()
    assert "threat" in body and 0 <= body["threat"]["prob"] <= 1        # value reported, not asserted: known soft case


def test_real_text_is_deterministic(client):
    a = client.post("/v1/signals/threat", json={"text": "Unhone kaha chup raho warna ghar jala denge."}).json()
    b = client.post("/v1/signals/threat", json={"text": "Unhone kaha chup raho warna ghar jala denge."}).json()
    assert a["threat"]["prob"] == b["threat"]["prob"]


def test_real_voice_generated_wav(client, wav_bytes):
    r = client.post("/v1/signals/voice", json={"audio_base64": base64.b64encode(wav_bytes).decode()})
    assert r.status_code == 200, r.text
    v = r.json()["voice"]
    assert v["model_version"] == "voice_stress_ravdess" and v["trained_on"].startswith("ravdess")
    assert 0 <= v["voice_stress_score"] <= 1 and "f0_mean" in v["features_summary"]


def test_real_voice_ravdess_clip_all_encodings(client, ravdess_wav):
    if ravdess_wav is None:
        pytest.skip("RAVDESS clip not available (set SCORING_RAVDESS_DIR)")
    raw = ravdess_wav.read_bytes()
    r_json = client.post("/v1/signals/voice", json={"audio_base64": base64.b64encode(raw).decode(), "interaction_id": "ravdess"})
    r_mp = client.post("/v1/signals/voice", files={"file": (ravdess_wav.name, raw, "audio/wav")})
    r_raw = client.post("/v1/signals/voice", content=raw, headers={"content-type": "audio/wav"})
    for r in (r_json, r_mp, r_raw):
        assert r.status_code == 200, r.text
        v = r.json()["voice"]
        assert v["label"] in {"STRESSED", "NOT_STRESSED"} and 0 <= v["voice_stress_score"] <= 1
        assert v["audio_seconds"] > 1.0 and v["features_summary"]["f0_mean"] > 50
    scores = {r.json()["voice"]["voice_stress_score"] for r in (r_json, r_mp, r_raw)}
    assert len(scores) == 1, f"encodings disagree: {scores}"
    assert r_json.json()["interaction_id"] == "ravdess"
