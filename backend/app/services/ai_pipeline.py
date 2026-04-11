import logging
import os
import re

logger = logging.getLogger(__name__)

# Simplified mock dictionaries for rule-based engine
CRITICAL_KEYWORDS = ["emergency", "severe", "cannot breathe", "bleeding", "collapse", "heart", "help"]
WARNING_KEYWORDS = ["pain", "fever", "dizzy", "weak", "vomiting", "headache"]
NORMAL_KEYWORDS = ["fine", "good", "okay", "better", "normal"]

def mock_stt(audio_url: str):
    """
    Mock STT to avoid heavy transcription dependencies in the initial pilot.
    In real app, this downloads `audio_url` and passes it to Groq Whisper API or OpenAI Whisper.
    For demonstration, we return some dummy text.
    """
    logger.info(f"Processing audio from {audio_url}")
    return "I am feeling a little pain today."

def extract_keywords_nlp(text: str):
    """
    NLP layer to extract keywords.
    Can be replaced by an LLM-based entity extraction.
    For reliability and cost, rule-based Regex is used in 2G environments as baseline.
    """
    text_lower = text.lower()
    found_critical = [kw for kw in CRITICAL_KEYWORDS if kw in text_lower]
    found_warning = [kw for kw in WARNING_KEYWORDS if kw in text_lower]
    
    return {
        "critical": found_critical,
        "warning": found_warning
    }

def rule_based_classification(symptoms: dict, dtmf_input: str = None):
    """
    The deterministic Decision Engine.
    MANDATORY rule: always favor the highest severity.
    DTMF overrides AI sentiment. (1: Fine, 2: Warning, 3: Critical)
    """
    # 1. Check direct DTMF override
    if dtmf_input == "3":
        return "CRITICAL"
    elif dtmf_input == "2":
        return "WARNING"
    elif dtmf_input == "1":
        return "NORMAL"
        
    # 2. Check extracted NLP features
    if len(symptoms.get("critical", [])) > 0:
        return "CRITICAL"
    elif len(symptoms.get("warning", [])) > 0:
        return "WARNING"
        
    # 3. Default fallback
    return "NORMAL"

def process_interaction_pipeline(audio_url: str = None, dtmf_input: str = None):
    """
    Full pipeline combining STT, Keyword extraction, and Classification.
    """
    transcript = ""
    symptoms = {"critical": [], "warning": []}
    
    if audio_url:
        transcript = mock_stt(audio_url)
        symptoms = extract_keywords_nlp(transcript)
        
    risk_level = rule_based_classification(symptoms, dtmf_input)
    
    return {
        "transcript": transcript,
        "extracted_symptoms": symptoms,
        "risk_classification": risk_level
    }
