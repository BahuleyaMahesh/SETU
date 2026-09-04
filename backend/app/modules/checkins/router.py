from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import CheckinService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/checkins", tags=["checkins"])


from .schemas import CheckinCreateRequest


@router.post("", response_model=dict)
@router.post("/", response_model=dict)
async def create_checkin(
    request: CheckinCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create check-in for patient"""
    service = CheckinService(db)
    target_patient_id = request.patient_id or (str(user.patient_id) if getattr(user, "patient_id", None) else None)
    if not target_patient_id:
        # If user doesn't have a linked patient_id directly on User object, check Patient model by user.id
        from ...db.models.patient import Patient
        from sqlalchemy import select
        stmt = select(Patient.id).where(Patient.id == user.id)
        res = await db.execute(stmt)
        p_id = res.scalar_one_or_none()
        if p_id:
            target_patient_id = str(p_id)
        else:
            # Fallback to first available patient for demo/testing
            stmt = select(Patient.id)
            res = await db.execute(stmt)
            p_id = res.scalars().first()
            if p_id:
                target_patient_id = str(p_id)

    if not target_patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient ID required")

    return await service.create_checkin(
        patient_id=target_patient_id,
        method=request.method,
        input_type=request.input_type,
        responses=request.responses,
    )


@router.get("/{checkin_id}")
async def get_checkin(
    checkin_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get check-in by ID"""
    service = CheckinService(db)
    result = await service.get_checkin(checkin_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found")
    await authorize_patient_access(result["patient_id"], user, db)
    return result


@router.get("/patient/{patient_id}/checkins", response_model=list[dict])
async def get_patient_checkins(
    patient_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get check-ins for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = CheckinService(db)
    return await service.get_patient_checkins(patient_id, limit, offset)
