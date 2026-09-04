from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.reminder import Reminder
from ...db.models.patient import Patient
from ...db.models.medication import Medication
from ...core.config import settings
from ..notifications.service import NotificationService
from ..calls.service import CallService


class ReminderService:
    """Reminder service"""

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

        # Send notification
        await self.notification_service.send_notification(
            str(reminder.patient_id),
            "patient",
            str(uuid.uuid4()),
            "Reminder",
            reminder.description or reminder.title or "Time for your medication",
        )

        reminder.status = "sent"
        reminder.sent_at = datetime.utcnow()
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
