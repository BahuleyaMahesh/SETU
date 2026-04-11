from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CallLog, VoiceInteraction, AlertEscalation, Patient
from app.services.ai_pipeline import process_interaction_pipeline
from app.services.telephony import escalate_call_to_asha, initial_ivr_greeting
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/twiml/{call_log_id}")
async def twiml_greeting(call_log_id: str):
    """
    Called by Twilio when the user answers. Returns the TwiML greeting.
    """
    logger.info(f"Twilio Webhook: TwiML for call_log {call_log_id}")
    return initial_ivr_greeting()

@router.post("/status/{call_log_id}")
async def status_callback(call_log_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Handles call status updates from Twilio (completed, failed, etc).
    """
    body = await request.form()
    call_status = body.get("CallStatus")
    
    call = db.query(CallLog).filter(CallLog.id == call_log_id).first()
    if call:
        call.status = call_status
        db.commit()
        
    return {"status": "ok"}

@router.post("/process-response")
async def process_response(request: Request, db: Session = Depends(get_db)):
    """
    Triggered when IVR collects an audio recording or DTMF digits.
    """
    body = await request.form()
    call_id = body.get("CallSid") # Twilio's Call ID
    audio_url = body.get("RecordingUrl")
    digits = body.get("Digits")
    
    call = db.query(CallLog).filter(CallLog.telephony_call_id == call_id).first()
    if not call:
        # For mock demo purposes
        call = db.query(CallLog).order_by(CallLog.started_at.desc()).first()
    
    analysis = process_interaction_pipeline(audio_url=audio_url, dtmf_input=digits)
    risk = analysis["risk_classification"]
    
    if call:
        call.risk_classification = risk
        interaction = VoiceInteraction(
            call_log_id=call.id,
            audio_url=audio_url,
            transcript=analysis["transcript"],
            extracted_symptoms=analysis["extracted_symptoms"]
        )
        db.add(interaction)
        
        # If Critical -> Escalate
        patient = db.query(Patient).filter(Patient.id == call.patient_id).first()
        if risk in ["WARNING", "CRITICAL"] and patient:
            alert = AlertEscalation(
                call_log_id=call.id,
                patient_id=patient.id,
                severity=risk
            )
            db.add(alert)
        db.commit()
    
    # If CRITICAL -> Escalation TwiML
    if risk == "CRITICAL":
        from fastapi.responses import HTMLResponse
        # Default asha phone for demo
        asha_phone = "+919876543210" 
        twiml = escalate_call_to_asha(asha_phone)
        return HTMLResponse(content=twiml, media_type="application/xml")
    
    from twilio.twiml.voice_response import VoiceResponse
    response = VoiceResponse()
    response.say("Thank you. I have recorded your response. Take care.", language="en-IN")
    response.hangup()
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=str(response), media_type="application/xml")
