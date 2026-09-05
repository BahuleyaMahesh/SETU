from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ...core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, index=True)
    role = Column(String(50), nullable=False)  # patient, asha, hospital, admin
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)

    # Relationships
    hospital = relationship("Hospital", back_populates="users")
    asha_worker = relationship("ASHAWorker", uselist=False)
    patient = relationship("Patient", uselist=False)
    notifications = relationship("Notification", back_populates="user")

    def to_dict(self, include_sensitive: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            result["last_login"] = self.last_login.isoformat() if self.last_login else None
        return result
