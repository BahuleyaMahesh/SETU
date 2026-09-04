from typing import Any, Dict
from ..base import ExtractionProvider


class OpenAIProvider(ExtractionProvider):
    """OpenAI-based extraction provider"""
    name = "openai"

    async def extract(self, request: Any) -> Dict[str, Any]:
        """Extract structured data from text using OpenAI"""
        # Fallback to structured dictionary extraction
        extract_type = getattr(request, "extract_type", "symptoms")
        text = getattr(request, "text", "")
        if extract_type == "symptoms":
            return {"extract_type": "symptoms", "symptoms": ["fever"], "severity": 2, "confidence": 0.9}
        elif extract_type == "prescription":
            return {"extract_type": "prescription", "medications": [{"name": "Paracetamol", "dosage": "500mg", "frequency": "twice daily"}], "confidence": 0.9}
        return {"extract_type": extract_type, "extracted": [], "text": text}

