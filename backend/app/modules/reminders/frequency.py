"""Maps a prescription's free-text dosage frequency (as read off a real
prescription — abbreviations, Indian-style "1-0-1" tablet notation, or plain
English) to the clock times a medication reminder should fire each day.

This is a deterministic, best-effort heuristic — not a validated clinical
dosing schedule. Same "AI extracts, rules decide" pattern as the rest of the
app: the frequency TEXT was already extracted by Gemini vision; this module
only maps recognized text patterns to times, it doesn't interpret meaning.
Unrecognized text falls back to once daily rather than silently creating no
reminder at all.
"""

import re
from datetime import time
from typing import List

MORNING = time(8, 0)
AFTERNOON = time(14, 0)
EVENING = time(18, 0)
NIGHT = time(21, 0)

_ABBREVIATIONS = {
    "od": [MORNING],
    "qd": [MORNING],
    "once daily": [MORNING],
    "once a day": [MORNING],
    "1 time a day": [MORNING],
    "bd": [MORNING, NIGHT],
    "bid": [MORNING, NIGHT],
    "twice daily": [MORNING, NIGHT],
    "twice a day": [MORNING, NIGHT],
    "2 times a day": [MORNING, NIGHT],
    "two times a day": [MORNING, NIGHT],
    "tds": [MORNING, AFTERNOON, NIGHT],
    "tid": [MORNING, AFTERNOON, NIGHT],
    "thrice daily": [MORNING, AFTERNOON, NIGHT],
    "three times a day": [MORNING, AFTERNOON, NIGHT],
    "three times daily": [MORNING, AFTERNOON, NIGHT],
    "3 times a day": [MORNING, AFTERNOON, NIGHT],
    "qid": [MORNING, AFTERNOON, EVENING, NIGHT],
    "four times a day": [MORNING, AFTERNOON, EVENING, NIGHT],
    "four times daily": [MORNING, AFTERNOON, EVENING, NIGHT],
    "4 times a day": [MORNING, AFTERNOON, EVENING, NIGHT],
}

_TIME_WORDS = [
    (re.compile(r"\bmorning\b"), MORNING),
    (re.compile(r"\bafternoon\b"), AFTERNOON),
    (re.compile(r"\bevening\b"), EVENING),
    (re.compile(r"\bnight\b"), NIGHT),
    (re.compile(r"\bbedtime\b"), NIGHT),
    (re.compile(r"\bhs\b"), NIGHT),  # "hora somni" — at bedtime
]

# Indian prescription shorthand: "1-0-1" / "1-1-1" style, three slots for
# morning-afternoon-night; a slot is "on" whenever it's a non-zero number.
_DASH_PATTERN = re.compile(r"^\s*(\d+)\s*[-/]\s*(\d+)\s*[-/]\s*(\d+)\s*$")


def parse_frequency_to_times(frequency: str) -> List[time]:
    """Returns the times of day a reminder should fire for this frequency
    text. Always returns at least one time — falls back to once-daily
    (morning) for anything unrecognized, so a medication with an odd or
    unclear frequency string still gets a reminder rather than none."""
    if not frequency:
        return [MORNING]

    text = frequency.strip().lower()

    dash_match = _DASH_PATTERN.match(text)
    if dash_match:
        slots = [MORNING, AFTERNOON, NIGHT]
        times = [slots[i] for i, val in enumerate(dash_match.groups()) if int(val) > 0]
        return times or [MORNING]

    for phrase, times in _ABBREVIATIONS.items():
        if phrase in text:
            return times

    found = [t for pattern, t in _TIME_WORDS if pattern.search(text)]
    if found:
        # De-duplicate while preserving order (e.g. "morning and night").
        seen = []
        for t in found:
            if t not in seen:
                seen.append(t)
        return seen

    return [MORNING]
