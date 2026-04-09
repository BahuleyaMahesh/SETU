from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import TelephonyWebhook
from app.services.ai_pipeline import process_audio
from app.services.rule_engine import determine_risk

router = APIRouter()

@router.post("/missed-call")
async def handle_missed_call(request: Request, db: Session = Depends(get_db)):
    """
    Triggered when a patient gives a missed call.
    The system should ideally look up the patient, verify their protocol,
    and then trigger an outbound call via Exotel/Twilio API.
    """
    body = await request.form()
    phone_number = body.get("From")
    
    # 1. Look up patient
    # patient = db.query(Patient).filter(Patient.phone_number == phone_number).first()
    
    # 2. Trigger outbound call (Mocked)
    return {"status": "success", "message": f"Initiating callback to {phone_number}"}

@router.post("/gather-audio")
async def handle_gather_audio(request: Request, db: Session = Depends(get_db)):
    """
    Triggered when IVR collects an audio recording or DTMF digits.
    """
    body = await request.form()
    call_id = body.get("CallSid")
    audio_url = body.get("RecordingUrl")
    digits = body.get("Digits")
    
    # Rule engine priority check
    if digits == "9":
        # CRITICAL ALERT OVERRIDE
        return {"status": "escalated", "classification": "CRITICAL"}
    
    if auto_url := audio_url:
        # Pass to AI Pipeline
        transcript, analysis = await process_audio(auto_url)
        
        # Pass AI analysis to Rule Engine for final classification
        classification = determine_risk(analysis["symptoms"])
        
        return {
            "transcript": transcript,
            "classification": classification,
            "analysis": analysis
        }
    
    return {"status": "no_input"}
