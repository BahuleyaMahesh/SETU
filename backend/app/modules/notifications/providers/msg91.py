from .base import NotificationProvider


class Msg91Provider(NotificationProvider):
    """Msg91 SMS provider"""

    async def send_sms(self, phone: str, message: str) -> dict:
        """Send SMS via Msg91"""
        # Mock implementation - in production, call Msg91 API
        return {"success": True, "phone": phone, "message": message}

    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: dict = None,
    ) -> dict:
        """Send notification"""
        return {
            "success": True,
            "user_id": user_id,
            "title": title,
            "message": message,
        }
