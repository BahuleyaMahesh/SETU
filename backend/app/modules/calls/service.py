from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.call import Call, CallStatus
from ...db.models.patient import Patient
from ...core.config import settings
from .providers.mock import MockProvider
from .providers.twilio import TwilioProvider
from .providers.telnyx import TelnyxProvider


class CallProviderFactory:
    """Factory for telephony providers"""

    @staticmethod
    def get_provider() -> Any:
        """Get configured telephony provider"""
        provider_name = settings.TELEPHONY_PROVIDER

        providers = {
            "mock": MockProvider,
            "twilio": TwilioProvider,
            "telnyx": TelnyxProvider,
        }

        provider_class = providers.get(provider_name, MockProvider)
        return provider_class()


class CallService:
    """Call service with IVR support"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = CallProviderFactory.get_provider()

    async def create_outbound_call(
        self,
        patient_id: str,
        from_phone: str = None,
        ivr_flow_id: str = None,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create outbound call"""
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()

        if not patient:
            return {"error": "Patient not found"}

        # Create call record
        call = Call(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            status="queued",
            call_type="outbound",
            call_direction="outbound",
            provider_call_id=None,
            recording_url=None,
            from_number=from_phone or settings.TWILIO_PHONE,
            to_number=patient.phone,
            ivr_flow_id=ivr_flow_id,
            call_alert_metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(call)
        await self.db.commit()

        # Initiate call via provider
        call_result = await self.provider.call(
            to=patient.phone,
            from_=from_phone,
            ivr_flow_id=ivr_flow_id,
            call_id=str(call.id),
        )

        call.provider_call_id = call_result.get("call_id")
        await self.db.commit()

        return {
            "id": str(call.id),
            "provider_call_id": call.provider_call_id,
            "status": call.status,
            "to": patient.phone,
        }

    async def handle_call_status(
        self,
        call_id: str,
        status: str,
        recording_url: str = None,
        transcript: str = None,
    ) -> Dict[str, Any]:
        """Update call status (webhook handler)"""
        stmt = select(Call).filter(Call.id == uuid.UUID(call_id))
        result = await self.db.execute(stmt)
        call = result.scalar_one_or_none()

        if not call:
            return {"error": "Call not found"}

        call.status = status
        if recording_url:
            call.recording_url = recording_url
        if transcript:
            call.transcript = transcript
        await self.db.commit()

        return {"success": True, "call_id": call_id}

    async def get_patient_calls(self, patient_id: str) -> list:
        """Get calls for patient"""
        stmt = select(Call).filter(Call.patient_id == uuid.UUID(patient_id))
        result = await self.db.execute(stmt)
        calls = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "status": c.status,
                "call_type": c.call_type,
                "from_number": c.from_number,
                "to_number": c.to_number,
                "recording_url": c.recording_url,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in calls
        ]

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send SMS via provider"""
        return await self.provider.send_sms(phone, message)
