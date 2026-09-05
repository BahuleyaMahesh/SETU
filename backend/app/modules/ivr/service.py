from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from ...db.models.call import Call
from ...core.config import settings
from ..speech.service import SpeechService
from ..extraction.service import ExtractionService


class IVRService:
    """Interactive Voice Response service"""

    # Predefined IVR flows
    FLOWS = {
        "checkin": {
            "name": "Check-in Flow",
            "steps": [
                {"id": "welcome", "type": "greeting", "text": "Welcome to SETU. Press 1 for check-in."},
                {"id": "option", "type": "menu", "options": ["1: Check-in", "2: Medication", "3: Emergency"]},
                {"id": "symptoms", "type": "question", "question": "How are you feeling?"},
                {"id": "severity", "type": "question", "question": "Rate your symptoms 1-10"},
                {"id": "end", "type": "farewell", "text": "Thank you for checking in. Take care!"},
            ],
        },
        "reminder": {
            "name": "Medication Reminder Flow",
            "steps": [
                {"id": "welcome", "type": "greeting", "text": "This is your medication reminder."},
                {"id": "medication", "type": "information", "text": "Please take your prescribed medication now."},
                {"id": "confirmation", "type": "question", "question": "Did you take your medication? Press 1 for yes, 2 for no."},
                {"id": "end", "type": "farewell", "text": "Thank you. Take care!"},
            ],
        },
        "emergency": {
            "name": "Emergency Flow",
            "steps": [
                {"id": "welcome", "type": "greeting", "text": "This is an emergency alert. Please stay calm."},
                {"id": "instructions", "type": "information", "text": "Help is on the way. Please follow any instructions given."},
                {"id": "contact", "type": "question", "question": "Are you with someone? Press 1 for yes, 2 for no."},
                {"id": "end", "type": "farewell", "text": "Help is coming. Stay safe."},
            ],
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.speech_service = SpeechService(db)
        self.extraction_service = ExtractionService(db)

    def get_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get IVR flow by ID"""
        return self.FLOWS.get(flow_id)

    def list_flows(self) -> Dict[str, Any]:
        """List all available flows"""
        return {
            "flows": [
                {"id": flow_id, "name": flow["name"]}
                for flow_id, flow in self.FLOWS.items()
            ]
        }

    async def process_dtmf_input(
        self,
        call_id: str,
        dtmf_input: str,
        current_step_id: str,
    ) -> Dict[str, Any]:
        """Process DTMF input during IVR flow"""
        flow_stmt = select(Call).filter(Call.id == uuid.UUID(call_id))
        flow_result = await self.db.execute(flow_stmt)
        call = flow_result.scalar_one_or_none()

        if not call:
            return {"error": "Call not found"}

        flow = self.FLOWS.get(call.ivr_flow_id or "checkin")

        # Process input
        response = {
            "call_id": call_id,
            "current_step": current_step_id,
            "next_step": None,
            "output": None,
            "collected_data": {},
        }

        if current_step_id == "option":
            if dtmf_input == "1":
                response["next_step"] = "symptoms"
                response["output"] = "Please describe your symptoms."
            elif dtmf_input == "2":
                response["next_step"] = "medication_question"
                response["output"] = "Have you taken your medication? Press 1 for yes."
            elif dtmf_input == "3":
                response["next_step"] = "emergency"
                response["output"] = "Connecting to emergency services."

        elif current_step_id == "symptoms":
            response["next_step"] = "severity"
            response["collected_data"] = {"symptoms": dtmf_input}

        elif current_step_id == "severity":
            response["next_step"] = "end"
            response["collected_data"] = {"severity": int(dtmf_input)}
            # Store responses
            if call.responses:
                call.responses.update(response["collected_data"])
            await self.db.commit()

        return response

    async def process_speech_input(
        self,
        call_id: str,
        audio_data: bytes,
    ) -> Dict[str, Any]:
        """Process speech input during IVR flow"""
        # Transcribe audio
        transcription = await self.speech_service.transcribe_audio(audio_data)

        # Extract symptoms if detected
        if transcription["confidence"] > 0.5:
            extraction = await self.extraction_service.extract_symptoms(transcription["transcript"])
        else:
            extraction = {}

        return {
            "transcript": transcription["transcript"],
            "confidence": transcription["confidence"],
            "extracted_symptoms": extraction.get("symptoms", []),
        }
