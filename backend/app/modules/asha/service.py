from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from fastapi import HTTPException, status

from ...db.models.asha import ASHAWorker
from ...db.models.patient import Patient
from ...db.models.alert import Alert
from ...db.models.checkin import Checkin
from ...db.models.user import User
from ...db.models.hospital import Hospital
from ...db.models.assignment import Assignment
from ...core.security import hash_password
from ...core.config import settings


class ASHAService:
    """ASHA worker service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _calculate_age(self, dob: datetime) -> int:
        today = datetime.utcnow().date()
        birth_date = dob.date() if hasattr(dob, 'date') else dob
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )

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
        """Get ASHA caseload summary using identical patient dataset resolution as get_asha_patients."""
        try:
            asha_uuid = uuid.UUID(asha_id)
            patients_stmt = select(Patient).filter(Patient.assigned_asha_id == asha_uuid)
        except Exception:
            patients_stmt = select(Patient)

        if hospital_id:
            try:
                patients_stmt = patients_stmt.filter(Patient.hospital_id == uuid.UUID(hospital_id))
            except Exception:
                pass

        patients_result = await self.db.execute(patients_stmt)
        patients = patients_result.scalars().all()

        risk_counts = {"normal": 0, "warning": 0, "critical": 0}
        for p in patients:
            level = (p.risk_level or "normal").lower()
            if level in risk_counts:
                risk_counts[level] += 1
            else:
                risk_counts["normal"] += 1

        alerts_stmt = select(Alert).filter(
            Alert.patient_id.in_([p.id for p in patients]) if patients else False,
            Alert.status != "resolved",
        )
        open_alerts = 0
        if patients:
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
        """Get patients for ASHA with full patient attributes"""
        try:
            asha_uuid = uuid.UUID(asha_id)
            patients_stmt = select(Patient).filter(Patient.assigned_asha_id == asha_uuid)
        except Exception:
            patients_stmt = select(Patient)

        if hospital_id:
            try:
                patients_stmt = patients_stmt.filter(Patient.hospital_id == uuid.UUID(hospital_id))
            except Exception:
                pass

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
                "age": self._calculate_age(p.date_of_birth) if p.date_of_birth else None,
                "gender": p.gender,
                "phone": p.phone,
                "address": p.address,
                "village": p.village,
                "district": p.district,
                "state": p.state,
                "pincode": p.pincode,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "risk_level": p.risk_level,
                "hospital_id": str(p.hospital_id) if p.hospital_id else None,
                "assigned_asha_id": str(p.assigned_asha_id) if p.assigned_asha_id else None,
                "last_checkin": (
                    last_checkin_at[p.last_check_in_id].isoformat()
                    if p.last_check_in_id and p.last_check_in_id in last_checkin_at
                    else None
                ),
            }
            for p in patients
        ]

    async def create_asha_patient(
        self,
        creator_user: User,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new patient transactionally by authenticated ASHA worker"""
        from ...db.models.user import User
        from ...db.models.hospital import Hospital
        from ...db.models.assignment import Assignment
        from ...core.security import hash_password

        # ASHA workers must have their own asha_worker_id (this is their
        # caseload). Hospital/admin callers legitimately have none — the
        # patient is created unassigned, matching the existing "Unassign /
        # reassign" pattern already used elsewhere in the roster UI, rather
        # than requiring hospital staff to pick an ASHA up front.
        asha_uuid = creator_user.asha_worker_id
        if creator_user.role == "asha" and not asha_uuid:
            raise HTTPException(status_code=400, detail="User has no assigned ASHA worker ID")

        # Determine hospital_id
        hospital_uuid = creator_user.hospital_id
        if not hospital_uuid:
            h_stmt = select(Hospital).limit(1)
            h_res = await self.db.execute(h_stmt)
            h_obj = h_res.scalar_one_or_none()
            if not h_obj:
                h_obj = Hospital(
                    id=uuid.uuid4(),
                    name="General Hospital",
                    code=f"HOSP-{uuid.uuid4().hex[:6].upper()}",
                    type="District",
                    district="Mandya",
                    state="Karnataka",
                )
                self.db.add(h_obj)
                await self.db.flush()
            hospital_uuid = h_obj.id

        phone = data.get("phone", "").strip()
        email = data.get("email")
        if not email:
            clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "")
            email = f"patient_{clean_phone or uuid.uuid4().hex[:8]}@setu.local"

        password = data.get("password") or "Patient@123"

        dob = None
        age = data.get("age")
        if age:
            try:
                today = datetime.utcnow().date()
                dob = today.replace(year=today.year - int(age))
            except Exception:
                dob = None

        # Create new Patient
        patient_id = uuid.uuid4()
        patient = Patient(
            id=patient_id,
            mrn=f"MRN-{uuid.uuid4().hex[:8].upper()}",
            full_name=data.get("full_name"),
            date_of_birth=dob,
            gender=data.get("gender", "Male"),
            phone=phone,
            address=data.get("address"),
            village=data.get("village"),
            district=data.get("district"),
            state=data.get("state") or "Karnataka",
            pincode=data.get("pincode"),
            latitude=float(data["latitude"]) if data.get("latitude") is not None else None,
            longitude=float(data["longitude"]) if data.get("longitude") is not None else None,
            hospital_id=hospital_uuid,
            assigned_asha_id=asha_uuid,
            risk_level="normal",
        )
        self.db.add(patient)
        await self.db.flush()

        # Check existing user
        user_stmt = select(User).filter(
            (User.email == email) | (User.phone == phone if phone else False)
        )
        user_res = await self.db.execute(user_stmt)
        existing_user = user_res.scalar_one_or_none()

        if existing_user:
            existing_user.patient_id = patient.id
            existing_user.hospital_id = hospital_uuid
            existing_user.asha_worker_id = asha_uuid
            if data.get("full_name"):
                existing_user.full_name = data.get("full_name")
        else:
            new_user = User(
                id=uuid.uuid4(),
                email=email,
                hashed_password=hash_password(password),
                full_name=data.get("full_name"),
                phone=phone,
                role="patient",
                is_active=True,
                patient_id=patient.id,
                hospital_id=hospital_uuid,
                asha_worker_id=asha_uuid,
            )
            self.db.add(new_user)

        # Assignment.asha_worker_id is NOT NULL — an assignment IS the
        # ASHA-patient link, so there's nothing to create when the patient
        # has no ASHA yet (hospital-created, unassigned).
        if asha_uuid:
            assign = Assignment(
                id=uuid.uuid4(),
                patient_id=patient.id,
                asha_worker_id=asha_uuid,
                assigned_by_id=creator_user.id,
                assigned_at=datetime.utcnow(),
                is_active=True,
            )
            self.db.add(assign)

        condition = data.get("condition")
        symptoms = data.get("symptoms")
        if condition or symptoms:
            raw_text = f"Condition: {condition or 'N/A'}. Symptoms: {symptoms or 'N/A'}"
            from ..clinical.service import ClinicalPipelineService
            clinical_service = ClinicalPipelineService(self.db)
            await clinical_service.process_clinical_input(
                patient_id=str(patient.id),
                reporter="asha" if creator_user.role == "asha" else "hospital",
                input_text=raw_text,
                # str(None) is the literal string "None", which uuid.UUID()
                # can't parse — pass real None through when there's no ASHA.
                asha_worker_id=str(asha_uuid) if asha_uuid else None,
                method="in_person",
            )
        else:
            await self.db.commit()

        return {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "full_name": patient.full_name,
            "gender": patient.gender,
            "phone": patient.phone,
            "address": patient.address,
            "village": patient.village,
            "district": patient.district,
            "state": patient.state,
            "pincode": patient.pincode,
            "latitude": patient.latitude,
            "longitude": patient.longitude,
            "risk_level": patient.risk_level,
            "assigned_asha_id": str(patient.assigned_asha_id) if patient.assigned_asha_id else None,
        }

    async def add_patient(
        self,
        asha_id: str,
        data: Dict[str, Any],
        creator_user: User,
    ) -> Dict[str, Any]:
        """Add a new patient transactionally by ASHA worker."""
        asha_uuid = None
        try:
            if asha_id and asha_id not in ("default", "me", "undefined"):
                asha_uuid = uuid.UUID(asha_id)
        except Exception:
            asha_uuid = None

        if not asha_uuid and creator_user.asha_worker_id:
            asha_uuid = creator_user.asha_worker_id

        asha = None
        if asha_uuid:
            asha_stmt = select(ASHAWorker).filter(ASHAWorker.id == asha_uuid)
            asha_res = await self.db.execute(asha_stmt)
            asha = asha_res.scalar_one_or_none()

        if not asha:
            first_stmt = select(ASHAWorker).limit(1)
            first_res = await self.db.execute(first_stmt)
            asha = first_res.scalar_one_or_none()

        if not asha:
            asha_uuid = uuid.uuid4()
            asha = ASHAWorker(
                id=asha_uuid,
                name=creator_user.full_name or "ASHA Worker",
                asha_id=f"ASHA-{uuid.uuid4().hex[:8].upper()}",
                phone=creator_user.phone or "+91-9876543210",
                district="Mandya",
                block="Rural Block A",
                assigned_villages=["Village Alpha"],
            )
            self.db.add(asha)
            await self.db.flush()
        else:
            asha_uuid = asha.id

        # Determine hospital_id
        hospital_uuid = None
        if data.get("hospital_id"):
            hospital_uuid = uuid.UUID(data["hospital_id"])
        elif creator_user.hospital_id:
            hospital_uuid = creator_user.hospital_id
        else:
            h_stmt = select(Hospital).limit(1)
            h_res = await self.db.execute(h_stmt)
            h_obj = h_res.scalar_one_or_none()
            if not h_obj:
                h_obj = Hospital(
                    id=uuid.uuid4(),
                    name="General Hospital",
                    code=f"HOSP-{uuid.uuid4().hex[:6].upper()}",
                    type="District",
                    district=asha.district or "Unknown",
                    state="Karnataka",
                )
                self.db.add(h_obj)
                await self.db.flush()
            hospital_uuid = h_obj.id

        phone = data.get("phone", "").strip()
        email = data.get("email")
        if not email:
            clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "")
            email = f"patient_{clean_phone or uuid.uuid4().hex[:8]}@setu.local"

        password = data.get("password") or "Patient@123"

        # Check if existing patient exists by ID, phone, or email
        existing_patient = None
        if data.get("patient_id"):
            p_stmt = select(Patient).filter(Patient.id == uuid.UUID(data["patient_id"]))
            p_res = await self.db.execute(p_stmt)
            existing_patient = p_res.scalar_one_or_none()

        if not existing_patient and (phone or email):
            user_stmt = select(User).filter(
                (User.email == email if email else False) |
                (User.phone == phone if phone else False)
            )
            user_res = await self.db.execute(user_stmt)
            existing_user = user_res.scalar_one_or_none()
            if existing_user and existing_user.patient_id:
                p_stmt = select(Patient).filter(Patient.id == existing_user.patient_id)
                p_res = await self.db.execute(p_stmt)
                existing_patient = p_res.scalar_one_or_none()

        if not existing_patient and phone:
            p_stmt = select(Patient).filter(Patient.phone == phone)
            p_res = await self.db.execute(p_stmt)
            existing_patient = p_res.scalar_one_or_none()

        dob = None
        age = data.get("age")
        if age:
            today = datetime.utcnow().date()
            dob = today.replace(year=today.year - int(age))

        if existing_patient:
            # Update fields if provided
            if data.get("full_name"):
                existing_patient.full_name = data["full_name"]
            if dob:
                existing_patient.date_of_birth = dob
            if data.get("gender"):
                existing_patient.gender = data["gender"]
            if phone:
                existing_patient.phone = phone
            if data.get("address"):
                existing_patient.address = data["address"]
            if data.get("village"):
                existing_patient.village = data["village"]
            if data.get("district"):
                existing_patient.district = data["district"]
            if data.get("state"):
                existing_patient.state = data["state"]
            if data.get("pincode"):
                existing_patient.pincode = data["pincode"]
            if data.get("latitude") is not None:
                existing_patient.latitude = float(data["latitude"])
            if data.get("longitude") is not None:
                existing_patient.longitude = float(data["longitude"])
            if hospital_uuid:
                existing_patient.hospital_id = hospital_uuid

            existing_patient.assigned_asha_id = asha_uuid

            # Ensure active assignment
            assign_stmt = select(Assignment).filter(
                Assignment.patient_id == existing_patient.id,
                Assignment.asha_worker_id == asha_uuid,
                Assignment.is_active == True,
            )
            assign_res = await self.db.execute(assign_stmt)
            if not assign_res.scalar_one_or_none():
                assign = Assignment(
                    id=uuid.uuid4(),
                    patient_id=existing_patient.id,
                    asha_worker_id=asha_uuid,
                    assigned_by_id=creator_user.id,
                    assigned_at=datetime.utcnow(),
                    is_active=True,
                )
                self.db.add(assign)

            # Record symptoms/condition check-in if provided
            condition = data.get("condition")
            symptoms = data.get("symptoms")
            if condition or symptoms:
                raw_text = f"Condition: {condition or 'N/A'}. Symptoms: {symptoms or 'N/A'}"
                checkin = Checkin(
                    id=uuid.uuid4(),
                    patient_id=existing_patient.id,
                    asha_worker_id=asha_uuid,
                    hospital_id=hospital_uuid,
                    method="in_person",
                    input_type="text",
                    raw_input=raw_text,
                    transcript=raw_text,
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    status="completed",
                )
                self.db.add(checkin)
                await self.db.flush()
                existing_patient.last_check_in_id = checkin.id

            await self.db.commit()

            return {
                "id": str(existing_patient.id),
                "mrn": existing_patient.mrn,
                "full_name": existing_patient.full_name,
                "age": self._calculate_age(existing_patient.date_of_birth) if existing_patient.date_of_birth else age,
                "gender": existing_patient.gender,
                "phone": existing_patient.phone,
                "address": existing_patient.address,
                "village": existing_patient.village,
                "district": existing_patient.district,
                "state": existing_patient.state,
                "pincode": existing_patient.pincode,
                "latitude": existing_patient.latitude,
                "longitude": existing_patient.longitude,
                "risk_level": existing_patient.risk_level,
                "hospital_id": str(existing_patient.hospital_id) if existing_patient.hospital_id else None,
                "assigned_asha_id": str(existing_patient.assigned_asha_id) if existing_patient.assigned_asha_id else None,
                "updated": True,
            }

        patient_id = uuid.uuid4()
        patient = Patient(
            id=patient_id,
            mrn=f"MRN-{uuid.uuid4().hex[:8].upper()}",
            full_name=data.get("full_name"),
            date_of_birth=dob,
            gender=data.get("gender", "Male"),
            phone=phone,
            address=data.get("address"),
            village=data.get("village") or (asha.assigned_villages[0] if asha.assigned_villages else "Rural Village"),
            district=data.get("district") or asha.district or "District",
            state=data.get("state") or "Karnataka",
            pincode=data.get("pincode"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            hospital_id=hospital_uuid,
            assigned_asha_id=asha_uuid,
            risk_level="normal",
        )
        self.db.add(patient)
        await self.db.flush()

        # Prevent User table email/phone duplicate key constraint violation
        user_stmt = select(User).filter(
            (User.email == email) | (User.phone == phone if phone else False)
        )
        user_res = await self.db.execute(user_stmt)
        existing_user = user_res.scalar_one_or_none()

        if existing_user:
            existing_user.patient_id = patient.id
            existing_user.hospital_id = hospital_uuid
            existing_user.asha_worker_id = asha_uuid
            if data.get("full_name"):
                existing_user.full_name = data.get("full_name")
        else:
            new_user = User(
                id=uuid.uuid4(),
                email=email,
                hashed_password=hash_password(password),
                full_name=data.get("full_name"),
                phone=phone,
                role="patient",
                is_active=True,
                patient_id=patient.id,
                hospital_id=hospital_uuid,
                asha_worker_id=asha_uuid,
            )
            self.db.add(new_user)

        assign = Assignment(
            id=uuid.uuid4(),
            patient_id=patient.id,
            asha_worker_id=asha_uuid,
            assigned_by_id=creator_user.id,
            assigned_at=datetime.utcnow(),
            is_active=True,
        )
        self.db.add(assign)

        condition = data.get("condition")
        symptoms = data.get("symptoms")
        if condition or symptoms:
            raw_text = f"Condition: {condition or 'N/A'}. Symptoms: {symptoms or 'N/A'}"
            checkin = Checkin(
                id=uuid.uuid4(),
                patient_id=patient.id,
                asha_worker_id=asha_uuid,
                hospital_id=hospital_uuid,
                method="in_person",
                input_type="text",
                raw_input=raw_text,
                transcript=raw_text,
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                status="completed",
            )
            self.db.add(checkin)
            await self.db.flush()
            patient.last_check_in_id = checkin.id

        await self.db.commit()

        return {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "full_name": patient.full_name,
            "age": age,
            "gender": patient.gender,
            "phone": patient.phone,
            "address": patient.address,
            "village": patient.village,
            "district": patient.district,
            "state": patient.state,
            "pincode": patient.pincode,
            "latitude": patient.latitude,
            "longitude": patient.longitude,
            "risk_level": patient.risk_level,
            "hospital_id": str(patient.hospital_id),
            "assigned_asha_id": str(patient.assigned_asha_id),
            "created_at": patient.created_at.isoformat() if patient.created_at else None,
        }

    async def remove_patient(self, asha_id: str, patient_id: str) -> Dict[str, Any]:
        """Unassign patient from ASHA worker (removes active assignment, keeps patient & history)."""
        patient_uuid = uuid.UUID(patient_id)
        asha_uuid = uuid.UUID(asha_id)

        patient_stmt = select(Patient).filter(Patient.id == patient_uuid)
        patient_res = await self.db.execute(patient_stmt)
        patient = patient_res.scalar_one_or_none()

        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        if patient.assigned_asha_id == asha_uuid:
            patient.assigned_asha_id = None

        assign_stmt = select(Assignment).filter(
            Assignment.patient_id == patient_uuid,
            Assignment.asha_worker_id == asha_uuid,
            Assignment.is_active == True,
        )
        assign_res = await self.db.execute(assign_stmt)
        active_assignments = assign_res.scalars().all()

        for assign in active_assignments:
            assign.is_active = False
            assign.ended_at = datetime.utcnow()
            assign.end_reason = "Unassigned by ASHA worker"

        await self.db.commit()
        return {"success": True, "message": "Patient successfully unassigned"}

