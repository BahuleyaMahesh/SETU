import logging
from app.database import engine, Base
from app.models import User, Patient, AshaWorker, CallLog, VoiceInteraction, AlertEscalation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")
    
    # Optional: seed some initial data here if needed

if __name__ == "__main__":
    init_db()
