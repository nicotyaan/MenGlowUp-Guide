from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


BONUS_BITS = {
    7: 1 << 0,
    30: 1 << 1,
    100: 1 << 2,
}


@dataclass
class StreakResult:
    streak_days: int
    date_key: str
    bonus_triggered_day: int | None


def _to_date_key(now_utc: datetime, tz_offset_hours: int) -> str:
    tz = timezone(timedelta(hours=tz_offset_hours))
    local_dt = now_utc.astimezone(tz)
    return local_dt.strftime("%Y-%m-%d")


def evaluate_streak(
    last_report_date: str | None,
    current_streak: int,
    tz_offset_hours: int,
    now_utc: datetime | None = None,
) -> StreakResult:
    now = now_utc or datetime.now(timezone.utc)
    today_key = _to_date_key(now, tz_offset_hours)
    if last_report_date == today_key:
        return StreakResult(current_streak, today_key, None)

    yesterday_key = _to_date_key(now - timedelta(days=1), tz_offset_hours)
    if last_report_date == yesterday_key:
        streak = current_streak + 1
    else:
        streak = 1

    bonus_day = None
    if streak in BONUS_BITS:
        bonus_day = streak
    return StreakResult(streak, today_key, bonus_day)
