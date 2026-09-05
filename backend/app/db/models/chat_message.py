from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sender_type = Column(String(50), nullable=False)  # patient, asha, hospital, system, ai
    message_type = Column(String(50), nullable=False)  # text, image, tool_call, tool_result
    content = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    alert_metadata = Column(JSON, default=dict)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)

    # Relationships
    sender = relationship("User", uselist=False)
    patient = relationship("Patient", back_populates="chat_messages")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "sender_id": str(self.sender_id),
            "sender_type": self.sender_type,
            "message_type": self.message_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "tool_name": self.tool_name,
                "tool_input": self.tool_input,
                "tool_output": self.tool_output,
                "confidence": self.confidence,
                "metadata": self.alert_metadata,
            })
        return result
