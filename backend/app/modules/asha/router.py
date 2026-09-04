from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import ASHAService
from ...core.security import get_current_user, require_asha, require_hospital, require_admin
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/asha", tags=["asha"])


@router.get("/", response_model=list[dict])
async def get_ashas(
    district: str = None,
    block: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get ASHA workers"""
    service = ASHAService(db)
    return await service.get_ashas(
        district=district,
        block=block,
        limit=limit,
        offset=offset,
    )


@router.get("/{asha_id}")
async def get_asha(
    asha_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get ASHA worker by ID"""
    if user.role == "asha" and str(getattr(user, "asha_worker_id", None)) != asha_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASHA not found")
    service = ASHAService(db)
    result = await service.get_asha(asha_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ASHA not found")
    return result


@router.get("/{asha_id}/patients", response_model=list[dict])
async def get_asha_patients(
    asha_id: str,
    risk_level: str = None,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get patients for ASHA"""
    if user.role == "asha" and str(getattr(user, "asha_worker_id", None)) != asha_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    elif user.role == "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    service = ASHAService(db)
    hospital_id = str(user.hospital_id) if user.role == "hospital" else None
    return await service.get_asha_patients(asha_id, risk_level, search, hospital_id=hospital_id)


@router.get("/{asha_id}/caseload")
async def get_asha_caseload(
    asha_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get ASHA caseload summary"""
    if user.role == "asha" and str(getattr(user, "asha_worker_id", None)) != asha_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    elif user.role == "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    service = ASHAService(db)
    hospital_id = str(user.hospital_id) if user.role == "hospital" else None
    return await service.get_asha_caseload(asha_id, hospital_id=hospital_id)
