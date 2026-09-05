from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os

from ...db.models.document import Document
from ...db.models.patient import Patient
from ...core.config import settings
from ...core.security import hash_file


class DocumentService:
    """Document management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(
        self,
        patient_id: str,
        file_path: str,
        file_name: str,
        file_size: int,
        file_type: str,
        upload_by: str,
        document_type: str = "medical_record",
    ) -> Dict[str, Any]:
        """Upload document"""
        # Calculate hash of the file already written to disk
        checksum = hash_file(file_path)

        # Check for duplicates — scoped to THIS patient only. Scoped
        # globally, two different patients uploading byte-identical files
        # (e.g. the same photo re-sent, or two people forwarding the same
        # WhatsApp image) collide: the second patient's upload silently
        # returns the FIRST patient's document row. Confirmed live — patient
        # A's document was handed back to patient B's account, and B's own
        # authorize_patient_access then correctly rejected it as "Not
        # found", making a real upload look like an instant, silent
        # failure. Same content uploaded twice for the SAME patient should
        # still dedupe (that part of the original intent was fine).
        existing_stmt = select(Document).filter(
            Document.checksum == checksum,
            Document.patient_id == uuid.UUID(patient_id),
        )
        existing_result = await self.db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            return existing.to_dict()

        # Create document record
        document = Document(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            document_type=document_type,
            document_name=file_name,
            storage_path=file_path,
            storage_provider="local",
            file_size=file_size,
            file_type=file_type,
            checksum=checksum,
            uploaded_by_id=uuid.UUID(upload_by) if upload_by else None,
            uploaded_at=datetime.utcnow(),
        )
        self.db.add(document)
        await self.db.commit()

        return document.to_dict()

    async def get_patient_documents(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get documents for patient"""
        stmt = (
            select(Document)
            .filter(Document.patient_id == uuid.UUID(patient_id))
            .order_by(Document.created_at.desc())
        )
        result = await self.db.execute(stmt)
        documents = result.scalars().all()

        return [d.to_dict() for d in documents]

    async def process_document(self, document_id: str) -> Dict[str, Any]:
        """Process document for extraction"""
        stmt = select(Document).filter(Document.id == uuid.UUID(document_id))
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return {"error": "Document not found"}

        # In production, trigger extraction service
        # For now, mark as processed
        document.processed = True
        document.processed_at = datetime.utcnow()
        await self.db.commit()

        return {"success": True, "document_id": document_id}

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        stmt = select(Document).filter(Document.id == uuid.UUID(document_id))
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return None

        return document.to_dict(include_full=True)

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete document"""
        stmt = select(Document).filter(Document.id == uuid.UUID(document_id))
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return {"error": "Document not found"}

        await self.db.delete(document)
        await self.db.commit()

        return {"success": True, "document_id": document_id}
