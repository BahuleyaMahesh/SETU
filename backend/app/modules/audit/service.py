from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.audit import AuditLog
from ...core.config import settings
from ...core.security import get_client_ip


class AuditService:
    """Audit logging service"""

    AUDIT_ACTIONS = {
        "login": "User login",
        "logout": "User logout",
        "create": "Record created",
        "update": "Record updated",
        "delete": "Record deleted",
        "access": "Record accessed",
        "escalate": "Alert escalated",
        "verify": "Record verified",
        "upload": "Document uploaded",
        "process": "Data processed",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict = None,
        new_value: Dict = None,
        metadata: Dict = None,
        ip_address: str = None,
    ) -> Dict[str, Any]:
        """Log audit action"""
        audit_log = AuditLog(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if user_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value or {},
            new_value=new_value or {},
            alert_metadata=metadata or {},
            ip_address=ip_address or (metadata.get("ip_address", "") if metadata else ""),
            user_agent=metadata.get("user_agent", "") if metadata else "",
            created_at=datetime.utcnow(),
        )
        self.db.add(audit_log)
        await self.db.commit()

        return {"id": str(audit_log.id)}

    async def get_user_audit_log(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log for user"""
        stmt = (
            select(AuditLog)
            .filter(AuditLog.user_id == uuid.UUID(user_id))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return [
            {
                "id": str(l.id),
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "old_value": l.old_value,
                "new_value": l.new_value,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]

    async def get_resource_audit_log(self, resource_type: str, resource_id: str) -> List[Dict[str, Any]]:
        """Get audit log for resource"""
        stmt = (
            select(AuditLog)
            .filter(AuditLog.resource_type == resource_type)
            .filter(AuditLog.resource_id == resource_id)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return [
            {
                "id": str(l.id),
                "user_id": str(l.user_id) if l.user_id else None,
                "action": l.action,
                "old_value": l.old_value,
                "new_value": l.new_value,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]

    async def log_login(self, user_id: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Log login action"""
        return await self.log_action(
            user_id=user_id,
            action="login",
            resource_type="user",
            resource_id=user_id,
            metadata={"ip_address": ip_address, "user_agent": user_agent},
        )

    async def log_logout(self, user_id: str) -> Dict[str, Any]:
        """Log logout action"""
        return await self.log_action(
            user_id=user_id,
            action="logout",
            resource_type="user",
            resource_id=user_id,
        )

    async def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Log security event"""
        return await self.log_action(
            user_id=details.get("user_id"),
            action=f"security_{event_type}",
            resource_type="security",
            resource_id=details.get("resource_id", ""),
            metadata=details,
        )
