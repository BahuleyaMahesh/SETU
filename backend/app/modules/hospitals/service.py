from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status

from ...db.models.hospital import Hospital
from ...db.models.user import User
from .schemas import HospitalCreate, HospitalUpdate, HospitalResponse


class HospitalService:
    """Service for hospital management"""

    def __init__(self, db):
        self.db = db

    async def create_hospital(
        self,
        hospital_data: HospitalCreate,
    ) -> Hospital:
        """Create a new hospital"""
        # Check if hospital code already exists
        existing = await self.db.query(Hospital).filter(
            Hospital.code == hospital_data.code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hospital code already exists",
            )

        hospital = Hospital(
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
        return await self.db.query(Hospital).filter(Hospital.id == hospital_id).first()

    async def get_hospital_by_code(self, code: str) -> Optional[Hospital]:
        """Get a hospital by code"""
        return await self.db.query(Hospital).filter(Hospital.code == code).first()

    async def update_hospital(
        self,
        hospital_id: str,
        hospital_data: HospitalUpdate,
    ) -> Hospital:
        """Update a hospital"""
        hospital = await self.get_hospital(hospital_id)
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital not found",
            )

        update_data = hospital_data.dict(exclude_unset=True)
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
        return await self.db.query(Hospital).filter(
            Hospital.district == district,
            Hospital.is_active == True
        ).all()

    async def get_hospitals_by_type(self, hospital_type: str) -> List[Hospital]:
        """Get all hospitals of a specific type"""
        return await self.db.query(Hospital).filter(
            Hospital.type == hospital_type,
            Hospital.is_active == True
        ).all()

    async def search_hospitals(
        self,
        search_term: str,
        district: str = None,
        limit: int = 20,
    ) -> List[Hospital]:
        """Search hospitals by name or code"""
        query = self.db.query(Hospital).filter(Hospital.is_active == True)

        if district:
            query = query.filter(Hospital.district == district)

        search_pattern = f"%{search_term}%"
        query = query.filter(
            (Hospital.name.ilike(search_pattern)) |
            (Hospital.code.ilike(search_pattern))
        )

        return query.order_by(Hospital.name).limit(limit).all()


def get_hospital_service(db):
    """Get hospital service instance"""
    return HospitalService(db)
