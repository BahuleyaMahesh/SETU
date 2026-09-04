from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os

from ...core.database import get_db
from .service import CallService
from ...modules.ivr.service import IVRService
from ...db.models.call import Call
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/calls", tags=["calls"])


@router.post("/outbound", response_model=dict)
async def create_outbound_call(
    patient_id: str,
    ivr_flow_id: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create outbound call to patient"""
    await authorize_patient_access(patient_id, user, db)
    service = CallService(db)
    return await service.create_outbound_call(patient_id, ivr_flow_id=ivr_flow_id)


@router.get("/{call_id}")
async def get_call(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get call by ID"""
    call_stmt = select(Call).filter(Call.id == uuid.UUID(call_id))
    result = await db.execute(call_stmt)
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    await authorize_patient_access(str(call.patient_id), user, db)
    return {"id": str(call.id), "status": call.status}


@router.get("/patient/{patient_id}/calls", response_model=list[dict])
async def get_patient_calls(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get calls for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = CallService(db)
    return await service.get_patient_calls(patient_id)


@router.post("/webhook/status")
async def handle_call_status(
    call_id: str,
    status: str,
    recording_url: str = None,
    transcript: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle call status webhook"""
    service = CallService(db)
    return await service.handle_call_status(call_id, status, recording_url, transcript)


@router.get("/ivr/flows")
async def list_ivr_flows():
    """List available IVR flows"""
    return {
        "flows": [
            {"id": "checkin", "name": "Check-in Flow"},
            {"id": "reminder", "name": "Medication Reminder Flow"},
            {"id": "emergency", "name": "Emergency Flow"},
        ]
    }
