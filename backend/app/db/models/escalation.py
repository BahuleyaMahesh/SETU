from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class EscalationStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ESCALATED_FURTHER = "escalated_further"


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    from_role = Column(String(50), nullable=False)  # asha, patient
    to_role = Column(String(50), nullable=False)  # hospital, admin
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, accepted, rejected, escalated_further
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_with = Column(String(50), nullable=True)  # resolved_at_level, escalated_further
    notes = Column(Text, nullable=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alert = relationship("Alert", back_populates="escalations")
    resolved_by = relationship("User", uselist=False)

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "alert_id": str(self.alert_id),
            "from_role": self.from_role,
            "to_role": self.to_role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "reason": self.reason,
                "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
                "resolved_with": self.resolved_with,
                "notes": self.notes,
                "metadata": self.alert_metadata,
            })
        return result
