from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.victim import Victim
from app.models.case import CaseFile
from app.models.consent import ConsentRecord
from app.models.interaction import Interaction
from app.models.distress import DistressScore
from app.models.alert import Alert
from app.models.dispatch_log import DispatchLog
from app.services.audit_ledger import compute_alert_hash, GENESIS_HASH
from app.services.ivrs_gateway import IVRSGatewayService
from app.services.encryption import decrypt_pii
from app.policy_constants import (
    ESCALATE_SCORE,
    NEUTRAL_TIER1_MSG,
    WELLNESS_TIER2_MSG,
    TIER1_HOURS,
    TIER2_HOURS,
    TIER3_HOURS,
    TIER4_HOURS,
)


async def _dispatch_once(db: AsyncSession, case_id: str, tier: str, action: str) -> bool:
    """True only the FIRST time this (case, tier) action fires within 48 hours."""
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
    stmt = select(DispatchLog).where(
        DispatchLog.case_id == case_id,
        DispatchLog.tier == tier,
        DispatchLog.dispatched_at > two_days_ago
    )
    recent = (await db.execute(stmt)).scalars().first()
    if recent:
        return False

    log_entry = DispatchLog(
        case_id=case_id,
        tier=tier,
        action=action,
        dispatched_at=datetime.now(timezone.utc)
    )
    db.add(log_entry)
    await db.commit()
    return True


class CheckInSchedulerService:
    @staticmethod
    async def evaluate_case_checkin_state(db: AsyncSession, case_id: str) -> dict:
        """
        Evaluates the check-in status for a specific case and determines the current Tier (0 to 4).
        Dispatches actions with strict idempotency and dynamic victim PII decryption.
        """
        # Fetch case
        case_stmt = select(CaseFile).where(CaseFile.id == case_id)
        case_result = await db.execute(case_stmt)
        case_file = case_result.scalar_one_or_none()
        if not case_file:
            return {"error": "Case not found"}

        # Fetch victim & decrypt phone
        victim = await db.get(Victim, case_file.victim_id)
        victim_phone = decrypt_pii(victim.contact_encrypted) if victim else None

        # Check for SAFE_PAUSE consent record
        consent_stmt = select(ConsentRecord).where(
            ConsentRecord.victim_id == case_file.victim_id,
            ConsentRecord.scope == "SAFE_PAUSE",
            ConsentRecord.status == "GRANTED"
        )
        consent_res = await db.execute(consent_stmt)
        if consent_res.scalar_one_or_none():
            return {
                "case_id": case_id,
                "tier": "PAUSED",
                "message": "Safe Pause (Streak Freeze) is active for victim. Check-in alerts paused.",
                "hours_elapsed": 0.0
            }

        # Get latest interaction
        int_stmt = select(Interaction).where(Interaction.case_id == case_id).order_by(desc(Interaction.occurred_at))
        int_res = await db.execute(int_stmt)
        latest_interaction = int_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if latest_interaction:
            last_contact = latest_interaction.occurred_at
            if last_contact.tzinfo is None:
                last_contact = last_contact.replace(tzinfo=timezone.utc)
        else:
            last_contact = case_file.created_at or now
            if last_contact.tzinfo is None:
                last_contact = last_contact.replace(tzinfo=timezone.utc)

        hours_elapsed = (now - last_contact).total_seconds() / 3600.0

        tier = "TIER_0"
        action = "NORMAL"

        if hours_elapsed < float(TIER1_HOURS):
            tier = "TIER_0"
            action = "SCHEDULED_PROMPT"

        elif float(TIER1_HOURS) <= hours_elapsed < float(TIER2_HOURS):
            tier = "TIER_1"
            action = "SEND_NEUTRAL_REMINDER_SMS"
            if victim_phone and await _dispatch_once(db, case_id, tier, action):
                await IVRSGatewayService.send_sms(
                    to_phone=victim_phone,
                    message=NEUTRAL_TIER1_MSG
                )

        elif float(TIER2_HOURS) <= hours_elapsed < float(TIER3_HOURS):
            tier = "TIER_2"
            action = "SEND_WELLNESS_CHECK_PING"
            if victim_phone and await _dispatch_once(db, case_id, tier, action):
                await IVRSGatewayService.send_sms(
                    to_phone=victim_phone,
                    message=WELLNESS_TIER2_MSG
                )

        elif float(TIER3_HOURS) <= hours_elapsed < float(TIER4_HOURS):
            tier = "TIER_3"
            action = "ASSIGN_HUMAN_COUNSELLOR_CALL"
            if victim_phone and await _dispatch_once(db, case_id, tier, action):
                await IVRSGatewayService.trigger_voice_call(
                    to_phone=victim_phone
                )

        else: # >= 168 hours (7 days)
            tier = "TIER_4"
            
            # Fetch latest distress score to evaluate combined condition
            latest_score = None
            if latest_interaction:
                score_stmt = select(DistressScore).where(DistressScore.interaction_id == latest_interaction.id)
                score_res = await db.execute(score_stmt)
                latest_score = score_res.scalar_one_or_none()

            composite = latest_score.composite_score if latest_score else 0.5
            threat = latest_score.threat_flag if latest_score else False

            # COMBINED CONDITION RULE: Never escalate to authorities on silence alone! (threshold >= 0.75)
            if composite >= ESCALATE_SCORE or threat:
                action = "ESCALATE_DISTRICT_PROTECTION_OFFICER"
                if await _dispatch_once(db, case_id, tier, action):
                    await CheckInSchedulerService._create_tier4_alert(db, case_file, latest_score)
            else:
                action = "ASSIGN_HIGH_PRIORITY_COUNSELLOR_OUTREACH"
                await _dispatch_once(db, case_id, tier, action)

        return {
            "case_id": case_id,
            "tier": tier,
            "action": action,
            "hours_elapsed": round(hours_elapsed, 2),
            "last_contact": last_contact.isoformat()
        }

    @staticmethod
    async def _create_tier4_alert(db: AsyncSession, case_file: CaseFile, distress_score: DistressScore | None):
        if not distress_score:
            return

        # Check existing alert
        existing_stmt = select(Alert).where(Alert.score_id == distress_score.id, Alert.risk_level == "CRITICAL")
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            return # Already created

        # Get latest alert hash for chaining
        latest_alert_stmt = select(Alert).order_by(desc(Alert.raised_at))
        latest_alert_res = await db.execute(latest_alert_stmt)
        latest_alert = latest_alert_res.scalars().first()

        prev_hash = latest_alert.current_hash if latest_alert else GENESIS_HASH
        now = datetime.now(timezone.utc)
        current_hash = compute_alert_hash(
            score_id=distress_score.id,
            risk_level="CRITICAL",
            raised_at=now,
            previous_hash=prev_hash
        )

        new_alert = Alert(
            score_id=distress_score.id,
            official_id=None,
            risk_level="CRITICAL",
            status="PENDING",
            raised_at=now,
            previous_hash=prev_hash,
            current_hash=current_hash
        )
        db.add(new_alert)
        await db.commit()
