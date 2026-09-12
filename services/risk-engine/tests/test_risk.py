from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.forecast import BASE_RATE
from app.fusion import fuse
from app.main import app
from app.schemas import FusionRequest, Sentiment, Threat, VoiceStress

client = TestClient(app)


def test_1_healthz():
    assert client.get("/healthz").json()["ok"] is True


def test_2_agree_confidence_beats_disagree():
    agree = fuse(FusionRequest(sentiment=Sentiment(score=.8),
                               voice_stress=VoiceStress(score=.82)))
    disagree = fuse(FusionRequest(sentiment=Sentiment(score=.9),
                                  voice_stress=VoiceStress(score=.2)))
    assert agree.confidence > disagree.confidence + 0.2
    assert agree.composite_score > 0.75


def test_3_threat_force_rule():
    out = fuse(FusionRequest(sentiment=Sentiment(score=.2),
                             threat=Threat(prob=.95)))
    assert out.composite_score >= 0.8
    assert "threat_force" in out.triggers
    assert out.label == "CRITICAL"


def test_4_degraded_when_no_signals():
    out = client.post("/v1/fusion", json={}).json()
    assert out["degraded"] is True and out["confidence"] < 0.1


def test_5_top_signals_are_known_names():
    out = client.post("/v1/fusion", json={
        "sentiment": {"score": 0.7}, "threat": {"prob": 0.4},
        "voice_stress": {"score": 0.6}}).json()
    assert set(out["top_signals"]) <= {"sentiment", "threat",
                                       "voice_stress", "engagement"}
    assert out["top_signals"][0] in ("sentiment", "threat")


def test_6_forecast_cold_start():
    out = client.post("/v1/forecast", json={
        "case_id": "c-1", "score_history": [0.5]}).json()
    assert out["p_escalation"] == BASE_RATE and out["horizon_days"] == 7


def test_7_forecast_detects_escalation():
    stable = client.post("/v1/forecast", json={
        "case_id": "c-2", "score_history": [0.3] * 10}).json()
    rising = client.post("/v1/forecast", json={
        "case_id": "c-3", "score_history":
            [0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.78, 0.82, 0.85, 0.9]}).json()
    assert rising["p_escalation"] > stable["p_escalation"]


def test_8_stale_signals_lose_weight():
    now = datetime.now(timezone.utc)
    fresh = fuse(FusionRequest(
        sentiment=Sentiment(score=.8, observed_at=now),
        voice_stress=VoiceStress(score=.82, observed_at=now)))
    old = fuse(FusionRequest(
        sentiment=Sentiment(score=.8, observed_at=now),
        voice_stress=VoiceStress(score=.82,
                                 observed_at=now - timedelta(days=30))))
    assert fresh.confidence > old.confidence
    assert "voice_stress" in old.stale


def test_9_conflict_is_detected_and_flagged():
    out = fuse(FusionRequest(sentiment=Sentiment(score=.9),
                             voice_stress=VoiceStress(score=.2)))
    assert out.conflict is True
    assert out.conflict_chi2 > 3.84


def test_10_explain_endpoint():
    r = client.post("/v1/explain", json={
        "sentiment": {"score": 0.8}, "threat": {"prob": 0.3},
        "voice_stress": {"score": 0.82}})
    assert r.status_code == 200
    body = r.json()
    assert set(body["sensors"]) == {"sentiment", "threat", "voice_stress"}
    assert "score_without_this" in body["sensors"]["threat"]


def test_11_metrics_endpoint_counts():
    client.post("/v1/fusion", json={"sentiment": {"score": 0.5}})
    m = client.get("/metrics").text
    assert "risk_fusion_requests_total" in m
    assert "risk_signal_mean" in m


def test_12_forecast_interval_ordered():
    out = client.post("/v1/forecast", json={
        "case_id": "c-4",
        "score_history": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85]}).json()
    if out.get("p10") is not None:
        assert out["p10"] <= out["p_escalation"] <= out["p90"]
