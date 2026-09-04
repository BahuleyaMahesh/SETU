from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "SETU"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:bahuleya007@localhost:5432/setu_db"
    )

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Providers
    SPEECH_PROVIDER: str = os.getenv("SPEECH_PROVIDER", "mock")
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "mock")
    TELEPHONY_PROVIDER: str = os.getenv("TELEPHONY_PROVIDER", "mock")
    NOTIFICATION_PROVIDER: str = os.getenv("NOTIFICATION_PROVIDER", "mock")
    MAP_PROVIDER: str = os.getenv("MAP_PROVIDER", "mock")

    # External API Keys
    BHASHINI_API_KEY: str = os.getenv("BHASHINI_API_KEY", "")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE: str = os.getenv("TWILIO_PHONE", "")
    MSG91_API_KEY: str = os.getenv("MSG91_API_KEY", "")
    TELNYX_API_KEY: str = os.getenv("TELNYX_API_KEY", "")
    TELNYX_PHONE: str = os.getenv("TELNYX_PHONE", "")
    TELNYX_ACCOUNT_SID: str = os.getenv("TELNYX_ACCOUNT_SID", "")
    TELNYX_TEXML_APPLICATION_SID: str = os.getenv("TELNYX_TEXML_APPLICATION_SID", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    # Optional: publicly reachable base URL for this backend (e.g. an ngrok
    # tunnel). When set, Twilio calls use it for status/recording webhooks
    # instead of inline TwiML.
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "")

    class Config:
        env_file = ".env"


settings = Settings()
