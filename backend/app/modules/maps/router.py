from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import MapsService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/maps", tags=["maps"])


@router.get("/asha/patients")
async def get_asha_patients_map(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get patient locations for ASHA map"""
    service = MapsService(db)
    return await service.get_asha_patients_location(str(user.asha_worker_id))


@router.get("/hospital/patients")
async def get_hospital_patients_map(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get patient locations for hospital map"""
    service = MapsService(db)
    return await service.get_hospital_patients_location(str(user.hospital_id))


@router.get("/nearby-hospitals/{patient_id}")
async def get_nearby_hospitals(
    patient_id: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get hospitals nearest to a patient, ranked by distance"""
    await authorize_patient_access(patient_id, user, db)
    service = MapsService(db)
    result = await service.get_nearby_hospitals(patient_id, limit=limit)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/geocode")
async def geocode_address(
    q: str,
    user: User = Depends(get_current_user),
):
    """Look up coordinates for a free-text address (for pinning a new patient location)"""
    service = MapsService(None)
    return await service.geocode_address(q)


@router.get("/emergency/{patient_id}")
async def get_emergency_response(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get emergency response information"""
    await authorize_patient_access(patient_id, user, db)
    service = MapsService(db)
    return await service.get_emergency_response(patient_id, str(user.id))


@router.post("/emergency/{patient_id}")
async def dispatch_emergency_response(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dispatch emergency response"""
    await authorize_patient_access(patient_id, user, db)
    service = MapsService(db)
    return await service.get_emergency_response(patient_id, str(user.id))
