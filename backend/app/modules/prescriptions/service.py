from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid

from ...db.models.prescription import Prescription, PrescriptionStatus
from ...db.models.medication import Medication
from ...db.models.patient import Patient
from ...db.models.document import Document
from ...core.config import settings
from ..extraction.service import ExtractionService
from .providers.vision import GeminiVisionProvider


class PrescriptionService:
    """Prescription management service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.extraction_service = ExtractionService(db)
        self.vision_provider = GeminiVisionProvider()

    async def create_prescription(
        self,
        patient_id: str,
        doctor_id: str,
        medications: List[Dict[str, Any]],
        notes: str = None,
        status: str = "pending",
    ) -> Dict[str, Any]:
        """Create new prescription"""
        prescription = Prescription(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            prescribed_by_id=uuid.UUID(doctor_id) if doctor_id else None,
            status=status,
            verification_notes=notes,
            created_at=datetime.utcnow(),
        )
        self.db.add(prescription)
        await self.db.flush()

        # Create medications
        medication_records = []
        for med in medications:
            medication = Medication(
                id=uuid.uuid4(),
                prescription_id=prescription.id,
                patient_id=uuid.UUID(patient_id),
                medication_name=med.get("name"),
                dosage=med.get("dosage"),
                frequency=med.get("frequency"),
                timing=med.get("timing"),
                duration=med.get("duration"),
                instructions=med.get("instructions"),
            )
            medication_records.append(medication)
            self.db.add(medication)

        await self.db.commit()

        return {
            "id": str(prescription.id),
            "status": prescription.status,
            "medications": medications,
        }

    async def get_patient_prescriptions(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get prescriptions for patient"""
        stmt = (
            select(Prescription)
            .options(selectinload(Prescription.medications))
            .filter(Prescription.patient_id == uuid.UUID(patient_id))
            .order_by(Prescription.created_at.desc())
        )
        result = await self.db.execute(stmt)
        prescriptions = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "status": p.status,
                "notes": p.verification_notes,
                "created_at": p.created_at.isoformat(),
                "medications": [
                    {
                        "name": m.medication_name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                    }
                    for m in p.medications or []
                ],
            }
            for p in prescriptions
        ]

    async def get_prescription(self, prescription_id: str) -> Optional[Dict[str, Any]]:
        """Get prescription by ID"""
        stmt = select(Prescription).filter(Prescription.id == uuid.UUID(prescription_id))
        result = await self.db.execute(stmt)
        prescription = result.scalar_one_or_none()

        if not prescription:
            return None

        return {
            "id": str(prescription.id),
            "patient_id": str(prescription.patient_id),
            "status": prescription.status,
            "notes": prescription.verification_notes,
            "created_at": prescription.created_at.isoformat(),
        }

    async def verify_prescription(self, prescription_id: str, verified_by: str) -> Dict[str, Any]:
        """Verify prescription"""
        stmt = select(Prescription).filter(Prescription.id == uuid.UUID(prescription_id))
        result = await self.db.execute(stmt)
        prescription = result.scalar_one_or_none()

        if not prescription:
            return {"error": "Prescription not found"}

        prescription.status = "verified"
        prescription.verified_by_id = uuid.UUID(verified_by)
        prescription.verified_at = datetime.utcnow()
        await self.db.commit()

        return {"success": True, "prescription_id": prescription_id}

    async def create_from_document(
        self,
        document_id: str,
        verified_by: str = None,
    ) -> Dict[str, Any]:
        """Create prescription from an uploaded document (image or text)."""
        doc_stmt = select(Document).filter(Document.id == uuid.UUID(document_id))
        doc_result = await self.db.execute(doc_stmt)
        document = doc_result.scalar_one_or_none()

        if not document:
            return {"error": "Document not found"}

        medications = []
        is_image = (document.file_type or "").startswith("image/")

        if is_image and self.vision_provider.available():
            vision_result = await self.vision_provider.extract_from_image(document.storage_path)
            medications = vision_result.get("medications", [])
        elif document.extraction_result and document.extraction_result.get("text"):
            extracted = await self.extraction_service.extract_prescription(
                document.extraction_result["text"]
            )
            medications = extracted.get("medications", [])

        if medications:
            document.extraction_result = {**(document.extraction_result or {}), "medications": medications}
            document.processed = True
            await self.db.commit()

            return await self.create_prescription(
                patient_id=str(document.patient_id),
                doctor_id=verified_by,
                medications=medications,
                notes="Extracted from document",
                status="verified" if verified_by else "pending",
            )

        return {"error": "No medications extracted from document"}

    async def get_medication(self, medication_id: str) -> Optional[Dict[str, Any]]:
        """Get medication by ID"""
        stmt = select(Medication).filter(Medication.id == uuid.UUID(medication_id))
        result = await self.db.execute(stmt)
        medication = result.scalar_one_or_none()

        if not medication:
            return None

        return {
            "id": str(medication.id),
            "name": medication.medication_name,
            "dosage": medication.dosage,
            "frequency": medication.frequency,
            "timing": medication.timing,
            "duration": medication.duration,
        }
