from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import Base, engine
from .core.logging import logger
from .modules.auth import router as auth_router
from .modules.patients import router as patients_router
from .modules.asha import router as asha_router
from .modules.hospitals import router as hospitals_router
from .modules.checkins import router as checkins_router
from .modules.risk import router as risk_router
from .modules.alerts import router as alerts_router
from .modules.escalation import router as escalation_router
from .modules.reminders import router as reminders_router
from .modules.maps import router as maps_router
from .modules.calls import router as calls_router
from .modules.documents import router as documents_router
from .modules.prescriptions import router as prescriptions_router
from .modules.analytics import router as analytics_router
from .modules.reports import router as reports_router
from .modules.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="SETU API",
    description="Post-Discharge Rural Health Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(asha_router)
app.include_router(hospitals_router)
app.include_router(checkins_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(escalation_router)
app.include_router(reminders_router)
app.include_router(maps_router)
app.include_router(calls_router)
app.include_router(documents_router)
app.include_router(prescriptions_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SETU API",
        "docs": "/docs",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
