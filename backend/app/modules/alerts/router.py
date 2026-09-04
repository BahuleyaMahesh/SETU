from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from .service import AlertService
from ...core.security import get_current_user, require_asha, require_hospital, authorize_patient_access
from ...db.models.user import User
from ...shared.schemas import AlertResponse, AlertCreateRequest, AlertStatusUpdateRequest


router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    status_filter: str = None,
    severity: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get alerts with optional filters"""
    if user.role not in ("patient", "asha", "hospital", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    service = AlertService(db)
    result = await service.get_alerts(
        patient_id=user.patient_id if user.role == "patient" else None,
        hospital_id=str(user.hospital_id) if user.role == "hospital" else None,
        asha_worker_id=str(user.asha_worker_id) if user.role == "asha" else None,
        status=status_filter,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return result


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get alert by ID"""
    service = AlertService(db)
    alerts = await service.get_alerts(alert_id=alert_id, limit=1)
    if not alerts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await authorize_patient_access(alerts[0]["patient_id"], user, db)
    return alerts[0]


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asha),
):
    """Acknowledge alert"""
    service = AlertService(db)
    alerts = await service.get_alerts(alert_id=alert_id, limit=1)
    if not alerts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await authorize_patient_access(alerts[0]["patient_id"], user, db)

    result = await service.acknowledge_alert(alert_id, str(user.id))
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_asha),
):
    """Resolve alert"""
    service = AlertService(db)
    alerts = await service.get_alerts(alert_id=alert_id, limit=1)
    if not alerts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await authorize_patient_access(alerts[0]["patient_id"], user, db)

    result = await service.resolve_alert(alert_id, str(user.id))
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/", response_model=AlertResponse)
async def create_alert(
    request: AlertCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new alert"""
    service = AlertService(db)
    alert = await service.create_alert(
        patient_id=str(user.patient_id) if user.role == "patient" else request.patient_id,
        severity=request.severity,
        title=request.title,
        description=request.description,
    )
    return {
        "id": str(alert.id),
        "patient_id": str(alert.patient_id),
        "severity": alert.severity,
        "status": alert.status,
        "title": alert.title,
        "description": alert.description,
        "triggered_by": (alert.alert_metadata or {}).get("triggered_by"),
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "created_at": alert.created_at.isoformat(),
    }
