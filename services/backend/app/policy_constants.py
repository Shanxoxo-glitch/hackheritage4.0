"""
Policy Constants Specification
-------------------------------
Single source of truth for decision policy thresholds, escalation hours, and templated messages.
"""

# Decision Policy Thresholds (matching contracts/decision-policy.md)
ESCALATE_SCORE: float = 0.75
HIGH_DISTRESS_THRESHOLD: float = 0.75
MODERATE_DISTRESS_THRESHOLD: float = 0.60
LOW_DISTRESS_THRESHOLD: float = 0.45
CONFIDENCE_GATE: float = 0.60

# Check-in Tier Thresholds (Hours Elapsed)
TIER1_HOURS: int = 24    # 1 day missed
TIER2_HOURS: int = 72    # 3 days missed
TIER3_HOURS: int = 120   # 5 days missed
TIER4_HOURS: int = 168   # 7 days missed

# Templated Neutral Communication Messages
NEUTRAL_TIER1_MSG: str = "Your daily community update is ready. Reply 1 to check in."
WELLNESS_TIER2_MSG: str = "We're checking in on you. Would you like a counsellor to call? Reply YES."

# Canonical Legal Stage Mapping (Orchestrator Adapter B compatibility)
STAGE_CANONICAL: dict[str, str] = {
    "FIR": "FIR",
    "CHARGESHEET": "investigation",
    "INVESTIGATION": "investigation",
    "TRIAL": "trial",
    "COMPENSATION": "compensation",
    "CLOSED": "compensation"
}
