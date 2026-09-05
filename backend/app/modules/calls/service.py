from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.call import Call, CallStatus
from ...db.models.patient import Patient
from ...core.config import settings
from ...core.phone import to_e164
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

        # Providers hard-reject anything that isn't strict +E164 (Telnyx
        # error 10016) — and patient phones are human-entered, so they
        # arrive as "+91-98765-43210", "9123456789", etc. Confirmed live:
        # a real scheduled call was rejected outright for exactly this.
        to_number = to_e164(patient.phone)
        if not to_number:
            return {"error": f"Patient has no usable phone number on record ({patient.phone!r})"}

        # The number we dial FROM has to be the configured number of the
        # provider actually placing the call — this was hardcoded to
        # TWILIO_PHONE, which is blank on this deployment (Telnyx is the
        # live provider), so every call record stored an empty from_number.
        from_number = from_phone or getattr(self.provider, "from_phone", None) or settings.TWILIO_PHONE

        # Create call record
        call = Call(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            status="queued",
            call_type="outbound",
            call_direction="outbound",
            provider_call_id=None,
            recording_url=None,
            from_number=from_number,
            to_number=to_number,
            ivr_flow_id=ivr_flow_id,
            call_alert_metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(call)
        await self.db.commit()

        # Initiate call via provider
        call_result = await self.provider.call(
            to=to_number,
            from_=from_number,
            ivr_flow_id=ivr_flow_id,
            call_id=str(call.id),
        )

        # A provider failure must be recorded as a real failure, not left
        # sitting at "queued" forever looking like it's still going to
        # happen — same reliability rule as everywhere else in this app: a
        # telephony outage must never silently read as a normal outcome.
        if call_result.get("error") or not call_result.get("call_id"):
            call.status = "failed"
            call.call_alert_metadata = {
                **(call.call_alert_metadata or {}),
                "provider_error": str(call_result.get("error") or "provider returned no call id"),
            }
            await self.db.commit()
            return {
                "id": str(call.id),
                "status": "failed",
                "to": to_number,
                "error": call_result.get("error") or "Call provider did not accept the call",
            }

        call.provider_call_id = call_result.get("call_id")
        call.status = call_result.get("status") or "initiated"
        await self.db.commit()

        return {
            "id": str(call.id),
            "provider_call_id": call.provider_call_id,
            "status": call.status,
            "to": to_number,
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
            call.speech_transcript = transcript
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
