import uuid
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, or_

from ...db.models.patient import Patient
from ...db.models.checkin import Checkin
from ...db.models.asha import ASHAWorker
from ...db.models.user import User
from ...db.models.alert import Alert
from ...db.models.call import Call
from ...db.models.risk import RiskRecord
from ..risk.service import RiskEngineService

SYMPTOM_MAP = {
    "chest pain": "chest_pain",
    "pain in chest": "chest_pain",
    "chest discomfort": "chest_pain",
    "chest pain is worse": "chest_pain",
    "severe chest pain": "chest_pain",

    "breathing difficulty": "breathing_difficulty",
    "shortness of breath": "breathing_difficulty",
    "difficulty breathing": "breathing_difficulty",
    "breathlessness": "breathing_difficulty",
    "trouble breathing": "breathing_difficulty",

    "weakness": "weakness",
    "feeling weak": "weakness",
    "body weakness": "weakness",
    "extreme weakness": "weakness",

    "dizziness": "dizziness",
    "dizzy": "dizziness",
    "feeling dizzy": "dizziness",
    "head spinning": "dizziness",

    "fever": "fever",
    "high fever": "high_fever",
    "temperature": "fever",
    "high temperature": "high_fever",

    "bleeding": "bleeding",
    "unconsciousness": "unconsciousness",
    "fainted": "unconsciousness",
    "passed out": "unconsciousness",
    "seizure": "seizure",
    "convulsions": "seizure",
    "stroke": "stroke_symptoms",
    "stroke_symptoms": "stroke_symptoms",

    "headache": "headache",
    "cough": "cough",
    "vomiting": "vomiting",
    "diarrhea": "diarrhea",
    "severe pain": "severe_pain",
    "fatigue": "fatigue",
    "dehydration": "dehydration",
}

SYMPTOM_DISPLAY_NAMES = {
    "chest_pain": "Chest Pain",
    "breathing_difficulty": "Breathing Difficulty",
    "weakness": "Weakness",
    "dizziness": "Dizziness",
    "fever": "Fever",
    "high_fever": "High Fever",
    "bleeding": "Bleeding",
    "unconsciousness": "Unconsciousness",
    "seizure": "Seizure",
    "stroke_symptoms": "Stroke Symptoms",
    "headache": "Headache",
    "cough": "Cough",
    "vomiting": "Vomiting",
    "diarrhea": "Diarrhea",
    "severe_pain": "Severe Pain",
    "fatigue": "Fatigue",
    "dehydration": "Dehydration",
}


def normalize_symptoms(input_text: str = "", explicit_symptoms: Optional[List[str]] = None) -> List[str]:
    """Extract canonical symptom keys from text and explicit symptom lists."""
    extracted = set()
    if explicit_symptoms:
        for sym in explicit_symptoms:
            sym_clean = str(sym).strip().lower().replace(" ", "_")
            if sym_clean in SYMPTOM_DISPLAY_NAMES:
                extracted.add(sym_clean)
            elif sym.lower() in SYMPTOM_MAP:
                extracted.add(SYMPTOM_MAP[sym.lower()])

    if input_text:
        text_lower = input_text.lower()
        for phrase, canonical_key in SYMPTOM_MAP.items():
            if phrase in text_lower:
                extracted.add(canonical_key)

    return list(extracted)


