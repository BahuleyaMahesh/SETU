from typing import Dict, Any

from .base import NotificationProvider


class SMSProvider(NotificationProvider):
    """SMS notification provider using configurable gateway"""

    name = "sms"

    def __init__(self, api_key: str = None, sender_id: str = None):
        self.api_key = api_key
        self.sender_id = sender_id or "SETUHC"

    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Send notification via SMS"""
        # In production, integrate with SMS gateway (MSG91, Twilio, etc.)
        return {
            "success": True,
            "provider": "sms",
            "notification_id": notification_id,
            "sent_to": user_id,
        }

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send an SMS message"""
        # In production, call SMS gateway API
        return {
            "success": True,
            "provider": "sms",
            "phone": phone,
            "message_length": len(message),
        }
