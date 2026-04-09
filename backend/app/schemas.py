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
