from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from ..base import ExtractionProvider



class MockProvider(ExtractionProvider):
    """Mock extraction provider for development"""

    name = "mock"

    async def extract(self, request: Any) -> Dict[str, Any]:
        # Simulate symptom extraction
        mock_symptoms = ["fever", "headache", "cough"]
        mock_medications = [
            {
                "name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration": 5
            }
        ]

        if request.extract_type == "symptoms":
            return {
                "extract_type": "symptoms",
                "symptoms": mock_symptoms,
                "severity": 3,
                "confidence": 0.85,
            }
        elif request.extract_type == "prescription":
            return {
                "extract_type": "prescription",
                "medications": mock_medications,
                "confidence": 0.90,
            }

        return {"extract_type": request.extract_type, "extracted": []}
