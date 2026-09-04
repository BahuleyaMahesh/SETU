from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class AddPatientRequest(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    password: Optional[str] = "Patient@123"
    age: Optional[int] = None
    gender: Optional[str] = "Male"
    condition: Optional[str] = None
    symptoms: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = "Karnataka"
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hospital_id: Optional[str] = None
