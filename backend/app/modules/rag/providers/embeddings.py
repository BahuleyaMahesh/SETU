from typing import List, Optional

from ....core.providers import gemini_embed, gemini_available


class GeminiEmbeddingProvider:
    """Wraps Gemini's embedding model for RAG chunk/query vectors."""

    name = "gemini"

    def available(self) -> bool:
        return gemini_available()

    async def embed(self, text: str) -> Optional[List[float]]:
        return await gemini_embed(text)
