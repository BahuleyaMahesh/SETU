from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.asha import ASHAWorker
from ...db.models.patient import Patient
from ...db.models.alert import Alert
from ...db.models.checkin import Checkin
from ...core.config import settings


class ASHAService:
    """ASHA worker service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_asha(self, asha_id: str) -> Optional[Dict[str, Any]]:
        """Get ASHA worker by ID"""
        stmt = select(ASHAWorker).filter(ASHAWorker.id == uuid.UUID(asha_id))
        result = await self.db.execute(stmt)
        asha = result.scalar_one_or_none()

        if not asha:
            return None

        return {
            "id": str(asha.id),
            "asha_id": asha.asha_id,
            "name": asha.name,
            "phone": asha.phone,
            "district": asha.district,
            "block": asha.block,
            "phc_id": asha.phc_id,
            "assigned_villages": asha.assigned_villages,
            "is_active": asha.is_active,
            "created_at": asha.created_at.isoformat(),
        }

    async def get_ashas(
        self,
        district: Optional[str] = None,
        block: Optional[str] = None,
        phc_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get ASHA workers with filters"""
        stmt = select(ASHAWorker)

        if district:
            stmt = stmt.filter(ASHAWorker.district == district)
        if block:
            stmt = stmt.filter(ASHAWorker.block == block)
        if phc_id:
            stmt = stmt.filter(ASHAWorker.phc_id == phc_id)

        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        ashas = result.scalars().all()

        return [
            {
                "id": str(a.id),
                "asha_id": a.asha_id,
                "name": a.name,
                "phone": a.phone,
                "district": a.district,
                "block": a.block,
                "phc_id": a.phc_id,
            }
            for a in ashas
        ]

    async def get_asha_caseload(self, asha_id: str, hospital_id: Optional[str] = None) -> Dict[str, Any]:
        """Get ASHA caseload summary.

        An ASHAWorker isn't tied to a single hospital in the schema — they can
        have patients across several. When called on behalf of a hospital
        user, `hospital_id` scopes the caseload to just that hospital's
        patients so one hospital can't see another's numbers through a
        shared ASHA worker.
        """
        # Get assigned patients
        patients_stmt = select(Patient).filter(Patient.assigned_asha_id == uuid.UUID(asha_id))
        if hospital_id:
            patients_stmt = patients_stmt.filter(Patient.hospital_id == uuid.UUID(hospital_id))
        patients_result = await self.db.execute(patients_stmt)
        patients = patients_result.scalars().all()

        # Count by risk level
        risk_counts = {"normal": 0, "warning": 0, "critical": 0}
        for p in patients:
            level = p.risk_level or "normal"
            risk_counts[level] = risk_counts.get(level, 0) + 1

        # Count open alerts
        alerts_stmt = select(Alert).filter(
            Alert.patient_id.in_([p.id for p in patients]),
            Alert.status != "resolved",
        )
        alerts_result = await self.db.execute(alerts_stmt)
        open_alerts = len(alerts_result.scalars().all())

        return {
            "total_patients": len(patients),
            "stable_patients": risk_counts["normal"],
            "warning_patients": risk_counts["warning"],
            "critical_patients": risk_counts["critical"],
            "open_alerts": open_alerts,
        }

    async def get_asha_patients(
        self,
        asha_id: str,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        hospital_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get patients for ASHA, optionally scoped to one hospital (see get_asha_caseload)"""
        patients_stmt = select(Patient).filter(Patient.assigned_asha_id == uuid.UUID(asha_id))
        if hospital_id:
            patients_stmt = patients_stmt.filter(Patient.hospital_id == uuid.UUID(hospital_id))

        if risk_level:
            patients_stmt = patients_stmt.filter(Patient.risk_level == risk_level)
        if search:
            patients_stmt = patients_stmt.filter(
                Patient.full_name.ilike(f"%{search}%")
            )

        result = await self.db.execute(patients_stmt)
        patients = result.scalars().all()

        checkin_ids = [p.last_check_in_id for p in patients if p.last_check_in_id]
        last_checkin_at = {}
        if checkin_ids:
            checkins_stmt = select(Checkin).filter(Checkin.id.in_(checkin_ids))
            checkins_result = await self.db.execute(checkins_stmt)
            last_checkin_at = {c.id: c.created_at for c in checkins_result.scalars().all()}

        return [
            {
                "id": str(p.id),
                "mrn": p.mrn,
                "full_name": p.full_name,
                "phone": p.phone,
                "village": p.village,
                "risk_level": p.risk_level,
                "last_checkin": (
                    last_checkin_at[p.last_check_in_id].isoformat()
                    if p.last_check_in_id and p.last_check_in_id in last_checkin_at
                    else None
                ),
            }
            for p in patients
        ]
