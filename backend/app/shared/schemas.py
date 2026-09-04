# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Auth schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    phone: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Patient schemas
class PatientCreate(BaseModel):
    mrn: str
    full_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    assigned_asha_id: Optional[str] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_level: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    mrn: str
    full_name: str
    gender: Optional[str]
    phone: Optional[str]
    risk_level: str
    created_at: datetime

    class Config:
        orm_mode = True


# ASHA schemas
class ASHACreate(BaseModel):
    name: str
    asha_id: str
    phone: str
    district: str
    block: Optional[str] = None
    phc_id: Optional[str] = None
    assigned_villages: Optional[List[str]] = None


class ASHAUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    assigned_villages: Optional[List[str]] = None


class ASHAResponse(BaseModel):
    id: str
    name: str
    asha_id: str
    district: str
    is_active: bool

    class Config:
        orm_mode = True


# Hospital schemas
class HospitalCreate(BaseModel):
    name: str
    code: str
    type: str
    district: str
    state: str
    pincode: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None


class HospitalResponse(BaseModel):
    id: str
    name: str
    code: str
    district: str
    state: str
    is_active: bool

    class Config:
        orm_mode = True


# Check-in schemas
class CheckinCreate(BaseModel):
    method: str
    input_type: str
    raw_input: Optional[str] = None
    transcript: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CheckinUpdate(BaseModel):
    status: Optional[str] = None
    transcript: Optional[str] = None


class CheckinResponse(BaseModel):
    id: str
    patient_id: str
    method: str
    input_type: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


# Risk schemas
class RiskEvaluationRequest(BaseModel):
    symptoms: List[str]
    severity: Optional[float] = None
    patient_id: Optional[str] = None


class RiskEvaluationResponse(BaseModel):
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    risk_reasons: List[str]
    action_required: Optional[str] = None


# Alert schemas
class AlertCreate(BaseModel):
    patient_id: str
    risk_level: Optional[str] = "medium"
    severity: Optional[str] = "medium"
    title: str
    description: Optional[str] = None


class AlertCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    severity: Optional[str] = "medium"
    risk_level: Optional[str] = "medium"
    title: str = "Alert"
    description: Optional[str] = None


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertStatusUpdateRequest(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    patient_id: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


# Reminder schemas
class ReminderCreate(BaseModel):
    reminder_type: str
    title: str
    description: Optional[str] = None
    schedule_type: str
    scheduled_at: datetime
    notification_method: Optional[str] = "sms"


class ReminderUpdate(BaseModel):
    status: Optional[str] = None
    is_active: Optional[bool] = None


class ReminderResponse(BaseModel):
    id: str
    patient_id: str
    title: str
    status: str
    scheduled_at: datetime

    class Config:
        orm_mode = True


# Prescription schemas
class MedicationCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    timing: Optional[str] = None
    duration: Optional[int] = None
    instructions: Optional[str] = None


class PrescriptionCreate(BaseModel):
    patient_id: str
    hospital_id: str
    prescribed_by_id: str
    medications: List[MedicationCreate]


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    status: str
    prescription_date: datetime

    class Config:
        orm_mode = True


# Document schemas
class DocumentCreate(BaseModel):
    document_type: str
    document_name: str
    file_data: bytes
    file_type: str
    file_size: int
    checksum: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    patient_id: str
    document_type: str
    document_name: str
    uploaded_at: datetime

    class Config:
        orm_mode = True


# Chat schemas
class ChatRequest(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "text"


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    message_type: str = "text"
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


# Analytics schemas
class AnalyticsQuery(BaseModel):
    hospital_id: Optional[str] = None
    asha_worker_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Report schemas
class ReportQuery(BaseModel):
    hospital_id: Optional[str] = None
    patient_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
