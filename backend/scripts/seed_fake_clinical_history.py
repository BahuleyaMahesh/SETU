"""One-off demo enrichment script — NOT part of the app's runtime code path.

Adds realistic-looking (entirely fabricated) historical checkins, risk
records, resolved alerts, and prescriptions/medications for the existing
demo patients, so pages/buttons that were showing empty states ("no
prescriptions", a single alert with no history, a bare one-line symptom
note) have a fuller, more demo-able trail behind them.

Does not touch any frontend/backend application code — this only inserts
rows into tables the app already reads from, using the app's own models.
Safe to re-run: every block checks for existing rows before inserting.

Run from backend/:  .venv\\Scripts\\python.exe -m scripts.seed_fake_clinical_history
"""
import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.future import select

from app.core.database import async_session
from app.db.models.patient import Patient
from app.db.models.checkin import Checkin
from app.db.models.risk import RiskRecord
from app.db.models.alert import Alert
from app.db.models.prescription import Prescription
from app.db.models.medication import Medication
from app.db.models.user import User
from app.db.models.asha import ASHAWorker

NOW = datetime(2026, 9, 4, 7, 0, 0)


def days_ago(n, hour=9, minute=0):
    return NOW - timedelta(days=n) + timedelta(hours=hour, minutes=minute)


async def get_ids(session):
    asha_user = (await session.execute(select(User).filter(User.email == "asha@setu.com"))).scalar_one()
    hospital_user = (await session.execute(select(User).filter(User.email == "hospital@setu.com"))).scalar_one()
    asha_worker = (await session.execute(select(ASHAWorker).filter(ASHAWorker.asha_id == "ASHA001"))).scalar_one()
    patients = (await session.execute(select(Patient))).scalars().all()
    by_name = {p.full_name: p for p in patients}
    return asha_user, hospital_user, asha_worker, by_name


async def add_checkin_with_risk(
    session, patient, asha_worker, created_at, raw_input, risk_level, risk_score,
    risk_factors, risk_reasons, severity, action_required=None,
):
    existing = await session.execute(
        select(Checkin).filter(Checkin.patient_id == patient.id, Checkin.raw_input == raw_input)
    )
    if existing.scalar_one_or_none():
        return None

    checkin = Checkin(
        id=uuid.uuid4(),
        patient_id=patient.id,
        asha_worker_id=asha_worker.id,
        hospital_id=patient.hospital_id,
        method="in_person",
        input_type="text",
        raw_input=raw_input,
        transcript=raw_input,
        latitude=patient.latitude,
        longitude=patient.longitude,
        status="completed",
        created_at=created_at,
    )
    session.add(checkin)
    await session.flush()

    risk = RiskRecord(
        id=uuid.uuid4(),
        patient_id=patient.id,
        checkin_id=checkin.id,
        asha_worker_id=asha_worker.id,
        risk_level=risk_level,
        risk_score=risk_score,
        risk_factors=risk_factors,
        risk_reasons=risk_reasons,
        severity=severity,
        action_required=action_required,
        alert_metadata={},
        created_at=created_at,
    )
    session.add(risk)
    await session.flush()
    return checkin, risk


async def add_resolved_alert(session, patient, risk, asha_worker, asha_user, created_at, title, description, severity):
    alert = Alert(
        id=uuid.uuid4(),
        patient_id=patient.id,
        risk_record_id=risk.id,
        hospital_id=patient.hospital_id,
        asha_worker_id=asha_worker.id,
        severity=severity,
        risk_level=risk.risk_level,
        alert_type="checkin_risk",
        title=title,
        description=description,
        status="resolved",
        acknowledged_at=created_at + timedelta(hours=2),
        acknowledged_by_id=asha_user.id,
        resolved_at=created_at + timedelta(hours=6),
        resolved_by_id=asha_user.id,
        resolution_notes="ASHA visited home, advised follow-up care. Patient stabilized.",
        alert_metadata={},
        created_at=created_at,
    )
    session.add(alert)


