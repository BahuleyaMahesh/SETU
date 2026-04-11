from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role
from app.schemas import OTPRequest, OTPVerify, Token, UserResponse
from app.security import create_access_token, require_role, get_current_user
from datetime import timedelta

router = APIRouter()

# In a real app, this would use Redis to store OTPs.
# Here we use a mock one for ease of demo
MOCK_OTP = "1234"

@router.post("/send-otp", status_code=status.HTTP_200_OK)
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    # Check if user exists. In production, we might not want to reveal this,
    # but for an internal rural app, it's fine.
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not user:
        # Auto-create for demo purposes, or return 404 in prod
        # Let's auto-create them as PATIENT by default to avoid blocking tests
        user = User(phone_number=request.phone_number, role=Role.PATIENT)
        db.add(user)
        db.commit()
    
    # Normally we'd call MSG91/Twilio here to send SMS
    return {"message": "OTP sent successfully", "mock_otp": MOCK_OTP}

@router.post("/verify-otp", response_model=Token)
def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    if request.otp != MOCK_OTP:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )
    
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": user.phone_number, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
