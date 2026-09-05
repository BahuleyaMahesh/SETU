from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class RiskRecord(Base):
    __tablename__ = "risk_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    checkin_id = Column(UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=True)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)
    risk_level = Column(String(20), nullable=False)  # normal, warning, critical
    risk_score = Column(Float, nullable=True)
    risk_factors = Column(JSON, default=list)
    risk_reasons = Column(JSON, default=list)
    severity = Column(Integer, nullable=False, default=0)
    action_required = Column(String(100), nullable=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="risk_history")
    checkin = relationship("Checkin", uselist=False)
    asha_worker = relationship("ASHAWorker", uselist=False)
    alerts = relationship("Alert", back_populates="risk_record")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "checkin_id": str(self.checkin_id) if self.checkin_id else None,
                "asha_worker_id": str(self.asha_worker_id) if self.asha_worker_id else None,
                "risk_factors": self.risk_factors,
                "risk_reasons": self.risk_reasons,
                "action_required": self.action_required,
                "metadata": self.alert_metadata,
            })
        return result
