from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.timeutils import next_local_time_as_utc
from .service import ReminderService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


def _parse_local_hhmm(value: str) -> time:
    """Parse an "HH:MM" local (IST) clock time from the UI's <input type=time>."""
    try:
        hour, minute = (int(part) for part in value.split(":")[:2])
        return time(hour, minute)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Time must be in HH:MM format")


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


@router.get("/patient/{patient_id}", response_model=list[dict])
async def get_patient_reminders(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get reminders for a specific patient — used by ASHA/hospital staff
    viewing a patient they're authorized to see (the patient-only "/"
    listing above only ever resolves the caller's own patient_id, so ASHA/
    hospital had no way to view a patient's reminders at all)."""
    await authorize_patient_access(patient_id, user, db)
    service = ReminderService(db)
    return await service.get_patient_reminders(patient_id)


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


@router.post("/{reminder_id}/send")
async def send_reminder(
    reminder_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send a scheduled reminder immediately (real SMS via the configured
    NotificationProvider) instead of waiting for its scheduled time."""
    service = ReminderService(db)
    reminder = await service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await authorize_patient_access(reminder["patient_id"], user, db)

    result = await service.send_reminder(reminder_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class RescheduleRequest(BaseModel):
    """`time` is a LOCAL (IST) clock time as "HH:MM" — the same thing the
    patient reads off their prescription ("8 in the morning"). Converted to
    naive UTC here so the caller never has to think about the offset."""
    time: str


@router.patch("/{reminder_id}/reschedule")
async def reschedule_reminder(
    reminder_id: str,
    request: RescheduleRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Change the local time of day a reminder fires, keeping it repeating
    daily. Used by the medication panel after a prescription is uploaded —
    the frequency heuristic picks sensible defaults (morning 8am, night 9pm)
    but a real patient's routine may differ."""
    service = ReminderService(db)
    reminder = await service.get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    await authorize_patient_access(reminder["patient_id"], user, db)

    slot = _parse_local_hhmm(request.time)
    result = await service.reschedule_reminder(reminder_id, next_local_time_as_utc(slot))
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class CreateMedicationReminderRequest(BaseModel):
    patient_id: str
    title: str
    time: str  # local (IST) "HH:MM"
    description: str | None = None
    medication_id: str | None = None


@router.post("/medication", response_model=dict)
async def create_medication_reminder(
    request: CreateMedicationReminderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add an extra daily medication reminder at a chosen local time — for
    doses the frequency text didn't capture, or a time the patient prefers."""
    await authorize_patient_access(request.patient_id, user, db)

    slot = _parse_local_hhmm(request.time)
    service = ReminderService(db)
    return await service.create_medication_reminder(
        patient_id=request.patient_id,
        title=request.title,
        scheduled_at=next_local_time_as_utc(slot),
        description=request.description,
        medication_id=request.medication_id,
    )


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
