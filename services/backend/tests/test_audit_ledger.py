from datetime import datetime
from app.services.audit_ledger import compute_alert_hash, verify_hash_chain, GENESIS_HASH

class MockAlert:
    def __init__(self, score_id, risk_level, raised_at, previous_hash):
        self.score_id = score_id
        self.risk_level = risk_level
        self.raised_at = raised_at
        self.previous_hash = previous_hash
        self.current_hash = compute_alert_hash(score_id, risk_level, raised_at, previous_hash)

def test_sha256_hash_chaining():
    now = datetime.utcnow()
    a1 = MockAlert("score-1", "MODERATE", now, GENESIS_HASH)
    a2 = MockAlert("score-2", "HIGH", now, a1.current_hash)
    a3 = MockAlert("score-3", "CRITICAL", now, a2.current_hash)

    chain = [a1, a2, a3]
    assert verify_hash_chain(chain) is True

def test_hash_chain_tamper_detection():
    now = datetime.utcnow()
    a1 = MockAlert("score-1", "MODERATE", now, GENESIS_HASH)
    a2 = MockAlert("score-2", "HIGH", now, a1.current_hash)
    
    # Tamper with a1 risk level!
    a1.risk_level = "LOW"

    chain = [a1, a2]
    assert verify_hash_chain(chain) is False
