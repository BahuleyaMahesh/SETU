import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.models import Patient, CallLog
from app.services.telephony import initiate_outbound_call

logger = logging.getLogger(__name__)

def schedule_daily_calls():
    """
    Job that runs daily at a specific time to initiate calls to active patients.
    """
    logger.info("Running daily scheduled calls...")
    db = SessionLocal()
    try:
        # Get all active patients
        patients = db.query(Patient).filter(Patient.is_active == True).all()
        for patient in patients:
            # Create a call log in DB
            call_log = CallLog(
                patient_id=patient.id,
                status="INITIATED"
            )
            db.add(call_log)
            db.commit()
            db.refresh(call_log)
            
            # Send to telephony
            # In a distributed system, this would push to Celery/SQS.
            # Here we call it directly (async wrapper or synchronous).
            result = initiate_outbound_call(patient.phone_number, str(call_log.id))
            
            if result.get("status") == "failed":
                call_log.status = "FAILED"
            else:
                call_log.telephony_call_id = result.get("sid", "mock_sid")
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error in schedule_daily_calls: {e}")
    finally:
        db.close()

def start_scheduler():
    """
    Initialize and start the background scheduler.
    """
    scheduler = BackgroundScheduler()
    # E.g. Run daily at 10:00 AM
    trigger = CronTrigger(hour=10, minute=0)
    scheduler.add_job(schedule_daily_calls, trigger)
    
    # Or to test right away, we could add a short interval job
    # scheduler.add_job(schedule_daily_calls, 'interval', seconds=60)
    
    scheduler.start()
    logger.info("Scheduler started.")
