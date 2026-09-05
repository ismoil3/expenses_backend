"""Ҳудуди давраҳо бо вақти маҳаллии корбар.

Дар база ҳама вақтҳо UTC-анд, вале «имрӯз» барои корбари Душанбе бояд
аз соати 00:00-и Душанбе оғоз ёбад, на аз UTC.
"""

from datetime import datetime, timedelta, timezone, tzinfo
from decimal import Decimal

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]

PERIODS = ("today", "week", "month")

# Агар пойгоҳи минтақаҳои вақт дар система набошад
_FALLBACK_OFFSETS = {
    "Asia/Dushanbe": 5,
    "Asia/Tashkent": 5,
    "Europe/Moscow": 3,
    "UTC": 0,
}


def user_tz(tz_name: str) -> tzinfo:
    if ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass
    hours = _FALLBACK_OFFSETS.get(tz_name, 0)
    return timezone(timedelta(hours=hours))


def now_local(tz_name: str) -> datetime:
    return datetime.now(user_tz(tz_name))


def period_bounds(
    tz_name: str, period: str, now: datetime | None = None
) -> tuple[datetime, datetime]:
    """`(оғоз, анҷом)` дар UTC барои «today» / «week» / «month»."""
    tz = user_tz(tz_name)
    local = now.astimezone(tz) if now else datetime.now(tz)

    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "week":
        start = midnight - timedelta(days=midnight.weekday())
    elif period == "month":
        start = midnight.replace(day=1)
    else:  # today
        start = midnight

    end = midnight + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def format_local_date(tz_name: str, lang: str) -> str:
    """«4 сентябр» / «4 сентября» / «4 September»."""
    local = now_local(tz_name)
    months = MONTHS.get(lang) or MONTHS["ru"]
    return f"{local.day} {months[local.month - 1]}"


def format_period_title(tz_name: str, lang: str, period: str) -> str:
    """Сарлавҳаи давра: сана, фосила ё номи моҳ.

    «Ҳафта · 5 сентябр» гумроҳкунанда буд — акнун «Ҳафта · 31 авг — 5 сен».
    """
    if period == "today":
        return format_local_date(tz_name, lang)

    tz = user_tz(tz_name)
    start, end = period_bounds(tz_name, period)
    first = start.astimezone(tz).date()
    last = (end - timedelta(seconds=1)).astimezone(tz).date()

    if period == "month":
        names = MONTHS_NOMINATIVE.get(lang) or MONTHS_NOMINATIVE["ru"]
        return names[first.month - 1]

    short = MONTHS_SHORT.get(lang) or MONTHS_SHORT["ru"]
    left = f"{first.day} {short[first.month - 1]}"
    right = f"{last.day} {short[last.month - 1]}"
    return f"{left} — {right}"


def day_buckets(
    tz_name: str, lang: str, period: str, totals: dict[str, Decimal]
) -> list[tuple[str, Decimal]]:
    """Тақсими давра ба сутунҳо барои диаграммаи «аз рӯи рӯзҳо».

    Ҳафта → 7 рӯз бо номи рӯзи ҳафта.
    Моҳ → ҳафтаҳо («1–7», «8–14»…), вагарна 30 сатр мешуд.
    """
    tz = user_tz(tz_name)
    start, end = period_bounds(tz_name, period)
    first = start.astimezone(tz).date()
    last = (end - timedelta(seconds=1)).astimezone(tz).date()

    if period == "week":
        names = WEEKDAYS.get(lang) or WEEKDAYS["ru"]
        buckets: list[tuple[str, Decimal]] = []
        cursor = first
        while cursor <= last:
            buckets.append(
                (names[cursor.weekday()], totals.get(cursor.isoformat(), Decimal(0)))
            )
            cursor += timedelta(days=1)
        return buckets

    groups: dict[int, Decimal] = {}
    labels: dict[int, tuple[int, int]] = {}
    cursor = first
    while cursor <= last:
        index = (cursor - first).days // 7
        groups[index] = groups.get(index, Decimal(0)) + totals.get(
            cursor.isoformat(), Decimal(0)
        )
        low, high = labels.get(index, (cursor.day, cursor.day))
        labels[index] = (min(low, cursor.day), max(high, cursor.day))
        cursor += timedelta(days=1)

    return [
        (f"{labels[i][0]}–{labels[i][1]}", groups[i]) for i in sorted(groups)
    ]


WEEKDAYS: dict[str, list[str]] = {
    "tg": ["Дш", "Сш", "Чш", "Пш", "Ҷм", "Шн", "Яш"],
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}

MONTHS_SHORT: dict[str, list[str]] = {
    "tg": ["янв", "фев", "мар", "апр", "май", "июн",
           "июл", "авг", "сен", "окт", "ноя", "дек"],
    "ru": ["янв", "фев", "мар", "апр", "мая", "июн",
           "июл", "авг", "сен", "окт", "ноя", "дек"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}

MONTHS_NOMINATIVE: dict[str, list[str]] = {
    "tg": ["Январ", "Феврал", "Март", "Апрел", "Май", "Июн",
           "Июл", "Август", "Сентябр", "Октябр", "Ноябр", "Декабр"],
    "ru": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
           "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}

MONTHS: dict[str, list[str]] = {
    "tg": [
        "январ", "феврал", "март", "апрел", "май", "июн",
        "июл", "август", "сентябр", "октябр", "ноябр", "декабр",
    ],
    "ru": [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    ],
    "en": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
}
