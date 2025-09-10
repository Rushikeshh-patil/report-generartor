from __future__ import annotations

from datetime import date, timedelta

try:
    from holidays.models import Holiday  # type: ignore
except Exception:  # pragma: no cover - during initial migration
    Holiday = None  # type: ignore


def is_business_day(d: date) -> bool:
    # Weekend check
    if d.weekday() >= 5:  # 5=Sat, 6=Sun
        return False
    if Holiday is None:
        return True
    try:
        h = Holiday.objects.filter(date=d).first()
        if h is None:
            return True
        return getattr(h, "is_business_day", False)
    except Exception:
        # If DB not ready, assume business day to avoid crashes
        return True


def add_business_days(start: date, days: int) -> date:
    d = start
    added = 0
    while added < days:
        d = d + timedelta(days=1)
        if is_business_day(d):
            added += 1
    return d

