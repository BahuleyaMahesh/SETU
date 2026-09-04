from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
import uuid

from fastapi import Depends

from ...db.models.patient import Patient
from ...db.models.user import User
from ...db.models.asha import ASHAWorker
from ...db.models.assignment import Assignment
from ...core.config import settings
from ...core.dependencies import get_db


class PatientService:
    """Patient management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_patient(
        self,
        mrn: str,
        full_name: str,
        date_of_birth: datetime,
        gender: str,
        phone: str,
        address: str,
        village: str,
        district: str,
        state: str,
        pincode: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        hospital_id: Optional[str] = None,
        assigned_asha_id: Optional[str] = None,
    ) -> Patient:
        """Create new patient"""
        patient = Patient(
            id=uuid.uuid4(),
            mrn=mrn,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender.upper()[:1],
            phone=phone,
            address=address,
            village=village,
            district=district,
            state=state,
            pincode=pincode,
            latitude=latitude,
            longitude=longitude,
            hospital_id=uuid.UUID(hospital_id) if hospital_id else None,
            assigned_asha_id=uuid.UUID(assigned_asha_id) if assigned_asha_id else None,
            risk_level="normal",
        )
        self.db.add(patient)
        await self.db.commit()
        return patient

    async def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID"""
        stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        result = await self.db.execute(stmt)
        patient = result.scalar_one_or_none()

        if not patient:
            return None

        return {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "age": self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": patient.gender,
            "phone": patient.phone,
            "address": patient.address,
            "village": patient.village,
            "district": patient.district,
            "state": patient.state,
            "pincode": patient.pincode,
            "latitude": patient.latitude,
            "longitude": patient.longitude,
            "hospital_id": str(patient.hospital_id) if patient.hospital_id else None,
            "assigned_asha_id": str(patient.assigned_asha_id) if patient.assigned_asha_id else None,
            "risk_level": patient.risk_level,
            "created_at": patient.created_at.isoformat(),
        }

    async def get_patients(
        self,
        hospital_id: Optional[str] = None,
        asha_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get patients with filters"""
        stmt = select(Patient)

        if hospital_id:
            stmt = stmt.filter(Patient.hospital_id == uuid.UUID(hospital_id))
        if asha_id:
            stmt = stmt.filter(Patient.assigned_asha_id == uuid.UUID(asha_id))
        if risk_level:
            stmt = stmt.filter(Patient.risk_level == risk_level)
        if search:
            stmt = stmt.filter(
                or_(
                    Patient.full_name.ilike(f"%{search}%"),
                    Patient.mrn.ilike(f"%{search}%"),
                    Patient.phone.ilike(f"%{search}%"),
                )
            )

        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        patients = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "mrn": p.mrn,
                "full_name": p.full_name,
                "age": self._calculate_age(p.date_of_birth) if p.date_of_birth else None,
                "gender": p.gender,
                "phone": p.phone,
                "village": p.village,
                "risk_level": p.risk_level,
                "last_checkin": p.last_checkin.isoformat() if p.last_checkin else None,
            }
            for p in patients
        ]

    async def update_patient(
        self,
        patient_id: str,
        **fields,
    ) -> Optional[Dict[str, Any]]:
        """Update patient"""
        stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        result = await self.db.execute(stmt)
        patient = result.scalar_one_or_none()

        if not patient:
            return None

        for field, value in fields.items():
            if hasattr(patient, field) and field != "id":
                setattr(patient, field, value)

        await self.db.commit()
        return await self.get_patient(patient_id)

    async def assign_asha(
        self,
        patient_id: str,
        asha_id: str,
        assigned_by_id: str,
    ) -> Dict[str, Any]:
        """Assign ASHA to patient"""
        # Check existing assignment
        assignment_stmt = select(Assignment).filter(
            Assignment.patient_id == uuid.UUID(patient_id),
            Assignment.is_active == True,
        )
        assignment_result = await self.db.execute(assignment_stmt)
        existing = assignment_result.scalar_one_or_none()

        if existing:
            existing.is_active = False

        # Create new assignment
        assignment = Assignment(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            asha_worker_id=uuid.UUID(asha_id),
            assigned_by_id=uuid.UUID(assigned_by_id),
            assigned_at=datetime.utcnow(),
            is_active=True,
        )
        self.db.add(assignment)

        # Update patient
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_result = await self.db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        if patient:
            patient.assigned_asha_id = uuid.UUID(asha_id)

        await self.db.commit()

        return {"success": True}

    async def get_asha_patients(
        self,
        asha_id: str,
        risk_level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get patients assigned to ASHA"""
        patients = await self.get_patients(
            asha_id=asha_id,
            risk_level=risk_level,
        )
        return patients

    async def get_patients_by_hospital(
        self,
        hospital_id: str,
        risk_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get patients by hospital with optional risk filter"""
        return await self.get_patients(
            hospital_id=hospital_id,
            risk_level=risk_filter,
        )

    async def get_patients_by_asha(
        self,
        asha_id: str,
    ) -> List[Dict[str, Any]]:
        """Get patients by ASHA"""
        return await self.get_patients(
            asha_id=asha_id,
        )

    def _calculate_age(self, dob: datetime) -> int:
        """Calculate age from date of birth"""
        today = datetime.utcnow().date()
        birth_date = dob.date() if hasattr(dob, 'date') else dob
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )


async def get_patient_service(db=Depends(get_db)):
    """Dependency provider for PatientService"""
    return PatientService(db)
