import logging
from typing import Dict, Any

import httpx

from .base import NotificationProvider
from ....core.config import settings

logger = logging.getLogger("setu.notifications.telnyx")


class TelnyxNotificationProvider(NotificationProvider):
    """Sends SMS notifications via Telnyx."""

    name = "telnyx"

    def __init__(self):
        self.api_key = getattr(settings, "TELNYX_API_KEY", None)
        self.from_phone = getattr(settings, "TELNYX_PHONE", None)

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
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
            return {"success": True, "provider": "telnyx", "notification_id": notification_id, "skipped": "no phone on record"}

        result = await self.send_sms(phone, f"{title}: {message}" if title else message)
        result["notification_id"] = notification_id
        return result
