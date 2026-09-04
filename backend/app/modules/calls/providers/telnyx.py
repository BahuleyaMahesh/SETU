import logging
from typing import Optional, Dict, Any

import httpx

from ..base import TelephonyProvider
from ....core.config import settings

logger = logging.getLogger("setu.calls.telnyx")


class TelnyxProvider(TelephonyProvider):
    """Telnyx telephony provider — real outbound SMS, and outbound calls via
    a TeXML Application.

    Unlike Twilio, Telnyx has no inline-TwiML equivalent: a TeXML
    Application must exist in the Telnyx Mission Control Portal with its
    "Voice URL" pointing at a live, publicly reachable endpoint that returns
    TeXML (Telnyx's TwiML-compatible XML) — same requirement this app
    already anticipates for Twilio via PUBLIC_BASE_URL. Without
    TELNYX_ACCOUNT_SID/TELNYX_TEXML_APPLICATION_SID configured, call()
    returns a simulated response; send_sms() has no such requirement and
    works standalone.
    """

    name = "telnyx"

    def __init__(self):
        self.api_key = getattr(settings, "TELNYX_API_KEY", None)
        self.from_phone = getattr(settings, "TELNYX_PHONE", None)
        self.account_sid = getattr(settings, "TELNYX_ACCOUNT_SID", None)
        self.application_sid = getattr(settings, "TELNYX_TEXML_APPLICATION_SID", None)

    async def call(
        self,
        to: str,
        from_: str = None,
        ivr_flow_id: str = None,
        call_id: str = None,
    ) -> Dict[str, Any]:
        """Initiate a real outbound call via a Telnyx TeXML Application, or a
        safe simulated fallback when credentials/application are not configured."""
        from_number = from_ or self.from_phone

        missing = None
        if not self.api_key:
            missing = "TELNYX_API_KEY"
        elif not from_number:
            missing = "TELNYX_PHONE"
        elif not self.account_sid:
            missing = "TELNYX_ACCOUNT_SID"
        elif not self.application_sid:
            missing = "TELNYX_TEXML_APPLICATION_SID"

        if missing:
            logger.warning(f"// SETU-CONFIG-REQUIRED: {missing} — Telnyx call credentials incomplete, using fallback response")
            return {
                "call_id": f"telnyx_sim_{call_id or '12345'}",
                "status": "queued",
                "to": to,
                "from": from_number or "+15005550006",
                "note": "Telnyx not fully configured; simulated call queued",
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"https://api.telnyx.com/v2/texml/Accounts/{self.account_sid}/Calls",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"ApplicationSid": self.application_sid, "To": to, "From": from_number},
                )
            response.raise_for_status()
            data = response.json()
            return {
                "call_id": data.get("sid") or data.get("call_sid") or data.get("CallSid"),
                "status": data.get("status", "queued"),
                "to": to,
                "from": from_number,
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Telnyx call failed: {e.response.text}")
            return {"error": e.response.text, "status": "failed"}
        except Exception as e:
            logger.error(f"Telnyx call failed: {e}")
            return {"error": str(e), "status": "failed"}

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send a real SMS via Telnyx, or a safe simulated fallback."""
        if not self.api_key or not self.from_phone:
            missing = "TELNYX_API_KEY" if not self.api_key else "TELNYX_PHONE"
            logger.warning(f"// SETU-CONFIG-REQUIRED: {missing} — Telnyx SMS credentials incomplete, using fallback response")
            return {
                "success": True,
                "phone": phone,
                "message_id": "telnyx_sim_sms",
                "note": "Telnyx not fully configured; simulated SMS sent",
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.telnyx.com/v2/messages",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"from": self.from_phone, "to": phone, "text": message},
                )
            response.raise_for_status()
            data = response.json().get("data", {})
            to_status = (data.get("to") or [{}])[0].get("status")
            return {"success": True, "phone": phone, "message_id": data.get("id"), "status": to_status}
        except httpx.HTTPStatusError as e:
            logger.error(f"Telnyx SMS failed: {e.response.text}")
            return {"success": False, "phone": phone, "error": e.response.text}
        except Exception as e:
            logger.error(f"Telnyx SMS failed: {e}")
            return {"success": False, "phone": phone, "error": str(e)}
