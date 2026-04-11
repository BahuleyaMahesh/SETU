from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict
from app.services.llm_convo import generate_conversational_response

router = APIRouter()

class ChatMessage(BaseModel):
    sender: str
    text: str

class ChatPayload(BaseModel):
    history: List[ChatMessage]
    latest_input: str

@router.post("/chat")
async def process_demo_chat(payload: ChatPayload):
    """
    Receives chat history from the React simulator and returns the LLM's response,
    including the risk classification and keywords.
    """
    history_dict = [{"sender": msg.sender, "text": msg.text} for msg in payload.history]
    
    # Process through the conversational LLM or sophisticated fallback
    ai_response = generate_conversational_response(history_dict, payload.latest_input)
    
    return {
        "reply_text": ai_response.get("reply_text", "I'm sorry, could you repeat that?"),
        "risk_classification": ai_response.get("risk_classification", "NORMAL"),
        "detected_keywords": ai_response.get("detected_keywords", [])
    }
