from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=False)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    end_reason = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="assignments")
    asha_worker = relationship("ASHAWorker", back_populates="assignments")
    assigned_by = relationship("User", uselist=False)

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "asha_worker_id": str(self.asha_worker_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "is_active": self.is_active,
        }
        if include_full:
            result.update({
                "ended_at": self.ended_at.isoformat() if self.ended_at else None,
                "end_reason": self.end_reason,
            })
        return result
