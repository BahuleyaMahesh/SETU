from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import AnalyticsService
from ...core.security import get_current_user, require_hospital, require_admin
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/risk")
async def get_risk_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get risk level distribution analytics"""
    service = AnalyticsService(db)
    return await service.get_risk_analytics(
        hospital_id=str(user.hospital_id) if user.role == "hospital" else None
    )


@router.get("/checkins")
async def get_checkin_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get check-in analytics"""
    service = AnalyticsService(db)
    return await service.get_checkin_analytics(
        hospital_id=str(user.hospital_id) if user.role == "hospital" else None
    )


@router.get("/alerts")
async def get_alert_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get alert analytics"""
    service = AnalyticsService(db)
    return await service.get_alert_analytics(
        hospital_id=str(user.hospital_id) if user.role == "hospital" else None
    )


@router.get("/asha-workload", response_model=list[dict])
async def get_asha_workload(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get ASHA workload metrics"""
    service = AnalyticsService(db)
    return await service.get_asha_workload()


@router.get("/trends")
async def get_trends(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get trend data"""
    service = AnalyticsService(db)
    return await service.get_trends(
        hospital_id=str(user.hospital_id) if user.role == "hospital" else None,
        days=days,
    )
