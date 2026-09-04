import json
import re
from typing import Any, Dict

from ....core.providers import gemini_generate_from_image, gemini_available

PRESCRIPTION_PROMPT = (
    "You are reading a photo of a doctor's prescription, discharge slip, or medication "
    "note for a rural health worker. It may be neatly printed, or it may be handwritten "
    "in a doctor's cursive — read handwriting carefully, the way a pharmacist would. "
    "Extract every medication you can confidently identify, along with its dosage, "
    "frequency, duration, and any instructions that are visible. "
    "Do this entry by entry: if the page has several medications and only some are "
    "clearly legible, still return the legible ones — do not discard everything just "
    "because part of the handwriting is messy or one line is unclear. Skip only the "
    "individual medications whose name you genuinely cannot make out. If you can read "
    "a medication's name but not its dosage or frequency, still include it with that "
    "field set to null rather than dropping it. "
    "Respond with JSON only, no prose, no markdown code fences. Respond with exactly "
    'this shape: {"medications": [{"name": str, "dosage": str|null, "frequency": str|null, '
    '"duration": int|null, "instructions": str|null}]}. '
    "If the image contains no legible medication names at all (blank, unrelated photo, "
    'or entirely illegible), return {"medications": []}.'
)

_IMAGE_MIME_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "heic": "image/heic",
    "heif": "image/heif",
}


def _guess_mime_type(image_path: str) -> str:
    ext = image_path.rsplit(".", 1)[-1].lower() if "." in image_path else ""
    return _IMAGE_MIME_TYPES.get(ext, "image/jpeg")


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
            data = json.loads(_extract_json_object(text))
            medications = data.get("medications", []) or []
            # Only a name is required to keep an entry — everything else can be
            # unclear on a handwritten page without losing the whole medication.
            medications = [m for m in medications if isinstance(m, dict) and (m.get("name") or "").strip()]
            return {"medications": medications}
        except Exception:
            return {"medications": [], "error": "unparseable_response"}


def _extract_json_object(text: str) -> str:
    """Pull the JSON object out of a model response that may add prose or a code fence."""
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return cleaned[brace_start:brace_end + 1]
    return cleaned
