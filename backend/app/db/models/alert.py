from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class AlertStatus:
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    risk_record_id = Column(UUID(as_uuid=True), ForeignKey("risk_history.id"), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    risk_level = Column(String(20), nullable=False)  # normal, warning, critical
    alert_type = Column(String(50), nullable=False)  # checkin_risk, symptom_alert, escalation
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="new")  # new, acknowledged, in_progress, resolved, escalated
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    escalated_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="alerts")
    risk_record = relationship("RiskRecord", back_populates="alerts")
    hospital = relationship("Hospital", back_populates="alerts")
    asha_worker = relationship("ASHAWorker", back_populates="alerts")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id], uselist=False)
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], uselist=False)
    escalated_to = relationship("User", foreign_keys=[escalated_to_id], uselist=False)
    escalations = relationship("Escalation", back_populates="alert")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "severity": self.severity,
            "risk_level": self.risk_level,
            "alert_type": self.alert_type,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "risk_record_id": str(self.risk_record_id) if self.risk_record_id else None,
                "hospital_id": str(self.hospital_id) if self.hospital_id else None,
                "asha_worker_id": str(self.asha_worker_id) if self.asha_worker_id else None,
                "description": self.description,
                "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
                "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
                "resolution_notes": self.resolution_notes,
                "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
                "metadata": self.alert_metadata,
            })
        return result
