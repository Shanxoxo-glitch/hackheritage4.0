"""
Backend -> scoring service integration for POST /api/v1/perception/score.

Two layers:
  * mocked   the ScoringClient is monkeypatched, so both the happy path and the
             degradation path run without the scoring service (these run in CI).
  * live     marked `live_scoring`, runs only when a scoring service is actually
             reachable at SCORING_URL (skipped otherwise).
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app as fastapi_app
from app.services import scoring_client as sc_module
from app.services.scoring_client import ScoringUnavailable

client = TestClient(fastapi_app)


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_create())


def _interaction_id():
    return str(uuid.uuid4())


TEXT_RESPONSE = {
    "schema_version": "1.0", "request_id": "r1", "interaction_id": None,
    "sentiment": {"label": "HIGH", "level": 2, "sentiment_score": 0.91, "probs": {"LOW": 0.02, "MODERATE": 0.07, "HIGH": 0.91},
                  "confidence": 0.91, "entropy": 0.2, "calibrated": True, "model_version": "distress_v3"},
    "threat": {"threat_flag": True, "prob": 0.98, "raw_prob": 0.61, "confidence": 0.98, "entropy": 0.1,
               "calibrated": True, "model_version": "threat_contrastive_v1"},
    "flags": [], "latency_ms": 22,
}
VOICE_RESPONSE = {
    "schema_version": "1.0", "request_id": "r2", "interaction_id": None,
    "voice": {"label": "STRESSED", "voice_stress_score": 0.77, "confidence": 0.77, "audio_seconds": 3.6,
              "features_summary": {"f0_mean": 180.0}, "model_version": "voice_stress_ravdess",
              "trained_on": "ravdess_all_24_actors"},
    "flags": [], "latency_ms": 40,
}


class FakeClient:
    base_url = "http://scoring-mock:8100"

    def __init__(self, text=TEXT_RESPONSE, voice=VOICE_RESPONSE, fail=None):
        self.text_response, self.voice_response, self.fail = text, voice, fail or set()

    async def score_text(self, text, interaction_id=None):
        if "text" in self.fail:
            raise ScoringUnavailable("model_unavailable: sentiment")
        return self.text_response

    async def score_voice_base64(self, audio_base64, interaction_id=None):
        if "voice" in self.fail:
            raise ScoringUnavailable("model_unavailable: voice")
        return self.voice_response

    async def health(self):
        if "health" in self.fail:
            raise ScoringUnavailable("ConnectError")
        return {"status": "ok", "models": {}}


@pytest.fixture
def fake_scoring(monkeypatch):
    def _install(**kwargs):
        fake = FakeClient(**kwargs)
        monkeypatch.setattr(sc_module, "scoring_client", fake)
        import app.api.v1.perception as perception
        monkeypatch.setattr(perception, "scoring_client", fake)
        return fake
    return _install


# ---------------------------------------------------------------- happy path
def test_score_uses_scoring_service_signals(fake_scoring):
    fake_scoring()
    r = client.post("/api/v1/perception/score", json={"interaction_id": _interaction_id(),
                                                     "text": "Case wapas le lo warna bhai ko uthwa lenge.",
                                                     "audio_base64": "ZmFrZQ=="})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["sentiment_score"] == 0.91 and body["voice_stress_score"] == 0.77
    assert body["threat_flag"] is True
    assert body["signal_source"] == "scoring_service" and body["degraded_signals"] == []
    assert body["model_versions"] == {"sentiment": "distress_v3", "threat": "threat_contrastive_v1",
                                      "voice": "voice_stress_ravdess"}
    expected = 0.50 * 0.91 + 0.30 * 0.77 + 0.20 * 1.0
    assert abs(body["composite_score"] - round(expected, 4)) < 1e-3
    assert body["confidence"] == 0.77 and body["trend_flag"] == "ESCALATING"


def test_text_only_interaction_marks_voice_not_provided(fake_scoring):
    """No audio in the payload is NOT a service failure, but it must not look like a real voice score."""
    fake_scoring()
    body = client.post("/api/v1/perception/score",
                       json={"interaction_id": _interaction_id(), "text": "they threatened me"}).json()
    assert body["degraded_signals"] == ["voice_not_provided"] and body["signal_source"] == "partial"
    assert "voice" not in body["model_versions"]


def test_response_keeps_the_existing_contract_fields(fake_scoring):
    fake_scoring()
    body = client.post("/api/v1/perception/score",
                       json={"interaction_id": _interaction_id(), "text": "hello"}).json()
    assert {"id", "interaction_id", "sentiment_score", "voice_stress_score", "threat_flag",
            "composite_score", "confidence", "trend_flag", "created_at"} <= set(body)


def test_low_distress_text_is_stable(fake_scoring):
    calm = {**TEXT_RESPONSE,
            "sentiment": {**TEXT_RESPONSE["sentiment"], "label": "LOW", "level": 0, "sentiment_score": 0.04,
                          "confidence": 0.95},
            "threat": {**TEXT_RESPONSE["threat"], "threat_flag": False, "prob": 0.02, "confidence": 0.98}}
    fake_scoring(text=calm)
    body = client.post("/api/v1/perception/score",
                       json={"interaction_id": _interaction_id(),
                             "text": "The hearing is on the 14th and I submitted the documents."}).json()
    assert body["threat_flag"] is False and body["trend_flag"] == "STABLE"
    assert body["composite_score"] < 0.6


# ---------------------------------------------------------------- degradation
def test_degrades_to_heuristic_when_scoring_is_down(fake_scoring):
    fake_scoring(fail={"text", "voice"})
    r = client.post("/api/v1/perception/score", json={"interaction_id": _interaction_id(),
                                                      "text": "he said he would kill me",
                                                      "audio_base64": "ZmFrZQ=="})
    assert r.status_code == 201, r.text                     # a scoring outage never fails the case
    body = r.json()
    assert body["signal_source"] == "heuristic_fallback"
    assert {"text", "voice"} <= set(body["degraded_signals"])
    assert body["threat_flag"] is True and body["sentiment_score"] == 0.85     # keyword heuristic
    assert body["confidence"] == 0.50


def test_partial_degradation_keeps_the_working_signal(fake_scoring):
    fake_scoring(fail={"voice"})
    body = client.post("/api/v1/perception/score", json={"interaction_id": _interaction_id(),
                                                        "text": "they threatened me",
                                                        "audio_base64": "ZmFrZQ=="}).json()
    assert body["signal_source"] == "partial" and body["degraded_signals"] == ["voice"]
    assert body["sentiment_score"] == 0.91                              # real text signal kept
    assert body["model_versions"]["sentiment"] == "distress_v3" and "voice" not in body["model_versions"]


def test_audio_url_is_not_scored_server_side(fake_scoring):
    fake_scoring()
    body = client.post("/api/v1/perception/score", json={"interaction_id": _interaction_id(), "text": "hi",
                                                         "audio_url": "http://example.invalid/a.wav"}).json()
    assert "voice_url_not_scored" in body["degraded_signals"] and body["signal_source"] == "partial"


def test_perception_health_reports_scoring_state(fake_scoring):
    fake_scoring()
    assert client.get("/api/v1/perception/health").json()["scoring_service"] == "up"
    fake_scoring(fail={"health"})
    down = client.get("/api/v1/perception/health").json()
    assert down["scoring_service"] == "down" and "heuristic" in down["note"]


# ---------------------------------------------------------------- live (skipped unless the service runs)
@pytest.mark.live_scoring
def test_live_scoring_service_end_to_end():
    import httpx
    from app.config import settings
    try:
        httpx.get(f"{settings.SCORING_URL}/healthz", timeout=3).raise_for_status()
    except Exception as exc:
        pytest.skip(f"no scoring service at {settings.SCORING_URL}: {type(exc).__name__}")
    r = client.post("/api/v1/perception/score",
                    json={"interaction_id": _interaction_id(),
                          "text": "Unhone kaha case wapas lo warna ghar jala denge."})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["signal_source"] in {"scoring_service", "partial"}
    assert body["model_versions"].get("threat") and body["threat_flag"] is True
