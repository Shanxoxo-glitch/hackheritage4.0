"""
Background Check-in Worker
--------------------------
Runs on a configurable interval (default: every 60 minutes) via APScheduler.
Scans ALL active case files in the database, evaluates each case's check-in state,
and automatically fires the appropriate Tier 1/2/3/4 action (SMS, voice call, alert).

This is the "proactive monitoring" engine — it runs entirely in the background
without any API call needed to trigger it.
"""

import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.case import CaseFile
from app.models.victim import Victim
from app.services.scheduler import CheckInSchedulerService
from app.services.encryption import decrypt_pii
from app.services.ivrs_gateway import IVRSGatewayService
from app.config import settings

logger = logging.getLogger("checkin_worker")


async def run_checkin_sweep():
    """
    Core background job: iterates all active case files, evaluates their Tier,
    and dispatches the appropriate action (SMS / voice call / alert creation).
    Called automatically by APScheduler every CHECKIN_WORKER_INTERVAL_MINUTES.
    """
    logger.info(f"[WORKER] Check-in sweep started at {datetime.now(timezone.utc).isoformat()}")

    async with AsyncSessionLocal() as db:
        # Fetch all open case files
        stmt = select(CaseFile)
        result = await db.execute(stmt)
        cases = result.scalars().all()

        if not cases:
            logger.info("[WORKER] No active cases found. Sweep complete.")
            return

        logger.info(f"[WORKER] Evaluating {len(cases)} active case(s)...")

        for case in cases:
            try:
                # Evaluate the tier for this case
                state = await CheckInSchedulerService.evaluate_case_checkin_state(db, str(case.id))
                tier = state.get("tier", "TIER_0")
                action = state.get("action", "NORMAL")
                hours = state.get("hours_elapsed", 0)

                if tier == "PAUSED":
                    logger.info(f"[WORKER] Case {case.id} → SAFE_PAUSE active, skipping.")
                    continue

                # Resolve victim phone number for dispatch
                victim_stmt = select(Victim).where(Victim.id == case.victim_id)
                victim_res = await db.execute(victim_stmt)
                victim = victim_res.scalar_one_or_none()
                victim_phone = decrypt_pii(victim.contact_encrypted) if victim else None

                logger.info(f"[WORKER] Case {case.id} → {tier} ({hours:.1f}h elapsed) → Action: {action}")

                # Dispatch action based on tier
                if action == "SEND_NEUTRAL_REMINDER_SMS" and victim_phone:
                    await IVRSGatewayService.send_sms(
                        to_phone=victim_phone,
                        message="Your daily community update is ready. Reply 1 to check in."
                    )
                elif action == "SEND_WELLNESS_CHECK_PING" and victim_phone:
                    await IVRSGatewayService.send_sms(
                        to_phone=victim_phone,
                        message="We're checking in on you. Would you like a counsellor to call? Reply YES."
                    )
                elif action == "ASSIGN_HUMAN_COUNSELLOR_CALL" and victim_phone:
                    await IVRSGatewayService.trigger_voice_call(to_phone=victim_phone)

                elif action == "ESCALATE_DISTRICT_PROTECTION_OFFICER":
                    logger.warning(
                        f"[WORKER] CRITICAL: Case {case.id} → Tier 4 escalation fired! "
                        f"Alert already created in DB by scheduler service."
                    )
                elif action == "ASSIGN_HIGH_PRIORITY_COUNSELLOR_OUTREACH":
                    logger.warning(
                        f"[WORKER] HIGH PRIORITY: Case {case.id} → 7+ days missed but risk "
                        f"below threshold. Routing to senior counsellor outreach."
                    )

            except Exception as e:
                logger.error(f"[WORKER] Error evaluating case {case.id}: {e}")

    logger.info(f"[WORKER] Sweep complete at {datetime.now(timezone.utc).isoformat()}")


def build_scheduler() -> AsyncIOScheduler:
    """
    Builds and returns the APScheduler AsyncIOScheduler.
    Uses Redis as the job store for persistence across restarts.
    Falls back to in-memory store if Redis is unavailable (local dev without Docker).
    """
    try:
        import redis
        host = settings.REDIS_URL.split("//")[1].split(":")[0]
        port = int(settings.REDIS_URL.split(":")[-1].split("/")[0])
        db = int(settings.REDIS_URL.split("/")[-1])
        
        # Test ping to check if Redis server is reachable
        r = redis.Redis(host=host, port=port, db=db, socket_timeout=1)
        r.ping()

        jobstores = {
            "default": RedisJobStore(
                jobs_key="sih2026_apscheduler_jobs",
                run_times_key="sih2026_apscheduler_run_times",
                host=host,
                port=port,
                db=db
            )
        }
        logger.info("[SCHEDULER] Using Redis job store for APScheduler.")
    except Exception:
        logger.info("[SCHEDULER] Redis not connected. Operating in standalone in-memory job store mode.")
        jobstores = {}

    scheduler = AsyncIOScheduler(jobstores=jobstores)

    scheduler.add_job(
        run_checkin_sweep,
        trigger="interval",
        minutes=settings.CHECKIN_WORKER_INTERVAL_MINUTES,
        id="checkin_sweep_job",
        name="Automated Check-in Tier Sweep",
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )

    return scheduler
