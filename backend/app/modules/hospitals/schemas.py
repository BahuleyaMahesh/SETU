from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class HospitalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    village: str = Field(..., min_length=1, max_length=255)
    district: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=1, max_length=255)
    pincode: str = Field(..., min_length=6, max_length=6)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    type: str = Field(default="PHC", description="PHC/CHC/SC/Hospital")


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    village: Optional[str] = Field(None, min_length=1, max_length=255)
    district: Optional[str] = Field(None, min_length=1, max_length=255)
    state: Optional[str] = Field(None, min_length=1, max_length=255)
    pincode: Optional[str] = Field(None, min_length=6, max_length=6)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    type: Optional[str] = None


class HospitalResponse(HospitalBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HospitalListResponse(BaseModel):
    total: int
    items: List[HospitalResponse]
