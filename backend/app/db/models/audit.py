from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ...core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_role = Column(String(50), nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_role": self.user_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
