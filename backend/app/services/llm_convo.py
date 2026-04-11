import os
import json
import logging
from groq import Groq
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# The API key should be loaded securely from the .env file in production
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class AIAnalysis(BaseModel):
    reply_text: str
    risk_classification: str
    detected_keywords: list[str]

system_prompt = """
You are SETU, an empathetic, AI health assistant for rural patients in India. 
You are currently on a voice call. Keep responses short (1-2 sentences max), empathetic, and spoken in a conversational, comforting tone.
Initially, if the user hasn't spoken, ask them: "Namaskara! How are you feeling today? You can speak naturally to me, or press 1 on your keypad for fine, 2 for pain, and 3 for an emergency."
Analyze their input contextually. Do not use hardcoded responses. React dynamically to what they say.
Classify the overall risk as exactly one of: NORMAL, WARNING, CRITICAL.
Identify a few underlying keywords or symptoms they mentioned (e.g. "headache", "chest pain", "fever").
Return ONLY a valid JSON object matching this schema:
{"reply_text": "string", "risk_classification": "NORMAL|WARNING|CRITICAL", "detected_keywords": ["keyword1", "keyword2"]}
"""

def generate_conversational_response(chat_history: list, latest_input: str) -> dict:
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history:
        messages.append({"role": "assistant" if msg["sender"] in ["ai", "system"] else "user", "content": msg["text"]})
        
    messages.append({"role": "user", "content": latest_input})

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=150
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        # Ensure schema safety
        if parsed.get("risk_classification") not in ["NORMAL", "WARNING", "CRITICAL"]:
            parsed["risk_classification"] = "NORMAL"
        return parsed
    except Exception as e:
        logger.error(f"Groq API Error: {e}. Falling back to sophisticated mock.")
        return _sophisticated_mock_fallback(latest_input)

def _sophisticated_mock_fallback(user_text: str) -> dict:
    """Simulates a context-aware LLM for demo purposes when no key is present."""
    text_lower = user_text.lower()
    
    # 1. Determine Intent / Risk
    if any(k in text_lower for k in ["emergency", "severe", "collapse", "can't breathe", "3"]):
        return {
            "reply_text": "I understand this is an emergency. Please try to stay calm. I am immediately connecting your ongoing call to your ASHA worker.",
            "risk_classification": "CRITICAL",
            "detected_keywords": ["emergency", "severe condition"]
        }
    elif any(k in text_lower for k in ["pain", "hurt", "weak", "fever", "dizzy", "headache", "2"]):
        return {
            "reply_text": "I'm so sorry to hear you're feeling that way. It's important we monitor that. I will alert your ASHA worker about this symptom right away.",
            "risk_classification": "WARNING",
            "detected_keywords": ["pain/discomfort reported", "requires attention"]
        }
    elif any(k in text_lower for k in ["fine", "good", "okay", "better", "normal", "1"]):
        return {
            "reply_text": "That's wonderful to hear! I'll mark your daily check-in as completely clear. Remember to drink plenty of water.",
            "risk_classification": "NORMAL",
            "detected_keywords": ["feeling fine", "recovering"]
        }
    else:
        # Spontaneous default if unclear
        return {
            "reply_text": "I see. I have noted down what you said. I will pass this directly to your care team so they can review your condition.",
            "risk_classification": "NORMAL",
            "detected_keywords": ["general update"]
        }
