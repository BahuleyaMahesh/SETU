from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid

from ...db.models.prescription import Prescription, PrescriptionStatus
from ...db.models.medication import Medication
from ...db.models.patient import Patient
from ...db.models.document import Document
from ...db.models.reminder import Reminder
from ...core.config import settings
from ..extraction.service import ExtractionService
from ..reminders.frequency import parse_frequency_to_times
from ...core.timeutils import next_local_time_as_utc
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

        # Create medications. dosage/frequency are NOT NULL columns, but a
        # handwritten prescription can have a clearly legible drug name with
        # an illegible dosage/frequency — default those instead of losing
        # the whole medication (or the whole prescription, since one bad
        # insert would otherwise abort the transaction for every entry).
        medication_records = []
        for med in medications:
            name = (med.get("name") or "").strip()
            if not name:
                continue
            medication = Medication(
                id=uuid.uuid4(),
                prescription_id=prescription.id,
                patient_id=uuid.UUID(patient_id),
                medication_name=name,
                dosage=(med.get("dosage") or "Not specified"),
                frequency=(med.get("frequency") or "Not specified"),
                timing=med.get("timing"),
                duration=med.get("duration"),
                instructions=med.get("instructions"),
            )
            medication_records.append(medication)
            self.db.add(medication)

        await self.db.flush()

        # Auto-create medication reminders from each medication's frequency
        # (e.g. "twice daily", "1-0-1") — one reminder per time-of-day slot,
        # repeating daily for the prescription's duration (or indefinitely
        # if duration wasn't read). This is the same NotificationProvider
        # pipeline (send_reminder) as every other reminder, just scheduled
        # automatically instead of created by hand.
        now = datetime.utcnow()
        for medication in medication_records:
            if (medication.dosage or "").strip().lower() == "not specified" and \
               (medication.frequency or "").strip().lower() == "not specified":
                continue  # nothing legible enough to schedule against

            times = parse_frequency_to_times(medication.frequency)
            ends_at = now + timedelta(days=medication.duration) if medication.duration else None

            for slot_time in times:
                # frequency.py's MORNING/AFTERNOON/EVENING/NIGHT are LOCAL
                # wall-clock times ("take it at 8 in the morning"), but every
                # timestamp here is naive UTC. Writing 08:00 straight onto a
                # utcnow() base stored it as 08:00 UTC = 1:30 PM IST, and the
                # 21:00 night dose would have alerted at 2:30 AM.
                scheduled_at = next_local_time_as_utc(slot_time, now)

                reminder = Reminder(
                    id=uuid.uuid4(),
                    patient_id=uuid.UUID(patient_id),
                    reminder_type="medication",
                    title=f"Take {medication.medication_name}",
                    description=(
                        f"{medication.dosage} — {medication.instructions}"
                        if medication.instructions else medication.dosage
                    ),
                    schedule_type="daily",
                    scheduled_at=scheduled_at,
                    ends_at=ends_at,
                    status="scheduled",
                    notification_method="sms",
                    medication_id=medication.id,
                    prescription_id=prescription.id,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(reminder)

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
        vision_error = None

        if is_image:
            if not self.vision_provider.available():
                return {
                    "error": "AI prescription reading isn't configured on this server "
                    "yet (missing Gemini API key). Your image was saved, but medications "
                    "couldn't be read automatically — please add them manually for now."
                }
            vision_result = await self.vision_provider.extract_from_image(document.storage_path)
            medications = vision_result.get("medications", [])
            vision_error = vision_result.get("error")
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

        if vision_error == "unparseable_response":
            return {"error": "The AI reader had trouble with this image. Please try again, or use a clearer, better-lit photo."}
        return {
            "error": "No medications could be read from this image. Make sure the "
            "prescription text is in focus, well-lit, and right-side up, then try again."
        }

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
