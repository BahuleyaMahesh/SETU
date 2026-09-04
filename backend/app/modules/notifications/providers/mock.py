from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class NotificationProvider(ABC):
    """Base class for notification providers"""

    name: str = "base"

    @abstractmethod
    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Send a notification"""
        pass

    @abstractmethod
    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send an SMS notification"""
        pass


class MockProvider(NotificationProvider):
    """Mock notification provider for development"""

    name = "mock"

    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "notification_id": notification_id,
            "sent_to": user_id,
        }

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        return {
            "success": True,
            "phone": phone,
        }
