"""Сабт, таҳрир ва нест кардани харҷҳо.

Ҳар функсия `user_id` мегирад ва ҳар query онро филтр мекунад —
маълумоти корбарони гуногун ҳеҷ гоҳ намеомезад.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, CategoryLimit, Expense, User
from app.services import fx
from app.services.categorizer import CategoryDecision
from app.services.parser import ParsedExpense
from app.services.period import period_bounds


async def create(
    session: AsyncSession,
    user: User,
    parsed: ParsedExpense,
    decision: CategoryDecision,
    *,
    source: str = "text",
    occurred_at: datetime | None = None,
) -> Expense:
    currency = parsed.currency or user.base_currency
    amount_base, rate = await fx.convert(
        session, parsed.amount, currency, user.base_currency
    )

    expense = Expense(
        user_id=user.id,
        category_id=decision.category.id,
        amount=parsed.amount,
        currency=currency,
        amount_base=amount_base,
        fx_rate=rate,
        description=parsed.description,
        raw_text=parsed.raw,
        source=source,
        cat_source=decision.source,
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )
    session.add(expense)
    await session.flush()
    return expense


async def rebase(session: AsyncSession, user: User, new_currency: str) -> int:
    """Валютаи асосиро иваз мекунад ва ҳама рақамҳоро ба он мегузаронад.

    Манбаи ҳақиқат `amount` + `currency` аст — маҳз он чи корбар навишт.
    `amount_base` танҳо нусхаи ҳисобшуда барои ҳисоботҳост. Агар онро
    аз нав ҳисоб накунем, баъди ивази валюта ҷамъҳо рақамҳои TJS ва USD-ро
    якҷоя мекарданд — ва ҳисобот бемаънӣ мешуд.
    """
    if new_currency == user.base_currency:
        return 0

    rates = await fx.get_rates(session)
    old_currency = user.base_currency

    rows = (
        await session.scalars(select(Expense).where(Expense.user_id == user.id))
    ).all()

    for expense in rows:
        rate = fx.rate_between(rates, expense.currency, new_currency)
        expense.fx_rate = rate
        expense.amount_base = (expense.amount * rate).quantize(Decimal("0.01"))

    # Лимитҳо низ дар валютаи асосӣ нигоҳ дошта мешаванд
    limit_rate = fx.rate_between(rates, old_currency, new_currency)
    limits = (
        await session.scalars(
            select(CategoryLimit).where(CategoryLimit.user_id == user.id)
        )
    ).all()
    for limit in limits:
        limit.amount = (limit.amount * limit_rate).quantize(Decimal("0.01"))

    user.base_currency = new_currency
    await session.flush()
    return len(rows)


async def get(session: AsyncSession, user_id: int, expense_id: int) -> Expense | None:
    """Танҳо харҷи ҲАМИН корбар. Вагарна `None` → 404."""
    return await session.scalar(
        select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)
    )


async def get_alive(
    session: AsyncSession, user_id: int, expense_id: int
) -> Expense | None:
    expense = await get(session, user_id, expense_id)
    return expense if expense and expense.deleted_at is None else None


async def soft_delete(session: AsyncSession, user_id: int, expense_id: int) -> bool:
    expense = await get_alive(session, user_id, expense_id)
    if expense is None:
        return False
    expense.deleted_at = datetime.now(timezone.utc)
    return True


async def restore(session: AsyncSession, user_id: int, expense_id: int) -> bool:
    expense = await get(session, user_id, expense_id)
    if expense is None or expense.deleted_at is None:
        return False
    expense.deleted_at = None
    return True


async def set_amount(
    session: AsyncSession,
    user: User,
    expense_id: int,
    amount: Decimal,
    currency: str | None = None,
    description: str | None = None,
) -> Expense | None:
    """Суммаро иваз мекунад ва курсро аз нав ҳисоб менамояд."""
    expense = await get_alive(session, user.id, expense_id)
    if expense is None:
        return None

    expense.amount = amount
    expense.currency = currency or expense.currency
    expense.amount_base, expense.fx_rate = await fx.convert(
        session, expense.amount, expense.currency, user.base_currency
    )
    if description:
        expense.description = description

    await session.flush()
    return expense


async def set_category(
    session: AsyncSession, user_id: int, expense_id: int, category: Category
) -> Expense | None:
    expense = await get_alive(session, user_id, expense_id)
    if expense is None:
        return None
    expense.category_id = category.id
    expense.cat_source = "explicit"
    await session.flush()
    return expense


async def last(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[Expense]:
    rows = await session.scalars(
        select(Expense)
        .where(Expense.user_id == user_id, Expense.deleted_at.is_(None))
        .order_by(desc(Expense.occurred_at), desc(Expense.id))
        .limit(limit)
    )
    return list(rows)


async def last_alive_id(session: AsyncSession, user_id: int) -> int | None:
    return await session.scalar(
        select(Expense.id)
        .where(Expense.user_id == user_id, Expense.deleted_at.is_(None))
        .order_by(desc(Expense.id))
        .limit(1)
    )


async def period_total(session: AsyncSession, user: User, period: str) -> Decimal:
    start, end = period_bounds(user.tz, period)
    total = await session.scalar(
        select(func.coalesce(func.sum(Expense.amount_base), 0)).where(
            Expense.user_id == user.id,
            Expense.deleted_at.is_(None),
            Expense.occurred_at >= start,
            Expense.occurred_at < end,
        )
    )
    return Decimal(total or 0)
