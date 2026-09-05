"""In-process background reminder scheduler.

Polls for due reminders and sends them, on a plain asyncio loop — no new
dependency (no APScheduler/Celery/Redis), consistent with this project's
"modular monolith, no message queues just to look complex" architecture
rule. Fine for this app's actual scale (a handful of reminders per patient);
would need a real job queue only at a scale this project isn't targeting.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.future import select

from .database import async_session
from ..db.models.reminder import Reminder

logger = logging.getLogger("setu.scheduler")

POLL_INTERVAL_SECONDS = 30


async def _send_due_reminders() -> None:
    async with async_session() as db:
        stmt = select(Reminder).filter(
            Reminder.status == "scheduled",
            Reminder.is_active == True,  # noqa: E712
            Reminder.scheduled_at <= datetime.utcnow(),
        )
        result = await db.execute(stmt)
        due = result.scalars().all()

        if not due:
            return

        from ..modules.reminders.service import ReminderService
        service = ReminderService(db)
        for reminder in due:
            try:
                outcome = await service.send_reminder(str(reminder.id))
                if outcome.get("error"):
                    logger.warning(f"Reminder {reminder.id} not sent: {outcome['error']}")
            except Exception as e:
                logger.error(f"Reminder {reminder.id} send failed: {e}")


async def run_reminder_scheduler() -> None:
    """Runs forever (until cancelled at app shutdown), checking for due
    reminders every POLL_INTERVAL_SECONDS."""
    logger.info(f"Reminder scheduler started (polling every {POLL_INTERVAL_SECONDS}s)")
    while True:
        try:
            await _send_due_reminders()
        except Exception as e:
            logger.error(f"Reminder scheduler poll failed: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
