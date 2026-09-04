from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class PrescriptionStatus:
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    prescribed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    prescription_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="unverified")  # unverified, verified, rejected
    verified_at = Column(DateTime, nullable=True)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verification_notes = Column(Text, nullable=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    document = relationship("Document", back_populates="prescription")
    hospital = relationship("Hospital", uselist=False)
    prescribed_by = relationship("User", foreign_keys=[prescribed_by_id], uselist=False)
    verified_by = relationship("User", foreign_keys=[verified_by_id], uselist=False)
    medications = relationship("Medication", back_populates="prescription", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="prescription")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "status": self.status,
            "prescription_date": self.prescription_date.isoformat() if self.prescription_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "document_id": str(self.document_id) if self.document_id else None,
                "hospital_id": str(self.hospital_id) if self.hospital_id else None,
                "verified_at": self.verified_at.isoformat() if self.verified_at else None,
                "verification_notes": self.verification_notes,
                "metadata": self.alert_metadata,
            })
        return result
