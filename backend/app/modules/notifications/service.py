from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.notification import Notification, NotificationStatus
from ...core.config import settings
from .providers.mock import MockProvider
from .providers.msg91 import Msg91Provider
from .providers.twilio import TwilioNotificationProvider
from .providers.telnyx import TelnyxNotificationProvider
from .providers.email import EmailNotificationProvider


class NotificationProviderFactory:
    """Factory for notification providers"""

    @staticmethod
    def get_provider() -> Any:
        """Get configured notification provider"""
        provider_name = settings.NOTIFICATION_PROVIDER

        providers = {
            "mock": MockProvider,
            "msg91": Msg91Provider,
            "twilio": TwilioNotificationProvider,
            "telnyx": TelnyxNotificationProvider,
            "email": EmailNotificationProvider,
        }

        provider_class = providers.get(provider_name, MockProvider)
        return provider_class()


class NotificationService:
    """Notification service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = NotificationProviderFactory.get_provider()

    async def send_notification(
        self,
        user_id: str,
        user_role: str,
        notification_id: str,
        title: str,
        message: str,
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Send notification"""
        # Create notification record
        notification = Notification(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            notification_type="push",
            title=title,
            message=message,
            status="pending",
            alert_metadata=metadata or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(notification)

        # Send via provider
        result = await self.provider.send_notification(
            user_id=user_id,
            user_role=user_role,
            notification_id=notification_id,
            title=title,
            message=message,
            metadata=metadata,
        )

        notification.status = "sent" if result.get("success", True) else "failed"
        await self.db.commit()

        return result

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send SMS notification"""
        return await self.provider.send_sms(phone, message)

    async def get_user_notifications(
        self,
        user_id: str,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        """Get notifications for user"""
        stmt = select(Notification).filter(Notification.user_id == uuid.UUID(user_id))

        if status:
            stmt = stmt.filter(Notification.status == status)

        result = await self.db.execute(stmt)
        notifications = result.scalars().all()

        return [
            {
                "id": str(n.id),
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]
