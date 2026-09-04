from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationProvider(ABC):
    """Base class for notification providers"""

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
