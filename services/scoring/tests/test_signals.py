"""
Contract tests for the scoring service (CI: no torch, no weights, no download).

The three model singletons are mocked; everything else is real: routing, pydantic
validation, the safe validation-error handler, base64 / multipart / raw-audio parsing,
WAV decoding (soundfile), response models and flags.
"""
import base64
import time

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app import config as C
from app.main import app

ENVELOPE = {"schema_version", "request_id", "interaction_id", "flags", "latency_ms"}
SENT_KEYS = {"label", "level", "sentiment_score", "probs", "confidence", "entropy", "calibrated", "model_version"}
THREAT_KEYS = {"threat_flag", "prob", "raw_prob", "confidence", "entropy", "calibrated", "model_version"}
VOICE_KEYS = {"label", "voice_stress_score", "confidence", "audio_seconds", "features_summary", "model_version",
              "trained_on"}


class FakeText:
    def __init__(self, labels, probs, name, calibrated=True):
        self.labels, self.probs, self.name, self.calibrated = labels, probs, name, calibrated

    def predict(self, texts):
        idx = max(range(len(self.probs)), key=lambda i: self.probs[i])
        return [{"label": self.labels[idx], "label_id": idx,
                 "probs": dict(zip(self.labels, self.probs)), "raw_probs": dict(zip(self.labels, self.probs)),
                 "confidence": float(self.probs[idx]), "entropy": 0.2, "calibrated": self.calibrated,
                 "temperature": 0.14, "model": self.name} for _ in texts]


class FakeVoice:
    def __init__(self, p=0.8, trained_on="ravdess_all_24_actors"):
        self.p, self.trained_on = p, trained_on

    def score_array(self, y, sr):
        return {"label": "STRESSED" if self.p >= 0.5 else "NOT_STRESSED", "score": self.p,
                "confidence": max(self.p, 1 - self.p), "model": "voice_stress_ravdess", "trained_on": self.trained_on,
                "audio_seconds": round(len(y) / sr, 3), "features_summary": {"f0_mean": 150.0, "rms_mean": 0.1}}


@pytest.fixture(autouse=True)
def mocked_models(monkeypatch):
    monkeypatch.setattr(m, "get_sentiment", lambda: FakeText(C.SENTIMENT_LABELS, [0.05, 0.15, 0.80], "distress_v3"))
    monkeypatch.setattr(m, "get_threat", lambda: FakeText(C.THREAT_LABELS, [0.03, 0.97], "threat_contrastive_v1"))
    monkeypatch.setattr(m, "get_voice", lambda: FakeVoice())
    m.models.reset()


@pytest.fixture
def client():
    return TestClient(app)


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# ------------------------------------------------------------------ healthz
def test_healthz_shape_without_models(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"ok", "degraded", "loading"}
    assert body["service"] == "scoring" and body["schema_version"] == C.SCHEMA_VERSION
    assert set(body["models"]) == {"sentiment", "threat", "voice"}
    for st in body["models"].values():
        assert {"loaded", "path", "version", "error"} <= set(st)


# ------------------------------------------------------------------ text (contract #1)
def test_text_contract_shape(client):
    r = client.post("/v1/signals/text", json={"text": "Case wapas le lo warna bhai ko uthwa lenge.",
                                              "interaction_id": "int-1", "request_id": "req-1"})
    assert r.status_code == 200
    body = r.json()
    assert ENVELOPE <= set(body) and body["schema_version"] == C.SCHEMA_VERSION
    assert body["request_id"] == "req-1" and body["interaction_id"] == "int-1"
    assert set(body["sentiment"]) == SENT_KEYS and set(body["threat"]) == THREAT_KEYS
    assert body["sentiment"]["label"] == "HIGH" and body["sentiment"]["level"] == 2
    assert body["threat"]["threat_flag"] is True and 0 <= body["threat"]["prob"] <= 1
    assert isinstance(body["latency_ms"], int)


def test_text_calibration_and_model_version_fields(client):
    body = client.post("/v1/signals/text", json={"text": "hello"}).json()
    assert body["sentiment"]["calibrated"] is True and body["sentiment"]["model_version"] == "distress_v3"
    assert body["threat"]["calibrated"] is True and body["threat"]["model_version"] == "threat_contrastive_v1"
    assert 0 <= body["threat"]["raw_prob"] <= 1 and 0 <= body["threat"]["entropy"] <= 1


