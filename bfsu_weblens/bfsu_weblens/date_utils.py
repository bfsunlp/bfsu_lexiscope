# -*- coding: utf-8 -*-
"""Publication-date parsing helpers for the WebLens result preview.

Search engines and imported files expose publication times in heterogeneous
forms: ISO timestamps, localized absolute dates, partial month/day values and
relative labels such as ``3 hours ago`` or ``2天前``.  The raw metadata value is
kept unchanged on each record; these helpers provide a normalized date for the
GUI and a chronological key for sorting.
"""
from __future__ import annotations

import calendar
from email.utils import parsedate_to_datetime
import re
from datetime import datetime, timedelta
from typing import Any

_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _reference_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if text:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            return parsed
        except ValueError:
            pass
    return datetime.now().replace(microsecond=0)


def _safe_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None


def _infer_year(month: int, day: int, reference: datetime) -> int:
    """Infer the year for search-engine month/day labels.

    Recent-result pages often omit the year.  Use the collection year unless
    that would put the result implausibly in the future; in that case use the
    previous year (important around New Year).
    """
    candidate = _safe_datetime(reference.year, month, day)
    if candidate and candidate.date() > (reference + timedelta(days=2)).date():
        return reference.year - 1
    return reference.year


def _shift_months(reference: datetime, months: int) -> datetime:
    total = reference.year * 12 + (reference.month - 1) - months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    day = min(reference.day, calendar.monthrange(year, month)[1])
    return reference.replace(year=year, month=month, day=day)


def _shift_years(reference: datetime, years: int) -> datetime:
    year = reference.year - years
    day = min(reference.day, calendar.monthrange(year, reference.month)[1])
    return reference.replace(year=year, day=day)


def _relative_datetime(text: str, reference: datetime) -> datetime | None:
    lower = text.casefold().strip()
    if lower in {"just now", "now", "today", "刚刚", "剛剛", "今天"}:
        return reference

    # English relative labels used by Google result cards.
    match = re.search(r"\b(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|days?|weeks?|months?|years?)\s+ago\b", lower)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit.startswith(("second", "sec")):
            return reference - timedelta(seconds=amount)
        if unit.startswith(("minute", "min")):
            return reference - timedelta(minutes=amount)
        if unit.startswith("hour"):
            return reference - timedelta(hours=amount)
        if unit.startswith("day"):
            return reference - timedelta(days=amount)
        if unit.startswith("week"):
            return reference - timedelta(weeks=amount)
        if unit.startswith("month"):
            return _shift_months(reference, amount)
        if unit.startswith("year"):
            return _shift_years(reference, amount)

    # Simplified/Traditional Chinese relative labels used by Google/Baidu.
    match = re.search(r"(\d+)\s*(秒|分钟|分鐘|小时|小時|天|日|周|週|个月|個月|月|年)前", text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == "秒":
            return reference - timedelta(seconds=amount)
        if unit in {"分钟", "分鐘"}:
            return reference - timedelta(minutes=amount)
        if unit in {"小时", "小時"}:
            return reference - timedelta(hours=amount)
        if unit in {"天", "日"}:
            return reference - timedelta(days=amount)
        if unit in {"周", "週"}:
            return reference - timedelta(weeks=amount)
        if unit in {"个月", "個月", "月"}:
            return _shift_months(reference, amount)
        if unit == "年":
            return _shift_years(reference, amount)

    day_offset = None
    if re.search(r"\byesterday\b", lower) or "昨天" in text:
        day_offset = 1
    elif "前天" in text:
        day_offset = 2
    if day_offset is not None:
        base = reference - timedelta(days=day_offset)
        hm = re.search(r"(?:yesterday|昨天|前天)\s*(\d{1,2})(?::(\d{1,2}))?", text, flags=re.I)
        if hm:
            hour = int(hm.group(1))
            minute = int(hm.group(2) or 0)
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                base = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return base
    return None


def parse_published_datetime(value: Any, reference: Any = None) -> datetime | None:
    """Parse a publication-time value without modifying the stored raw text."""
    text = " ".join(str(value or "").strip().split())
    if not text:
        return None
    ref = _reference_datetime(reference)

    relative = _relative_datetime(text, ref)
    if relative is not None:
        return relative.replace(tzinfo=None)

    # ISO 8601 and common year-first numeric timestamps.
    iso_candidate = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    # RFC-style HTTP/news dates, e.g. Wed, 23 Sep 2026 10:30:00 GMT.
    try:
        parsed = parsedate_to_datetime(text)
        if parsed is not None:
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            return parsed
    except (TypeError, ValueError, OverflowError):
        pass

    match = re.search(
        r"(?<!\d)(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})(?:日)?(?:[ T]\s*(\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?)?",
        text,
    )
    if match:
        return _safe_datetime(
            int(match.group(1)), int(match.group(2)), int(match.group(3)),
            int(match.group(4) or 0), int(match.group(5) or 0), int(match.group(6) or 0),
        )

    # Day-month-year numeric values (the WebLens preview standard).
    match = re.search(
        r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{4})(?:[ T]\s*(\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?)?",
        text,
    )
    if match:
        return _safe_datetime(
            int(match.group(3)), int(match.group(2)), int(match.group(1)),
            int(match.group(4) or 0), int(match.group(5) or 0), int(match.group(6) or 0),
        )

    # Chinese month/day values with omitted year, e.g. 9月23日 10:30.
    match = re.search(r"(?<!\d)(\d{1,2})月(\d{1,2})日?(?:\s*(\d{1,2})(?::(\d{1,2}))?)?", text)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        year = _infer_year(month, day, ref)
        return _safe_datetime(year, month, day, int(match.group(3) or 0), int(match.group(4) or 0))

    # English absolute dates: Sep 23, 2026 / September 23 2026.
    match = re.search(r"\b([A-Za-z]{3,9})\s+(\d{1,2})(?:,)?\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?\b", text)
    if match:
        month = _MONTHS.get(match.group(1).casefold())
        if month:
            return _safe_datetime(int(match.group(3)), month, int(match.group(2)), int(match.group(4) or 0), int(match.group(5) or 0))

    # English absolute dates: 23 Sep 2026.
    match = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?\b", text)
    if match:
        month = _MONTHS.get(match.group(2).casefold())
        if month:
            return _safe_datetime(int(match.group(3)), month, int(match.group(1)), int(match.group(4) or 0), int(match.group(5) or 0))

    # English month/day with omitted year, e.g. Sep 23.
    match = re.search(r"\b([A-Za-z]{3,9})\s+(\d{1,2})(?:,)?\b", text)
    if match:
        month = _MONTHS.get(match.group(1).casefold())
        if month:
            day = int(match.group(2))
            return _safe_datetime(_infer_year(month, day, ref), month, day)

    # Numeric month/day with omitted year. Search engines commonly emit this
    # in East-Asian result pages; interpret it as month-day and infer the year.
    match = re.search(r"(?<!\d)(\d{1,2})[-/](\d{1,2})(?![-/\d])", text)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return _safe_datetime(_infer_year(month, day, ref), month, day)

    return None


def format_published_date(value: Any, reference: Any = None) -> str:
    """Return an unambiguous day-month-year display value for Result Preview."""
    parsed = parse_published_datetime(value, reference)
    if parsed is None:
        return str(value or "")
    return parsed.strftime("%d-%m-%Y")


def published_sort_key(value: Any, reference: Any = None) -> tuple[int, int, int, int, int, int] | None:
    """Return a chronological sort key, or ``None`` when the value is unknown."""
    parsed = parse_published_datetime(value, reference)
    if parsed is None:
        return None
    return (parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second)
