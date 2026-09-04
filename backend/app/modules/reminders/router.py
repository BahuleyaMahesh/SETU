from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import ReminderService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


@router.get("/", response_model=list[dict])
async def get_reminders(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get reminders for patient"""
    if user.role != "patient" or not user.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    service = ReminderService(db)
    return await service.get_patient_reminders(str(user.patient_id))


@router.get("/{reminder_id}")
async def get_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get reminder by ID"""
    service = ReminderService(db)
    reminder = await service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await authorize_patient_access(reminder["patient_id"], user, db)
    return reminder


@router.patch("/{reminder_id}/complete")
async def complete_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark reminder as completed"""
    service = ReminderService(db)
    reminder = await service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await authorize_patient_access(reminder["patient_id"], user, db)

    result = await service.complete_reminder(reminder_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.patch("/{reminder_id}/cancel")
async def cancel_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cancel reminder"""
    service = ReminderService(db)
    reminder = await service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await authorize_patient_access(reminder["patient_id"], user, db)

    result = await service.cancel_reminder(reminder_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
