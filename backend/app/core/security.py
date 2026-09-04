from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets

from .config import settings
from .database import get_db

_bearer_scheme = HTTPBearer(auto_error=False)


def hash_file(file_path: str) -> str:
    """Hash a file for integrity verification"""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def get_client_ip(request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    )
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, hash_value = hashed.split("$")
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        )
        return computed.hex() == hash_value
    except (ValueError, AttributeError):
        return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db=Depends(get_db)
):
    """Get current authenticated user from Bearer token"""
    from ..modules.auth.tokens import verify_token
    from ..db.models.user import User
    from sqlalchemy import select

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Attach extra claims from token
    user.hospital_id = payload.get("hospital_id")
    user.asha_worker_id = payload.get("asha_worker_id")
    user.patient_id = payload.get("patient_id")

    return user


async def require_role(*allowed_roles: str):
    """Require specific role"""
    async def check_role(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return current_user
    return check_role


async def require_patient(current_user=Depends(get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return current_user


async def require_asha(current_user=Depends(get_current_user)):
    if current_user.role != "asha":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return current_user


async def require_hospital(current_user=Depends(get_current_user)):
    if current_user.role != "hospital":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return current_user


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return current_user


async def authorize_patient_access(patient_id: str, current_user, db) -> None:
    """Raise 404 if current_user is not permitted to access this patient's data.

    Uses 404 rather than 403 so an unauthorized caller cannot use the response
    code to confirm whether a given patient_id exists (see docs/security.md).
    """
    if current_user.role == "admin":
        return

    if current_user.role == "patient":
        if str(getattr(current_user, "patient_id", None)) != str(patient_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return

    from ..db.models.patient import Patient
    from sqlalchemy import select

    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if current_user.role == "asha" and str(patient.assigned_asha_id) != str(getattr(current_user, "asha_worker_id", None)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    elif current_user.role == "hospital" and str(patient.hospital_id) != str(getattr(current_user, "hospital_id", None)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    elif current_user.role not in ("asha", "hospital", "patient", "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
