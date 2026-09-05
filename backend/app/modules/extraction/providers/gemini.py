from typing import Any, Dict
from ..base import ExtractionProvider
from ....core.providers import gemini_generate_json


class GeminiProvider(ExtractionProvider):
    """Gemini-based structured extraction.

    Extraction only — this never assigns a risk level. The deterministic
    rule engine (app.modules.risk.rules) is the sole source of risk decisions.
    """

    name = "gemini"

    async def extract(self, request: Any) -> Dict[str, Any]:
        extract_type = getattr(request, "extract_type", "symptoms")
        text = getattr(request, "text", "") or ""

        if extract_type == "symptoms":
            return await self._extract_symptoms(text)
        elif extract_type == "prescription":
            return await self._extract_prescription(text)
        return {"extract_type": extract_type, "extracted": [], "text": text}

    async def _extract_symptoms(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract structured symptom data from this patient's spoken check-in transcript. "
            "Return a JSON object with keys: symptoms (array of short lowercase symptom names), "
            "duration_days (number or null), severity_words (array of the patient's own words "
            "describing severity), confidence (0 to 1 float). "
            "Only extract what the patient literally reported — do not diagnose, and do not "
            "assess risk or urgency yourself.\n\n"
            f"Transcript: {text}"
        )
        result = await gemini_generate_json(prompt)
        if result is None:
            return {
                "extract_type": "symptoms",
                "symptoms": [],
                "severity": 0,
                "confidence": 0.0,
                "error": "gemini_unavailable",
            }

        severity_words = result.get("severity_words", []) or []
        return {
            "extract_type": "symptoms",
            "symptoms": result.get("symptoms", []) or [],
            "duration_days": result.get("duration_days"),
            "severity_words": severity_words,
            "severity": len(severity_words),
            "confidence": result.get("confidence", 0.7),
        }

    async def _extract_prescription(self, text: str) -> Dict[str, Any]:
        prompt = (
            "Extract structured medication data from this prescription text. Return a JSON "
            "object with a single key 'medications': an array of objects each with "
            "name, dosage, frequency, duration (integer days or null), instructions "
            "(string or null).\n\n"
            f"Prescription text: {text}"
        )
        result = await gemini_generate_json(prompt)
        if result is None:
            return {
                "extract_type": "prescription",
                "medications": [],
                "confidence": 0.0,
                "error": "gemini_unavailable",
            }

        return {
            "extract_type": "prescription",
            "medications": result.get("medications", []) or [],
            "confidence": 0.85,
        }
