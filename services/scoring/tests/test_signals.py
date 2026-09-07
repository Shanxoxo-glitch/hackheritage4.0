"""
Contract-shape tests for scoring contracts #1-3 + a latency test.

Models are mocked (monkeypatched get_sentiment / get_threat / get_voice), so
this suite runs in CI with NO model download and no torch. It asserts the
EXACT key sets and types the backend / orchestrator / risk engine rely on.
"""
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import main as m
from app import models as model_registry


# ----------------------------------------------------------------- fakes
class FakeText:
    def __init__(self, labels, probs, name):
        self.labels, self.probs, self.name = labels, probs, name

    def predict(self, texts):
        idx = int(np.argmax(self.probs))
        return [{"label": self.labels[idx], "label_id": idx,
                 "probs": dict(zip(self.labels, self.probs)), "raw_probs": dict(zip(self.labels, self.probs)),
                 "confidence": float(max(self.probs)), "entropy": 0.12, "calibrated": True,
                 "temperature": 0.14, "model": self.name} for _ in texts]


class FakeVoice:
    name, trained_on = "voice_stress_ravdess", "ravdess_all_24_actors"

    def score_array(self, y, sr):
        return {"label": "STRESSED", "score": 0.81, "confidence": 0.81, "model": self.name,
                "trained_on": self.trained_on, "meaningful": True, "audio_seconds": 2.5,
                "features_summary": {"f0_mean": 210.3, "jitter": 0.02}}


@pytest.fixture(autouse=True)
def mocked_models(monkeypatch):
    model_registry.reset()
    monkeypatch.setattr(m, "get_sentiment", lambda: FakeText(["LOW", "MODERATE", "HIGH"], [0.05, 0.15, 0.80], "distress_v3"))
    monkeypatch.setattr(m, "get_threat", lambda: FakeText(["NOT_THREAT", "THREAT"], [0.03, 0.97], "threat_v7"))
    monkeypatch.setattr(m, "get_voice", lambda: FakeVoice())
    monkeypatch.setattr(m, "decode_audio_b64", lambda b64: (np.zeros(16000, np.float32), 16000))
    yield


client = TestClient(m.app)

TEXT_KEYS = {"schema_version", "request_id", "interaction_id", "sentiment", "threat", "flags", "latency_ms"}
SENTIMENT_KEYS = {"label", "level", "sentiment_score", "probs", "confidence", "entropy", "calibrated", "model_version"}
THREAT_KEYS = {"threat_flag", "prob", "raw_prob", "confidence", "entropy", "calibrated", "model_version"}
VOICE_KEYS = {"label", "voice_stress_score", "confidence", "audio_seconds", "features_summary", "model_version", "trained_on"}


