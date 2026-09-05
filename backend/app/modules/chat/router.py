from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from ...core.database import get_db
from .service import ChatService
from ...core.security import get_current_user, authorize_patient_access
from ...db.models.user import User


router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessageInput(BaseModel):
    message: Optional[str] = None
    content: Optional[str] = None
    conversation_id: Optional[str] = None
    role: Optional[str] = "user"


class StaffChatMessageInput(BaseModel):
    patient_id: str
    message: Optional[str] = None
    content: Optional[str] = None
    conversation_id: Optional[str] = None


class RosterQueryInput(BaseModel):
    message: Optional[str] = None
    content: Optional[str] = None
    conversation_id: Optional[str] = None


@router.post("/conversation", response_model=dict)
async def create_conversation(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new conversation"""
    service = ChatService(db)
    return await service.create_conversation(patient_id, str(user.id))


@router.post("/message", response_model=dict)
async def send_message(
    payload: Optional[ChatMessageInput] = Body(None),
    conversation_id: Optional[str] = None,
    role: Optional[str] = "user",
    content: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send message in conversation with symptom detection, safety guidance & care connection"""
    service = ChatService(db)
    user_text = (payload.content or payload.message if payload else None) or content or ""
    conv_id = (payload.conversation_id if payload else None) or conversation_id

    if not user_text.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    return await service.process_patient_message(user=user, user_message=user_text, conversation_id=conv_id)


@router.post("/staff-message", response_model=dict)
async def send_staff_message(
    payload: StaffChatMessageInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """ASHA/hospital care-assistant chat about a specific patient — same
    safety rules and real clinical pipeline as the patient's own chat."""
    if user.role not in ("asha", "hospital", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    await authorize_patient_access(payload.patient_id, user, db)

    user_text = payload.content or payload.message or ""
    if not user_text.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    service = ChatService(db)
    result = await service.process_staff_message(
        user=user,
        patient_id=payload.patient_id,
        user_message=user_text,
        conversation_id=payload.conversation_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/roster-query", response_model=dict)
async def roster_query(
    payload: RosterQueryInput,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """ASHA/hospital care-assistant chat over their WHOLE patient roster —
    "which patients are critical", "when did X last check in", "who's in
    Whitefield" — instead of requiring one patient to be picked first (see
    /staff-message for that per-patient flow). The roster itself is fetched
    server-side scoped to exactly what this role is already authorized to
    see everywhere else in the app (ASHA: their own assigned patients;
    hospital: their own hospital's patients) — never broader than that."""
    if user.role not in ("asha", "hospital"):
        raise HTTPException(status_code=403, detail="Access denied")

    user_text = payload.content or payload.message or ""
    if not user_text.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    service = ChatService(db)
    result = await service.process_roster_query(
        user=user,
        user_message=user_text,
        conversation_id=payload.conversation_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/conversation/{conversation_id}", response_model=list[dict])
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get messages in conversation"""
    service = ChatService(db)
    return await service.get_conversation_messages(conversation_id)


@router.get("/tools", response_model=list[dict])
async def get_tools():
    """Get available chat tools"""
    return ChatService(None).get_tools()


@router.post("/tool/{tool_name}")
async def execute_tool(
    tool_name: str,
    input: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Execute chat tool"""
    service = ChatService(db)
    return await service.process_tool_call(tool_name, input)
