from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from .providers.mock import MockProvider
from .providers.bhashini import BhashiniProvider
from .providers.indicwhisper import IndicWhisperProvider
from .providers.sarvam import SarvamProvider


class SpeechProviderFactory:
    """Factory for speech providers"""

    @staticmethod
    def get_provider() -> Any:
        """Get configured speech provider"""
        provider_name = settings.SPEECH_PROVIDER

        providers = {
            "mock": MockProvider,
            "bhashini": BhashiniProvider,
            "indicwhisper": IndicWhisperProvider,
            "sarvam": SarvamProvider,
        }

        provider_class = providers.get(provider_name, MockProvider)
        return provider_class()


class SpeechService:
    """Speech-to-text service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = SpeechProviderFactory.get_provider()

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        """Transcribe audio to text"""
        return await self.provider.transcribe(
            audio_data=audio_data,
            language=language,
            model=model,
        )

    async def detect_language(self, audio_data: bytes) -> str:
        """Detect language from audio"""
        return await self.provider.detect_language(audio_data)
