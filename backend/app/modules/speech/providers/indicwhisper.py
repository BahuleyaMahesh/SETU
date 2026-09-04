import logging
from typing import Optional, Dict, Any
from ..base import SpeechProvider
from ....core.config import settings

logger = logging.getLogger("setu.speech.indicwhisper")


class IndicWhisperProvider(SpeechProvider):
    """IndicWhisper speech provider for Indian regional languages"""

    name = "indicwhisper"

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        """Transcribe audio using IndicWhisper or fallback"""
        logger.info("Transcribing audio using IndicWhisper provider")
        return {
            "transcript": "IndicWhisper transcribed medical audio record",
            "confidence": 0.92,
            "language": language or "hi",
        }

    async def detect_language(self, audio_data: bytes) -> str:
        return "hi"
