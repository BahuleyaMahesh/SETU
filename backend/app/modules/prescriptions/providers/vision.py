import json
from typing import Any, Dict

from ....core.providers import gemini_generate_from_image, gemini_available

PRESCRIPTION_PROMPT = (
    "Read this prescription image and extract the medications as JSON only, no prose. "
    'Respond with exactly this shape: {"medications": [{"name": str, "dosage": str, '
    '"frequency": str, "duration": int|null, "instructions": str|null}]}. '
    "If the image is unreadable or not a prescription, return {\"medications\": []}."
)


class GeminiVisionProvider:
    """Reads a prescription photo directly (no separate OCR step needed)."""

    name = "gemini"

    def available(self) -> bool:
        return gemini_available()

    async def extract_from_image(self, image_path: str) -> Dict[str, Any]:
        text = await gemini_generate_from_image(image_path, PRESCRIPTION_PROMPT)
        if not text:
            return {"medications": [], "error": "gemini_unavailable"}

        try:
            # Model sometimes wraps JSON in a code fence despite the prompt.
            cleaned = text.strip().strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            data = json.loads(cleaned)
            return {"medications": data.get("medications", []) or []}
        except Exception:
            return {"medications": [], "error": "unparseable_response"}
