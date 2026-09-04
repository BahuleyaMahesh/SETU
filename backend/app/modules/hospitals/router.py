from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ...core.security import get_current_user
from ...db.models.user import User
from ...shared.schemas import HospitalResponse
from ..hospitals.service import get_hospital_service

router = APIRouter(prefix="/api/v1/hospitals", tags=["hospitals"])


@router.get("", response_model=List[HospitalResponse])
async def list_hospitals(
    current_user: User = Depends(get_current_user),
    service=Depends(get_hospital_service),
):
    """List hospitals"""

    if current_user.role not in ["admin", "hospital"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    hospitals = await service.search_hospitals(search_term="", limit=100)
    return hospitals


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_hospital_service),
):
    """Get a hospital by ID"""
    hospital = await service.get_hospital(hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found",
        )

    return hospital


@router.get("/{hospital_id}/patients")
async def get_hospital_patients(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_hospital_service),
):
    """Get patients at a hospital"""

    if current_user.role == "hospital" and str(current_user.hospital_id) != hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    from ..patients.service import get_patient_service
    patient_service = get_patient_service(None)

    patients = await patient_service.get_patients_by_hospital(hospital_id)
    return [p.to_dict() for p in patients]


@router.get("/{hospital_id}/summary")
async def get_hospital_summary(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    service=Depends(get_hospital_service),
):
    """Get hospital summary"""

    if current_user.role == "hospital" and str(current_user.hospital_id) != hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    from ..patients.service import get_patient_service
    patient_service = get_patient_service(None)

    patients_by_risk = await patient_service.get_patients_by_hospital_and_risk(hospital_id)

    return {
        "total_patients": sum(len(p) for p in patients_by_risk.values()),
        "by_risk": {k: len(v) for k, v in patients_by_risk.items()},
    }
