from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class TelephonyWebhook(BaseModel):
    CallSid: str
    From: str
    To: str
    CallStatus: str
    RecordUrl: Optional[str] = None
    Digits: Optional[str] = None

class AIAssessmentResponse(BaseModel):
    intent: str
    symptoms: List[str]
    sentiment: str
    requires_attention: bool

class AlertResponse(BaseModel):
    id: UUID
    patient_id: UUID
    severity: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone_number: Optional[str] = None
    role: Optional[str] = None

class OTPRequest(BaseModel):
    phone_number: str

class OTPVerify(BaseModel):
    phone_number: str
    otp: str

class UserResponse(BaseModel):
    id: UUID
    phone_number: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
