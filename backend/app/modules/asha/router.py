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
    if user.role == "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    service = ASHAService(db)

    # Auto-resolve ASHA worker ID if user is an ASHA worker
    if user.role == "asha":
        if user.asha_worker_id:
            asha_id = str(user.asha_worker_id)
        else:
            # Auto-create profile if missing
            from ...db.models.asha import ASHAWorker
            import uuid
            new_asha = ASHAWorker(
                id=uuid.uuid4(),
                name=user.full_name,
                asha_id=f"ASHA-{uuid.uuid4().hex[:8].upper()}",
                phone=user.phone or "+91-9876543210",
                district="Mandya",
            )
            db.add(new_asha)
            await db.flush()
            user.asha_worker_id = new_asha.id
            await db.commit()
            asha_id = str(new_asha.id)

    hospital_id = str(user.hospital_id) if user.role == "hospital" else None
    return await service.get_asha_patients(asha_id, risk_level, search, hospital_id=hospital_id)


@router.get("/{asha_id}/caseload")
async def get_asha_caseload(
    asha_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get ASHA caseload summary"""
    if user.role == "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    service = ASHAService(db)
    if user.role == "asha":
        if user.asha_worker_id:
            asha_id = str(user.asha_worker_id)
        else:
            from ...db.models.asha import ASHAWorker
            import uuid
            new_asha = ASHAWorker(
                id=uuid.uuid4(),
                name=user.full_name,
                asha_id=f"ASHA-{uuid.uuid4().hex[:8].upper()}",
                phone=user.phone or "+91-9876543210",
                district="Mandya",
            )
            db.add(new_asha)
            await db.flush()
            user.asha_worker_id = new_asha.id
            await db.commit()
            asha_id = str(new_asha.id)

    hospital_id = str(user.hospital_id) if user.role == "hospital" else None
    return await service.get_asha_caseload(asha_id, hospital_id=hospital_id)


@router.post("/patients")
async def add_asha_patient(
    patient_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new patient by authenticated ASHA worker"""
    if current_user.role != "asha":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authenticated ASHA workers can add patients",
        )
    if not current_user.asha_worker_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ASHA worker profile is not linked to this account",
        )

    service = ASHAService(db)
    return await service.create_asha_patient(current_user, patient_data)


@router.delete("/{asha_id}/patients/{patient_id}")
async def remove_asha_patient(
    asha_id: str,
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Unassign patient from ASHA worker (removes active assignment, preserves patient & records)"""
    if user.role == "asha" and str(getattr(user, "asha_worker_id", None)) != asha_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif user.role not in ("asha", "hospital", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    service = ASHAService(db)
    return await service.remove_patient(asha_id, patient_id)