# ----------------------------------------------------------------- contract #1
def test_text_contract_shape():
    r = client.post("/v1/signals/text", json={"text": "Case wapas lo warna dekh lenge.", "interaction_id": "int-1"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert set(b) == TEXT_KEYS
    assert set(b["sentiment"]) == SENTIMENT_KEYS
    assert set(b["threat"]) == THREAT_KEYS
    assert b["schema_version"] == "1.0" and b["interaction_id"] == "int-1"
    s, t = b["sentiment"], b["threat"]
    assert s["label"] in ("LOW", "MODERATE", "HIGH") and s["level"] in (0, 1, 2)
    assert 0.0 <= s["sentiment_score"] <= 1.0 and abs(sum(s["probs"].values()) - 1) < 1e-6
    assert isinstance(t["threat_flag"], bool) and 0.0 <= t["prob"] <= 1.0
    assert isinstance(b["latency_ms"], int) and isinstance(b["flags"], list)


def test_sentiment_score_is_expected_level():
    b = client.post("/v1/signals/text", json={"text": "x"}).json()
    assert abs(b["sentiment"]["sentiment_score"] - (0.15 * 1 + 0.80 * 2) / 2) < 1e-6


def test_text_validation():
    assert client.post("/v1/signals/text", json={"text": ""}).status_code == 422
    assert client.post("/v1/signals/text", json={}).status_code == 422
    assert client.post("/v1/signals/text", json={"text": "x" * 4001}).status_code == 422


# ----------------------------------------------------------------- contract #3
def test_threat_contract_shape():
    r = client.post("/v1/signals/threat", json={"text": "He said he knows where my family lives."})
    assert r.status_code == 200, r.text
    b = r.json()
    assert set(b) == {"schema_version", "request_id", "interaction_id", "threat", "flags", "latency_ms"}
    assert set(b["threat"]) == THREAT_KEYS
    assert b["threat"]["threat_flag"] is True and b["threat"]["prob"] == pytest.approx(0.97)


def test_threat_flag_threshold(monkeypatch):
    monkeypatch.setattr(m, "get_threat", lambda: FakeText(["NOT_THREAT", "THREAT"], [0.6, 0.4], "threat_v7"))
    assert client.post("/v1/signals/threat", json={"text": "x"}).json()["threat"]["threat_flag"] is False


# ----------------------------------------------------------------- contract #2
def test_voice_contract_shape():
    r = client.post("/v1/signals/voice", json={"audio_base64": "AAAA", "interaction_id": "int-2"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert set(b) == {"schema_version", "request_id", "interaction_id", "voice", "flags", "latency_ms"}
    assert set(b["voice"]) == VOICE_KEYS
    assert b["voice"]["label"] in ("NOT_STRESSED", "STRESSED") and 0.0 <= b["voice"]["voice_stress_score"] <= 1.0


def test_voice_requires_audio():
    assert client.post("/v1/signals/voice", json={}).status_code == 400
    assert client.post("/v1/signals/voice", json={"audio_url": "http://x/y.wav"}).status_code == 400  # disabled by default


# ----------------------------------------------------------------- flags + degradation
def test_threat_without_distress_flag(monkeypatch):
    monkeypatch.setattr(m, "get_sentiment", lambda: FakeText(["LOW", "MODERATE", "HIGH"], [0.9, 0.07, 0.03], "distress_v3"))
    b = client.post("/v1/signals/text", json={"text": "They told me to forget what I saw, I am fine."}).json()
    assert "threat_without_expressed_distress" in b["flags"]


def test_confidence_gate_flag(monkeypatch):
    monkeypatch.setattr(m, "get_threat", lambda: FakeText(["NOT_THREAT", "THREAT"], [0.45, 0.55], "threat_v7"))
    b = client.post("/v1/signals/threat", json={"text": "x"}).json()
    assert "below_confidence_gate" in b["flags"] and "human_review_recommended" in b["flags"]


def test_503_model_unavailable_shape(monkeypatch):
    def boom():
        raise FileNotFoundError("threat_v7 missing")
    monkeypatch.setattr(m, "get_threat", boom)
    for path in ("/v1/signals/text", "/v1/signals/threat"):
        r = client.post(path, json={"text": "x"})
        assert r.status_code == 503
        b = r.json()
        assert b["error"] == "model_unavailable" and b["signal"] == "threat" and "detail" in b


def test_healthz_without_models():
    r = client.get("/healthz")
    assert r.status_code == 200
    b = r.json()
    assert set(b) == {"status", "service", "version", "schema_version", "models"}
    assert set(b["models"]) == {"sentiment", "threat", "voice"}
    assert b["status"] in ("ok", "degraded", "loading")


# ----------------------------------------------------------------- latency
def test_latency_under_100ms():
    client.post("/v1/signals/text", json={"text": "warm"})
    timings = []
    for _ in range(30):
        t0 = time.perf_counter()
        assert client.post("/v1/signals/text", json={"text": "Hearing kal hai, thoda tension hai."}).status_code == 200
        timings.append((time.perf_counter() - t0) * 1000)
    p95 = sorted(timings)[int(0.95 * len(timings)) - 1]
    assert p95 < 100, f"p95 request overhead {p95:.1f} ms (mocked models)"