class ClinicalPipelineService:
    """Unified Clinical & Risk Pipeline Service for Patient & ASHA inputs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.risk_service = RiskEngineService(db)

    async def process_clinical_input(
        self,
        patient_id: str,
        reporter: str,  # "patient" or "asha"
        input_text: str = "",
        explicit_symptoms: Optional[List[str]] = None,
        asha_worker_id: Optional[str] = None,
        method: str = "app",
    ) -> Dict[str, Any]:
        """
        Process clinical input from Patient or ASHA:
        1. Extract/normalize symptoms
        2. Create Checkin observation record in PostgreSQL
        3. Consolidate combined active symptoms
        4. Evaluate risk via deterministic rules
        5. Persist RiskRecord, Patient risk_level, and trigger Alerts if warning/critical
        """
        canonical_symptoms = normalize_symptoms(input_text, explicit_symptoms)

        formatted_input = f"[REPORTER:{reporter}] {input_text or ', '.join(explicit_symptoms or [])}"
        # 2. Persist Checkin record
        checkin = Checkin(
            id=uuid.uuid4(),
            patient_id=uuid.UUID(patient_id),
            asha_worker_id=uuid.UUID(asha_worker_id) if asha_worker_id else None,
            method=method,
            input_type="text" if input_text else "structured",
            raw_input=formatted_input,
            status="completed",
            created_at=datetime.utcnow(),
        )
        self.db.add(checkin)
        await self.db.flush()

        # Update last_check_in_id on Patient
        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_res = await self.db.execute(patient_stmt)
        patient = patient_res.scalar_one_or_none()
        if patient:
            patient.last_check_in_id = checkin.id

        await self.db.commit()

        # 3. Retrieve all historical check-ins to build consolidated combined symptoms
        checkin_stmt = (
            select(Checkin)
            .filter(Checkin.patient_id == uuid.UUID(patient_id))
            .order_by(Checkin.created_at.desc())
        )
        checkin_res = await self.db.execute(checkin_stmt)
        all_checkins = checkin_res.scalars().all()

        active_symptom_keys = set()
        for c in all_checkins:
            if c.raw_input:
                extracted = normalize_symptoms(c.raw_input)
                active_symptom_keys.update(extracted)

        # Ensure current symptoms are included
        active_symptom_keys.update(canonical_symptoms)

        # 4. Evaluate risk using deterministic rules
        patient_age = None
        if patient and patient.date_of_birth:
            today = datetime.utcnow().date()
            patient_age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )

        await self.risk_service.evaluate_risk(
            patient_id=patient_id,
            symptoms=list(active_symptom_keys),
            patient_age=patient_age,
        )

        return await self.get_patient_clinical_profile(patient_id)

    async def get_patient_clinical_profile(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full clinical profile for Patient, ASHA, or Hospital view."""
        try:
            p_uuid = uuid.UUID(patient_id)
        except Exception:
            return None

        stmt = select(Patient).filter(Patient.id == p_uuid)
        res = await self.db.execute(stmt)
        patient = res.scalar_one_or_none()
        if not patient:
            return None

        # Fetch ASHA Worker Info
        asha_info = None
        if patient.assigned_asha_id:
            asha_stmt = select(ASHAWorker).filter(ASHAWorker.id == patient.assigned_asha_id)
            asha_res = await self.db.execute(asha_stmt)
            asha_obj = asha_res.scalar_one_or_none()
            if asha_obj:
                asha_info = {
                    "id": str(asha_obj.id),
                    "full_name": asha_obj.name,
                    "phone": asha_obj.phone,
                    "district": asha_obj.district,
                }
            else:
                user_stmt = select(User).filter(User.asha_worker_id == patient.assigned_asha_id)
                user_res = await self.db.execute(user_stmt)
                user_obj = user_res.scalar_one_or_none()
                if user_obj:
                    asha_info = {
                        "id": str(patient.assigned_asha_id),
                        "full_name": user_obj.full_name,
                        "phone": user_obj.phone,
                        "district": patient.district or "Mandya",
                    }

        # Fetch Checkins
        c_stmt = select(Checkin).filter(Checkin.patient_id == p_uuid).order_by(Checkin.created_at.asc())
        c_res = await self.db.execute(c_stmt)
        checkins = c_res.scalars().all()

        # Build combined symptoms with individual observations
        symptoms_map = {}
        patient_obs = []
        asha_obs = []

        for c in checkins:
            text = c.raw_input or ""
            reporter = "patient"
            if "[REPORTER:asha]" in text:
                reporter = "asha"
                text = text.replace("[REPORTER:asha]", "").strip()
            elif "[REPORTER:patient]" in text:
                reporter = "patient"
                text = text.replace("[REPORTER:patient]", "").strip()
            elif c.asha_worker_id:
                reporter = "asha"

            c_time = c.created_at.isoformat() if c.created_at else datetime.utcnow().isoformat()
            syms = normalize_symptoms(text)

            for sym in syms:
                obs_entry = {
                    "reporter": reporter,
                    "timestamp": c_time,
                    "original_wording": text,
                }
                if reporter == "patient":
                    patient_obs.append({"symptom": sym, **obs_entry})
                else:
                    asha_obs.append({"symptom": sym, **obs_entry})

                if sym not in symptoms_map:
                    symptoms_map[sym] = {
                        "symptom_key": sym,
                        "symptom_name": SYMPTOM_DISPLAY_NAMES.get(sym, sym.replace("_", " ").title()),
                        "observations": [],
                    }
                symptoms_map[sym]["observations"].append(obs_entry)

        combined_symptoms = list(symptoms_map.values())

        # Fetch Risk History
        r_stmt = select(RiskRecord).filter(RiskRecord.patient_id == p_uuid).order_by(desc(RiskRecord.created_at))
        r_res = await self.db.execute(r_stmt)
        risk_records = r_res.scalars().all()

        latest_risk = None
        if risk_records:
            latest_risk = risk_records[0].to_dict(include_full=True)

        risk_history = [r.to_dict(include_full=True) for r in risk_records]

        # Fetch Alerts
        a_stmt = select(Alert).filter(Alert.patient_id == p_uuid).order_by(desc(Alert.created_at))
        a_res = await self.db.execute(a_stmt)
        alerts = [a.to_dict(include_full=True) for a in a_res.scalars().all()]

        # Fetch Calls
        call_stmt = select(Call).filter(Call.patient_id == p_uuid).order_by(desc(Call.created_at))
        call_res = await self.db.execute(call_stmt)
        calls = [c.to_dict(include_full=True) for c in call_res.scalars().all()]

        age = None
        if patient.date_of_birth:
            today = datetime.utcnow().date()
            age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )

        return {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
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
            "hospital_id": str(patient.hospital_id) if patient.hospital_id else None,
            "assigned_asha_id": str(patient.assigned_asha_id) if patient.assigned_asha_id else None,
            "asha_worker": asha_info,
            "risk_level": patient.risk_level or "normal",
            "combined_symptoms": combined_symptoms,
            "patient_symptoms": patient_obs,
            "asha_symptoms": asha_obs,
            "latest_risk": latest_risk,
            "risk_history": risk_history,
            "alerts": alerts,
            "checkins": [c.to_dict(include_full=True) for c in checkins],
            "calls": calls,
            "created_at": patient.created_at.isoformat() if patient.created_at else None,
        }
