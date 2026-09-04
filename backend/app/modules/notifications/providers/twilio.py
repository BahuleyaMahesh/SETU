import logging
from typing import Dict, Any

from .base import NotificationProvider
from ....core.config import settings

logger = logging.getLogger("setu.notifications.twilio")


class TwilioNotificationProvider(NotificationProvider):
    """Sends SMS notifications via Twilio."""

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

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
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

    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """SMS has no separate push channel — send the message body as an SMS
        when a phone number is available in metadata, else no-op."""
        phone = (metadata or {}).get("phone")
        if not phone:
            return {"success": True, "provider": "twilio", "notification_id": notification_id, "skipped": "no phone on record"}

        result = await self.send_sms(phone, f"{title}: {message}" if title else message)
        result["notification_id"] = notification_id
        return result
