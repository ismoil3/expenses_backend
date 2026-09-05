"""Курси валюта.

Муҳим: курс **дар лаҳзаи сабт** ҳисоб ва дар худи сатри харҷ нигоҳ дошта
мешавад. Курс пагоҳ дигар шавад ҳам, ҳисоботи гузашта тағйир намеёбад —
«честные цифры».

Манбаъ: open.er-api.com (ройгон, бе калид). Агар дастрас набошад —
курси охирини сабтшуда, вагарна қимати захиравӣ.
"""

import logging
from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import CURRENCIES, settings
from app.db.models import FxRate

log = logging.getLogger(__name__)

PIVOT = "USD"
_HTTP_TIMEOUT = 8.0

# Захиравӣ: 1 USD = X (танҳо агар API ва база холӣ бошанд)
FALLBACK: dict[str, Decimal] = {
    "USD": Decimal("1"),
    "TJS": Decimal("10.95"),
    "RUB": Decimal("92.00"),
}

_QUANT_RATE = Decimal("0.00000001")
_QUANT_MONEY = Decimal("0.01")


def _pair(code: str) -> str:
    return f"{PIVOT}_{code}"


async def _fetch_remote() -> dict[str, Decimal] | None:
    url = f"{settings.FX_API_URL.rstrip('/')}/{PIVOT}"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        log.warning("FX fetch failed: %s: %s", exc.__class__.__name__, exc)
        return None

    rates = payload.get("rates") or payload.get("conversion_rates") or {}
    result: dict[str, Decimal] = {}
    for code in CURRENCIES:
        value = rates.get(code)
        if value:
            try:
                result[code] = Decimal(str(value))
            except Exception:
                continue
    result[PIVOT] = Decimal("1")
    return result if len(result) >= 2 else None


async def _load_stored(session, day: date | None = None) -> dict[str, Decimal]:
    """Курсҳои рӯзи додашуда ё охирин рӯзи мавҷуд."""
    query = select(FxRate).order_by(FxRate.day.desc())
    if day is not None:
        query = select(FxRate).where(FxRate.day == day)

    rows = (await session.scalars(query)).all()
    result: dict[str, Decimal] = {}
    latest_day: date | None = None
    for row in rows:
        if latest_day is None:
            latest_day = row.day
        if row.day != latest_day:
            break
        code = row.pair.split("_", 1)[1]
        result[code] = row.rate
    return result


async def _store(session, day: date, rates: dict[str, Decimal]) -> None:
    for code, rate in rates.items():
        await session.execute(
            pg_insert(FxRate)
            .values(day=day, pair=_pair(code), rate=rate)
            .on_conflict_do_update(
                index_elements=[FxRate.day, FxRate.pair], set_={"rate": rate}
            )
        )
    await session.commit()


async def get_rates(session) -> dict[str, Decimal]:
    """Курсҳои имрӯза (1 USD = X). Ҳамеша чизе бармегардонад."""
    today = date.today()

    stored = await _load_stored(session, today)
    if len(stored) >= len(CURRENCIES):
        return stored

    remote = await _fetch_remote()
    if remote:
        try:
            await _store(session, today, remote)
        except Exception as exc:
            log.warning("FX store failed: %s", exc)
            await session.rollback()
        return remote

    latest = await _load_stored(session)
    if latest:
        log.info("FX: курси охирини сабтшуда истифода шуд")
        return latest

    log.warning("FX: қимати захиравӣ истифода шуд")
    return dict(FALLBACK)


def rate_between(rates: dict[str, Decimal], src: str, dst: str) -> Decimal:
    """Курси `src → dst` аз ҷадвали 1 USD = X."""
    if src == dst:
        return Decimal("1")
    src_rate = rates.get(src) or FALLBACK.get(src) or Decimal("1")
    dst_rate = rates.get(dst) or FALLBACK.get(dst) or Decimal("1")
    if src_rate == 0:
        return Decimal("1")
    return (dst_rate / src_rate).quantize(_QUANT_RATE)


async def convert(
    session, amount: Decimal, src: str, dst: str
) -> tuple[Decimal, Decimal]:
    """`(сумма дар валютаи асосӣ, курси истифодашуда)`."""
    if src == dst:
        return amount.quantize(_QUANT_MONEY), Decimal("1")

    rates = await get_rates(session)
    rate = rate_between(rates, src, dst)
    return (amount * rate).quantize(_QUANT_MONEY), rate
