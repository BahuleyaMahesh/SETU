from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from ...core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # prescription, medical_record, report, consent
    document_name = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # S3 path or local path
    storage_provider = Column(String(50), default="local")  # local, s3, gcs
    file_size = Column(Integer, nullable=True)  # bytes
    file_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA256
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    extraction_result = Column(JSON, nullable=True)
    alert_metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="documents")
    uploaded_by = relationship("User", uselist=False)
    prescription = relationship("Prescription", back_populates="document")

    def to_dict(self, include_full: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "document_type": self.document_type,
            "document_name": self.document_name,
            "file_type": self.file_type,
            "processed": self.processed,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
        if include_full:
            result.update({
                "storage_path": self.storage_path,
                "storage_provider": self.storage_provider,
                "file_size": self.file_size,
                "checksum": self.checksum,
                "extraction_result": self.extraction_result,
                "metadata": self.alert_metadata,
            })
        return result
