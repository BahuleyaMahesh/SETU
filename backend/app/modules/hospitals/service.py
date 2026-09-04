from typing import Optional, List
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from ...db.models.hospital import Hospital
from ...core.dependencies import get_db
from ...shared.schemas import HospitalCreate, HospitalUpdate


class HospitalService:
    """Service for hospital management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_hospital(self, hospital_data: HospitalCreate) -> Hospital:
        """Create a new hospital"""
        existing_stmt = select(Hospital).filter(Hospital.code == hospital_data.code)
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hospital code already exists",
            )

        hospital = Hospital(
            id=uuid.uuid4(),
            name=hospital_data.name,
            code=hospital_data.code,
            type=hospital_data.type,
            district=hospital_data.district,
            state=hospital_data.state,
            pincode=hospital_data.pincode,
            address=hospital_data.address,
            latitude=hospital_data.latitude,
            longitude=hospital_data.longitude,
            contact_phone=hospital_data.contact_phone,
            contact_email=hospital_data.contact_email,
            is_active=True,
        )
        self.db.add(hospital)
        await self.db.commit()
        await self.db.refresh(hospital)

        return hospital

    async def get_hospital(self, hospital_id: str) -> Optional[Hospital]:
        """Get a hospital by ID"""
        stmt = select(Hospital).filter(Hospital.id == uuid.UUID(hospital_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_hospital_by_code(self, code: str) -> Optional[Hospital]:
        """Get a hospital by code"""
        stmt = select(Hospital).filter(Hospital.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_hospital(self, hospital_id: str, hospital_data: HospitalUpdate) -> Hospital:
        """Update a hospital"""
        hospital = await self.get_hospital(hospital_id)
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital not found",
            )

        update_data = hospital_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(hospital, field, value)

        await self.db.commit()
        await self.db.refresh(hospital)

        return hospital

    async def deactivate_hospital(self, hospital_id: str) -> bool:
        """Deactivate a hospital"""
        hospital = await self.get_hospital(hospital_id)
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital not found",
            )

        hospital.is_active = False
        await self.db.commit()
        return True

    async def get_hospitals_by_district(self, district: str) -> List[Hospital]:
        """Get all hospitals in a district"""
        stmt = select(Hospital).filter(
            Hospital.district == district,
            Hospital.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_hospitals_by_type(self, hospital_type: str) -> List[Hospital]:
        """Get all hospitals of a specific type"""
        stmt = select(Hospital).filter(
            Hospital.type == hospital_type,
            Hospital.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_hospitals(
        self,
        search_term: str = "",
        district: str = None,
        limit: int = 20,
    ) -> List[Hospital]:
        """Search hospitals by name or code"""
        stmt = select(Hospital).filter(Hospital.is_active == True)

        if district:
            stmt = stmt.filter(Hospital.district == district)

        if search_term:
            pattern = f"%{search_term}%"
            stmt = stmt.filter(or_(Hospital.name.ilike(pattern), Hospital.code.ilike(pattern)))

        stmt = stmt.order_by(Hospital.name).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()


async def get_hospital_service(db: AsyncSession = Depends(get_db)) -> HospitalService:
    """Dependency provider for HospitalService"""
    return HospitalService(db)
