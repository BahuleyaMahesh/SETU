import asyncio
from sqlalchemy.future import select
from datetime import datetime
import uuid

from app.db.models.user import User
from app.db.models.hospital import Hospital
from app.db.models.patient import Patient
from app.db.models.asha import ASHAWorker
from app.db.models.assignment import Assignment
from app.core.database import async_session
from app.core.security import hash_password


async def seed_data():
    """Seed initial development data"""
    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(select(Hospital))
        existing_hospital = result.scalar_one_or_none()
        if existing_hospital:
            print("Data already seeded")
            return

        # Create hospital
        hospital = Hospital(
            id=uuid.uuid4(),
            name="City General Hospital",
            code="CGH001",
            type="District",
            district="Bangalore",
            state="Karnataka",
            pincode="560001",
            address="123 Medical Street, Bangalore",
            latitude=12.9716,
            longitude=77.5946,
            contact_phone="+91-80-XXXX-XXXX",
            contact_email="contact@cityhospital.com",
            is_active=True,
        )
        session.add(hospital)
        await session.flush()

        # Create ASHA worker
        asha = ASHAWorker(
            id=uuid.uuid4(),
            name="Priya Sharma",
            asha_id="ASHA001",
            phone="+91-98765-43210",
            district="Bangalore",
            block="Whitefield",
            phc_id="PHC001",
            assigned_villages=["Village A", "Village B"],
            is_active=True,
        )
        session.add(asha)
        await session.flush()

        # Create users
        patient_user = User(
            id=uuid.uuid4(),
            email="patient@setu.com",
            hashed_password=hash_password("password123"),
            full_name="Ramesh Kumar",
            phone="+91-98765-43211",
            role="patient",
            is_active=True,
            is_email_verified=True,
            is_phone_verified=True,
        )
        session.add(patient_user)
        await session.flush()

        asha_user = User(
            id=uuid.uuid4(),
            email="asha@setu.com",
            hashed_password=hash_password("password123"),
            full_name="Priya Sharma",
            phone="+91-98765-43210",
            role="asha",
            is_active=True,
            asha_worker_id=asha.id,
        )
        session.add(asha_user)
        await session.flush()

        hospital_user = User(
            id=uuid.uuid4(),
            email="hospital@setu.com",
            hashed_password=hash_password("password123"),
            full_name="Dr. Sharma",
            phone="+91-80-XXXX-XXXX",
            role="hospital",
            is_active=True,
            hospital_id=hospital.id,
        )
        session.add(hospital_user)
        await session.flush()

        # Create patient
        patient = Patient(
            id=uuid.uuid4(),
            mrn="MRN001",
            full_name="Ramesh Kumar",
            date_of_birth=datetime(1960, 5, 15),
            gender="M",
            phone="+91-98765-43211",
            address="456 Patient Lane, Bangalore",
            village="Village A",
            district="Bangalore",
            state="Karnataka",
            pincode="560001",
            latitude=12.9716,
            longitude=77.5946,
            hospital_id=hospital.id,
            assigned_asha_id=asha.id,
            risk_level="normal",
        )
        session.add(patient)
        await session.flush()

        patient_user.patient_id = patient.id
        asha.user_id = asha_user.id if hasattr(asha, 'user_id') else None

        # Create assignment
        assignment = Assignment(
            id=uuid.uuid4(),
            patient_id=patient.id,
            asha_worker_id=asha.id,
            assigned_by_id=hospital_user.id,
            assigned_at=datetime.utcnow(),
            is_active=True,
        )
        session.add(assignment)

        await session.commit()
        print("Demo data seeded successfully!")
        print("Demo users:")
        print("  Patient: patient@setu.com / password123")
        print("  ASHA: asha@setu.com / password123")
        print("  Hospital: hospital@setu.com / password123")


if __name__ == "__main__":
    asyncio.run(seed_data())
