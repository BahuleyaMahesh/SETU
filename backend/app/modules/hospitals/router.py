from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.security import get_current_user
from ...db.models.user import User
from ...shared.schemas import HospitalResponse
from .service import get_hospital_service, HospitalService

router = APIRouter(prefix="/api/v1/hospitals", tags=["hospitals"])


@router.get("", response_model=List[HospitalResponse])
async def list_hospitals(
    current_user: User = Depends(get_current_user),
    service: HospitalService = Depends(get_hospital_service),
):
    """List hospitals"""

    if current_user.role not in ["admin", "hospital"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    hospitals = await service.search_hospitals(limit=100)
    return [h.to_dict() for h in hospitals]


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    service: HospitalService = Depends(get_hospital_service),
):
    """Get a hospital by ID"""
    hospital = await service.get_hospital(hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found",
        )

    return hospital.to_dict()


@router.get("/{hospital_id}/patients")
async def get_hospital_patients(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get patients at a hospital"""

    if current_user.role == "hospital" and str(current_user.hospital_id) != hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    from ..patients.service import PatientService

    patient_service = PatientService(db)
    return await patient_service.get_patients_by_hospital(hospital_id)


@router.get("/{hospital_id}/summary")
async def get_hospital_summary(
    hospital_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get hospital summary"""

    if current_user.role == "hospital" and str(current_user.hospital_id) != hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    from ..analytics.service import AnalyticsService

    analytics_service = AnalyticsService(db)
    distribution = await analytics_service.get_patient_risk_distribution(hospital_id)

    return {
        "total_patients": distribution["total"],
        "by_risk": {
            "normal": distribution["normal"],
            "warning": distribution["warning"],
            "critical": distribution["critical"],
        },
    }
