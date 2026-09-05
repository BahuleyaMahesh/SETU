from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Vector embedding stored as JSON array
    token_count = Column(Integer, nullable=True)
    chunk_alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("RAGDocument", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk'),
    )

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_full:
            result.update({
                "content": self.content,
                "embedding": self.embedding,
                "chunk_metadata": self.chunk_metadata,
            })
        return result
