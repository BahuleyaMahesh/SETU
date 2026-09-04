from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import ReportService
from ...core.security import get_current_user, require_hospital, require_admin, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/patient/{patient_id}", response_model=dict)
async def get_patient_report(
    patient_id: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate patient report"""
    await authorize_patient_access(patient_id, user, db)
    service = ReportService(db)
    return await service.get_patient_report(patient_id, days)


@router.get("/hospital", response_model=dict)
async def get_hospital_report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate hospital report"""
    service = ReportService(db)
    return await service.get_hospital_report(str(user.hospital_id))


@router.get("/alerts", response_model=dict)
async def get_alert_report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate alert report"""
    service = ReportService(db)
    return await service.get_alert_report(str(user.hospital_id))


@router.get("/follow-up", response_model=dict)
async def get_follow_up_report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate follow-up report"""
    service = ReportService(db)
    return await service.get_follow_up_report(str(user.hospital_id))
