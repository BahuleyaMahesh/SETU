"""
Deterministic Risk Rules for SETU

RULE: AI extracts and assists.
Deterministic rules decide risk.
Humans act.

This module contains the risk evaluation rules that determine patient risk levels.
The rules are deterministic and based on clinical criteria.
AI can assist with symptom extraction but CANNOT make risk decisions.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    """Represents a risk factor with its weight and severity level"""
    name: str
    weight: int  # Score multiplier
    level: str  # risk level: normal, warning, critical


@dataclass
class RiskEvaluation:
    """Risk evaluation result"""
    risk_level: RiskLevel
    score: float
    factors: List[str]
    reasons: List[str]
    action_required: Optional[str] = None


# Risk factors with their weights and associated levels
RISK_FACTORS: Dict[str, RiskFactor] = {
    # Critical symptoms - immediate risk
    "breathing_difficulty": RiskFactor("breathing_difficulty", weight=10, level="critical"),
    "chest_pain": RiskFactor("chest_pain", weight=10, level="critical"),
    "bleeding": RiskFactor("bleeding", weight=10, level="critical"),
    "unconsciousness": RiskFactor("unconsciousness", weight=10, level="critical"),
    "seizure": RiskFactor("seizure", weight=10, level="critical"),
    "stroke_symptoms": RiskFactor("stroke_symptoms", weight=10, level="critical"),
    "severe_pain": RiskFactor("severe_pain", weight=5, level="warning"),
    "high_fever": RiskFactor("high_fever", weight=5, level="critical"),  # >102F
    "fever": RiskFactor("fever", weight=2, level="warning"),
    "dehydration": RiskFactor("dehydration", weight=5, level="warning"),
    "vomiting": RiskFactor("vomiting", weight=1, level="normal"),
    "diarrhea": RiskFactor("diarrhea", weight=1, level="normal"),
    # High-risk patient factors
    "age_over_60": RiskFactor("age_over_60", weight=5, level="warning"),
    "age_under_1": RiskFactor("age_under_1", weight=5, level="warning"),
    "pregnant": RiskFactor("pregnant", weight=3, level="warning"),
    "diabetes": RiskFactor("diabetes", weight=3, level="warning"),
    "heart_disease": RiskFactor("heart_disease", weight=4, level="warning"),
    "lung_disease": RiskFactor("lung_disease", weight=3, level="warning"),
    "immunocompromised": RiskFactor("immunocompromised", weight=4, level="warning"),
}

# Critical thresholds for risk level determination
CRITICAL_THRESHOLD = 7
WARNING_THRESHOLD = 3


def evaluate_risk(symptoms: List[str], patient_age: Optional[int] = None,
                  medical_conditions: Optional[List[str]] = None) -> RiskEvaluation:
    """
    Evaluate patient risk using deterministic rules.

    Args:
        symptoms: List of reported symptoms
        patient_age: Patient's age (optional)
        medical_conditions: List of medical conditions (optional)

    Returns:
        RiskEvaluation with risk level, score, factors, and reasons
    """
    score = 0.0
    factors = []
    reasons = []

    # Check for critical symptoms first (these trigger immediate critical level)
    critical_symptoms = ["breathing_difficulty", "chest_pain", "bleeding",
                        "unconsciousness", "seizure", "stroke_symptoms"]

    has_critical_symptom = False
    for symptom in symptoms:
        if symptom.lower() in critical_symptoms:
            score += RISK_FACTORS[symptom.lower()].weight
            factors.append(symptom.lower())
            reasons.append(f"Critical symptom: {symptom}")
            has_critical_symptom = True

    # If we have a critical symptom, determine exact level based on total score
    if has_critical_symptom:
        score = max(score, CRITICAL_THRESHOLD)  # At least critical minimum
    else:
        # Check non-critical symptoms
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            if symptom_lower in RISK_FACTORS:
                factor = RISK_FACTORS[symptom_lower]
                score += factor.weight
                factors.append(symptom_lower)
                reasons.append(f"Symptom: {symptom}")

    # Apply patient risk factors
    if patient_age is not None:
        if patient_age > 60:
            score += RISK_FACTORS["age_over_60"].weight
            factors.append("age_over_60")
            reasons.append("Advanced age (>60 years)")
        elif patient_age < 1:
            score += RISK_FACTORS["age_under_1"].weight
            factors.append("age_under_1")
            reasons.append("Infant age (<1 year)")

    if medical_conditions:
        for condition in medical_conditions:
            condition_lower = condition.lower()
            if condition_lower in RISK_FACTORS:
                factor = RISK_FACTORS[condition_lower]
                score += factor.weight
                factors.append(condition_lower)
                reasons.append(f"Medical condition: {condition}")

    # Determine risk level based on score
    risk_level = _determine_risk_level(score)

    # Get required action based on risk level
    action_required = _get_action_required(risk_level)

    return RiskEvaluation(
        risk_level=risk_level,
        score=round(score, 2),
        factors=factors,
        reasons=reasons,
        action_required=action_required,
    )


def _determine_risk_level(score: float) -> RiskLevel:
    """Determine risk level based on score using deterministic rules"""
    if score >= CRITICAL_THRESHOLD:
        return RiskLevel.CRITICAL
    elif score >= WARNING_THRESHOLD:
        return RiskLevel.WARNING
    else:
        return RiskLevel.NORMAL


def _get_action_required(risk_level: RiskLevel) -> Optional[str]:
    """Get required action based on risk level"""
    actions = {
        RiskLevel.CRITICAL: "Immediate medical attention required - call emergency services",
        RiskLevel.WARNING: "Monitor closely, seek medical attention if symptoms worsen",
        RiskLevel.NORMAL: "Continue routine care and monitoring",
    }
    return actions.get(risk_level)


def is_risk_elevated(evaluation: RiskEvaluation, target_level: RiskLevel) -> bool:
    """Check if risk is at or above target level"""
    level_order = {RiskLevel.NORMAL: 0, RiskLevel.WARNING: 1, RiskLevel.CRITICAL: 2}
    return level_order.get(evaluation.risk_level, 0) >= level_order.get(target_level, 0)


def get_critical_symptoms() -> List[str]:
    """Get list of critical symptoms that require immediate attention"""
    return ["breathing_difficulty", "chest_pain", "bleeding",
            "unconsciousness", "seizure", "stroke_symptoms"]


def get_high_risk_patient_conditions() -> List[str]:
    """Get list of conditions that increase patient risk"""
    return ["diabetes", "heart_disease", "lung_disease", "immunocompromised"]
