from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    medication_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)  # once_daily, twice_daily, every_6h, etc.
    timing = Column(String(100), nullable=True)  # morning, afternoon, evening, bedtime
    duration = Column(Integer, nullable=True)  # days
    duration_unit = Column(String(20), default="days")
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prescription = relationship("Prescription", back_populates="medications")
    patient = relationship("Patient", uselist=False)
    reminders = relationship("Reminder", back_populates="medication")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "prescription_id": str(self.prescription_id),
            "patient_id": str(self.patient_id),
            "medication_name": self.medication_name,
            "generic_name": self.generic_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat() if self.start_date else None,
        }
        if include_full:
            result.update({
                "timing": self.timing,
                "duration": self.duration,
                "duration_unit": self.duration_unit,
                "instructions": self.instructions,
                "end_date": self.end_date.isoformat() if self.end_date else None,
            })
        return result
