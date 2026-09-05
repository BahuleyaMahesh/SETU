from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..base import SpeechProvider



class MockProvider(SpeechProvider):
    """Mock speech provider for development"""

    name = "mock"

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        # Simulate speech-to-text
        return {
            "transcript": "I have fever and headache since yesterday",
            "confidence": 0.95,
            "language": language or "en",
        }

    async def detect_language(self, audio_data: bytes) -> str:
        return "en"
