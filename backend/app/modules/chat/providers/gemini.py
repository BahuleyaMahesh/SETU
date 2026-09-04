from typing import Optional

from ....core.providers import gemini_generate_text, gemini_available


class GeminiChatProvider:
    """Generates the conversational phrasing of patient-facing chat replies.

    This provider never decides severity or risk — ChatService's keyword
    detection (deterministic) has already made that call before this is
    invoked. Gemini's only job here is to phrase safe, grounded guidance in
    plain language, matching SETU's "AI extracts/assists, rules decide"
    principle.
    """

    name = "gemini"

    def available(self) -> bool:
        return gemini_available()

    async def generate_response(
        self,
        user_message: str,
        severity: str,
        context: Optional[str] = None,
    ) -> Optional[str]:
        system_instruction = (
            "You are a calm, brief health-companion assistant for SETU, a post-discharge "
            "rural patient monitoring platform in India. You are speaking directly to a "
            "patient, not a clinician. You NEVER diagnose, prescribe medication, or contradict "
            "the severity level given to you — a deterministic rule engine (not you) has "
            "already made that decision. Your only job is to phrase safe, warm, practical "
            "guidance in plain language, under 120 words, with short bullet points where "
            "helpful. If severity is 'critical', strongly and clearly urge the patient to "
            "contact their ASHA worker or go to the nearest hospital immediately, and do not "
            "suggest home remedies."
        )
        prompt = (
            f"Patient-reported severity (already decided by the rule engine — do not override): {severity}\n"
            f"Patient's message: {user_message}\n"
        )
        if context:
            prompt += f"\nGround your answer in this care guidance where relevant:\n{context}\n"

        return await gemini_generate_text(prompt, system_instruction=system_instruction)
