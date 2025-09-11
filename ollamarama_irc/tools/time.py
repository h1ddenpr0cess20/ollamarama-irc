from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_time(timezone_name: Optional[str] = None) -> Dict[str, Any]:
    """Return the current time in the requested timezone.

    Supports ``UTC``, ``local``, or any IANA timezone (e.g. ``America/New_York``).

    Args:
        timezone_name: Target timezone identifier. When omitted or ``local``,
            uses the system local timezone.

    Returns:
        Mapping with ISO datetime, unix timestamp, timezone label, abbreviation,
        and UTC offset minutes. Returns ``{"error": str}`` for unknown zones.
    """
    tz_arg = (timezone_name or "local").strip()
    if tz_arg.lower() == "local":
        now = datetime.now().astimezone()
        tz_label = "local"
    elif tz_arg.upper() == "UTC":
        now = datetime.now(timezone.utc)
        tz_label = "UTC"
    else:
        try:
            tz = ZoneInfo(tz_arg)
        except ZoneInfoNotFoundError:
            return {"error": f"Unknown timezone: {tz_arg}"}
        now = datetime.now(tz)
        tz_label = tz_arg

    iso = now.isoformat()
    unix = int(now.timestamp())
    abbrev = now.tzname() or ""
    offset = now.utcoffset() or timedelta(0)
    offset_minutes = int(offset.total_seconds() // 60)
    return {
        "datetime": iso,
        "unix": unix,
        "timezone": tz_label,
        "abbrev": abbrev,
        "utc_offset_minutes": offset_minutes,
    }
