from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import PrescriptionService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/prescriptions", tags=["prescriptions"])


@router.post("/", response_model=dict)
async def create_prescription(
    patient_id: str,
    medications: list[dict],
    notes: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new prescription"""
    if user.role not in ("hospital", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    await authorize_patient_access(patient_id, user, db)
    service = PrescriptionService(db)
    return await service.create_prescription(
        patient_id=patient_id,
        doctor_id=str(user.id),
        medications=medications,
        notes=notes,
    )


@router.get("/patient/{patient_id}", response_model=list[dict])
async def get_patient_prescriptions(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get prescriptions for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = PrescriptionService(db)
    return await service.get_patient_prescriptions(patient_id)


@router.get("/{prescription_id}")
async def get_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get prescription by ID"""
    service = PrescriptionService(db)
    result = await service.get_prescription(prescription_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prescription not found")
    await authorize_patient_access(result["patient_id"], user, db)
    return result


@router.post("/from-document/{document_id}", response_model=dict)
async def create_from_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a prescription by reading an uploaded document (photo or text).

    A patient can trigger this for their own uploads (self-service scan), or
    hospital/admin/asha staff can trigger it for a patient they're
    authorized to see — either way ownership is checked, not just role.
    """
    from ...modules.documents.service import DocumentService

    doc_service = DocumentService(db)
    document = await doc_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    await authorize_patient_access(document["patient_id"], user, db)

    service = PrescriptionService(db)
    result = await service.create_from_document(
        document_id,
        verified_by=str(user.id) if user.role in ("hospital", "admin") else None,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.patch("/verify/{prescription_id}")
async def verify_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Verify prescription"""
    service = PrescriptionService(db)
    result = await service.verify_prescription(prescription_id, str(user.id))
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/medications/{medication_id}")
async def get_medication(
    medication_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get medication by ID"""
    service = PrescriptionService(db)
    result = await service.get_medication(medication_id)
    if not result:
        raise HTTPException(status_code=404, detail="Medication not found")
    return result
