from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class CheckinCreateRequest(BaseModel):
    method: str = "web"  # web, voice, ivr, app
    input_type: str = "text"  # text, audio, structured
    responses: Dict[str, Any] = {}
    patient_id: Optional[str] = None


class CheckinResponse(BaseModel):
    id: str
    patient_id: str
    method: str
    status: str
    created_at: str

    class Config:
        from_attributes = True
