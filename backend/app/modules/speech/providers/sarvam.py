import asyncio
import logging
from typing import Optional, Dict, Any

import httpx

from ..base import SpeechProvider
from ....core.config import settings

logger = logging.getLogger("setu.speech.sarvam")

# Sarvam's sync STT endpoint is measurably flaky under real use — confirmed
# live against a real check-in call and reproduced directly: identical
# requests returned 200, a transient 404, and a >30s read timeout within the
# same minute. A single attempt therefore loses a real patient's spoken
# symptoms to a blip, so retry before giving up. The timeout is generous
# because the audio is up to 25s of speech (record_start's max_length).
REQUEST_TIMEOUT_SECONDS = 60.0
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.5


class SarvamProvider(SpeechProvider):
    """Sarvam AI speech provider — real speech-to-text for Indian languages
    via https://api.sarvam.ai/speech-to-text (Saaras model). Falls back to a
    clearly-labeled canned response if SARVAM_API_KEY is missing or the call
    fails, matching every other provider in this codebase's safe-fallback
    pattern — never lets a transcription failure become a silent wrong
    clinical read."""

    name = "sarvam"

    def __init__(self):
        self.api_key = getattr(settings, "SARVAM_API_KEY", None)

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("// SETU-CONFIG-REQUIRED: SARVAM_API_KEY — Sarvam AI Speech API key missing, using fallback response")
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language or "unknown",
                "error": "sarvam_unavailable",
            }

        last_error = "unknown error"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        "https://api.sarvam.ai/speech-to-text",
                        headers={"api-subscription-key": self.api_key},
                        files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
                        data={
                            "model": model or "saaras:v3",
                            # "unknown" auto-detects the spoken language rather than
                            # assuming Hindi — patients may speak any of several
                            # regional languages, not knowable in advance per call.
                            "language_code": language or "unknown",
                        },
                    )
                response.raise_for_status()
                data = response.json()
                return {
                    "transcript": data.get("transcript", ""),
                    "confidence": data.get("language_probability", 0.0) or 0.0,
                    "language": data.get("language_code") or language or "unknown",
                }
            except httpx.HTTPStatusError as e:
                # 4xx that isn't rate-limiting is a real request problem —
                # retrying the identical payload won't help.
                last_error = e.response.text or f"HTTP {e.response.status_code}"
                if 400 <= e.response.status_code < 500 and e.response.status_code not in (404, 408, 429):
                    logger.error(f"Sarvam transcription failed (no retry): {last_error}")
                    break
                logger.warning(f"Sarvam transcription attempt {attempt}/{MAX_ATTEMPTS} failed: {last_error}")
            except Exception as e:
                # httpx.ReadTimeout stringifies to "" — name the exception type
                # so the log says what actually happened instead of a blank.
                last_error = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
                logger.warning(f"Sarvam transcription attempt {attempt}/{MAX_ATTEMPTS} failed: {last_error}")

            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)

        logger.error(f"Sarvam transcription failed after {MAX_ATTEMPTS} attempts: {last_error}")
        return {"transcript": "", "confidence": 0.0, "language": language or "unknown", "error": last_error}

    async def detect_language(self, audio_data: bytes) -> str:
        result = await self.transcribe(audio_data, language="unknown")
        return result.get("language") or "unknown"
