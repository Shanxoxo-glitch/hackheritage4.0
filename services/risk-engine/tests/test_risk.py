# ---- v3 suite: all 5 v2 tests preserved + cover the bugs v2 shipped with ---
import math
from datetime import datetime, timedelta, timezone

import joblib
import pytest
from fastapi.testclient import TestClient

from app import forecast as forecast_module
from app import fusion
from app.fusion import fuse
from app.main import app
from app.schemas import (Engagement, ForecastRequest, FusionRequest,
                         Sentiment, Threat, VoiceStress)


@pytest.fixture(autouse=True)
def _hermetic(tmp_path, monkeypatch):
    """Tests never read/write the developer's real artifacts/."""
    monkeypatch.setattr(fusion, "NOISE_FILE", tmp_path / "detector_noise.json")
    fusion._noise_cache = None
    monkeypatch.setattr(forecast_module, "ARTIFACT", tmp_path / "forecaster.pkl")
    forecast_module.MODEL = None
    forecast_module.MODEL_VERSION = "heuristic-v0"
    yield
    forecast_module.MODEL = None
    forecast_module.MODEL_VERSION = "heuristic-v0"
    fusion._noise_cache = None


@pytest.fixture()
def client():
    with TestClient(app) as c:      # context manager -> lifespan -> load_model()
        yield c


# ---- v2 regression tests ----------------------------------------------------
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


def test_10_explain_endpoint(client):
    r = client.post("/v1/explain", json={
        "sentiment": {"score": 0.8}, "threat": {"prob": 0.3},
        "voice_stress": {"score": 0.82}})
    assert r.status_code == 200
    body = r.json()
    assert set(body["sensors"]) == {"sentiment", "threat", "voice_stress"}
    assert "score_without_this" in body["sensors"]["threat"]


def test_11_metrics_endpoint_counts(client):
    client.post("/v1/fusion", json={"sentiment": {"score": 0.5}})
    m = client.get("/metrics").text
    assert "risk_fusion_requests_total" in m
    assert "risk_signal_mean" in m


def test_12_forecast_interval_ordered(client):
    out = client.post("/v1/forecast", json={
        "case_id": "c-4",
        "score_history": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85]}).json()
    if out.get("p10") is not None:
        assert out["p10"] <= out["p_escalation"] <= out["p90"]


# ---- v3: crash-level bugs that v2 shipped with ------------------------------
def test_13_features_contract():
    f = forecast_module._features([0.3, 0.4, 0.5])
    assert len(f) == len(forecast_module.FEATURES) == 5


def test_14_corrupt_artifact_falls_back(tmp_path, monkeypatch):
    bad = tmp_path / "bad.pkl"
    bad.write_bytes(b"garbage")
    monkeypatch.setattr(forecast_module, "ARTIFACT", bad)
    assert forecast_module.load_model() is False
    assert forecast_module.MODEL is None
    assert forecast_module.MODEL_VERSION == "heuristic-v0"


def test_15_ensemble_artifact_served_end_to_end(tmp_path, monkeypatch):
    """The v2 crash: dict artifact has no .predict_proba. Now wrapped."""
    pytest.importorskip("sklearn")
    from sklearn.linear_model import LogisticRegression
    m = LogisticRegression().fit(
        [[0.1, 0.1, 0.0, 0.0, 0.0], [0.9, 0.9, 0.5, 0.5, 1.0]], [0, 1])
    cal = LogisticRegression().fit([[0.2], [0.8]], [0, 1])
    artifact = {"version": "test-ens-v3", "models": [m], "calibrator": cal,
                "feature_names": list(forecast_module.FEATURES),
                "feature_means": dict(zip(forecast_module.FEATURES, [0.5] * 5)),
                "coefs": dict(zip(forecast_module.FEATURES, [0.0] * 5)),
                "horizon_days": 7}
    pkl = tmp_path / "f.pkl"
    joblib.dump(artifact, pkl)
    monkeypatch.setattr(forecast_module, "ARTIFACT", pkl)
    assert forecast_module.load_model() is True
    out = forecast_module.forecast(ForecastRequest(
        case_id="c-ens", score_history=[0.3, 0.4, 0.5, 0.6]))
    assert out.model_version == "test-ens-v3"
    assert out.p10 is not None and out.p90 is not None
    assert out.p10 <= out.p_escalation <= out.p90
    assert out.drivers


def test_16_feature_skew_rejected(tmp_path, monkeypatch):
    pkl = tmp_path / "skew.pkl"
    joblib.dump({"feature_names": ["a", "b", "c", "d", "e"]}, pkl)
    monkeypatch.setattr(forecast_module, "ARTIFACT", pkl)
    assert forecast_module.load_model() is False    # never serve a skewed model


# ---- v3: behavioral bugs ----------------------------------------------------
def test_17_single_sensor_never_conflicts():
    out = fuse(FusionRequest(sentiment=Sentiment(score=1.0)))
    assert out.conflict is False
    assert out.conflict_chi2 == 0.0


def test_18_engagement_reported_stale():
    old = datetime.now(timezone.utc) - timedelta(days=30)
    out = fuse(FusionRequest(engagement=Engagement(
        messages_last_7d=2, observed_at=old)))
    assert "engagement" in out.stale


def test_19_dirty_history_stays_finite(client):
    r = client.post("/v1/forecast", json={
        "case_id": "c-dirty",
        "score_history": [2.5, float("nan"), -1.0, 0.6, 0.7]})
    assert r.status_code == 200
    p = r.json()["p_escalation"]
    assert math.isfinite(p) and 0.0 <= p <= 0.97


def test_20_unknown_stage_is_safe(client):
    r = client.post("/v1/forecast", json={
        "case_id": "c-stage", "score_history": [0.3, 0.5, 0.7],
        "legal_stage": "appeal_hearing"})
    assert r.status_code == 200
    assert 0.0 <= r.json()["p_escalation"] <= 0.97


def test_21_metrics_content_type(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")


def test_22_healthz_reports_model(client):
    assert client.get("/healthz").json()["model"] == "heuristic-v0"
