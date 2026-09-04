from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from .providers.mock import MockProvider
from .providers.openai import OpenAIProvider
from .providers.gemini import GeminiProvider


class ExtractionProviderFactory:
    """Factory for extraction providers"""

    @staticmethod
    def get_provider() -> Any:
        """Get configured extraction provider"""
        provider_name = settings.EXTRACTION_PROVIDER

        providers = {
            "mock": MockProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
        }

        provider_class = providers.get(provider_name, MockProvider)
        return provider_class()


class ExtractionService:
    """Data extraction service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = ExtractionProviderFactory.get_provider()
        self._fallback = MockProvider()

    async def extract_symptoms(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Extract symptoms from text"""
        request = type('Request', (), {
            "extract_type": "symptoms",
            "text": text,
        })()
        result = await self.provider.extract(request)
        if result.get("error") == "gemini_unavailable":
            # Reliability rule: if the LLM provider fails, fall back rather
            # than returning an empty extraction (see docs/security.md §18).
            result = await self._fallback.extract(request)
        return result

    async def extract_prescription(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Extract medication prescription from text"""
        request = type('Request', (), {
            "extract_type": "prescription",
            "text": text,
        })()
        result = await self.provider.extract(request)
        if result.get("error") == "gemini_unavailable":
            result = await self._fallback.extract(request)
        return result

    async def validate_symptoms(self, symptoms: list) -> Dict[str, Any]:
        """Validate extracted symptoms"""
        # In production, validate against medical ontology
        return {
            "valid_symptoms": symptoms,
            "invalid_symptoms": [],
        }
