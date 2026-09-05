"""Лимитҳои моҳона аз рӯи категория.

Бот ҳангоми сабти харҷ огоҳ мекунад — вале **танҳо як бор** дар ҳар зина:
дафъаи аввале, ки харҷ аз 80% ё аз 100% гузашт. Вагарна ҳар харҷи баъдӣ
ҳамон огоҳиро такрор мекард ва бот безоркунанда мешуд.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, CategoryLimit, Expense, User
from app.services.period import period_bounds

WARN_AT = Decimal("0.8")  # 80% — зинаи огоҳии аввал
MAX_LIMITS = 20


@dataclass(slots=True)
class LimitView:
    category: Category
    amount: Decimal  # худи лимит
    spent: Decimal  # харҷи моҳи ҷорӣ
    share: float  # 0..1+ (метавонад аз 1 гузарад)


@dataclass(slots=True)
class LimitStatus:
    """Ҳолати лимит баъди сабти харҷ.

    `crossed` танҳо дар лаҳзаи гузаштани зина пур мешавад — маҳз он
    огоҳии калонро меорад. Дар ҳолати оддӣ як сатри кӯтоҳ мемонад:
    корбар ҳамеша мебинад, ки дар кадом ҳолат аст.
    """

    category: Category
    amount: Decimal
    spent: Decimal
    crossed: str | None  # "near" | "exceeded" | None

    @property
    def share(self) -> float:
        return float(self.spent / self.amount) if self.amount else 0.0

    @property
    def mark(self) -> str:
        if self.share >= 1:
            return "🔴"
        return "🟡" if self.share >= float(WARN_AT) else "🟢"


async def _spent(
    session: AsyncSession, user: User, category_id: int
) -> Decimal:
    start, end = period_bounds(user.tz, "month")
    total = await session.scalar(
        select(func.coalesce(func.sum(Expense.amount_base), 0)).where(
            Expense.user_id == user.id,
            Expense.category_id == category_id,
            Expense.deleted_at.is_(None),
            Expense.occurred_at >= start,
            Expense.occurred_at < end,
        )
    )
    return Decimal(total or 0)


async def get(
    session: AsyncSession, user_id: int, category_id: int
) -> CategoryLimit | None:
    return await session.scalar(
        select(CategoryLimit).where(
            CategoryLimit.user_id == user_id,
            CategoryLimit.category_id == category_id,
        )
    )


async def list_for_user(session: AsyncSession, user: User) -> list[LimitView]:
    """Лимитҳо бо харҷи моҳи ҷорӣ — аз пуртар ба холитар."""
    start, end = period_bounds(user.tz, "month")

    spent = dict(
        (
            await session.execute(
                select(Expense.category_id, func.sum(Expense.amount_base))
                .where(
                    Expense.user_id == user.id,
                    Expense.deleted_at.is_(None),
                    Expense.occurred_at >= start,
                    Expense.occurred_at < end,
                )
                .group_by(Expense.category_id)
            )
        ).all()
    )

    rows = await session.scalars(
        select(CategoryLimit).where(CategoryLimit.user_id == user.id)
    )

    views = [
        LimitView(
            category=row.category,
            amount=row.amount,
            spent=Decimal(spent.get(row.category_id, 0)),
            share=float(Decimal(spent.get(row.category_id, 0)) / row.amount)
            if row.amount
            else 0.0,
        )
        for row in rows
    ]
    views.sort(key=lambda view: view.share, reverse=True)
    return views


async def count_for_user(session: AsyncSession, user_id: int) -> int:
    return (
        await session.scalar(
            select(func.count(CategoryLimit.id)).where(
                CategoryLimit.user_id == user_id
            )
        )
        or 0
    )


async def set_limit(
    session: AsyncSession, user: User, category_id: int, amount: Decimal
) -> bool:
    """`False` — ҳадди шумораи лимитҳо пур шудааст."""
    existing = await get(session, user.id, category_id)
    if existing is None and await count_for_user(session, user.id) >= MAX_LIMITS:
        return False

    await session.execute(
        pg_insert(CategoryLimit)
        .values(user_id=user.id, category_id=category_id, amount=amount)
        .on_conflict_do_update(
            index_elements=[CategoryLimit.user_id, CategoryLimit.category_id],
            set_={"amount": amount},
        )
    )
    return True


async def remove(session: AsyncSession, user_id: int, category_id: int) -> bool:
    limit = await get(session, user_id, category_id)
    if limit is None:
        return False
    await session.delete(limit)
    return True


async def check(
    session: AsyncSession, user: User, expense: Expense
) -> LimitStatus | None:
    """Ҳолати лимити категорияи ҳамин харҷ.

    `None` — лимит гузошта нашудааст. Вагарна ҳамеша ҳолат бармегардад,
    вале `crossed` танҳо дар лаҳзаи гузаштани зина пур мешавад: муқоиса
    бо ҳолати «то ин харҷ». Вагарна баъди гузаштани лимит ҳар харҷ
    ҳамон огоҳии калонро такрор мекард.
    """
    limit = await get(session, user.id, expense.category_id)
    if limit is None or limit.amount <= 0:
        return None

    spent = await _spent(session, user, expense.category_id)
    before = spent - expense.amount_base
    threshold = limit.amount * WARN_AT

    if spent >= limit.amount > before:
        crossed = "exceeded"
    elif spent >= threshold > before:
        crossed = "near"
    else:
        crossed = None

    return LimitStatus(
        category=limit.category,
        amount=limit.amount,
        spent=spent,
        crossed=crossed,
    )
