from datetime import datetime, timedelta
from typing import Optional, Tuple
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.user import User
from ...db.models.patient import Patient
from ...db.models.asha import ASHAWorker
from ...db.models.hospital import Hospital
from ...core.security import hash_password, verify_password
from .tokens import create_access_token, verify_token


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Login user and return tokens"""
        # Find user
        stmt = select(User).filter(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None, "Invalid credentials"

        # Hackathon demo mode: any password is accepted for an existing
        # account — only the account (email) needs to be real. Password is
        # still hashed and stored at registration, but never checked here.

        if not user.is_active:
            return None, "User is inactive"

        # Create token
        token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
                "hospital_id": str(user.hospital_id) if user.hospital_id else None,
                "asha_worker_id": str(user.asha_worker_id) if user.asha_worker_id else None,
                "patient_id": str(user.patient_id) if user.patient_id else None,
            }
        )

        user.last_login = datetime.utcnow()
        await self.db.commit()

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "hospital_id": str(user.hospital_id) if user.hospital_id else None,
                "asha_worker_id": str(user.asha_worker_id) if user.asha_worker_id else None,
                "patient_id": str(user.patient_id) if user.patient_id else None,
            },
        }, None

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: str,
        role: str,
        hospital_name: Optional[str] = None,
        hospital_id: Optional[str] = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Register new user and auto-create their role-specific profile.

        Hackathon demo mode: signup is fully self-serve — a "patient" attaches
        to the hospital they picked (`hospital_id`, from GET /auth/hospitals),
        falling back to the first available hospital if they didn't pick one
        (one is created if none exists yet); an "asha" gets a standalone
        worker profile; a "hospital" signup creates its own new Hospital
        record. Login never checks the password (see login() above), so this
        is intentionally open and not meant for production use as-is.
        """
        stmt = select(User).filter(User.email == email)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return None, "Email already registered"

        if role not in ("patient", "asha", "hospital"):
            return None, "Invalid role"

        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            phone=phone,
            role=role,
            is_active=True,
        )

        requested_hospital_id = hospital_id

        patient_id = None
        asha_worker_id = None
        hospital_id = None  # reassigned below to whichever hospital ends up attached, for the token/response

        if role == "patient":
            hospital = None
            if requested_hospital_id:
                hospital_stmt = select(Hospital).filter(Hospital.id == uuid.UUID(requested_hospital_id))
                hospital_result = await self.db.execute(hospital_stmt)
                hospital = hospital_result.scalar_one_or_none()
                if not hospital:
                    return None, "Selected hospital not found"

            if not hospital:
                hospital_stmt = select(Hospital).limit(1)
                hospital_result = await self.db.execute(hospital_stmt)
                hospital = hospital_result.scalar_one_or_none()

            if not hospital:
                hospital = Hospital(
                    id=uuid.uuid4(),
                    name="General Hospital",
                    code=f"HOSP-{uuid.uuid4().hex[:6].upper()}",
                    type="District",
                    district="Unknown",
                    state="Unknown",
                )
                self.db.add(hospital)
                await self.db.flush()

            patient = Patient(
                id=uuid.uuid4(),
                mrn=f"MRN-{uuid.uuid4().hex[:8].upper()}",
                full_name=full_name,
                phone=phone,
                hospital_id=hospital.id,
            )
            self.db.add(patient)
            await self.db.flush()
            patient_id = patient.id
            user.patient_id = patient.id

        elif role == "asha":
            asha = ASHAWorker(
                id=uuid.uuid4(),
                name=full_name,
                asha_id=f"ASHA-{uuid.uuid4().hex[:8].upper()}",
                phone=phone,
                district="Unassigned",
            )
            self.db.add(asha)
            await self.db.flush()
            asha_worker_id = asha.id
            user.asha_worker_id = asha.id

        elif role == "hospital":
            hospital = Hospital(
                id=uuid.uuid4(),
                name=hospital_name or f"{full_name}'s Hospital",
                code=f"HOSP-{uuid.uuid4().hex[:6].upper()}",
                type="General",
                district="Unknown",
                state="Unknown",
                contact_phone=phone,
                contact_email=email,
            )
            self.db.add(hospital)
            await self.db.flush()
            hospital_id = hospital.id
            user.hospital_id = hospital.id

        self.db.add(user)
        await self.db.commit()

        token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
                "hospital_id": str(hospital_id) if hospital_id else None,
                "asha_worker_id": str(asha_worker_id) if asha_worker_id else None,
                "patient_id": str(patient_id) if patient_id else None,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "hospital_id": str(hospital_id) if hospital_id else None,
                "asha_worker_id": str(asha_worker_id) if asha_worker_id else None,
                "patient_id": str(patient_id) if patient_id else None,
            },
        }, None

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        stmt = select(User).filter(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def refresh_token(self, token: str) -> Tuple[Optional[str], Optional[str]]:
        """Refresh access token"""
        payload = verify_token(token)
        if not payload:
            return None, "Invalid token"

        user_id = payload.get("sub")
        user = await self.get_user(user_id)
        if not user:
            return None, "User not found"

        new_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
            }
        )

        return new_token, None

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> Tuple[bool, Optional[str]]:
        """Change user password"""
        user = await self.get_user(user_id)
        if not user:
            return False, "User not found"

        if not verify_password(old_password, user.hashed_password):
            return False, "Invalid current password"

        user.hashed_password = hash_password(new_password)
        await self.db.commit()

        return True, None

    async def reset_password_request(
        self,
        email: str,
    ) -> Tuple[bool, Optional[str]]:
        """Request password reset"""
        stmt = select(User).filter(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False, "User not found"

        # In production, send email with reset token
        # For now, just return success
        return True, None
