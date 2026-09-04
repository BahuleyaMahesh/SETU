from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class SpeechProvider(ABC):
    """Base class for speech-to-text providers"""

    name: str = "base"

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        """Transcribe audio to text"""
        pass

    @abstractmethod
    async def detect_language(self, audio_data: bytes) -> str:
        """Detect language from audio"""
        pass
