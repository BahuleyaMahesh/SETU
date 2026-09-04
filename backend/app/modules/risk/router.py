from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import RiskEngineService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User
from ...shared.schemas import RiskEvaluationRequest, RiskEvaluationResponse


router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


@router.post("/evaluate", response_model=RiskEvaluationResponse)
async def evaluate_risk(
    request: RiskEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Evaluate patient risk score"""
    patient_id = request.patient_id or (str(user.patient_id) if user.patient_id else None)
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id required")
    await authorize_patient_access(patient_id, user, db)

    service = RiskEngineService(db)
    result = await service.evaluate_risk(
        patient_id=patient_id,
        symptoms=request.symptoms,
        severity_score=request.severity or 0,
    )
    return result


@router.get("/history/{patient_id}", response_model=list[dict])
async def get_risk_history(
    patient_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get risk history for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = RiskEngineService(db)
    return await service.get_risk_history(patient_id, limit)


@router.get("/latest/{patient_id}")
async def get_latest_risk(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get latest risk record for patient"""
    await authorize_patient_access(patient_id, user, db)
    service = RiskEngineService(db)
    result = await service.get_latest_risk(patient_id)
    if not result:
        raise HTTPException(status_code=404, detail="No risk records found")
    return result
