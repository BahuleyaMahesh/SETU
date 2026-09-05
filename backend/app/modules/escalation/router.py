from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import EscalationService
from ...core.security import get_current_user, require_asha, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/escalations", tags=["escalation"])


@router.get("/{escalation_id}")
async def get_escalation(
    escalation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get escalation by ID"""
    service = EscalationService(db)
    escalation = await service.get_escalation_by_id(escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if escalation["patient_id"]:
        await authorize_patient_access(escalation["patient_id"], user, db)
    return escalation


@router.get("/alert/{alert_id}")
async def get_alert_escalations(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get escalation history for alert"""
    service = EscalationService(db)
    patient_id = await service.get_alert_patient_id(alert_id)
    if not patient_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    await authorize_patient_access(patient_id, user, db)
    return await service.get_alert_escalations(alert_id)


@router.patch("/{escalation_id}/accept")
async def accept_escalation(
    escalation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asha),
):
    """Accept escalation"""
    service = EscalationService(db)
    escalation = await service.get_escalation_by_id(escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if escalation["patient_id"]:
        await authorize_patient_access(escalation["patient_id"], user, db)

    result = await service.accept_escalation(escalation_id, str(user.id), user.role)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.patch("/{escalation_id}/escalate-further")
async def escalate_further(
    escalation_id: str,
    reason: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asha),
):
    """Escalate to next level"""
    service = EscalationService(db)
    escalation = await service.get_escalation_by_id(escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if escalation["patient_id"]:
        await authorize_patient_access(escalation["patient_id"], user, db)

    result = await service.escalate_further(escalation_id, str(user.id), reason)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