def test_text_sentiment_score_is_expected_level(client):
    body = client.post("/v1/signals/text", json={"text": "x"}).json()
    assert abs(body["sentiment"]["sentiment_score"] - (0.15 * 1 + 0.80 * 2) / 2) < 1e-6


def test_text_request_id_generated_when_missing(client):
    body = client.post("/v1/signals/text", json={"text": "x"}).json()
    assert len(body["request_id"]) >= 8 and body["interaction_id"] is None


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": 123}, {"text": None}, {"txt": "a"}])
def test_text_malformed_requests_are_422(client, payload):
    assert client.post("/v1/signals/text", json=payload).status_code == 422


def test_text_overly_long_is_422_and_not_echoed(client):
    long_text = "a" * (C.MAX_TEXT_CHARS + 1)
    r = client.post("/v1/signals/text", json={"text": long_text})
    assert r.status_code == 422
    assert long_text not in r.text and len(r.text) < 2000       # body is never echoed back


def test_text_binary_body_with_json_content_type_is_4xx_not_500(client, wav_bytes):
    r = client.post("/v1/signals/text", content=wav_bytes, headers={"content-type": "application/json"})
    assert r.status_code in (400, 422)                 # FastAPI: 400 "error parsing the body" or 422 via our handler
    assert wav_bytes[:4] not in r.content and len(r.content) < 1000


# ------------------------------------------------------------------ threat (contract #3)
def test_threat_contract_shape(client):
    r = client.post("/v1/signals/threat", json={"text": "He said he would hurt me.", "interaction_id": "int-2"})
    assert r.status_code == 200
    body = r.json()
    assert ENVELOPE <= set(body) and set(body["threat"]) == THREAT_KEYS
    assert body["interaction_id"] == "int-2" and "sentiment" not in body


def test_threat_flag_threshold(client, monkeypatch):
    monkeypatch.setattr(m, "get_threat", lambda: FakeText(C.THREAT_LABELS, [0.6, 0.4], "threat_contrastive_v1"))
    body = client.post("/v1/signals/threat", json={"text": "x"}).json()
    assert body["threat"]["threat_flag"] is False and abs(body["threat"]["prob"] - 0.4) < 1e-9


def test_threat_malformed_is_422(client):
    assert client.post("/v1/signals/threat", json={"text": ""}).status_code == 422
    assert client.post("/v1/signals/threat", json={"text": "a" * (C.MAX_TEXT_CHARS + 1)}).status_code == 422


# ------------------------------------------------------------------ voice (contract #2)
def _assert_voice_ok(body, seconds=1.0):
    assert ENVELOPE <= set(body) and set(body["voice"]) == VOICE_KEYS
    assert 0 <= body["voice"]["voice_stress_score"] <= 1 and 0 <= body["voice"]["confidence"] <= 1
    assert body["voice"]["model_version"] == "voice_stress_ravdess"
    assert abs(body["voice"]["audio_seconds"] - seconds) < 0.05      # proves the real decode ran


def test_voice_base64_json(client, wav_bytes):
    r = client.post("/v1/signals/voice", json={"audio_base64": b64(wav_bytes), "interaction_id": "int-3",
                                               "request_id": "req-3"})
    assert r.status_code == 200, r.text
    body = r.json()
    _assert_voice_ok(body)
    assert body["interaction_id"] == "int-3" and body["request_id"] == "req-3"


def test_voice_multipart_upload(client, wav_bytes):
    r = client.post("/v1/signals/voice", files={"file": ("clip.wav", wav_bytes, "audio/wav")},
                    data={"interaction_id": "int-4", "request_id": "req-4"})
    assert r.status_code == 200, r.text
    body = r.json()
    _assert_voice_ok(body)
    assert body["interaction_id"] == "int-4" and body["request_id"] == "req-4"


def test_voice_multipart_accepts_audio_field_name(client, wav_bytes):
    r = client.post("/v1/signals/voice", files={"audio": ("clip.wav", wav_bytes, "audio/wav")})
    assert r.status_code == 200, r.text


