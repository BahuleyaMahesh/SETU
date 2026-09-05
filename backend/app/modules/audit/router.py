from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import AuditService
from ...core.security import get_current_user
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/user/{user_id}", response_model=list[dict])
async def get_user_audit_log(
    user_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get audit log for user"""
    if user.role not in ("admin", "hospital") and str(user.id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuditService(db)
    return await service.get_user_audit_log(user_id, limit)


@router.get("/resource/{resource_type}/{resource_id}", response_model=list[dict])
async def get_resource_audit_log(
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get audit log for resource"""
    service = AuditService(db)
    return await service.get_resource_audit_log(resource_type, resource_id)
