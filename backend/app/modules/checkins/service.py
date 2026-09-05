from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.checkin import Checkin, CheckInMethod, CheckInInputType
from ...db.models.response import Response
from ...db.models.patient import Patient
from ...core.config import settings


class CheckinService:
    """Check-in service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_checkin(
        self,
        patient_id: str,
        method: str,
        input_type: str,
        responses: Dict[str, Any],
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Create check-in record"""
        checkin = Checkin(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            method=method,
            input_type=input_type,
            raw_input=str(responses),
            status="completed",
            created_at=datetime.utcnow(),
        )
        self.db.add(checkin)

        # Update patient's last check-in
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        if patient:
            patient.last_checkin = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(checkin)

        return {
            "id": str(checkin.id),
            "patient_id": str(checkin.patient_id),
            "method": checkin.method,
            "input_type": checkin.input_type,
            "created_at": checkin.created_at.isoformat(),
        }

    async def get_checkin(self, checkin_id: str) -> Optional[Dict[str, Any]]:
        """Get check-in by ID"""
        stmt = select(Checkin).filter(Checkin.id == uuid.UUID(checkin_id))
        result = await self.db.execute(stmt)
        checkin = result.scalar_one_or_none()

        if not checkin:
            return None

        return {
            "id": str(checkin.id),
            "patient_id": str(checkin.patient_id),
            "method": checkin.method,
            "input_type": checkin.input_type,
            "status": checkin.status,
            "created_at": checkin.created_at.isoformat(),
        }

    async def get_patient_checkins(
        self,
        patient_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get check-ins for patient"""
        stmt = (
            select(Checkin)
            .filter(Checkin.patient_id == uuid.UUID(patient_id))
            .order_by(Checkin.created_at.desc())
            .offset(offset).limit(limit)
        )
        result = await self.db.execute(stmt)
        checkins = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "method": c.method,
                "input_type": c.input_type,
                "responses": c.responses,
                "created_at": c.created_at.isoformat(),
            }
            for c in checkins
        ]

    async def get_latest_checkin(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get latest check-in for patient"""
        stmt = (
            select(Checkin)
            .filter(Checkin.patient_id == uuid.UUID(patient_id))
            .order_by(Checkin.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        checkin = result.scalar_one_or_none()

        if not checkin:
            return None

        return {
            "id": str(checkin.id),
            "method": checkin.method,
            "input_type": checkin.input_type,
            "responses": checkin.responses,
            "created_at": checkin.created_at.isoformat(),
        }

    async def add_response(
        self,
        checkin_id: str,
        question_id: str,
        answer: Any,
        confidence: float = None,
    ) -> Dict[str, Any]:
        """Add response to check-in"""
        stmt = select(Checkin).filter(Checkin.id == uuid.UUID(checkin_id))
        result = await self.db.execute(stmt)
        checkin = result.scalar_one_or_none()

        if not checkin:
            return {"error": "Check-in not found"}

        # Initialize responses if needed
        if not checkin.responses:
            checkin.responses = {}

        checkin.responses[question_id] = {
            "answer": answer,
            "confidence": confidence,
        }
        await self.db.commit()

        return {"success": True, "checkin_id": checkin_id}