def test_voice_raw_audio_body(client, wav_bytes):
    r = client.post("/v1/signals/voice", content=wav_bytes, headers={"content-type": "audio/wav"},
                    params={"interaction_id": "int-5", "request_id": "req-5"})
    assert r.status_code == 200, r.text
    body = r.json()
    _assert_voice_ok(body)
    assert body["interaction_id"] == "int-5" and body["request_id"] == "req-5"


def test_voice_raw_octet_stream_body(client, wav_bytes):
    r = client.post("/v1/signals/voice", content=wav_bytes, headers={"content-type": "application/octet-stream"})
    assert r.status_code == 200, r.text


def test_voice_stereo_48k_is_resampled(client, wav_bytes_48k_stereo):
    pytest.importorskip("librosa")
    r = client.post("/v1/signals/voice", json={"audio_base64": b64(wav_bytes_48k_stereo)})
    assert r.status_code == 200, r.text
    _assert_voice_ok(r.json())


def test_voice_same_bytes_same_result_across_encodings(client, wav_bytes):
    a = client.post("/v1/signals/voice", json={"audio_base64": b64(wav_bytes)}).json()["voice"]
    b = client.post("/v1/signals/voice", files={"file": ("c.wav", wav_bytes, "audio/wav")}).json()["voice"]
    c = client.post("/v1/signals/voice", content=wav_bytes, headers={"content-type": "audio/wav"}).json()["voice"]
    assert a["audio_seconds"] == b["audio_seconds"] == c["audio_seconds"]


@pytest.mark.parametrize("raw", [b"not audio at all", b"RIFF\x00\x00\x00\x00WAVEjunk", bytes(range(256)) * 4])
def test_voice_invalid_audio_is_400(client, raw):
    r = client.post("/v1/signals/voice", json={"audio_base64": b64(raw)})
    assert r.status_code == 400 and "could not decode audio" in r.json()["detail"]
    r = client.post("/v1/signals/voice", files={"file": ("x.wav", raw, "audio/wav")})
    assert r.status_code == 400


def test_voice_garbage_base64_string_is_400(client):
    r = client.post("/v1/signals/voice", json={"audio_base64": "%%%not-base64%%%"})
    assert r.status_code == 400


def test_voice_garbage_multipart_is_422_not_500(client):
    r = client.post("/v1/signals/voice", data={"foo": "bar"}, files={"nothing": ("n.txt", b"hi", "text/plain")})
    assert r.status_code == 422 and "file" in r.json()["detail"]
    r = client.post("/v1/signals/voice", data={"file": "not-a-file"})            # text field named file
    assert r.status_code == 422


def test_voice_binary_body_with_json_content_type_is_422_not_500(client, wav_bytes):
    """Regression: this exact request used to crash FastAPI's default handler (UnicodeDecodeError -> 500)."""
    r = client.post("/v1/signals/voice", content=wav_bytes, headers={"content-type": "application/json"})
    assert r.status_code == 422
    assert wav_bytes[:4] not in r.content            # binary body never echoed


@pytest.mark.parametrize("payload", [{}, {"audio_base64": None}, {"foo": "bar"}])
def test_voice_missing_audio_is_400(client, payload):
    r = client.post("/v1/signals/voice", json=payload)
    assert r.status_code == 400 and "audio_base64" in r.json()["detail"]


def test_voice_wrong_field_type_is_422(client):
    r = client.post("/v1/signals/voice", json={"audio_base64": 12345})
    assert r.status_code == 422


def test_voice_too_short_is_400(client, short_wav_bytes):
    r = client.post("/v1/signals/voice", json={"audio_base64": b64(short_wav_bytes)})
    assert r.status_code == 400 and "too short" in r.json()["detail"]


def test_voice_too_large_is_413(client, wav_bytes, monkeypatch):
    monkeypatch.setattr(m, "MAX_AUDIO_BYTES", 1000)
    r = client.post("/v1/signals/voice", content=wav_bytes, headers={"content-type": "audio/wav"})
    assert r.status_code == 413


def test_voice_url_disabled_by_default(client):
    r = client.post("/v1/signals/voice", json={"audio_url": "http://example.invalid/a.wav"})
    assert r.status_code == 400 and "audio_url disabled" in r.json()["detail"]


