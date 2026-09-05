from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class CallStatus:
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    call_type = Column(String(50), nullable=False)  # outbound, inbound, ivr
    call_direction = Column(String(20), nullable=False)  # inbound, outbound
    status = Column(String(50), nullable=False)  # queued, ringing, in_progress, completed, failed
    provider_call_id = Column(String(255), unique=True, index=True)
    from_number = Column(String(20))
    to_number = Column(String(20))
    duration = Column(Integer, default=0)  # seconds
    cost = Column(Float, nullable=True)
    recording_url = Column(String(500), nullable=True)
    call_alert_metadata = Column(JSON, default=dict)
    ivr_flow_id = Column(String(100), nullable=True)
    ivr_step = Column(String(50), nullable=True)
    dtmf_input = Column(Text, nullable=True)
    speech_transcript = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="calls")
    asha_worker = relationship("ASHAWorker", uselist=False)
    hospital = relationship("Hospital", uselist=False)
    ivr_sessions = relationship("IVRSession", back_populates="call")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "call_type": self.call_type,
            "call_direction": self.call_direction,
            "status": self.status,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "asha_worker_id": str(self.asha_worker_id) if self.asha_worker_id else None,
                "hospital_id": str(self.hospital_id) if self.hospital_id else None,
                "provider_call_id": self.provider_call_id,
                "from_number": self.from_number,
                "to_number": self.to_number,
                "recording_url": self.recording_url,
                "ivr_flow_id": self.ivr_flow_id,
                "dtmf_input": self.dtmf_input,
                "speech_transcript": self.speech_transcript,
                "error_message": self.error_message,
            })
        return result
