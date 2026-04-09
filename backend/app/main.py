from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import webhooks

app = FastAPI(
    title="SETU API",
    description="Backend for SETU - AI Powered Voice-Based Patient Monitoring",
    version="1.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

@app.get("/")
def read_root():
    return {"message": "Welcome to SETU API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
