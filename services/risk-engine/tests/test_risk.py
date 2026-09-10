# ---- v2 tests -----------------------------------------------------------
from datetime import datetime, timedelta, timezone


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
