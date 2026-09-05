import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...core.database import get_db
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User
from ...db.models.patient import Patient
from .service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class PatientMessageRequest(BaseModel):
    patient_id: str
    message: str


@router.post("/patient-message", response_model=dict)
async def message_patient(
    request: PatientMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send an ad-hoc message from ASHA/hospital staff (or the patient
    themselves) to a patient — reuses the same NotificationProvider pipeline
    as automated reminders rather than a separate implementation.

    Most patients created via the ASHA/hospital "Add Patient" flow have no
    linked User/login at all (Patient has no direct user_id — see
    User.patient_id for the reverse link), so this can't assume an email
    account exists the way reminders do. Tries the patient's own linked
    account email first (if they've self-registered), then falls back to
    SMS via the configured provider. Whichever channel is actually used —
    or that neither is available — is returned honestly to the caller; this
    never claims delivery that didn't happen (same principle as the patient
    chat's connection-failure fallback: don't imply something happened when
    it didn't).
    """
    await authorize_patient_access(request.patient_id, user, db)

    patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(request.patient_id))
    patient_result = await db.execute(patient_stmt)
    patient = patient_result.scalar_one_or_none()
    if not patient:
        return {"success": False, "detail": "Patient not found"}

    service = NotificationService(db)

    user_stmt = select(User).filter(User.patient_id == patient.id)
    user_result = await db.execute(user_stmt)
    patient_user = user_result.scalar_one_or_none()

    if patient_user and patient_user.email:
        result = await service.send_notification(
            str(patient_user.id),
            "patient",
            str(uuid.uuid4()),
            "Message from your care team",
            request.message,
            metadata={"phone": patient.phone, "email": patient_user.email},
        )
        result.setdefault("channel", "email")
        result.setdefault("success", True)
        return result

    if patient.phone:
        result = await service.send_sms(patient.phone, request.message)
        result.setdefault("channel", "sms")
        return result

    return {"success": False, "detail": "This patient has no email or phone on record to message."}
