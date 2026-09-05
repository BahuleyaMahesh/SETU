from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Date, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mrn = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20))
    phone = Column(String(20))
    alternate_phone = Column(String(20))
    address = Column(Text)
    village = Column(String(100))
    district = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    latitude = Column(Float)
    longitude = Column(Float)
    risk_level = Column(String(20), default="normal")  # normal, warning, critical
    last_check_in_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    assigned_asha_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)

    # Relationships
    hospital = relationship("Hospital", back_populates="patients")
    assigned_asha = relationship("ASHAWorker", back_populates="assigned_patients")
    assignments = relationship("Assignment", back_populates="patient")
    calls = relationship("Call", back_populates="patient")
    checkins = relationship("Checkin", back_populates="patient")
    responses = relationship("Response", back_populates="patient")
    risk_history = relationship("RiskRecord", back_populates="patient")
    alerts = relationship("Alert", back_populates="patient")
    reminders = relationship("Reminder", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    documents = relationship("Document", back_populates="patient")
    chat_messages = relationship("ChatMessage", back_populates="patient")
    consents = relationship("Consent", back_populates="patient")

    def to_dict(self, include_sensitive: bool = False, include_location: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "mrn": self.mrn,
            "full_name": self.full_name,
            "gender": self.gender,
            "phone": self.phone,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            result.update({
                "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
                "alternate_phone": self.alternate_phone,
                "village": self.village,
                "district": self.district,
                "state": self.state,
                "pincode": self.pincode,
            })
        if include_location:
            result.update({
                "latitude": self.latitude,
                "longitude": self.longitude,
            })
        return result
