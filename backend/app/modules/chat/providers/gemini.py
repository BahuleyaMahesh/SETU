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
            "suggest home remedies. This chat renders PLAIN TEXT ONLY, not markdown — never "
            "use **bold**, ### headers, or _italics_; for a bullet point, start the line with "
            "a plain hyphen (-) and nothing else."
        )
        prompt = (
            f"Patient-reported severity (already decided by the rule engine — do not override): {severity}\n"
            f"Patient's message: {user_message}\n"
        )
        if context:
            prompt += f"\nGround your answer in this care guidance where relevant:\n{context}\n"

        return await gemini_generate_text(prompt, system_instruction=system_instruction)

    async def generate_call_guidance(
        self,
        transcript: str,
        risk_level: str,
    ) -> Optional[str]:
        """Phrases the spoken closing guidance for an outbound check-in call
        (calls/router.py's Call Control webhook) — short enough to be read
        aloud by TTS, not read as text. Same rule as generate_response: risk_level
        is already decided by the deterministic rule engine; Gemini only
        phrases what to say about it, tailored to what the patient actually
        described instead of a generic canned line."""
        system_instruction = (
            "You are a calm health assistant phoning a rural patient in India right after "
            "they described their symptoms on a check-in call. Your reply will be read aloud "
            "by text-to-speech, so write ONLY plain spoken sentences — no bullet points, no "
            "headers, no markdown, no lists. HARD LIMIT: at most 2 short sentences, under 35 "
            "words total — every extra second is dead air on a real phone call. You NEVER "
            "diagnose or name a condition, and you NEVER contradict the risk level given to "
            "you — a deterministic rule engine, not you, already decided it. "
            "If risk level is 'critical': in ONE sentence give the single most important "
            "immediate safe action for exactly what they described (e.g. apply firm pressure "
            "with a clean cloth on a bleeding wound, keep a bleeding limb still and raised, "
            "loosen tight clothing for breathing trouble), then in a second short sentence say "
            "to seek medical attention immediately — never suggest they wait it out. "
            "If risk level is 'warning': in one short sentence give simple, safe self-care "
            "(rest, hydrate, monitor) appropriate to what they described, and briefly mention "
            "their ASHA worker will follow up. "
            "If risk level is 'normal': the rule engine found nothing on its recognized list "
            "(it only knows a small set of symptom keywords), but the patient still described "
            "something real — give ONE short sentence of safe, generic, well-known first-aid or "
            "home-care advice for exactly what they described (e.g. a fall/sprain: rest, ice, "
            "keep it elevated; a minor cut: clean it and cover with a plain bandage; suspected "
            "food poisoning: sip water/ORS often and rest, avoid solid food for a while; a mild "
            "headache: rest your eyes, hydrate, step away from work for a few minutes). Only if "
            "what they described sounds like it could still be serious despite the rule engine's "
            "verdict, add that they should mention it to their ASHA worker at the next visit — "
            "otherwise skip that line entirely and keep it to one sentence."
        )
        prompt = (
            f"Risk level (already decided by the rule engine — do not override): {risk_level}\n"
            f"What the patient said on the call: {transcript}\n"
        )
        return await gemini_generate_text(prompt, system_instruction=system_instruction)

    async def answer_roster_query(
        self,
        question: str,
        roster_context: str,
        role: str,
    ) -> Optional[str]:
        """Answers a free-text question against a staff member's own patient
        roster (already scoped server-side — an ASHA's own caseload, or a
        hospital's own patients — before this is ever called). Gemini only
        reads and summarizes the data it's given here; it never decides risk
        (that's the deterministic rule engine, same as everywhere else in
        this app) and it never sees a patient outside the caller's own
        authorization, since the roster text itself is pre-filtered."""
        who = "an ASHA field worker" if role == "asha" else "hospital clinical staff"
        system_instruction = (
            f"You are a clinical data assistant for {who} on SETU, a post-discharge rural "
            "patient monitoring platform in India. Below is the COMPLETE and ONLY patient "
            "roster data available to you — every patient this person is authorized to see, "
            "with the same deterministic risk levels and reasons the app itself computed. "
            "All times in the roster are already given in IST (India local time) — repeat them "
            "exactly as shown, do not convert, relabel as UTC, or add a timezone suffix. "
            "Answer the question using ONLY this data. Never invent a patient, a name, a "
            "number, or a symptom that isn't listed. If the question asks you to count, "
            "filter, or sort, do it accurately by reading the list — do not estimate. If the "
            "data needed to answer isn't in the roster below, say so plainly rather than "
            "guessing. You never decide or change a risk level yourself — those are already "
            "final, computed by SETU's rule engine, not by you. If the question implies an "
            "action (call, message, schedule, escalate, create an alert), tell them which "
            "button or page in the app does that — you cannot perform it yourself. Keep "
            "answers concise and scannable. This chat renders PLAIN TEXT ONLY, not markdown — "
            "never use **bold**, ### headers, or _italics_; for a list of patients, put each "
            "on its own line starting with a plain hyphen (-), nothing else."
        )
        prompt = f"Patient roster:\n{roster_context}\n\nQuestion: {question}\n"
        return await gemini_generate_text(prompt, system_instruction=system_instruction)
