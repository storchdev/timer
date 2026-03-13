from __future__ import annotations

from datetime import datetime
import math

import parsedatetime


def parse_human_datetime(value: str, base: datetime | None = None) -> datetime:
    now = base or datetime.now()
    cal = parsedatetime.Calendar()
    parsed, status = cal.parseDT(value, sourceTime=now)
    if status == 0:
        raise ValueError(f"Could not parse time: {value}")
    return parsed


def parse_human_offset_seconds(value: str, base: datetime | None = None) -> int:
    now = base or datetime.now()
    parsed = parse_human_datetime(value, now)
    seconds = math.ceil((parsed - now).total_seconds())
    if seconds <= 0:
        raise ValueError(
            "Offset must be a future expression like '20 minutes' or '2 hours'."
        )
    return seconds
