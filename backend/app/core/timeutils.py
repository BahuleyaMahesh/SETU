"""Local (IST) wall-clock <-> naive-UTC conversion.

Every timestamp column in this DB is naive UTC (`datetime.utcnow()`), which
is correct — but a lot of this app's times originate as HUMAN clock times:
"take this tablet in the morning", "call me at 6:30pm". Those are local
times (IST for this deployment), and writing them straight onto a
`datetime.utcnow()` base silently shifts them by the UTC offset.

Confirmed live: medication reminders built from MORNING = time(8, 0) were
stored as 08:00 UTC, i.e. 1:30 PM IST, and a NIGHT = time(21, 0) dose
reminder would have fired at 2:30 AM IST.

Uses a fixed offset from settings rather than zoneinfo/pytz: India has no
DST and a single nationwide offset, so a fixed offset is exactly correct
here and avoids depending on the tzdata package being present on Windows.
"""

from datetime import datetime, time, timedelta

from .config import settings


def _offset() -> timedelta:
    return timedelta(minutes=settings.LOCAL_UTC_OFFSET_MINUTES)


def utc_to_local(dt: datetime) -> datetime:
    """Naive-UTC datetime -> naive local (IST) datetime."""
    return dt + _offset()


def local_to_utc(dt: datetime) -> datetime:
    """Naive local (IST) datetime -> naive UTC datetime."""
    return dt - _offset()


def next_local_time_as_utc(slot: time, now_utc: datetime = None) -> datetime:
    """Next upcoming occurrence of a local wall-clock time, as naive UTC.

    `slot` is a LOCAL time ("8 in the morning" means 8am IST). Returns the
    next time that clock time comes around, expressed in naive UTC so it can
    be stored and compared against `datetime.utcnow()` directly.
    """
    now_utc = now_utc or datetime.utcnow()
    now_local = utc_to_local(now_utc)

    target_local = now_local.replace(
        hour=slot.hour, minute=slot.minute, second=0, microsecond=0
    )
    if target_local <= now_local:
        target_local += timedelta(days=1)

    return local_to_utc(target_local)


def format_local(dt: datetime) -> str:
    """Human-readable local time, for log lines and notification text."""
    return utc_to_local(dt).strftime("%d %b %Y, %I:%M %p IST")
