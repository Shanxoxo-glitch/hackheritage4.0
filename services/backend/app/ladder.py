"""Tier 0-4 Escalation Ladder Service."""
from app.services.scheduler import CheckInSchedulerService

# Export alias for compatibility
EscalationLadder = CheckInSchedulerService
check_in_scheduler = CheckInSchedulerService

__all__ = ["CheckInSchedulerService", "EscalationLadder", "check_in_scheduler"]
