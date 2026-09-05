import logging
from typing import Optional, Dict, Any
from ..base import TelephonyProvider
from ....core.config import settings

logger = logging.getLogger("setu.calls.twilio")


class TwilioProvider(TelephonyProvider):
    """Twilio telephony provider — places real outbound calls and SMS."""

    name = "twilio"

    def __init__(self):
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
        self.from_phone = getattr(settings, "TWILIO_PHONE", None)
        self._client = None

    def _get_client(self):
        if not self.account_sid or not self.auth_token:
            return None
        if self._client is None:
            from twilio.rest import Client
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    def _build_checkin_twiml(self) -> str:
        """Simple check-in TwiML that works with no public webhook: greet,
        get consent, ask how the patient is feeling, and record the answer.
        """
        from twilio.twiml.voice_response import VoiceResponse, Gather

        response = VoiceResponse()
        response.say(
            "Hello, this is SETU calling for your daily health check-in. "
            "This call is recorded for your care. Press 1 to continue.",
        )
        gather = Gather(num_digits=1, timeout=8)
        response.append(gather)
        response.say("How are you feeling today? Please describe your symptoms after the tone.")
        response.record(max_length=60, play_beep=True, transcribe=False)
        response.say("Thank you. Your care team will follow up if needed. Goodbye.")
        return str(response)

    async def call(
        self,
        to: str,
        from_: str = None,
        ivr_flow_id: str = None,
        call_id: str = None,
    ) -> Dict[str, Any]:
        """Initiate a real outbound call via Twilio, or a safe simulated
        fallback when credentials are not configured."""
        from_number = from_ or self.from_phone

        client = self._get_client()
        if not client or not from_number:
            missing = "TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN" if not client else "TWILIO_PHONE"
            logger.warning(f"// SETU-CONFIG-REQUIRED: {missing} — Twilio call credentials incomplete, using fallback response")
            return {
                "call_id": f"twilio_sim_{call_id or '12345'}",
                "status": "queued",
                "to": to,
                "from": from_number or "+15005550006",
                "note": "Twilio not fully configured; simulated call queued",
            }

        try:
            kwargs: Dict[str, Any] = {"to": to, "from_": from_number}
            if settings.PUBLIC_BASE_URL:
                kwargs["url"] = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/calls/webhook/twiml"
                kwargs["status_callback"] = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/calls/webhook/status"
            else:
                kwargs["twiml"] = self._build_checkin_twiml()

            twilio_call = client.calls.create(**kwargs)
            return {
                "call_id": twilio_call.sid,
                "status": twilio_call.status,
                "to": to,
                "from": from_number,
            }
        except Exception as e:
            logger.error(f"Twilio call failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send a real SMS via Twilio, or a safe simulated fallback."""
        client = self._get_client()
        if not client or not self.from_phone:
            missing = "TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN" if not client else "TWILIO_PHONE"
            logger.warning(f"// SETU-CONFIG-REQUIRED: {missing} — Twilio SMS credentials incomplete, using fallback response")
            return {
                "success": True,
                "phone": phone,
                "message_id": "twilio_sim_sms",
                "note": "Twilio not fully configured; simulated SMS sent",
            }

        try:
            msg = client.messages.create(to=phone, from_=self.from_phone, body=message)
            return {"success": True, "phone": phone, "message_id": msg.sid, "status": msg.status}
        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            return {"success": False, "phone": phone, "error": str(e)}
