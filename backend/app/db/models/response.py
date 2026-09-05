from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Response(Base):
    __tablename__ = "responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkin_id = Column(UUID(as_uuid=True), ForeignKey("checkins.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    question = Column(String(255), nullable=False)
    answer = Column(Text, nullable=True)
    answer_type = Column(String(50), nullable=False)  # text, number, date, choice, multi_select
    answer_value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    extracted_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    checkin = relationship("Checkin", back_populates="responses")
    patient = relationship("Patient", back_populates="responses")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "checkin_id": str(self.checkin_id),
            "patient_id": str(self.patient_id),
            "question": self.question,
            "answer": self.answer,
            "answer_type": self.answer_type,
            "answer_value": self.answer_value,
            "confidence": self.confidence,
            "extracted_metadata": self.extracted_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
