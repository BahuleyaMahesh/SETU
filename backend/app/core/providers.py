"""Shared helpers for external AI providers (currently: Gemini, via google-genai).

Centralizes API-key configuration so individual provider modules don't each
reimplement client setup. All calls are wrapped in `asyncio.to_thread`
because the google-genai SDK is synchronous and this codebase is async.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from .config import settings

logger = logging.getLogger("setu.providers.gemini")

_client = None


def gemini_available() -> bool:
    return bool(settings.GEMINI_API_KEY)


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def gemini_generate_json(prompt: str, system_instruction: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Ask Gemini for a JSON object. Returns None if unavailable or on error."""
    if not gemini_available():
        return None

    def _call():
        from google.genai import types
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )
        return response.text

    try:
        import json
        text = await asyncio.to_thread(_call)
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini JSON generation failed: {e}")
        return None


async def gemini_generate_text(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """Ask Gemini for plain-text output. Returns None if unavailable or on error."""
    if not gemini_available():
        return None

    def _call():
        from google.genai import types
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
        )
        return response.text

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:
        logger.error(f"Gemini text generation failed: {e}")
        return None


async def gemini_generate_from_image(image_path: str, prompt: str) -> Optional[str]:
    """Ask Gemini to read an image (e.g. a prescription photo) and respond to a prompt."""
    if not gemini_available():
        return None

    def _call():
        from google.genai import types
        client = _get_client()

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = image_path.rsplit(".", 1)[-1].lower()
        mime_type = "image/png" if ext == "png" else "image/jpeg"

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
        )
        return response.text

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:
        logger.error(f"Gemini image generation failed: {e}")
        return None


async def gemini_embed(text: str) -> Optional[List[float]]:
    """Return an embedding vector for text, or None if unavailable/failed."""
    if not gemini_available():
        return None

    def _call():
        client = _get_client()
        result = client.models.embed_content(model=settings.GEMINI_EMBEDDING_MODEL, contents=text)
        return list(result.embeddings[0].values)

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:
        logger.error(f"Gemini embedding failed: {e}")
        return None