async def add_prescription(session, patient, hospital_user, prescribed_at, meds, notes):
    existing = await session.execute(select(Prescription).filter(Prescription.patient_id == patient.id))
    if existing.scalars().first():
        return
    prescription = Prescription(
        id=uuid.uuid4(),
        patient_id=patient.id,
        document_id=None,
        hospital_id=patient.hospital_id,
        prescribed_by_id=hospital_user.id,
        prescription_date=prescribed_at,
        status="verified",
        verified_at=prescribed_at,
        verified_by_id=hospital_user.id,
        verification_notes=notes,
        alert_metadata={},
        created_at=prescribed_at,
    )
    session.add(prescription)
    await session.flush()

    for m in meds:
        session.add(Medication(
            id=uuid.uuid4(),
            prescription_id=prescription.id,
            patient_id=patient.id,
            medication_name=m["name"],
            dosage=m["dosage"],
            frequency=m["frequency"],
            timing=m.get("timing"),
            duration=m.get("duration"),
            instructions=m.get("instructions"),
            start_date=prescribed_at,
            created_at=prescribed_at,
        ))


async def cleanup_stray_test_data(session, by_name):
    """Remove one known leftover test artifact from an earlier verification
    session: Kavya Nair's risk_level is 'normal', but she has a leftover
    'fell from the roof' checkin + critical alert from testing the trauma-
    keyword chat feature, never cleaned up. Inconsistent with her current
    status, so it gets removed before her real history is added."""
    kavya = by_name.get("Kavya Nair")
    if not kavya:
        return
    stray_checkins = (await session.execute(
        select(Checkin).filter(Checkin.patient_id == kavya.id, Checkin.raw_input.ilike("%fell from the roof%"))
    )).scalars().all()
    for c in stray_checkins:
        risk_records = (await session.execute(
            select(RiskRecord).filter(RiskRecord.checkin_id == c.id)
        )).scalars().all()
        for rr in risk_records:
            alerts = (await session.execute(
                select(Alert).filter(Alert.risk_record_id == rr.id)
            )).scalars().all()
            for a in alerts:
                await session.delete(a)
            await session.delete(rr)
        await session.delete(c)
    if stray_checkins:
        print(f"Cleaned up {len(stray_checkins)} stray test checkin(s) for Kavya Nair")


