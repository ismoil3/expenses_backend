"""Ҳисоботҳо — ҳама дар валютаи асосии корбар (`amount_base`).

Ҳама функсияҳо фосилаи тайёр мегиранд, на номи давра: ҳамин тавр як
код ҳам ба «имрӯз» дар бот хизмат мекунад, ҳам ба фосилаи дилхоҳ, ки
корбар дар панел интихоб мекунад.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Expense, User


def _scope(user: User, start: datetime, end: datetime):
    return (
        Expense.user_id == user.id,
        Expense.deleted_at.is_(None),
        Expense.occurred_at >= start,
        Expense.occurred_at < end,
    )


async def by_category(
    session: AsyncSession, user: User, start: datetime, end: datetime
) -> tuple[list[tuple[Category, Decimal]], Decimal]:
    """`([(категория, сумма), …], ҳамагӣ)` — аз калон ба хурд."""
    rows = await session.execute(
        select(Category, func.sum(Expense.amount_base).label("total"))
        .join(Expense, Expense.category_id == Category.id)
        .where(*_scope(user, start, end))
        .group_by(Category.id)
        .order_by(func.sum(Expense.amount_base).desc())
    )

    result = [(category, Decimal(total)) for category, total in rows.all()]
    return result, sum((amount for _, amount in result), Decimal(0))


async def totals(
    session: AsyncSession, user: User, start: datetime, end: datetime
) -> tuple[Decimal, int]:
    """`(ҷамъ, шумора)` барои фосила."""
    row = await session.execute(
        select(
            func.coalesce(func.sum(Expense.amount_base), 0),
            func.count(Expense.id),
        ).where(*_scope(user, start, end))
    )
    total, count = row.one()
    return Decimal(total or 0), int(count or 0)


async def by_day(
    session: AsyncSession, user: User, start: datetime, end: datetime
) -> list[tuple[str, Decimal]]:
    """`[("2026-09-04", 1250.00), …]` — танҳо рӯзҳои дорои харҷ."""
    day = func.date(func.timezone(user.tz, Expense.occurred_at))

    rows = await session.execute(
        select(day.label("day"), func.sum(Expense.amount_base))
        .where(*_scope(user, start, end))
        .group_by(day)
        .order_by(day)
    )
    return [(str(value), Decimal(total)) for value, total in rows.all()]
