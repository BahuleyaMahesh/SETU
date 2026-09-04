from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from ...core.security import get_current_user, authorize_patient_access
from ...core.dependencies import get_db
from ...db.models.user import User
from ...shared.schemas import PatientCreate, PatientUpdate, PatientResponse
from ..patients.service import get_patient_service

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


@router.post("", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_patient_service),
):
    """Create a new patient"""
    if current_user.role not in ["hospital", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospitals can create patients",
        )

    hospital_id = current_user.hospital_id if current_user.role == "hospital" else None
    if not hospital_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital ID required",
        )

    patient = await service.create_patient(
        hospital_id=str(hospital_id),
        patient_data=patient_data,
        user_id=str(current_user.id),
    )
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_patient_service),
):
    """Get a patient by ID"""
    await authorize_patient_access(patient_id, current_user, service.db)

    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: PatientUpdate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_patient_service),
):
    """Update a patient"""
    if current_user.role not in ("hospital", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    await authorize_patient_access(patient_id, current_user, service.db)

    update_fields = patient_data.model_dump(exclude_unset=True)
    updated = await service.update_patient(patient_id, **update_fields)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return updated


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    risk_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service=Depends(get_patient_service),
):
    """List patients"""
    if current_user.role == "hospital":
        patients = await service.get_patients_by_hospital(
            hospital_id=str(current_user.hospital_id),
            risk_filter=risk_level,
        )
    elif current_user.role == "asha":
        patients = await service.get_patients_by_asha(str(current_user.asha_worker_id))
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return patients
