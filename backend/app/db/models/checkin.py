from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class CheckInMethod:
    PHONE = "phone"
    IN_PERSON = "in_person"
    IVR = "ivr"
    APP = "app"


class CheckInInputType:
    SPEECH = "speech"
    TEXT = "text"
    IVR_DTMF = "ivr_dtmf"


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    method = Column(String(50), nullable=False)  # phone, in_person, ivr, app
    input_type = Column(String(50), nullable=False)  # speech, text, ivr_dtmf
    raw_input = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String(50), default="completed")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="checkins")
    asha_worker = relationship("ASHAWorker", uselist=False)
    hospital = relationship("Hospital", uselist=False)
    responses = relationship("Response", back_populates="checkin")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "method": self.method,
            "input_type": self.input_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "ashas_worker_id": str(self.asha_worker_id) if self.asha_worker_id else None,
                "hospital_id": str(self.hospital_id) if self.hospital_id else None,
                "raw_input": self.raw_input,
                "transcript": self.transcript,
                "latitude": self.latitude,
                "longitude": self.longitude,
            })
        return result
