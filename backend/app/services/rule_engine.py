from typing import List

# Predefined critical and warning keywords mapping
# This logic forms the hard safety-net regardless of what the LLM predicts.

CRITICAL_KEYWORDS = {
    "chest pain", "breathing difficulty", "unconscious", 
    "heavy bleeding", "stroke symptoms", "heart attack", "suicide"
}

WARNING_KEYWORDS = {
    "fever", "headache", "vomiting", "dizziness", 
    "stomach ache", "weakness"
}

def determine_risk(symptoms: List[str]) -> str:
    """
    Evaluates the list of symptoms identified by the AI pipeline
    and maps them to a risk classification purely based on rules.
    """
    symptoms_set = set([s.lower() for s in symptoms])
    
    # 1. Highest Priority Check -> CRITICAL
    if symptoms_set.intersection(CRITICAL_KEYWORDS):
        return "CRITICAL"
        
    # 2. Secondary Check -> WARNING
    if symptoms_set.intersection(WARNING_KEYWORDS):
        return "WARNING"
        
    # 3. Default -> NORMAL
    return "NORMAL"
