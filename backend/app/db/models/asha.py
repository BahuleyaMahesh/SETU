from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class ASHAWorker(Base):
    __tablename__ = "asha_workers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    asha_id = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    district = Column(String(100), nullable=False)
    block = Column(String(100), nullable=True)
    phc_id = Column(String(50), nullable=True)
    assigned_villages = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="asha_worker", uselist=False)
    assigned_patients = relationship("Patient", back_populates="assigned_asha")
    assignments = relationship("Assignment", back_populates="asha_worker")
    alerts = relationship("Alert", back_populates="asha_worker")

    def to_dict(self, include_sensitive: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "name": self.name,
            "asha_id": self.asha_id,
            "district": self.district,
            "block": self.block,
            "phc_id": self.phc_id,
            "assigned_villages": self.assigned_villages,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            result["phone"] = self.phone
        return result
