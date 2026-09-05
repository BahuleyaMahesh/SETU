from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.risk import RiskRecord
from ...db.models.checkin import Checkin
from ...db.models.alert import Alert
from ...db.models.patient import Patient
from ...core.config import settings


class ReportService:
    """Reporting service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_patient_report(
        self,
        patient_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Generate patient report"""
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()

        if not patient:
            return {"error": "Patient not found"}

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get risk history
        risk_stmt = (
            select(RiskRecord)
            .filter(RiskRecord.patient_id == uuid.UUID(patient_id))
            .filter(RiskRecord.created_at >= start_date)
            .order_by(RiskRecord.created_at.desc())
        )
        risk_result = await self.db.execute(risk_stmt)
        risk_records = risk_result.scalars().all()

        # Get check-ins
        checkin_stmt = (
            select(Checkin)
            .filter(Checkin.patient_id == uuid.UUID(patient_id))
            .filter(Checkin.created_at >= start_date)
            .order_by(Checkin.created_at.desc())
        )
        checkin_result = await self.db.execute(checkin_stmt)
        checkins = checkin_result.scalars().all()

        # Get alerts
        alert_stmt = (
            select(Alert)
            .filter(Alert.patient_id == uuid.UUID(patient_id))
            .filter(Alert.created_at >= start_date)
            .order_by(Alert.created_at.desc())
        )
        alert_result = await self.db.execute(alert_stmt)
        alerts = alert_result.scalars().all()

        return {
            "patient": {
                "id": str(patient.id),
                "mrn": patient.mrn,
                "full_name": patient.full_name,
                "age": self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                "gender": patient.gender,
                "phone": patient.phone,
                "village": patient.village,
                "risk_level": patient.risk_level,
            },
            "risk_history": [
                {
                    "date": r.created_at.isoformat(),
                    "risk_level": r.risk_level,
                    "score": r.score,
                    "symptoms": r.symptoms,
                }
                for r in risk_records
            ],
            "checkins": [
                {
                    "date": c.created_at.isoformat(),
                    "method": c.method,
                    "responses": c.responses,
                }
                for c in checkins
            ],
            "alerts": [
                {
                    "date": a.created_at.isoformat(),
                    "severity": a.severity,
                    "status": a.status,
                    "title": a.title,
                }
                for a in alerts
            ],
        }

    async def get_hospital_report(self, hospital_id: str) -> Dict[str, Any]:
        """Generate hospital report"""
        # Get hospital patients count
        patient_stmt = select(Patient).filter(Patient.hospital_id == uuid.UUID(hospital_id))
        patient_result = await self.db.execute(patient_stmt)
        patients = patient_result.scalars().all()

        # Count by risk level
        risk_counts = {"normal": 0, "warning": 0, "critical": 0}
        for p in patients:
            level = p.risk_level or "normal"
            risk_counts[level] = risk_counts.get(level, 0) + 1

        # Get open alerts
        alert_stmt = select(Alert).filter(Alert.patient_id.in_([p.id for p in patients]), Alert.status != "resolved")
        alert_result = await self.db.execute(alert_stmt)
        open_alerts = len(alert_result.scalars().all())

        return {
            "hospital_id": hospital_id,
            "total_patients": len(patients),
            "risk_distribution": risk_counts,
            "open_alerts": open_alerts,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_alert_report(self, hospital_id: str) -> Dict[str, Any]:
        """Generate alert report"""
        # Get patient IDs
        patient_stmt = select(Patient).filter(Patient.hospital_id == uuid.UUID(hospital_id))
        patient_result = await self.db.execute(patient_stmt)
        patient_ids = [r[0] for r in patient_result.fetchall()]

        # Get alerts
        alert_stmt = select(Alert).filter(Alert.patient_id.in_(patient_ids))
        alert_result = await self.db.execute(alert_stmt)
        alerts = alert_result.scalars().all()

        # Count by status
        status_counts = {}
        for a in alerts:
            status = a.status or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by severity
        severity_counts = {}
        for a in alerts:
            severity = a.severity or "unknown"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "hospital_id": hospital_id,
            "total_alerts": len(alerts),
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
        }

    async def get_follow_up_report(self, hospital_id: str) -> Dict[str, Any]:
        """Generate follow-up report"""
        # Get patients with last check-ins
        patient_stmt = select(Patient).filter(Patient.hospital_id == uuid.UUID(hospital_id))
        patient_result = await self.db.execute(patient_stmt)
        patients = patient_result.scalars().all()

        follow_up_data = []
        for p in patients:
            days_since_checkin = None
            if p.last_checkin:
                delta = datetime.utcnow() - p.last_checkin
                days_since_checkin = delta.days

            follow_up_data.append({
                "patient_id": str(p.id),
                "mrn": p.mrn,
                "full_name": p.full_name,
                "last_checkin": p.last_checkin.isoformat() if p.last_checkin else None,
                "days_since_checkin": days_since_checkin,
                "risk_level": p.risk_level,
                "needs_follow_up": days_since_checkin is None or days_since_checkin > 7,
            })

        return {
            "hospital_id": hospital_id,
            "patients": follow_up_data,
            "pending_follow_up": len([p for p in follow_up_data if p["needs_follow_up"]]),
        }

    def _calculate_age(self, dob: datetime) -> int:
        """Calculate age from date of birth"""
        today = datetime.utcnow().date()
        birth_date = dob.date() if hasattr(dob, 'date') else dob
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
