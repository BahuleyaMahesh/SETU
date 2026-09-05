from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class IVRSession(Base):
    __tablename__ = "ivr_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    flow_id = Column(String(100), nullable=False)
    current_step = Column(String(50), nullable=False)
    status = Column(String(50), default="active")  # active, completed, failed
    session_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    call = relationship("Call", back_populates="ivr_sessions")
    patient = relationship("Patient", uselist=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "call_id": str(self.call_id),
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "flow_id": self.flow_id,
            "current_step": self.current_step,
            "status": self.status,
            "session_data": self.session_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
