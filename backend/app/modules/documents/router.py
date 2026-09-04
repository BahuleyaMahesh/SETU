import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import DocumentService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    patient_id: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload document for patient"""
    target_patient_id = patient_id or (str(user.patient_id) if user.patient_id else None)
    if not target_patient_id:
        raise HTTPException(status_code=400, detail="patient_id required")
    await authorize_patient_access(target_patient_id, user, db)

    # Save file under a unique name so two uploads sharing an original
    # filename (e.g. both named "prescription.jpg") never collide on disk —
    # the original name is preserved separately as document_name.
    os.makedirs("uploads", exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    file_path = f"uploads/{uuid.uuid4().hex}{ext}"
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    service = DocumentService(db)
    return await service.upload_document(
        patient_id=target_patient_id,
        file_path=file_path,
        file_name=file.filename,
        file_size=len(contents),
        file_type=file.content_type,
        upload_by=str(user.id),
    )


@router.get("/patient/{patient_id}", response_model=list[dict])
async def get_patient_documents(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get documents for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = DocumentService(db)
    return await service.get_patient_documents(patient_id)


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get document by ID"""
    service = DocumentService(db)
    result = await service.get_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    await authorize_patient_access(result["patient_id"], user, db)
    return result


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete document"""
    service = DocumentService(db)
    existing = await service.get_document(document_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")
    await authorize_patient_access(existing["patient_id"], user, db)
    if user.role not in ("hospital", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    result = await service.delete_document(document_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/process/{document_id}")
async def process_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Process document for extraction"""
    service = DocumentService(db)
    existing = await service.get_document(document_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")
    await authorize_patient_access(existing["patient_id"], user, db)

    result = await service.process_document(document_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
