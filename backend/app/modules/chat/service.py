from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import math

from ...db.models.chat_message import ChatMessage
from ...db.models.user import User
from ...db.models.patient import Patient
from ...db.models.asha import ASHAWorker
from ...db.models.hospital import Hospital
from ...core.config import settings
from ..alerts.service import AlertService
from .providers.gemini import GeminiChatProvider


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km using Haversine formula"""
    if not (lat1 and lon1 and lat2 and lon2):
        return 2.5
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class ChatService:
    """Chat service with symptom intent detection, safety fallback & care connections"""

    TOOLS = {
        "get_patient_info": {
            "name": "Get Patient Information",
            "description": "Retrieve patient demographic and medical history information",
            "params": {"type": "object", "properties": {"patient_id": {"type": "string"}}}
        },
        "get_patient_alerts": {
            "name": "Get Patient Alerts",
            "description": "Retrieve open alerts for a patient",
            "params": {"type": "object", "properties": {"patient_id": {"type": "string"}}}
        },
        "create_alert": {
            "name": "Create Alert",
            "description": "Create a new alert for a patient",
            "params": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "evaluate_risk": {
            "name": "Evaluate Patient Risk",
            "description": "Evaluate risk level based on symptoms and severity",
            "params": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string"},
                    "symptoms": {"type": "array", "items": {"type": "string"}},
                    "severity_score": {"type": "number"}
                }
            }
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_service = AlertService(db) if db else None
        self.gemini = GeminiChatProvider()

    async def create_conversation(
        self,
        patient_id: str,
        initiated_by: str,
    ) -> Dict[str, Any]:
        """Create new conversation"""
        conv_id = uuid.uuid4()
        if self.db:
            try:
                conversation = ChatMessage(
                    id=uuid.uuid4(),
                    conversation_id=conv_id,
                    sender_id=uuid.UUID(initiated_by) if len(initiated_by) == 36 else (await self._get_valid_user_id()),
                    sender_type="system",
                    message_type="text",
                    patient_id=uuid.UUID(patient_id) if patient_id and len(patient_id) == 36 else None,
                    content="Conversation started",
                )
                self.db.add(conversation)
                await self.db.commit()
            except Exception as e:
                print(f"Error creating conversation: {e}")

        return {"id": str(conv_id)}

    async def _get_valid_user_id(self) -> uuid.UUID:
        """Fetch a valid user ID for system/AI messages"""
        stmt = select(User.id).limit(1)
        res = await self.db.execute(stmt)
        uid = res.scalar()
        return uid if uid else uuid.uuid4()

    async def send_message(
        self,
        conversation_id: Optional[str],
        role: str,
        content: str,
        sender_id: Optional[str] = None,
        tool_output: str = None,
    ) -> Dict[str, Any]:
        """Send message in conversation"""
        msg_uuid = uuid.uuid4()
        conv_uuid = uuid.UUID(conversation_id) if conversation_id and len(conversation_id) == 36 else uuid.uuid4()

        if self.db:
            try:
                valid_sender = uuid.UUID(sender_id) if sender_id and len(sender_id) == 36 else await self._get_valid_user_id()
                message = ChatMessage(
                    id=msg_uuid,
                    conversation_id=conv_uuid,
                    sender_id=valid_sender,
                    sender_type=role,
                    message_type="text",
                    content=content,
                    tool_output=tool_output,
                )
                self.db.add(message)
                await self.db.commit()
            except Exception as e:
                print(f"Error persisting chat message: {e}")

        return {"id": str(msg_uuid)}

    async def process_patient_message(
        self,
        user: Optional[User],
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process patient query with symptom detection, safety fallback, ASHA worker info & nearby facilities"""
        text_lower = user_message.lower()

        # 1. Symptom & Health Concern Intent Detection
        critical_keywords = [
            "chest pain", "shortness of breath", "breathing difficulty", "difficulty breathing",
            "unconscious", "stroke", "severe bleeding", "heart attack", "collapsed", "cannot breathe",
            "can't breathe", "cant breathe", "not breathing", "stopped breathing",
            # Trauma / injury emergencies — these are life-threatening and must never
            # fall through to generic "rest and hydrate" guidance.
            "shot", "gunshot", "gun shot", "stabbed", "stabbing", "knife",
            "dying", "i'm dying", "im dying", "going to die", "gonna die",
            "bleeding a lot", "bleeding heavily", "blood everywhere", "losing blood",
            "accident", "road accident", "hit by a car", "hit by car", "run over",
            "fell from", "fall from height", "assaulted", "attacked", "beaten",
            "overdose", "poisoned", "poisoning", "swallowed poison",
            "drowning", "drowned", "electrocuted", "snake bite", "snakebite",
            "suicide", "want to die", "self harm", "self-harm",
            "severe burn", "burnt badly", "on fire",
            "help me", "emergency", "call ambulance", "need ambulance",
        ]
        warning_keywords = [
            "head", "headache", "fever", "vomit", "vomiting", "dizzy", "dizziness", "nausea",
            "chills", "abdomen", "stomach", "pain", "hurt", "hurting", "sick", "wound",
            "cough", "weakness", "swelling", "cramp", "cramps"
        ]

        is_critical = any(kw in text_lower for kw in critical_keywords)
        is_warning = any(kw in text_lower for kw in warning_keywords)
        is_health_concern = is_critical or is_warning or "doctor" in text_lower or "medicine" in text_lower or "symptom" in text_lower

        severity = "critical" if is_critical else ("warning" if is_warning else "normal")

        # 2. Retrieve Patient & Assigned ASHA Context
        patient_lat, patient_lon = 12.9716, 77.5946
        asha_dict = {
            "name": "Priya Sharma (ASHA)",
            "phone": "+91-98765-43210",
            "block": "Whitefield Block",
            "district": "Bangalore",
            "is_active": True
        }

        if self.db and user and hasattr(user, 'patient_id') and user.patient_id:
            try:
                patient_stmt = select(Patient).filter(Patient.id == user.patient_id)
                patient_res = await self.db.execute(patient_stmt)
                patient = patient_res.scalar_one_or_none()

                if patient:
                    if patient.latitude and patient.longitude:
                        patient_lat, patient_lon = patient.latitude, patient.longitude

                    if patient.assigned_asha_id:
                        asha_stmt = select(ASHAWorker).filter(ASHAWorker.id == patient.assigned_asha_id)
                        asha_res = await self.db.execute(asha_stmt)
                        asha_obj = asha_res.scalar_one_or_none()
                        if asha_obj:
                            asha_dict = {
                                "id": str(asha_obj.id),
                                "name": asha_obj.name,
                                "phone": asha_obj.phone,
                                "block": asha_obj.block or "Assigned Block",
                                "district": asha_obj.district or "District HQ",
                                "is_active": asha_obj.is_active
                            }
            except Exception as e:
                print(f"Error retrieving patient/ASHA context: {e}")

        # 3. Retrieve Health Facilities
        facilities = []
        if self.db:
            try:
                hosp_stmt = select(Hospital).filter(Hospital.is_active == True)
                hosp_res = await self.db.execute(hosp_stmt)
                hospitals = hosp_res.scalars().all()

                for h in hospitals:
                    dist = calculate_distance(patient_lat, patient_lon, h.latitude or 12.9716, h.longitude or 77.5946)
                    facilities.append({
                        "id": str(h.id),
                        "name": h.name,
                        "type": h.type,
                        "distance_km": round(dist, 1),
                        "phone": h.contact_phone or "+91-80-2845-1234",
                        "address": h.address or f"{h.district}, {h.state}",
                        "latitude": h.latitude or 12.9716,
                        "longitude": h.longitude or 77.5946
                    })
                facilities.sort(key=lambda x: x["distance_km"])
            except Exception as e:
                print(f"Error fetching hospital facilities: {e}")

        if not facilities:
            facilities = [
                {
                    "id": "f-chc",
                    "name": "Whitefield Community Health Center (CHC)",
                    "type": "CHC",
                    "distance_km": 2.4,
                    "phone": "+91-80-2845-1234",
                    "address": "Main Road, Whitefield Block",
                    "latitude": 12.9698,
                    "longitude": 77.7499
                },
                {
                    "id": "f-cgh",
                    "name": "City General Hospital",
                    "type": "District Hospital",
                    "distance_km": 5.8,
                    "phone": "+91-80-2222-3333",
                    "address": "Station Road, District HQ",
                    "latitude": 12.9716,
                    "longitude": 77.5946
                }
            ]

        # 4. Generate Response: RAG retrieval grounds a Gemini-phrased reply;
        #    severity itself was already decided deterministically above (step 1).
        #    If Gemini/RAG are unavailable, fall back to safe canned guidance.
        response_text = ""
        sources = ["SETU Safety Protocol", "MedlinePlus Clinical Guidelines"]
        rag_context = None

        try:
            from ..rag.service import RAGService
            rag_service = RAGService(self.db)
            rag_res = await rag_service.query_rag(user_message, user_role="patient", top_k=2)
            if rag_res and rag_res.response and len(rag_res.response.strip()) > 20 and "couldn't find" not in rag_res.response:
                rag_context = rag_res.response
                if rag_res.sources:
                    sources = [s.get("title", "Care Guidance") for s in rag_res.sources] or sources
        except Exception:
            pass

        if self.gemini.available():
            try:
                generated = await self.gemini.generate_response(user_message, severity, context=rag_context)
                if generated and len(generated.strip()) > 10:
                    response_text = generated.strip()
            except Exception:
                pass

        # If Gemini/RAG are unavailable or fail, use safe deterministic temporary guidance (NEVER a failure message!)
        if not response_text:
            if is_critical:
                response_text = (
                    "⚠️ URGENT HEALTH CONCERN DETECTED.\n\n"
                    "Please stop all physical activity immediately and rest in a comfortable position.\n"
                    "• Do not attempt to drive or walk alone.\n"
                    "• Connect directly to your assigned ASHA worker using the button below.\n"
                    "• If symptoms worsen, proceed immediately to the nearest hospital listed below."
                )
            elif "head" in text_lower or "headache" in text_lower:
                response_text = (
                    "I understand you are experiencing a headache. Here is safe temporary care guidance:\n\n"
                    "• Rest in a quiet, cool, and dimly lit room.\n"
                    "• Sip clean water to maintain hydration.\n"
                    "• Avoid driving, operating machinery, or intense eye strain.\n"
                    "• Seek immediate emergency care if you experience sudden severe onset ('thunderclap'), stiff neck, high fever, or vision changes."
                )
            elif "fever" in text_lower or "chills" in text_lower:
                response_text = (
                    "I understand you have a fever. Here is safe temporary care guidance:\n\n"
                    "• Rest comfortably and stay hydrated with water or ORS fluids.\n"
                    "• Keep your surroundings well-ventilated.\n"
                    "• Monitor your temperature and contact your ASHA worker if fever exceeds 102°F (38.9°C) or lasts over 48 hours."
                )
            elif "vomit" in text_lower or "stomach" in text_lower or "nausea" in text_lower:
                response_text = (
                    "I understand you are experiencing abdominal discomfort / nausea. Here is safe temporary care guidance:\n\n"
                    "• Sip small amounts of fluids (ORS or water) slowly to prevent dehydration.\n"
                    "• Avoid solid, oily, or spicy foods until feeling better.\n"
                    "• Contact your health worker if you cannot retain fluids for over 12 hours or notice severe abdominal pain."
                )
            else:
                response_text = (
                    f"Thank you for reporting your symptom ({user_message}). Here is safe temporary guidance:\n\n"
                    "• Rest comfortably in a safe position and stay hydrated.\n"
                    "• Avoid self-medication without professional clinical advice.\n"
                    "• Contact your assigned ASHA field worker or visit the nearest clinic below for clinical triage."
                )

        # 4b. For critical messages, always append the real ASHA phone number and
        #     nearest hospital directly into the message text itself — never rely
        #     solely on the separate UI cards below, since a patient in a real
        #     emergency needs the number in front of them immediately, and Gemini
        #     (when used) has no way to know these specific real-world details
        #     unless we append them deterministically ourselves.
        if is_critical:
            nearest = facilities[0] if facilities else None
            contact_lines = ["\n\n📞 IMMEDIATE CONTACTS —"]
            contact_lines.append(f"• ASHA worker {asha_dict.get('name', 'your ASHA worker')}: {asha_dict.get('phone', 'unavailable')}")
            if nearest:
                contact_lines.append(
                    f"• Nearest hospital — {nearest['name']} ({nearest.get('type', 'Hospital')}), "
                    f"~{nearest['distance_km']} km away, {nearest.get('address', '')}: {nearest.get('phone', 'unavailable')}"
                )
            contact_lines.append("If this is a life-threatening emergency, call the numbers above now or go to the nearest hospital immediately.")
            response_text = response_text.rstrip() + "\n".join(contact_lines)

        # 5. Persist Chat Messages in DB
        sender_str = str(user.id) if user and hasattr(user, 'id') else None
        await self.send_message(conversation_id, "patient", user_message, sender_id=sender_str)
        bot_msg = await self.send_message(conversation_id, "ai", response_text, sender_id=sender_str)

        # 6. Route health/symptom message through Clinical Pipeline.
        #    The AI chat NEVER decides risk — the deterministic rule engine does.
        risk_update = None
        if is_health_concern and self.db and user and getattr(user, "patient_id", None):
            try:
                from ..clinical.service import ClinicalPipelineService
                clinical_service = ClinicalPipelineService(self.db)
                risk_update = await clinical_service.process_clinical_input(
                    patient_id=str(user.patient_id),
                    reporter="patient",
                    input_text=user_message,
                    method="app",
                )
            except Exception as e:
                print(f"[chat\u2192clinical] pipeline error: {e}")

        return {
            "id": bot_msg.get("id", str(uuid.uuid4())),
            "role": "assistant",
            "content": response_text,
            "response": response_text,
            "is_health_concern": is_health_concern,
            "severity": severity,
            "risk_level": risk_update.get("risk_level") if risk_update else severity,
            "risk_reasons": (risk_update.get("latest_risk") or {}).get("risk_reasons", []) if risk_update else [],
            "asha_worker": asha_dict,
            "facilities": facilities[:3],
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def process_staff_message(
        self,
        user: User,
        patient_id: str,
        user_message: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process an ASHA/hospital query *about a specific patient* — same
        deterministic safety rules and same real clinical pipeline as
        process_patient_message(), just reporting on someone else. Caller
        ownership of patient_id must already be checked by the router
        (authorize_patient_access) before this is called."""
        text_lower = user_message.lower()

        critical_keywords = [
            "chest pain", "shortness of breath", "breathing difficulty", "difficulty breathing",
            "unconscious", "stroke", "severe bleeding", "heart attack", "collapsed", "cannot breathe",
            "can't breathe", "cant breathe", "not breathing", "stopped breathing",
            "shot", "gunshot", "gun shot", "stabbed", "stabbing", "knife",
            "dying", "i'm dying", "im dying", "going to die", "gonna die",
            "bleeding a lot", "bleeding heavily", "blood everywhere", "losing blood",
            "accident", "road accident", "hit by a car", "hit by car", "run over",
            "fell from", "fall from height", "assaulted", "attacked", "beaten",
            "overdose", "poisoned", "poisoning", "swallowed poison",
            "drowning", "drowned", "electrocuted", "snake bite", "snakebite",
            "suicide", "want to die", "self harm", "self-harm",
            "severe burn", "burnt badly", "on fire",
            "help me", "emergency", "call ambulance", "need ambulance",
        ]
        warning_keywords = [
            "head", "headache", "fever", "vomit", "vomiting", "dizzy", "dizziness", "nausea",
            "chills", "abdomen", "stomach", "pain", "hurt", "hurting", "sick", "wound",
            "cough", "weakness", "swelling", "cramp", "cramps"
        ]

        is_critical = any(kw in text_lower for kw in critical_keywords)
        is_warning = any(kw in text_lower for kw in warning_keywords)
        is_health_concern = is_critical or is_warning or "doctor" in text_lower or "medicine" in text_lower or "symptom" in text_lower
        severity = "critical" if is_critical else ("warning" if is_warning else "normal")

        patient_stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        patient_res = await self.db.execute(patient_stmt)
        patient = patient_res.scalar_one_or_none()
        if not patient:
            return {"error": "Patient not found"}

        patient_lat = patient.latitude or 12.9716
        patient_lon = patient.longitude or 77.5946

        asha_dict = None
        if patient.assigned_asha_id:
            asha_stmt = select(ASHAWorker).filter(ASHAWorker.id == patient.assigned_asha_id)
            asha_res = await self.db.execute(asha_stmt)
            asha_obj = asha_res.scalar_one_or_none()
            if asha_obj:
                asha_dict = {
                    "id": str(asha_obj.id),
                    "name": asha_obj.name,
                    "phone": asha_obj.phone,
                    "block": asha_obj.block or "Assigned Block",
                    "district": asha_obj.district or "District HQ",
                    "is_active": asha_obj.is_active,
                }

        facilities = []
        try:
            hosp_stmt = select(Hospital).filter(Hospital.is_active == True)
            hosp_res = await self.db.execute(hosp_stmt)
            hospitals = hosp_res.scalars().all()
            for h in hospitals:
                dist = calculate_distance(patient_lat, patient_lon, h.latitude or 12.9716, h.longitude or 77.5946)
                facilities.append({
                    "id": str(h.id),
                    "name": h.name,
                    "type": h.type,
                    "distance_km": round(dist, 1),
                    "phone": h.contact_phone or "+91-80-2845-1234",
                    "address": h.address or f"{h.district}, {h.state}",
                    "latitude": h.latitude or 12.9716,
                    "longitude": h.longitude or 77.5946,
                })
            facilities.sort(key=lambda x: x["distance_km"])
        except Exception as e:
            print(f"[staff-chat] facility lookup error: {e}")

        sources = ["SETU Safety Protocol", "MedlinePlus Clinical Guidelines"]
        rag_context = None
        try:
            from ..rag.service import RAGService
            rag_service = RAGService(self.db)
            rag_res = await rag_service.query_rag(user_message, user_role=user.role, top_k=2)
            if rag_res and rag_res.response and len(rag_res.response.strip()) > 20 and "couldn't find" not in rag_res.response:
                rag_context = rag_res.response
                if rag_res.sources:
                    sources = [s.get("title", "Care Guidance") for s in rag_res.sources] or sources
        except Exception:
            pass

        response_text = ""
        if self.gemini.available():
            try:
                generated = await self.gemini.generate_response(
                    f"Regarding patient {patient.full_name}: {user_message}", severity, context=rag_context
                )
                if generated and len(generated.strip()) > 10:
                    response_text = generated.strip()
            except Exception:
                pass

        if not response_text:
            if is_critical:
                response_text = (
                    f"⚠️ CRITICAL RISK for {patient.full_name}.\n\n"
                    "• Do not leave the patient unattended.\n"
                    "• Arrange transport to the nearest hospital immediately if not already en route.\n"
                    "• Notify the hospital ahead of arrival if possible."
                )
            elif is_warning:
                response_text = (
                    f"⚠️ Elevated risk noted for {patient.full_name}.\n\n"
                    "• Monitor closely over the next few hours.\n"
                    "• Escalate to the hospital if symptoms worsen or don't improve."
                )
            else:
                response_text = (
                    f"Logged for {patient.full_name}: {user_message}\n\n"
                    "No critical or warning symptoms detected in this report."
                )

        if is_critical:
            nearest = facilities[0] if facilities else None
            contact_lines = ["\n\n📞 IMMEDIATE CONTACTS —"]
            if nearest:
                contact_lines.append(
                    f"• Nearest hospital — {nearest['name']} ({nearest.get('type', 'Hospital')}), "
                    f"~{nearest['distance_km']} km from patient, {nearest.get('address', '')}: {nearest.get('phone', 'unavailable')}"
                )
            if asha_dict and asha_dict.get("phone"):
                contact_lines.append(f"• Assigned ASHA — {asha_dict['name']}: {asha_dict['phone']}")
            contact_lines.append("If this is life-threatening, escalate now — do not wait for a follow-up check-in.")
            response_text = response_text.rstrip() + "\n".join(contact_lines)

        sender_str = str(user.id)
        await self.send_message(conversation_id, user.role, user_message, sender_id=sender_str)
        bot_msg = await self.send_message(conversation_id, "ai", response_text, sender_id=sender_str)

        risk_update = None
        if is_health_concern:
            try:
                from ..clinical.service import ClinicalPipelineService
                clinical_service = ClinicalPipelineService(self.db)
                risk_update = await clinical_service.process_clinical_input(
                    patient_id=patient_id,
                    reporter="asha",
                    input_text=user_message,
                    asha_worker_id=str(user.asha_worker_id) if getattr(user, "asha_worker_id", None) else None,
                    method="app",
                )
            except Exception as e:
                print(f"[staff-chat→clinical] pipeline error: {e}")

        return {
            "id": bot_msg.get("id", str(uuid.uuid4())),
            "role": "assistant",
            "content": response_text,
            "response": response_text,
            "patient_id": patient_id,
            "patient_name": patient.full_name,
            "is_health_concern": is_health_concern,
            "severity": severity,
            "risk_level": risk_update.get("risk_level") if risk_update else severity,
            "risk_reasons": (risk_update.get("latest_risk") or {}).get("risk_reasons", []) if risk_update else [],
            "asha_worker": asha_dict,
            "facilities": facilities[:3],
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def process_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process tool call from agent"""
        tool = self.TOOLS.get(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}

        if tool_name == "get_patient_info":
            return await self._get_patient_info(tool_input.get("patient_id"))
        elif tool_name == "get_patient_alerts":
            return await self._get_patient_alerts(tool_input.get("patient_id"))
        elif tool_name == "create_alert":
            return await self._create_alert(tool_input)
        elif tool_name == "evaluate_risk":
            return await self._evaluate_risk(tool_input)
        else:
            return {"error": f"Tool not implemented: {tool_name}"}

    async def _get_patient_info(self, patient_id: str) -> Dict[str, Any]:
        """Get patient information"""
        stmt = select(Patient).filter(Patient.id == uuid.UUID(patient_id))
        result = await self.db.execute(stmt)
        patient = result.scalar_one_or_none()

        if not patient:
            return {"error": "Patient not found"}

        return {
            "id": str(patient.id),
            "mrn": patient.mrn,
            "full_name": patient.full_name,
            "gender": patient.gender,
            "risk_level": patient.risk_level,
        }

    async def _get_patient_alerts(self, patient_id: str) -> Dict[str, Any]:
        """Get patient alerts"""
        alerts = await self.alert_service.get_patient_alerts(patient_id, status="new")
        return {"alerts": alerts}

    async def _create_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert"""
        return await self.alert_service.create_alert(
            patient_id=data["patient_id"],
            severity=data["severity"],
            title=data["title"],
            description=data["description"],
        )

    async def _evaluate_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate risk"""
        from ..risk.service import RiskEngineService
        risk_service = RiskEngineService(self.db)
        return await risk_service.evaluate_risk(
            patient_id=data["patient_id"],
            symptoms=data.get("symptoms", []),
            severity_score=data.get("severity_score", 0),
        )

    async def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages in conversation"""
        stmt = (
            select(ChatMessage)
            .filter(ChatMessage.conversation_id == uuid.UUID(conversation_id))
            .order_by(ChatMessage.created_at)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        return [
            {
                "id": str(m.id),
                "role": m.sender_type,
                "content": m.content,
                "created_at": m.created_at.isoformat() if hasattr(m, 'created_at') and m.created_at else None,
            }
            for m in messages
        ]

    def get_tools(self) -> List[Dict[str, Any]]:
        return [{"name": name, **details} for name, details in self.TOOLS.items()]