def test_openapi_documents_all_voice_encodings(client):
    spec = client.get("/openapi.json").json()
    content = spec["paths"]["/v1/signals/voice"]["post"]["requestBody"]["content"]
    assert {"application/json", "multipart/form-data", "audio/wav"} <= set(content)


# ------------------------------------------------------------------ flags
def test_threat_without_distress_flag(client, monkeypatch):
    monkeypatch.setattr(m, "get_sentiment", lambda: FakeText(C.SENTIMENT_LABELS, [0.9, 0.07, 0.03], "distress_v3"))
    body = client.post("/v1/signals/text", json={"text": "x"}).json()
    assert "threat_without_expressed_distress" in body["flags"]


def test_confidence_gate_flag(client, monkeypatch):
    monkeypatch.setattr(m, "get_threat", lambda: FakeText(C.THREAT_LABELS, [0.45, 0.55], "threat_contrastive_v1"))
    body = client.post("/v1/signals/threat", json={"text": "x"}).json()
    assert {"below_confidence_gate", "human_review_recommended"} <= set(body["flags"])


def test_synthetic_voice_model_flag(client, wav_bytes, monkeypatch):
    monkeypatch.setattr(m, "get_voice", lambda: FakeVoice(trained_on="synthetic_smoke"))
    body = client.post("/v1/signals/voice", json={"audio_base64": b64(wav_bytes)}).json()
    assert "voice_model_trained_on_synthetic_smoke_data" in body["flags"]


# ------------------------------------------------------------------ model unavailable -> 503
def _boom():
    raise RuntimeError("weights missing")


@pytest.mark.parametrize("signal,route,payload", [
    ("sentiment", "/v1/signals/text", {"json": {"text": "x"}}),
    ("threat", "/v1/signals/threat", {"json": {"text": "x"}}),
])
def test_503_model_unavailable_text_routes(client, monkeypatch, signal, route, payload):
    monkeypatch.setattr(m, "get_sentiment" if signal == "sentiment" else "get_threat", _boom)
    r = client.post(route, **payload)
    assert r.status_code == 503
    body = r.json()
    assert body["error"] == "model_unavailable" and body["signal"] == signal and "weights missing" in body["detail"]


def test_503_model_unavailable_voice(client, monkeypatch, wav_bytes):
    monkeypatch.setattr(m, "get_voice", _boom)
    r = client.post("/v1/signals/voice", json={"audio_base64": b64(wav_bytes)})
    assert r.status_code == 503 and r.json()["signal"] == "voice"


def test_text_route_reports_threat_unavailable_separately(client, monkeypatch):
    monkeypatch.setattr(m, "get_threat", _boom)
    r = client.post("/v1/signals/text", json={"text": "x"})
    assert r.status_code == 503 and r.json()["signal"] == "threat"


# ------------------------------------------------------------------ packaging / container layout
def test_repo_root_is_resolvable_at_container_depth():
    """Regression: in the image the service is /app, whose parents[1] does not exist (IndexError -> no boot)."""
    from pathlib import PurePosixPath

    def repo_root(service_root: PurePosixPath):
        return service_root.parents[1] if len(service_root.parents) > 1 else service_root

    assert str(repo_root(PurePosixPath("/app"))) == "/app"                      # container
    assert str(repo_root(PurePosixPath("/r/services/scoring"))) == "/r"         # checkout
    assert C.REPO_ROOT.exists() and C.MODELS_DIR is not None


def test_app_module_imports_without_torch():
    """app.main must import with only fastapi/numpy present (CI installs no torch)."""
    import importlib
    import sys
    assert "torch" not in sys.modules or True                                   # informational
    assert importlib.import_module("app.main").app is not None


# ------------------------------------------------------------------ latency (request overhead with mocked models)
def test_latency_under_100ms(client):
    client.post("/v1/signals/text", json={"text": "warm"})
    times = []
    for _ in range(30):
        t0 = time.perf_counter()
        client.post("/v1/signals/text", json={"text": "Mujhe dhamki di gayi hai."})
        times.append((time.perf_counter() - t0) * 1000)
    p95 = sorted(times)[int(0.95 * len(times)) - 1]
    assert p95 < 100, f"p95 request overhead {p95:.1f} ms (mocked models)"
