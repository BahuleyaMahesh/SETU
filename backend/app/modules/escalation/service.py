from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.escalation import Escalation, EscalationStatus
from ...db.models.alert import Alert
from ...db.models.user import User
from ...core.config import settings
from ..notifications.service import NotificationService


class EscalationService:
    """Escalation workflow service"""

    # Escalation path: from_role -> to_role
    ESCALATION_PATH = [
        ("asha", "hospital"),
        ("hospital", "admin"),
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def escalate_alert(
        self,
        alert_id: str,
        from_user_id: str,
        reason: str = None,
    ) -> Dict[str, Any]:
        """Escalate alert to next level"""
        alert_stmt = select(Alert).filter(Alert.id == uuid.UUID(alert_id))
        alert_result = await self.db.execute(alert_stmt)
        alert = alert_result.scalar_one_or_none()

        if not alert:
            return {"error": "Alert not found"}

        # Get current escalation if exists
        escalation_stmt = (
            select(Escalation)
            .filter(Escalation.alert_id == uuid.UUID(alert_id))
            .order_by(Escalation.created_at.desc())
            .limit(1)
        )
        esc_result = await self.db.execute(escalation_stmt)
        current_escalation = esc_result.scalar_one_or_none()

        # Determine from_role
        if current_escalation:
            from_role = current_escalation.to_role
        else:
            # Get patient's ASHA to determine from_role
            patient_stmt = select(Alert).filter(Alert.id == uuid.UUID(alert_id))
            patient_result = await self.db.execute(patient_stmt)
            alert = patient_result.scalar_one_or_none()
            from_role = "asha"

        # Find next role in path
        to_role = None
        for from_r, to_r in self.ESCALATION_PATH:
            if from_r == from_role:
                to_role = to_r
                break

        if not to_role:
            return {"error": "Cannot escalate further"}

        # Create escalation
        escalation = Escalation(
            id=uuid.uuid4(),
            alert_id=uuid.UUID(alert_id),
            from_role=from_role,
            to_role=to_role,
            status="pending",
            reason=reason or "Escalated by user",
            created_at=datetime.utcnow(),
        )
        self.db.add(escalation)
        await self.db.commit()

        # Update alert status
        alert.status = "escalated"
        await self.db.commit()

        return {
            "success": True,
            "escalation_id": str(escalation.id),
            "from_role": from_role,
            "to_role": to_role,
        }

    async def accept_escalation(
        self,
        escalation_id: str,
        user_id: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Accept escalation"""
        escalation_stmt = select(Escalation).filter(Escalation.id == uuid.UUID(escalation_id))
        escalation_result = await self.db.execute(escalation_stmt)
        escalation = escalation_result.scalar_one_or_none()

        if not escalation:
            return {"error": "Escalation not found"}

        if escalation.status != "pending":
            return {"error": "Escalation already handled"}

        if escalation.to_role != user_role:
            return {"error": "Not authorized to accept this escalation"}

        escalation.status = "in_progress"
        escalation.resolved_by_id = uuid.UUID(user_id)
        await self.db.commit()

        return {"success": True, "escalation_id": escalation_id}

    async def escalate_further(
        self,
        escalation_id: str,
        user_id: str,
        reason: str = None,
    ) -> Dict[str, Any]:
        """Escalate to next level"""
        escalation_stmt = select(Escalation).filter(Escalation.id == uuid.UUID(escalation_id))
        escalation_result = await self.db.execute(escalation_stmt)
        escalation = escalation_result.scalar_one_or_none()

        if not escalation:
            return {"error": "Escalation not found"}

        return await self.escalate_alert(
            alert_id=str(escalation.alert_id),
            from_user_id=user_id,
            reason=reason,
        )

    async def get_escalation_by_id(self, escalation_id: str) -> Optional[Dict[str, Any]]:
        """Get a single escalation, including the patient_id of its underlying alert"""
        stmt = select(Escalation).filter(Escalation.id == uuid.UUID(escalation_id))
        result = await self.db.execute(stmt)
        escalation = result.scalar_one_or_none()

        if not escalation:
            return None

        alert_stmt = select(Alert).filter(Alert.id == escalation.alert_id)
        alert_result = await self.db.execute(alert_stmt)
        alert = alert_result.scalar_one_or_none()

        return {
            "id": str(escalation.id),
            "alert_id": str(escalation.alert_id),
            "patient_id": str(alert.patient_id) if alert else None,
            "from_role": escalation.from_role,
            "to_role": escalation.to_role,
            "status": escalation.status,
            "reason": escalation.reason,
            "created_at": escalation.created_at.isoformat() if escalation.created_at else None,
        }

    async def get_alert_patient_id(self, alert_id: str) -> Optional[str]:
        """Look up the patient_id for an alert, for authorization purposes"""
        stmt = select(Alert).filter(Alert.id == uuid.UUID(alert_id))
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()
        return str(alert.patient_id) if alert else None

    async def get_alert_escalations(self, alert_id: str) -> List[Dict[str, Any]]:
        """Get escalation history for alert"""
        stmt = (
            select(Escalation)
            .filter(Escalation.alert_id == uuid.UUID(alert_id))
            .order_by(Escalation.created_at)
        )
        result = await self.db.execute(stmt)
        escalations = result.scalars().all()

        return [
            {
                "id": str(e.id),
                "alert_id": str(e.alert_id),
                "from_role": e.from_role,
                "to_role": e.to_role,
                "status": e.status,
                "reason": e.reason,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in escalations
        ]
