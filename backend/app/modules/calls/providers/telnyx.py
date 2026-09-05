import logging
from typing import Optional, Dict, Any

import httpx

from ..base import TelephonyProvider
from ....core.config import settings
from ....core.phone import to_e164

logger = logging.getLogger("setu.calls.telnyx")


class TelnyxProvider(TelephonyProvider):
    """Telnyx telephony provider — real outbound SMS, and outbound calls via
    the native Call Control API (JSON event-driven), not the TeXML/Twilio-
    compatibility REST layer.

    TeXML's `POST /v2/texml/Accounts/{account_sid}/Calls` endpoint requires
    an `account_sid` that Telnyx does not expose anywhere in the Mission
    Control Portal or its docs — confirmed empirically (two plausible
    candidate values both rejected with a real, non-generic 404, ruling out
    "any value works" theories) after documentation and support both failed
    to produce a real answer. `POST /v2/calls` sidesteps this entirely: it
    takes a `connection_id` pointing at a Call Control Application (a
    "Voice API Application" in the portal — a different resource type from
    a TeXML Application), which is empirically confirmed working. In
    exchange, control flow is imperative JSON commands answering webhook
    events (call.answered, call.gather.ended, call.recording.saved, ...)
    rather than declarative XML — see webhook/events in calls/router.py.

    Without TELNYX_CONNECTION_ID configured, call() returns a simulated
    response; send_sms() has no such requirement and works standalone.
    """

    name = "telnyx"

    def __init__(self):
        self.api_key = getattr(settings, "TELNYX_API_KEY", None)
        self.from_phone = getattr(settings, "TELNYX_PHONE", None)
        self.connection_id = getattr(settings, "TELNYX_CONNECTION_ID", None)

    async def call(
        self,
        to: str,
        from_: str = None,
        ivr_flow_id: str = None,
        call_id: str = None,
    ) -> Dict[str, Any]:
        """Initiate a real outbound call via Telnyx's native Call Control
        API, or a safe simulated fallback when credentials/connection are
        not configured. The Call Control Application's webhook_event_url
        (set when the connection was created) drives the rest of the call —
        see /api/v1/calls/webhook/events."""
        # Telnyx rejects anything that isn't strict +E164 (error 10016) —
        # normalize here too, not just in CallService, so any other caller
        # (webhooks, scripts, a future feature) can't reintroduce the bug.
        to = to_e164(to)
        from_number = to_e164(from_ or self.from_phone)

        missing = None
        if not self.api_key:
            missing = "TELNYX_API_KEY"
        elif not from_number:
            missing = "TELNYX_PHONE"
        elif not self.connection_id:
            missing = "TELNYX_CONNECTION_ID"

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
                    "https://api.telnyx.com/v2/calls",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"connection_id": self.connection_id, "to": to, "from": from_number},
                )
            response.raise_for_status()
            data = response.json().get("data", {})
            return {
                "call_id": data.get("call_control_id"),
                "status": data.get("call_state", "queued"),
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
        phone = to_e164(phone)
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
                    json={"from": to_e164(self.from_phone), "to": phone, "text": message},
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
