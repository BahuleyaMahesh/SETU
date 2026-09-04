from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import uuid

from ...db.models.risk import RiskRecord
from ...db.models.patient import Patient
from ...db.models.checkin import Checkin
from ...db.models.user import User
from ...core.config import settings
from ..notifications.service import NotificationService
from ..alerts.service import AlertService
from .rules import evaluate_risk as evaluate_risk_rules, RiskLevel


class RiskEngineService:
    """Risk engine service — delegates scoring to the deterministic rule
    engine in risk/rules.py (see docs/security.md: AI extracts, rules decide)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
        self.alert_service = AlertService(db)

    async def evaluate_risk(
        self,
        patient_id: str,
        symptoms: List[str],
        severity_score: float = 0,
        patient_age: Optional[int] = None,
        medical_conditions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Evaluate risk for a patient using the deterministic rule engine."""
        evaluation = evaluate_risk_rules(
            symptoms=symptoms,
            patient_age=patient_age,
            medical_conditions=medical_conditions,
        )

        risk = RiskRecord(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            risk_level=evaluation.risk_level.value,
            risk_score=evaluation.score,
            risk_factors=evaluation.factors,
            risk_reasons=evaluation.reasons,
            severity=int(severity_score or 0),
            action_required=evaluation.action_required,
            created_at=datetime.utcnow(),
        )
        self.db.add(risk)

        # Update patient risk level
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        if patient:
            patient.risk_level = evaluation.risk_level.value
            patient.last_risk_evaluation = datetime.utcnow()

        requires_escalation = evaluation.risk_level == RiskLevel.CRITICAL
        if requires_escalation:
            await self._create_alert(patient_id, evaluation.reasons, evaluation.score)

        await self.db.commit()

        return {
            "risk_score": evaluation.score,
            "risk_level": evaluation.risk_level.value,
            "risk_factors": evaluation.factors,
            "risk_reasons": evaluation.reasons,
            "action_required": evaluation.action_required,
        }

    async def _create_alert(
        self,
        patient_id: str,
        reasons: List[str],
        score: float,
    ):
        """Create critical alert via AlertService and notify the assigned ASHA."""
        await self.alert_service.create_alert(
            patient_id=patient_id,
            severity="critical",
            risk_level="critical",
            alert_type="checkin_risk",
            title="Critical risk detected",
            description="; ".join(reasons) if reasons else f"Risk score: {score}",
            triggered_by="risk_engine",
        )

        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        if patient and patient.assigned_asha_id:
            asha_user_stmt = select(User).filter(User.asha_worker_id == patient.assigned_asha_id)
            asha_user_result = await self.db.execute(asha_user_stmt)
            asha_user = asha_user_result.scalar_one_or_none()
            if asha_user:
                await self.notification_service.send_notification(
                    str(asha_user.id),
                    "asha",
                    str(uuid.uuid4()),
                    "Critical Patient Risk",
                    f"Patient {patient.full_name} has critical risk: {'; '.join(reasons) if reasons else score}",
                )

    async def get_risk_history(self, patient_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get risk history for patient"""
        stmt = (
            select(RiskRecord)
            .filter(RiskRecord.patient_id == uuid.UUID(patient_id))
            .order_by(desc(RiskRecord.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "risk_level": r.risk_level,
                "risk_score": r.risk_score,
                "risk_factors": r.risk_factors,
                "risk_reasons": r.risk_reasons,
                "severity": r.severity,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]

    async def get_latest_risk(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get latest risk record for patient"""
        stmt = (
            select(RiskRecord)
            .filter(RiskRecord.patient_id == uuid.UUID(patient_id))
            .order_by(desc(RiskRecord.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return {
            "id": str(record.id),
            "risk_level": record.risk_level,
            "risk_score": record.risk_score,
            "risk_factors": record.risk_factors,
            "risk_reasons": record.risk_reasons,
            "severity": record.severity,
            "created_at": record.created_at.isoformat(),
        }
