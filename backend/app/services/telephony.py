import os
from twilio.rest import Client
import logging

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACmock")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "mocktoken")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")
BASE_URL = os.getenv("BASE_URL", "https://api.setu-health.in") # Replace with ngrok for local dev

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID != "ACmock" else None
logger = logging.getLogger(__name__)

def initiate_outbound_call(patient_phone: str, call_log_id: str):
    """
    Triggers a scheduled automated call to the patient.
    """
    if not client:
        logger.warning(f"Twilio Mock: Initiating call to {patient_phone} for log {call_log_id}")
        return {"status": "mock_queued", "sid": f"SMmock_{call_log_id}"}
        
    try:
        call = client.calls.create(
            to=patient_phone,
            from_=TWILIO_PHONE_NUMBER,
            # Webhook Twilio calls once the user answers
            url=f"{BASE_URL}/api/v1/webhooks/twiml/{call_log_id}",
            status_callback=f"{BASE_URL}/api/v1/webhooks/status/{call_log_id}",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            method="POST"
        )
        return {"status": call.status, "sid": call.sid}
    except Exception as e:
        logger.error(f"Failed to initiate call: {e}")
        return {"status": "failed", "error": str(e)}

def escalate_call_to_asha(asha_phone: str):
    """
    Generates TwiML to Dial the ASHA worker into the current call.
    Uses <Dial> verb to bridge the patient to the ASHA worker live.
    """
    from twilio.twiml.voice_response import VoiceResponse, Dial
    
    response = VoiceResponse()
    response.say("Connecting you to your ASHA worker. Please wait.", language="en-IN")
    dial = Dial()
    dial.number(asha_phone)
    response.append(dial)
    
    return str(response)

def initial_ivr_greeting():
    """
    TwiML for the first AI prompt.
    """
    from twilio.twiml.voice_response import VoiceResponse, Gather
    
    response = VoiceResponse()
    # Using Gather to capture speech or DTMF (keypad)
    gather = Gather(
        input='dtmf speech', 
        action=f"{BASE_URL}/api/v1/webhooks/process-response", 
        timeout=5, 
        speechTimeout="auto",
        language="kn-IN" # Kannada
    )
    gather.say("Namaskara. How are you feeling today? Please speak, or press 1 if you are fine, 2 for pain, and 3 for an emergency.", language="en-IN")
    response.append(gather)
    # Fallback if no input
    response.redirect(f"{BASE_URL}/api/v1/webhooks/fallback")
    
    return str(response)
