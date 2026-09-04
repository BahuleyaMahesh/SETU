from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.alert import Alert, AlertStatus
from ...db.models.escalation import Escalation
from ...core.config import settings
from ..notifications.service import NotificationService


class AlertService:
    """Alert service with lifecycle management"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def create_alert(
        self,
        patient_id: str,
        severity: str,
        title: str,
        description: str,
        risk_level: str = None,
        alert_type: str = "symptom_alert",
        triggered_by: str = "manual",
        metadata: Dict = None,
    ) -> Alert:
        """Create new alert"""
        if not risk_level:
            risk_level = {"critical": "critical", "high": "warning", "medium": "warning", "low": "normal"}.get(
                severity, "warning"
            )

        alert = Alert(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            severity=severity,
            risk_level=risk_level,
            alert_type=alert_type,
            status="new",
            title=title,
            description=description,
            alert_metadata={**(metadata or {}), "triggered_by": triggered_by},
            created_at=datetime.utcnow(),
        )
        self.db.add(alert)
        await self.db.commit()
        return alert

    async def get_alerts(
        self,
        alert_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        hospital_id: Optional[str] = None,
        asha_worker_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get alerts with filters"""
        stmt = select(Alert)

        if alert_id:
            stmt = stmt.filter(Alert.id == uuid.UUID(alert_id))
        if patient_id:
            stmt = stmt.filter(Alert.patient_id == uuid.UUID(patient_id))
        if hospital_id:
            stmt = stmt.filter(Alert.hospital_id == uuid.UUID(hospital_id))
        if asha_worker_id:
            stmt = stmt.filter(Alert.asha_worker_id == uuid.UUID(asha_worker_id))
        if status:
            stmt = stmt.filter(Alert.status == status)
        if severity:
            stmt = stmt.filter(Alert.severity == severity)

        stmt = stmt.order_by(Alert.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        alerts = result.scalars().all()

        return [
            {
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "severity": a.severity,
                "status": a.status,
                "title": a.title,
                "description": a.description,
                "triggered_by": (a.alert_metadata or {}).get("triggered_by"),
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> Dict[str, Any]:
        """Acknowledge alert"""
        alert_stmt = select(Alert).filter(Alert.id == uuid.UUID(alert_id))
        alert_result = await self.db.execute(alert_stmt)
        alert = alert_result.scalar_one_or_none()

        if not alert:
            return {"error": "Alert not found"}

        if alert.status == "resolved":
            return {"error": "Alert already resolved"}

        alert.status = "acknowledged"
        alert.acknowledged_by_id = uuid.UUID(user_id)
        alert.acknowledged_at = datetime.utcnow()
        await self.db.commit()

        return {"success": True, "alert": alert_id}

    async def resolve_alert(self, alert_id: str, user_id: str) -> Dict[str, Any]:
        """Resolve alert"""
        alert_stmt = select(Alert).filter(Alert.id == uuid.UUID(alert_id))
        alert_result = await self.db.execute(alert_stmt)
        alert = alert_result.scalar_one_or_none()

        if not alert:
            return {"error": "Alert not found"}

        if alert.status == "resolved":
            return {"error": "Alert already resolved"}

        alert.status = "resolved"
        alert.resolved_by_id = uuid.UUID(user_id)
        alert.resolved_at = datetime.utcnow()
        await self.db.commit()

        return {"success": True, "alert": alert_id}

    async def get_patient_alerts(
        self,
        patient_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get active alerts for patient"""
        return await self.get_alerts(
            patient_id=str(patient_id),
            status=status,
        )

    async def get_open_alerts_count(self, patient_id: str) -> int:
        """Get count of open alerts for patient"""
        stmt = (
            select(Alert)
            .filter(Alert.patient_id == uuid.UUID(patient_id))
            .filter(Alert.status != "resolved")
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
