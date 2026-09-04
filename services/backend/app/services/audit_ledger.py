import hashlib
from datetime import datetime

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def compute_alert_hash(
    score_id: str,
    risk_level: str,
    raised_at: str | datetime,
    previous_hash: str = GENESIS_HASH
) -> str:
    """
    Computes a SHA-256 cryptographic hash chained to the previous record's hash.
    Ensures alert logs are tamper-evident for courtroom admissibility.
    """
    raised_at_str = raised_at.isoformat() if isinstance(raised_at, datetime) else str(raised_at)
    payload = f"{score_id}:{risk_level}:{raised_at_str}:{previous_hash}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def verify_hash_chain(alerts_list: list) -> bool:
    """
    Verifies that a sequence of alert objects maintains a valid hash chain.
    """
    prev_hash = GENESIS_HASH
    for alert in alerts_list:
        expected = compute_alert_hash(
            score_id=str(alert.score_id),
            risk_level=str(alert.risk_level),
            raised_at=alert.raised_at,
            previous_hash=prev_hash
        )
        if alert.current_hash != expected or alert.previous_hash != prev_hash:
            return False
        prev_hash = alert.current_hash
    return True
