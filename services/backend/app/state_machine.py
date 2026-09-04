"""Case Legal State Machine (FIR -> Investigation -> Trial -> Compensation)."""
class CaseStateMachine:
    VALID_STAGES = ["FIR", "INVESTIGATION", "CHARGESHEET", "TRIAL", "COMPENSATION", "CLOSED"]

    @classmethod
    def can_transition(cls, current_stage: str, next_stage: str) -> bool:
        current = current_stage.upper()
        target = next_stage.upper()
        if current not in cls.VALID_STAGES or target not in cls.VALID_STAGES:
            return False
        return cls.VALID_STAGES.index(target) > cls.VALID_STAGES.index(current)