async def main():
    async with async_session() as session:
        asha_user, hospital_user, asha_worker, by_name = await get_ids(session)

        await cleanup_stray_test_data(session, by_name)
        await session.commit()
        # re-fetch patients after cleanup/flush
        asha_user, hospital_user, asha_worker, by_name = await get_ids(session)

        # Enrich the user's own self-registered "Bright Gamer" patient account
        # so it isn't a dead end when they click around as themselves.
        bg = by_name.get("Bright Gamer")
        if bg and not bg.village:
            bg.village = "Whitefield"
            bg.district = "Bangalore Urban"
            bg.state = "Karnataka"
            bg.pincode = "560066"
            bg.address = "12 Cross, Whitefield Main Road"
            bg.latitude = 12.9698
            bg.longitude = 77.7550
            bg.assigned_asha_id = asha_worker.id
            print("Enriched Bright Gamer's patient profile (village/location/ASHA)")

        await session.commit()

        # ---- Lakshmi Devi: post-cardiac surgery, normal -> warning -> critical ----
        p = by_name["Lakshmi Devi"]
        r1 = await add_checkin_with_risk(
            session, p, asha_worker, days_ago(10),
            "[REPORTER:asha] Condition: Post-cardiac surgery recovery. Symptoms: mild fatigue only, "
            "wound healing well, taking medications as prescribed.",
            "normal", 1.0, ["fatigue"], ["Mild fatigue is expected during early cardiac recovery"], 0,
        )
        r2 = await add_checkin_with_risk(
            session, p, asha_worker, days_ago(5),
            "[REPORTER:asha] Condition: Post-cardiac surgery recovery. Symptoms: occasional chest "
            "discomfort on exertion, mild ankle swelling noted. Follow-up blood test shows hemoglobin "
            "at 10.2 g/dL (mildly low), advised iron supplementation and reduced activity.",
            "warning", 4.5, ["exertional_chest_discomfort", "peripheral_edema", "low_hemoglobin"],
            ["Exertional chest discomfort after cardiac surgery warrants monitoring",
             "Mild ankle swelling can indicate fluid retention", "Hemoglobin below normal range (10.2 g/dL)"],
            2, action_required="Schedule cardiology follow-up within 3 days",
        )
        if r2:
            await add_resolved_alert(
                session, p, r2[1], asha_worker, asha_user, days_ago(5),
                "Warning risk detected", "Exertional chest discomfort and low hemoglobin flagged on follow-up.",
                "medium",
            )
        await add_prescription(
            session, p, hospital_user, days_ago(18, hour=10),
            [
                {"name": "Aspirin", "dosage": "75mg", "frequency": "once daily", "timing": "morning", "duration": 90, "instructions": "Take after food"},
                {"name": "Atorvastatin", "dosage": "20mg", "frequency": "once daily", "timing": "night", "duration": 90},
                {"name": "Metoprolol", "dosage": "25mg", "frequency": "twice daily", "duration": 60},
            ],
            "Post-CABG discharge prescription.",
        )

        # ---- Mahadevaiah H: post-stroke rehab, normal -> warning -> critical ----
        p = by_name["Mahadevaiah H"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(12),
            "[REPORTER:asha] Condition: Post-stroke rehabilitation. Symptoms: attending physiotherapy "
            "sessions regularly, mild residual weakness in left hand, otherwise stable.",
            "normal", 1.5, ["mild_weakness"], ["Residual weakness expected during stroke rehabilitation"], 0,
        )
        r2 = await add_checkin_with_risk(
            session, p, asha_worker, days_ago(6),
            "[REPORTER:asha] Condition: Post-stroke rehabilitation. Symptoms: brief episode of slurred "
            "speech this morning that resolved within minutes. Blood pressure reading 162/102 (elevated). "
            "Advised strict BP monitoring and medication compliance check.",
            "warning", 5.0, ["transient_speech_difficulty", "elevated_blood_pressure"],
            ["Transient neurological symptoms after stroke require close monitoring",
             "Blood pressure significantly above target range (162/102)"],
            2, action_required="Urgent BP recheck and medication review",
        )
        if r2:
            await add_resolved_alert(
                session, p, r2[1], asha_worker, asha_user, days_ago(6),
                "Warning risk detected", "Transient slurred speech and elevated BP flagged.", "medium",
            )
        await add_prescription(
            session, p, hospital_user, days_ago(20, hour=10),
            [
                {"name": "Aspirin", "dosage": "150mg", "frequency": "once daily", "duration": 180},
                {"name": "Atorvastatin", "dosage": "40mg", "frequency": "once daily", "timing": "night", "duration": 180},
                {"name": "Amlodipine", "dosage": "5mg", "frequency": "once daily", "duration": 90},
            ],
            "Post-stroke secondary prevention regimen.",
        )

        # ---- Anjali Reddy: post C-section, normal -> warning -> critical ----
        p = by_name["Anjali Reddy"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(8),
            "[REPORTER:asha] Condition: Post-C-section recovery. Symptoms: wound healing well, "
            "mild soreness, mother and baby both feeding well.",
            "normal", 1.0, ["mild_soreness"], ["Mild incisional soreness is expected post-surgery"], 0,
        )
        r2 = await add_checkin_with_risk(
            session, p, asha_worker, days_ago(3),
            "[REPORTER:asha] Condition: Post-C-section recovery. Symptoms: mild fever (100.4F), "
            "slight redness around incision site. Blood test shows WBC count elevated at 12,400/uL, "
            "suggestive of early localized infection. Advised wound care and started on oral antibiotics.",
            "warning", 4.0, ["low_grade_fever", "wound_redness", "elevated_wbc"],
            ["Low-grade fever with wound redness can indicate early surgical site infection",
             "WBC count above normal range (12,400/uL)"],
            2, action_required="Wound review in 48 hours, escalate if fever persists",
        )
        if r2:
            await add_resolved_alert(
                session, p, r2[1], asha_worker, asha_user, days_ago(3),
                "Warning risk detected", "Low-grade fever and wound redness flagged, antibiotics started.", "medium",
            )
        await add_prescription(
            session, p, hospital_user, days_ago(3, hour=11),
            [
                {"name": "Cefixime", "dosage": "200mg", "frequency": "twice daily", "duration": 7, "instructions": "Complete full course"},
                {"name": "Paracetamol", "dosage": "650mg", "frequency": "as needed for fever", "duration": 5},
                {"name": "Ranitidine", "dosage": "150mg", "frequency": "twice daily", "duration": 7},
            ],
            "Started after wound infection flagged on follow-up visit.",
        )

        # ---- Manjunath Gowda: diabetes post-discharge, normal -> warning -> critical ----
        p = by_name["Manjunath Gowda"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(14),
            "[REPORTER:asha] Condition: Diabetes management post-discharge. Symptoms: none, fasting "
            "blood glucose 118 mg/dL, well controlled on current medication.",
            "normal", 1.0, ["controlled_glucose"], ["Fasting glucose within acceptable range"], 0,
        )
        r2 = await add_checkin_with_risk(
            session, p, asha_worker, days_ago(6),
            "[REPORTER:asha] Condition: Diabetes management post-discharge. Symptoms: fasting blood "
            "glucose risen to 210 mg/dL, mild dizziness after meals reported. Advised diet review and "
            "medication adjustment discussion with hospital.",
            "warning", 4.0, ["hyperglycemia", "post_meal_dizziness"],
            ["Fasting glucose significantly above target (210 mg/dL)", "Dizziness may indicate glucose instability"],
            2, action_required="Diet counseling and glucose recheck in 1 week",
        )
        if r2:
            await add_resolved_alert(
                session, p, r2[1], asha_worker, asha_user, days_ago(6),
                "Warning risk detected", "Rising fasting glucose and post-meal dizziness flagged.", "medium",
            )
        await add_prescription(
            session, p, hospital_user, days_ago(25, hour=10),
            [
                {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily", "duration": 90},
                {"name": "Glimepiride", "dosage": "2mg", "frequency": "once daily", "timing": "morning", "duration": 90},
                {"name": "Insulin Glargine", "dosage": "10 units", "frequency": "once daily", "timing": "bedtime", "duration": 30, "instructions": "Subcutaneous injection"},
            ],
            "Diabetes management post-discharge.",
        )

        # ---- Ravi Kumar S: diabetes + lung infection, normal -> warning (current) ----
        p = by_name["Ravi Kumar S"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(9),
            "[REPORTER:asha] Condition: Diabetes, post-discharge from lung infection. Symptoms: "
            "feeling stable, appetite normal, no fever.",
            "normal", 1.5, ["stable"], ["Patient stable after lung infection discharge"], 0,
        )
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(4),
            "[REPORTER:asha] Condition: Diabetes, post-discharge from lung infection. Symptoms: "
            "mild dry cough returned, no fever, oxygen saturation 97% on home pulse oximeter.",
            "normal", 2.0, ["mild_cough"], ["Mild residual cough without fever, oxygen saturation normal"], 0,
        )
        await add_prescription(
            session, p, hospital_user, days_ago(9, hour=10),
            [
                {"name": "Azithromycin", "dosage": "500mg", "frequency": "once daily", "duration": 3, "instructions": "Complete full course"},
                {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily", "duration": 90},
            ],
            "Discharge prescription following lung infection treatment.",
        )

        # ---- Kavya Nair: post-appendix surgery, normal ----
        p = by_name["Kavya Nair"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(7),
            "[REPORTER:asha] Condition: Post-appendix surgery recovery. Symptoms: incision healing "
            "well, mild soreness only, resumed light activity.",
            "normal", 1.0, ["mild_soreness"], ["Mild soreness is normal during early post-op recovery"], 0,
        )
        await add_prescription(
            session, p, hospital_user, days_ago(12, hour=10),
            [
                {"name": "Amoxicillin-Clavulanate", "dosage": "625mg", "frequency": "twice daily", "duration": 5, "instructions": "Post-surgical antibiotic course"},
                {"name": "Pantoprazole", "dosage": "40mg", "frequency": "once daily", "timing": "morning", "duration": 10},
            ],
            "Post-appendectomy discharge prescription.",
        )

        # ---- Sunita Bai: post-delivery, normal ----
        p = by_name["Sunita Bai"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(6),
            "[REPORTER:asha] Condition: Post-delivery recovery. Symptoms: mild soreness, hemoglobin "
            "at discharge was 9.6 g/dL (mild anemia), started on iron supplementation.",
            "normal", 1.5, ["postpartum_anemia"], ["Mild postpartum anemia (Hb 9.6 g/dL), being managed with supplementation"], 0,
        )
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(1),
            "[REPORTER:asha] Condition: Post-delivery recovery. Symptoms: recovering well, follow-up "
            "blood test shows hemoglobin improved to 11.5 g/dL, feeling stronger, no complaints.",
            "normal", 0.5, [], ["Hemoglobin trending back to normal range with supplementation"], 0,
        )
        await add_prescription(
            session, p, hospital_user, days_ago(6, hour=9),
            [
                {"name": "Iron + Folic Acid", "dosage": "1 tablet", "frequency": "once daily", "duration": 90, "instructions": "Take with vitamin C source for better absorption"},
                {"name": "Calcium + Vitamin D3", "dosage": "500mg", "frequency": "once daily", "duration": 90},
            ],
            "Postpartum anemia management and supplementation.",
        )

        # ---- Basavaraj Patil: post-fracture, normal ----
        p = by_name["Basavaraj Patil"]
        await add_checkin_with_risk(
            session, p, asha_worker, days_ago(10),
            "[REPORTER:asha] Condition: Post-fracture recovery. Symptoms: cast in place, pain "
            "manageable with medication, no swelling.",
            "normal", 1.0, ["managed_pain"], ["Pain well controlled with prescribed medication"], 0,
        )
        await add_prescription(
            session, p, hospital_user, days_ago(15, hour=10),
            [
                {"name": "Calcium + Vitamin D3", "dosage": "500mg", "frequency": "once daily", "duration": 60},
                {"name": "Paracetamol", "dosage": "500mg", "frequency": "as needed for pain", "duration": 14},
            ],
            "Post-fracture bone healing support.",
        )

        # ---- Bright Gamer: general post-discharge follow-up, normal ----
        p = by_name.get("Bright Gamer")
        if p:
            await add_checkin_with_risk(
                session, p, asha_worker, days_ago(4),
                "[REPORTER:asha] Condition: General post-discharge follow-up. Symptoms: none reported, "
                "vitals stable, recovering as expected.",
                "normal", 0.5, [], ["Stable recovery, no active symptoms reported"], 0,
            )
            await add_prescription(
                session, p, hospital_user, days_ago(4, hour=10),
                [
                    {"name": "Multivitamin", "dosage": "1 tablet", "frequency": "once daily", "duration": 30},
                ],
                "Routine post-discharge supplementation.",
            )

        await session.commit()
        print("Done seeding fake clinical history.")


if __name__ == "__main__":
    asyncio.run(main())
