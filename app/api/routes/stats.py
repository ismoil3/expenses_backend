"""Ҳисоботҳо барои панел — ҳама дар валютаи асосии корбар.

Ҳар endpoint ё давраи тайёр (`period=today|week|month`) мегирад,
ё фосилаи дилхоҳ (`from`/`to`), ки корбар дар панел интихоб мекунад.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.serializers import category_out
from app.db.models import User
from app.schemas import CategorySlice, DayPoint, SummaryOut
from app.services import stats as stats_service
from app.services.period import period_bounds

router = APIRouter(prefix="/api/stats", tags=["stats"])

PeriodQuery = Query(default="month", pattern="^(today|week|month)$")
FromQuery = Query(default=None, alias="from")
ToQuery = Query(default=None, alias="to")

# Фосилаи «ҳама вақт» — аз оғози лоиҳа то ҳозир
EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _bounds(
    user: User, period: str, date_from: datetime | None, date_to: datetime | None
) -> tuple[datetime, datetime]:
    """Фосилаи возеҳ давраи тайёрро иваз мекунад."""
    if date_from is None and date_to is None:
        return period_bounds(user.tz, period)

    start = date_from or EPOCH
    end = date_to or datetime.now(timezone.utc)
    return _aware(start), _aware(end)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@router.get("/summary", response_model=SummaryOut)
async def summary(
    user: CurrentUser,
    session: SessionDep,
    period: str = PeriodQuery,
    date_from: datetime | None = FromQuery,
    date_to: datetime | None = ToQuery,
) -> SummaryOut:
    """Ҷамъи фосила + муқоиса бо ҳамон қадар вақти пеш аз он."""
    start, end = _bounds(user, period, date_from, date_to)
    span = end - start

    total, count = await stats_service.totals(session, user, start, end)
    previous, _ = await stats_service.totals(session, user, start - span, start)

    change = None
    if previous > 0:
        change = round(float((total - previous) / previous) * 100, 1)

    return SummaryOut(
        period=period,
        total=total,
        previous_total=previous,
        change_percent=change,
        currency=user.base_currency,
        count=count,
    )


@router.get("/by-category", response_model=list[CategorySlice])
async def by_category(
    user: CurrentUser,
    session: SessionDep,
    period: str = PeriodQuery,
    date_from: datetime | None = FromQuery,
    date_to: datetime | None = ToQuery,
) -> list[CategorySlice]:
    start, end = _bounds(user, period, date_from, date_to)
    rows, total = await stats_service.by_category(session, user, start, end)

    return [
        CategorySlice(
            category=category_out(category, user.lang),
            total=amount,
            share=round(float(amount / total), 4) if total else 0.0,
        )
        for category, amount in rows
    ]


@router.get("/by-day", response_model=list[DayPoint])
async def by_day(
    user: CurrentUser,
    session: SessionDep,
    period: str = PeriodQuery,
    date_from: datetime | None = FromQuery,
    date_to: datetime | None = ToQuery,
) -> list[DayPoint]:
    """Ҳар рӯзи фосила, аз ҷумла рӯзҳои холӣ — то график холигӣ надошта бошад."""
    start, end = _bounds(user, period, date_from, date_to)
    rows = dict(await stats_service.by_day(session, user, start, end))

    # Фосилаи хеле дароз графикро нофаҳмо мекунад
    span_days = (end - start).days + 1
    if span_days > 180:
        return [DayPoint(day=day, total=total) for day, total in sorted(rows.items())]

    points: list[DayPoint] = []
    cursor = start.date()
    last_day = (end - timedelta(seconds=1)).date()
    while cursor <= last_day:
        key = cursor.isoformat()
        points.append(DayPoint(day=key, total=rows.get(key, Decimal(0))))
        cursor += timedelta(days=1)
    return points
