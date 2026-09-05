from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(50), nullable=False)  # medline_plus, icmr, mohfw
    source_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(500), nullable=True)
    published_date = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "source_type": self.source_type,
            "source_id": self.source_id,
            "title": self.title,
            "source_url": self.source_url,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }
        if include_full:
            result.update({
                "content": self.content,
                "metadata": self.alert_metadata,
            })
        return result
