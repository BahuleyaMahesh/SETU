from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.reminder import Reminder
from ...db.models.patient import Patient
from ...db.models.medication import Medication
from ...core.config import settings
from ...core.timeutils import format_local
from ..notifications.service import NotificationService
from ..calls.service import CallService


class ReminderService:
    """Reminder service"""

    # Bounded retry for a reminder whose send/call the provider rejected —
    # enough to ride out a transient outage, few enough that a permanently
    # bad number ends in a visible "failed" instead of retrying forever.
    MAX_SEND_ATTEMPTS = 3
    RETRY_BACKOFF_MINUTES = 2

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
        self.call_service = CallService(db)

    async def create_reminder(
        self,
        patient_id: str,
        reminder_type: str,
        scheduled_at: datetime,
        message: str = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create reminder"""
        reminder = Reminder(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            reminder_type=reminder_type,
            title=message or f"{reminder_type.replace('_', ' ').title()} Reminder",
            description=message,
            schedule_type="one_time",
            scheduled_at=scheduled_at,
            status="scheduled",
            alert_metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(reminder)
        await self.db.commit()

        return {
            "id": str(reminder.id),
            "patient_id": str(reminder.patient_id),
            "reminder_type": reminder.reminder_type,
            "scheduled_at": reminder.scheduled_at.isoformat(),
            "status": reminder.status,
        }

    async def create_medication_reminder(
        self,
        patient_id: str,
        medication_id: str,
        frequency: str,
        start_date: datetime,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """Create recurring medication reminder"""
        reminder = Reminder(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            reminder_type="medication",
            title="Medication Reminder",
            schedule_type="daily",
            medication_id=uuid.UUID(medication_id),
            scheduled_at=start_date,
            ends_at=end_date,
            status="scheduled",
            alert_metadata={
                "frequency": frequency,
            },
            created_at=datetime.utcnow(),
        )
        self.db.add(reminder)
        await self.db.commit()

        return {"id": str(reminder.id)}

    async def send_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """Send reminder immediately"""
        stmt = select(Reminder).filter(Reminder.id == uuid.UUID(reminder_id))
        result = await self.db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            return {"error": "Reminder not found"}

        if reminder.status != "scheduled":
            return {"error": "Reminder already sent/cancelled"}

        patient_stmt = select(Patient).filter(Patient.id == reminder.patient_id)
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        if not patient:
            return {"error": "Patient not found"}

        send_error = None
        if reminder.notification_method == "call":
            # Scheduled check-in call — goes straight to the patient's own
            # phone, no User/email account required (unlike email/SMS
            # reminders below). This is the point: rural patients with no
            # login of their own still get reached, by an actual phone call.
            call_outcome = await self.call_service.create_outbound_call(str(patient.id))
            # The provider's outcome was being discarded here, so a call the
            # provider outright REJECTED (e.g. a non-E164 number — Telnyx
            # error 10016, confirmed live) still marked the reminder "sent"
            # and quietly rolled it to tomorrow. Surface it instead: the
            # scheduler logs this, and the reminder stays "scheduled" so a
            # transient provider failure gets retried on the next poll.
            send_error = (call_outcome or {}).get("error")
        else:
            from ...db.models.user import User
            user_stmt = select(User).filter(User.patient_id == patient.id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if not user:
                return {"error": "No user account linked to this patient"}

            # Send notification. user_id must be the users.id row
            # (Notification's real FK target) — patient.id was being passed
            # here before, which would violate the FK constraint the instant
            # this ran for real, and metadata.phone was never set, so the
            # Telnyx provider would have silently no-op'd ("no phone on
            # record") even past that.
            # Subject was hardcoded "Reminder" and the body was just the raw
            # dosage — which reads "Not specified" whenever the prescription
            # image didn't have a legible dose, i.e. an email saying nothing
            # but "Not specified". Build something a patient can actually act
            # on: what to take, when, and who it's from.
            subject = reminder.title or "Medication reminder"
            body_lines = [
                f"Hello {patient.full_name or 'there'},",
                "",
                f"This is your SETU reminder: {reminder.title or 'take your medication'}.",
            ]
            dose = (reminder.description or "").strip()
            if dose and dose.lower() not in ("not specified", "not specified — not specified"):
                body_lines.append(f"Dose: {dose}")
            body_lines += [
                f"Scheduled for: {format_local(reminder.scheduled_at)}",
                "",
                "If you are feeling unwell, contact your ASHA worker or nearest health centre.",
                "— SETU Care Team",
            ]

            notify_result = await self.notification_service.send_notification(
                str(user.id),
                "patient",
                str(uuid.uuid4()),
                subject,
                "\n".join(body_lines),
                metadata={"phone": patient.phone, "email": user.email},
            )
            if notify_result and notify_result.get("success") is False:
                send_error = notify_result.get("error") or "Notification provider rejected the message"

        if send_error:
            # Retry with a short backoff rather than either (a) silently
            # marking it sent, or (b) leaving scheduled_at in the past, which
            # would make the 30s scheduler hammer the provider forever.
            # Give up after MAX_SEND_ATTEMPTS so a permanently bad number
            # (wrong format, disconnected) ends in an honest "failed" the
            # staff can see, not an infinite quiet retry.
            meta = dict(reminder.alert_metadata or {})
            attempts = int(meta.get("send_attempts", 0)) + 1
            meta["send_attempts"] = attempts
            meta["last_error"] = str(send_error)[:500]
            reminder.alert_metadata = meta

            if attempts >= self.MAX_SEND_ATTEMPTS:
                reminder.status = "failed"
            else:
                reminder.scheduled_at = datetime.utcnow() + timedelta(minutes=self.RETRY_BACKOFF_MINUTES)

            await self.db.commit()
            return {"error": send_error, "reminder_id": reminder_id, "attempts": attempts}

        # A previously-failing reminder that just succeeded starts clean.
        if (reminder.alert_metadata or {}).get("send_attempts"):
            meta = dict(reminder.alert_metadata)
            meta.pop("send_attempts", None)
            meta.pop("last_error", None)
            reminder.alert_metadata = meta

        reminder.sent_at = datetime.utcnow()
        reminder.completed_occurrences = (reminder.completed_occurrences or 0) + 1

        # Daily medication reminders repeat — reschedule for the same time
        # tomorrow instead of terminating after the first send, until the
        # prescription's duration (ends_at) runs out. One-time reminders
        # (or a daily one past its end date) go to a real terminal "sent".
        next_occurrence = reminder.scheduled_at + timedelta(days=1)
        if reminder.schedule_type == "daily" and (reminder.ends_at is None or next_occurrence <= reminder.ends_at):
            reminder.scheduled_at = next_occurrence
            reminder.status = "scheduled"
        else:
            reminder.status = "sent"

        await self.db.commit()

        return {"success": True, "reminder_id": reminder_id}

    async def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """Get a single reminder by id, including its owning patient_id"""
        stmt = select(Reminder).filter(Reminder.id == uuid.UUID(reminder_id))
        result = await self.db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            return None

        return {
            "id": str(reminder.id),
            "patient_id": str(reminder.patient_id),
            "reminder_type": reminder.reminder_type,
            "schedule_type": reminder.schedule_type,
            "scheduled_at": reminder.scheduled_at.isoformat(),
            "status": reminder.status,
            "title": reminder.title,
            "description": reminder.description,
        }

    async def complete_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """Mark reminder as completed"""
        stmt = select(Reminder).filter(Reminder.id == uuid.UUID(reminder_id))
        result = await self.db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            return {"error": "Reminder not found"}

        reminder.status = "completed"
        reminder.completed_occurrences = (reminder.completed_occurrences or 0) + 1
        reminder.alert_metadata = {**(reminder.alert_metadata or {}), "completed_at": datetime.utcnow().isoformat()}
        await self.db.commit()

        return {"success": True, "reminder_id": reminder_id}

    async def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """Cancel reminder"""
        stmt = select(Reminder).filter(Reminder.id == uuid.UUID(reminder_id))
        result = await self.db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            return {"error": "Reminder not found"}

        reminder.status = "cancelled"
        reminder.is_active = False
        reminder.alert_metadata = {**(reminder.alert_metadata or {}), "cancelled_at": datetime.utcnow().isoformat()}
        await self.db.commit()

        return {"success": True, "reminder_id": reminder_id}

    async def reschedule_reminder(self, reminder_id: str, scheduled_at: datetime) -> Dict[str, Any]:
        """Move a reminder to a new time (naive UTC), keeping it daily.

        Re-activates a reminder that had been cancelled or had run out of
        retry attempts — changing the time is an explicit instruction to
        start firing again, so leaving it inactive would silently ignore it.
        """
        stmt = select(Reminder).filter(Reminder.id == uuid.UUID(reminder_id))
        result = await self.db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            return {"error": "Reminder not found"}

        reminder.scheduled_at = scheduled_at
        reminder.status = "scheduled"
        reminder.is_active = True
        reminder.schedule_type = "daily"
        meta = dict(reminder.alert_metadata or {})
        meta.pop("send_attempts", None)
        meta.pop("last_error", None)
        reminder.alert_metadata = meta
        await self.db.commit()

        return {
            "success": True,
            "reminder_id": reminder_id,
            "scheduled_at": scheduled_at.isoformat(),
        }

    async def create_medication_reminder(
        self,
        patient_id: str,
        title: str,
        scheduled_at: datetime,
        description: str = None,
        medication_id: str = None,
    ) -> Dict[str, Any]:
        """Create one extra daily medication reminder at a specific time."""
        now = datetime.utcnow()
        reminder = Reminder(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            reminder_type="medication",
            title=title,
            description=description,
            schedule_type="daily",
            scheduled_at=scheduled_at,
            status="scheduled",
            is_active=True,
            notification_method="sms",
            medication_id=uuid.UUID(medication_id) if medication_id else None,
            created_at=now,
            updated_at=now,
        )
        self.db.add(reminder)
        await self.db.commit()

        return {
            "id": str(reminder.id),
            "title": reminder.title,
            "scheduled_at": reminder.scheduled_at.isoformat(),
            "status": reminder.status,
        }

    async def get_patient_reminders(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get reminders for patient"""
        stmt = (
            select(Reminder)
            .filter(Reminder.patient_id == uuid.UUID(patient_id))
            .order_by(Reminder.scheduled_at)
        )
        result = await self.db.execute(stmt)
        reminders = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "reminder_type": r.reminder_type,
                "schedule_type": r.schedule_type,
                "scheduled_at": r.scheduled_at.isoformat(),
                "status": r.status,
                "title": r.title,
                "description": r.description,
            }
            for r in reminders
        ]
