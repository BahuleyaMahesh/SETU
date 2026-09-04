from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from .service import AuthService
from .schemas import LoginRequest, RegisterRequest, LoginResponse


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/hospitals")
async def list_hospitals_for_signup(db: AsyncSession = Depends(get_db)):
    """Minimal, unauthenticated hospital list for the sign-up form's hospital picker"""
    from ...db.models.hospital import Hospital

    stmt = select(Hospital).filter(Hospital.is_active == True).order_by(Hospital.name)
    result = await db.execute(stmt)
    hospitals = result.scalars().all()
    return [{"id": str(h.id), "name": h.name} for h in hospitals]


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    service = AuthService(db)
    result, error = await service.login(request.email, request.password)

    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    return result


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    service = AuthService(db)
    result, error = await service.register(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        role=request.role,
        hospital_name=request.hospital_name,
        hospital_id=request.hospital_id,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return result


@router.post("/refresh")
async def refresh(token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token"""
    service = AuthService(db)
    new_token, error = await service.refresh_token(token)

    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    return {"access_token": new_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """Logout user"""
    return {"message": "Logged out successfully"}


from ...core.security import get_current_user
from ...db.models.user import User


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None,
        "asha_worker_id": str(user.asha_worker_id) if user.asha_worker_id else None,
        "patient_id": str(user.patient_id) if user.patient_id else None,
    }
