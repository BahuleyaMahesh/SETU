from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False)  # CHC, PHC, District, Private, etc.
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10))
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="hospital")
    patients = relationship("Patient", back_populates="hospital")
    alerts = relationship("Alert", back_populates="hospital")
    reports = relationship("Report", back_populates="hospital")

    def to_dict(self, include_sensitive: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "name": self.name,
            "code": self.code,
            "type": self.type,
            "district": self.district,
            "state": self.state,
            "pincode": self.pincode,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            result.update({
                "address": self.address,
                "contact_phone": self.contact_phone,
                "contact_email": self.contact_email,
                "latitude": self.latitude,
                "longitude": self.longitude,
            })
        return result
