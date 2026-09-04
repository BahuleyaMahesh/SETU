from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
import uuid

from ...db.models.risk import RiskRecord
from ...db.models.checkin import Checkin
from ...db.models.alert import Alert
from ...db.models.patient import Patient
from ...db.models.asha import ASHAWorker
from ...core.config import settings


class AnalyticsService:
    """Analytics and reporting service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_risk_analytics(self, hospital_id: str = None) -> Dict[str, Any]:
        """Get risk level distribution"""
        stmt = select(RiskRecord)

        if hospital_id:
            # Join with patients to filter by hospital
            from sqlalchemy import join
            patient_stmt = select(Patient.id).filter(Patient.hospital_id == uuid.UUID(hospital_id))
            patient_result = await self.db.execute(patient_stmt)
            patient_ids = [r[0] for r in patient_result.fetchall()]
            stmt = stmt.filter(RiskRecord.patient_id.in_(patient_ids))

        result = await self.db.execute(stmt)
        records = result.scalars().all()

        # Count by risk level
        risk_counts = {"normal": 0, "warning": 0, "critical": 0}
        for r in records:
            level = r.risk_level or "normal"
            risk_counts[level] = risk_counts.get(level, 0) + 1

        return {
            "distribution": risk_counts,
            "total_evaluations": len(records),
        }

    async def get_patient_risk_distribution(self, hospital_id: str = None) -> Dict[str, Any]:
        """Current patient headcount by risk tier (Patient.risk_level as it stands
        right now), not historical evaluation events like get_risk_analytics()."""
        stmt = select(Patient)
        if hospital_id:
            stmt = stmt.filter(Patient.hospital_id == uuid.UUID(hospital_id))

        result = await self.db.execute(stmt)
        patients = result.scalars().all()

        counts = {"normal": 0, "warning": 0, "critical": 0}
        for p in patients:
            level = p.risk_level or "normal"
            counts[level] = counts.get(level, 0) + 1

        return {
            "total": len(patients),
            "critical": counts["critical"],
            "warning": counts["warning"],
            "normal": counts["normal"],
        }

    async def get_checkin_analytics(self, hospital_id: str = None) -> Dict[str, Any]:
        """Get check-in analytics"""
        stmt = select(Checkin)
        if hospital_id:
            from sqlalchemy import join
            patient_stmt = select(Patient.id).filter(Patient.hospital_id == uuid.UUID(hospital_id))
            patient_result = await self.db.execute(patient_stmt)
            patient_ids = [r[0] for r in patient_result.fetchall()]
            stmt = stmt.filter(Checkin.patient_id.in_(patient_ids))

        result = await self.db.execute(stmt)
        checkins = result.scalars().all()

        # Count by method
        method_counts = {}
        for c in checkins:
            method = c.method or "unknown"
            method_counts[method] = method_counts.get(method, 0) + 1

        return {
            "method_distribution": method_counts,
            "total_checkins": len(checkins),
        }

    async def get_alert_analytics(self, hospital_id: str = None) -> Dict[str, Any]:
        """Get alert analytics"""
        stmt = select(Alert)

        if hospital_id:
            from sqlalchemy import join
            patient_stmt = select(Patient.id).filter(Patient.hospital_id == uuid.UUID(hospital_id))
            patient_result = await self.db.execute(patient_stmt)
            patient_ids = [r[0] for r in patient_result.fetchall()]
            stmt = stmt.filter(Alert.patient_id.in_(patient_ids))

        result = await self.db.execute(stmt)
        alerts = result.scalars().all()

        # Count by status
        status_counts = {}
        for a in alerts:
            status = a.status or "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "status_distribution": status_counts,
            "total_alerts": len(alerts),
        }

    async def get_asha_workload(self) -> List[Dict[str, Any]]:
        """Get ASHA workload metrics"""
        # Get all ASHAs
        asha_stmt = select(ASHAWorker)
        asha_result = await self.db.execute(asha_stmt)
        ashas = asha_result.scalars().all()

        workload = []
        for asha in ashas:
            # Count patients
            patient_stmt = select(Patient).filter(Patient.assigned_asha_id == asha.id)
            patient_result = await self.db.execute(patient_stmt)
            patients = patient_result.scalars().all()

            # Count open alerts
            alert_stmt = select(Alert).filter(
                Alert.patient_id.in_([p.id for p in patients]),
                Alert.status != "resolved",
            )
            alert_result = await self.db.execute(alert_stmt)
            open_alerts = len(alert_result.scalars().all())

            # Count critical patients
            critical_stmt = select(Patient).filter(
                Patient.assigned_asha_id == asha.id,
                Patient.risk_level == "critical",
            )
            critical_result = await self.db.execute(critical_stmt)
            critical_patients = critical_result.scalars().all()

            workload.append({
                "asha_id": str(asha.id),
                "asha_name": asha.name,
                "total_patients": len(patients),
                "critical_patients": len(critical_patients),
                "warning_patients": len([p for p in patients if p.risk_level == "warning"]),
                "stable_patients": len([p for p in patients if p.risk_level == "normal"]),
                "open_alerts": open_alerts,
            })

        return workload

    async def get_trends(self, hospital_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get trend data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Risk trend
        risk_stmt = select(RiskRecord)
        if hospital_id:
            from sqlalchemy import join
            patient_stmt = select(Patient.id).filter(Patient.hospital_id == uuid.UUID(hospital_id))
            patient_result = await self.db.execute(patient_stmt)
            patient_ids = [r[0] for r in patient_result.fetchall()]
            risk_stmt = risk_stmt.filter(RiskRecord.patient_id.in_(patient_ids))
        risk_stmt = risk_stmt.filter(
            RiskRecord.created_at >= start_date,
            RiskRecord.created_at <= end_date,
        )

        result = await self.db.execute(risk_stmt)
        risk_records = result.scalars().all()

        # Daily risk counts
        daily_risks = {}
        for r in risk_records:
            date = r.created_at.strftime("%Y-%m-%d")
            daily_risks[date] = daily_risks.get(date, {"normal": 0, "warning": 0, "critical": 0})
            daily_risks[date][r.risk_level or "normal"] += 1

        return {
            "risk_trend": daily_risks,
            "total_evaluations": len(risk_records),
        }
