from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    report_type = Column(String(50), nullable=False)  # patient, hospital, alert, follow_up, analytics
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(JSON, default=dict)
    status = Column(String(50), default="generated")  # draft, generated, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    hospital = relationship("Hospital", back_populates="reports")
    patient = relationship("Patient", uselist=False)
    asha_worker = relationship("ASHAWorker", uselist=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "hospital_id": str(self.hospital_id) if self.hospital_id else None,
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "report_type": self.report_type,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
