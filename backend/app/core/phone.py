"""Phone number normalization to +E164.

Telephony providers (Telnyx, Twilio) hard-reject anything that isn't strict
+E164 — Telnyx returns error 10016 "Phone number must be in +E164 format"
and the call is never placed at all. This app's phone numbers come from
human data entry (ASHA/hospital "Add Patient" forms, patient self-signup)
so they show up in every shape a person might type: "+91-98765-43210",
"98765 43210", "09123456789", "919123456789". Confirmed live: a real
scheduled check-in call failed with 10016 because the patient's number was
stored as a bare 10-digit "9123456789".

Normalizing at the point of dialing (rather than mangling what's stored, or
forcing every form to validate) keeps the displayed number as the humans
entered it while still giving the provider what it requires.
"""

import re

DEFAULT_COUNTRY_CODE = "91"  # India — this platform's deployment target


def to_e164(phone: str, default_country_code: str = DEFAULT_COUNTRY_CODE) -> str:
    """Best-effort conversion of a human-entered phone number to +E164.

    Returns "" for input with no usable digits. Never raises — a bad number
    should surface as a provider error the app can report honestly, not as
    an exception in the middle of placing a call.
    """
    if not phone:
        return ""

    raw = str(phone).strip()
    had_plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)

    if not digits:
        return ""

    # Already explicitly international ("+91...") — trust the country code
    # the caller gave and just strip the separators.
    if had_plus:
        return f"+{digits}"

    # Indian trunk prefix: "09123456789" -> drop the leading 0.
    if len(digits) > 10 and digits.startswith("0"):
        digits = digits.lstrip("0")

    # Bare national number ("9123456789") — prepend the default country code.
    if len(digits) == 10:
        return f"+{default_country_code}{digits}"

    # Country code present but no "+" ("919123456789").
    return f"+{digits}"
