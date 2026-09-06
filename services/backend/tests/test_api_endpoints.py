import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.database import engine, Base
import app.models  # ensure models registered


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_create_tables())

client = TestClient(fastapi_app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_quick_exit_purge_endpoint():
    response = client.get("/api/v1/auth/purge", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://weather.com"

def test_victim_onboarding_and_case_flow():
    # 1. Onboard victim
    v_res = client.post("/api/v1/cases/victims", json={
        "name": "Sunita Devi",
        "contact": "+919123456789",
        "email": "sunita@example.com",
        "vulnerability_category": "SC/ST_PoA_Sec3",
        "preferred_language": "hi"
    })
    assert v_res.status_code == 201
    victim = v_res.json()
    assert victim["name"] == "Sunita Devi"
    assert "id" in victim

    # 2. Create case file
    c_res = client.post("/api/v1/cases/files", json={
        "victim_id": victim["id"],
        "fir_number": "FIR-2026-9901",
        "act_section": "SC/ST PoA Act 1989 Section 3(1)(r)",
        "case_stage": "FIR",
        "registered_on": "2026-09-01"
    })
    assert c_res.status_code == 201
    case_file = c_res.json()
    assert case_file["fir_number"] == "FIR-2026-9901"

    # 3. Submit Check-in
    chk_res = client.post("/api/v1/checkin/submit", json={
        "case_id": case_file["id"],
        "channel": "PWA",
        "language": "hi",
        "transcript": "Aaj sab theek hai."
    })
    assert chk_res.status_code == 200
    chk = chk_res.json()
    assert chk["status"] == "CHECKIN_SUCCESSFUL"
    assert "interaction_id" in chk

    # 4. Score Interaction
    score_res = client.post("/api/v1/perception/score", json={
        "interaction_id": chk["interaction_id"],
        "text": "Aaj sab theek hai."
    })
    assert score_res.status_code == 201
    score = score_res.json()
    assert "composite_score" in score

    # 5. Create Risk Alert
    alert_res = client.post("/api/v1/escalate/alerts", json={
        "score_id": score["id"],
        "risk_level": "MODERATE"
    })
    assert alert_res.status_code == 201
    alert = alert_res.json()
    assert "current_hash" in alert
    assert "previous_hash" in alert

    # 6. Fetch Triage Queue
    triage_res = client.get("/api/v1/escalate/triage-queue")
    assert triage_res.status_code == 200
    triage = triage_res.json()
    assert len(triage) >= 1
    assert any(item["alert_id"] == alert["id"] for item in triage)
    assert "triage_priority_score" in triage[0]


def test_v1_case_context_contract_verdict():
    # 1. Onboard victim
    v_res = client.post("/api/v1/cases/victims", json={
        "name": "Ananya Sharma",
        "contact": "+919876543210",
        "vulnerability_category": "SC/ST_PoA_Sec3",
        "preferred_language": "hi"
    })
    victim = v_res.json()

    # 2. Create case
    c_res = client.post("/api/v1/cases/files", json={
        "victim_id": victim["id"],
        "fir_number": "FIR-2026-CONTEXT-01",
        "act_section": "PoA Section 3",
        "case_stage": "FIR",
        "registered_on": "2026-09-01"
    })
    case = c_res.json()

    # 3. Call GET /v1/case/{case_id}/context
    res = client.get(f"/v1/case/{case['id']}/context")
    assert res.status_code == 200
    ctx = res.json()

    # Verify exact keys required by reviewer's verdict test
    expected_keys = {
        "case_stage", "days_to_next_hearing", "language",
        "consent_scopes", "recent_checkins", "recent_messages", "score_history"
    }
    assert set(ctx.keys()) == expected_keys
    assert ctx["case_stage"] == "FIR"
    assert ctx["language"] == "hi"


def test_v1_alerts_orchestrator_contract_verdict():
    # 1. Onboard victim & create case
    v_res = client.post("/api/v1/cases/victims", json={
        "name": "Priya Verma",
        "contact": "+919876543211",
        "preferred_language": "en"
    })
    victim = v_res.json()

    c_res = client.post("/api/v1/cases/files", json={
        "victim_id": victim["id"],
        "fir_number": "FIR-2026-ALERTS-01",
        "act_section": "PoA Section 3",
        "registered_on": "2026-09-01"
    })
    case = c_res.json()

    # 2. Post orchestrator-shaped alert to /v1/alerts
    alert_payload = {
        "case_id": case["id"],
        "severity": "high",
        "reasons": ["composite 0.82 >= 0.75"],
        "summary_text": "High distress detected during call"
    }
    res = client.post("/v1/alerts", json=alert_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["risk_level"] == "HIGH"
    assert "current_hash" in data
    assert "previous_hash" in data


def test_v1_consent_contract():
    # Onboard victim & case
    v_res = client.post("/api/v1/cases/victims", json={
        "name": "Kavita Ram",
        "contact": "+919876543212"
    })
    victim = v_res.json()

    # Grant SAFE_PAUSE consent
    res = client.post("/v1/consent", json={
        "victim_id": victim["id"],
        "scope": "SAFE_PAUSE",
        "granted": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GRANTED"
    assert data["scope"] == "SAFE_PAUSE"

    # Revoke SAFE_PAUSE consent
    res2 = client.post("/v1/consent", json={
        "victim_id": victim["id"],
        "scope": "SAFE_PAUSE",
        "granted": False
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "REVOKED"


def test_checkin_status_idempotency_verdict():
    # Onboard victim & case
    v_res = client.post("/api/v1/cases/victims", json={
        "name": "Meena Kumari",
        "contact": "+919876543213"
    })
    victim = v_res.json()

    c_res = client.post("/api/v1/cases/files", json={
        "victim_id": victim["id"],
        "fir_number": "FIR-2026-IDEM-01",
        "act_section": "PoA Section 3",
        "registered_on": "2026-09-01"
    })
    case = c_res.json()

    # Evaluate check-in status twice (verifying idempotency)
    res1 = client.get(f"/checkin/status/{case['id']}")
    assert res1.status_code == 200
    assert "tier" in res1.json()

    res2 = client.get(f"/checkin/status/{case['id']}")
    assert res2.status_code == 200
    assert res2.json()["tier"] == res1.json()["tier"]
