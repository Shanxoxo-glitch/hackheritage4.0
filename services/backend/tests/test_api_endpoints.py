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

