from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    reminder_type = Column(String(50), nullable=False)  # medication, appointment, checkin, follow_up
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    schedule_type = Column(String(50), nullable=False)  # one_time, daily, weekly, monthly
    scheduled_at = Column(DateTime, nullable=False)
    repeats_on = Column(JSON, default=list)  # days of week for weekly
    ends_at = Column(DateTime, nullable=True)
    total_occurrences = Column(Integer, default=1)
    completed_occurrences = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="scheduled")  # scheduled, sent, failed, cancelled
    sent_at = Column(DateTime, nullable=True)
    notification_method = Column(String(50), default="sms")  # sms, call, app
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="reminders")
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=True)
    prescription = relationship("Prescription", uselist=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=True)
    medication = relationship("Medication", back_populates="reminders")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "reminder_type": self.reminder_type,
            "title": self.title,
            "schedule_type": self.schedule_type,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "description": self.description,
                "repeats_on": self.repeats_on,
                "ends_at": self.ends_at.isoformat() if self.ends_at else None,
                "total_occurrences": self.total_occurrences,
                "completed_occurrences": self.completed_occurrences,
                "sent_at": self.sent_at.isoformat() if self.sent_at else None,
                "notification_method": self.notification_method,
                "metadata": self.alert_metadata,
            })
        return result
