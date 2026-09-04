from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    """Patient information for risk evaluation"""
    id: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_conditions: Optional[List[str]] = None
    risk_level: Optional[str] = None


class RiskEvaluationRequest(BaseModel):
    """Request for risk evaluation"""
    symptoms: List[str] = Field(..., description="List of symptoms reported by patient")
    severity: Optional[float] = Field(None, description="Self-reported severity (0-10)")
    patient_id: Optional[str] = None
    patient_info: Optional[PatientInfo] = None


class RiskEvaluationResponse(BaseModel):
    """Response with risk evaluation results"""
    risk_score: float = Field(..., description="Numerical risk score")
    risk_level: str = Field(..., description="risk_level: normal, warning, critical")
    risk_factors: List[str] = Field(default=[], description="Risk factors identified")
    risk_reasons: List[str] = Field(default=[], description="Explanation for risk level")
    action_required: Optional[str] = Field(None, description="Recommended action")


class RiskHistoryResponse(BaseModel):
    """Risk history record response"""
    id: str
    patient_id: str
    checkin_id: Optional[str]
    risk_level: str
    risk_score: Optional[float]
    risk_factors: List[str]
    risk_reasons: List[str]
    severity: int
    action_required: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class RiskAnalyticsResponse(BaseModel):
    """Risk analytics response"""
    total_evaluations: int
    by_level: Dict[str, int]
    by_day: List[Dict[str, Any]]
    average_score: float
    critical_count: int
    warning_count: int
