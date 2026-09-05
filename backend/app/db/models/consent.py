from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Consent(Base):
    __tablename__ = "consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    consent_type = Column(String(50), nullable=False)  # data_sharing, telemedicine, medication, research
    granted_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="consents")
    granted_by = relationship("User", foreign_keys=[granted_by_id], uselist=False)
    revoked_by = relationship("User", foreign_keys=[revoked_by_id], uselist=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "consent_type": self.consent_type,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
