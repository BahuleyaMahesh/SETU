import datetime
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    ASHA = "ASHA"
    PATIENT = "PATIENT"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, unique=True, index=True)
    role = Column(SQLEnum(Role), default=Role.PATIENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    phone_number = Column(String, index=True) # Legacy but kept for sync
    name = Column(String)
    language = Column(String, default="kn-IN") # Default Kannada
    is_active = Column(Boolean, default=True)
    care_protocol = Column(JSON, default=dict)
    last_called_at = Column(DateTime)
    asha_worker_id = Column(UUID(as_uuid=True), ForeignKey("asha_workers.id"))

class AshaWorker(Base):
    __tablename__ = "asha_workers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    phone_number = Column(String) # Legacy but kept for sync
    name = Column(String)
    primary_phc = Column(String)

class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    telephony_call_id = Column(String, unique=True, index=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime)
    status = Column(String) # IN_PROGRESS, COMPLETED, FAILED
    risk_classification = Column(String) # NORMAL, WARNING, CRITICAL

class VoiceInteraction(Base):
    __tablename__ = "voice_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_log_id = Column(UUID(as_uuid=True), ForeignKey("call_logs.id"))
    question_asked = Column(String)
    audio_url = Column(String)
    transcript = Column(String)
    extracted_symptoms = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AlertEscalation(Base):
    __tablename__ = "alert_escalations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_log_id = Column(UUID(as_uuid=True), ForeignKey("call_logs.id"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    severity = Column(String) # WARNING, CRITICAL
    status = Column(String, default="OPEN") # OPEN, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime)
