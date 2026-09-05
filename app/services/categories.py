"""Кор бо категорияҳо: хондан, сохтан, хотираи корбар."""

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, CategoryMemory, Expense
from app.db.seed import EXTRA_COLORS, FALLBACK_KEY
from app.services.ai import NewCategory

MAX_CUSTOM_CATEGORIES = 30


async def list_for_user(session: AsyncSession, user_id: int) -> list[Category]:
    """Категорияҳои система + шахсии ҳамин корбар."""
    rows = await session.scalars(
        select(Category)
        .where(or_(Category.user_id.is_(None), Category.user_id == user_id))
        .order_by(Category.sort, Category.id)
    )
    return list(rows)


async def get_for_user(
    session: AsyncSession, user_id: int, category_id: int
) -> Category | None:
    """Категорияи дастрас — шахсии худаш ё система. Вагарна `None`."""
    return await session.scalar(
        select(Category).where(
            Category.id == category_id,
            or_(Category.user_id.is_(None), Category.user_id == user_id),
        )
    )


async def fallback(session: AsyncSession) -> Category:
    """Категорияи «Дигар» — ҷои афтодани ҳар чизи нофаҳмо."""
    category = await session.scalar(
        select(Category).where(Category.user_id.is_(None), Category.key == FALLBACK_KEY)
    )
    if category is None:  # seed нашудааст — набояд рӯй диҳад
        raise RuntimeError("Категорияи 'other' ёфт нашуд: seed-ро иҷро кунед")
    return category


def find_by_key(categories: list[Category], key: str) -> Category | None:
    key = key.strip().lower()
    for category in categories:
        if category.key == key:
            return category
    return None


def find_by_name(categories: list[Category], word: str) -> Category | None:
    """«кафе», «cafe», «Кафе» — номи категория дар ҳар се забон."""
    word = word.strip().lower()
    if not word:
        return None
    for category in categories:
        names = (category.name_tg, category.name_ru, category.name_en)
        if any(word == name.lower() for name in names):
            return category
    return None


async def count_custom(session: AsyncSession, user_id: int) -> int:
    return await session.scalar(
        select(func.count(Category.id)).where(Category.user_id == user_id)
    ) or 0


async def create_custom(
    session: AsyncSession, user_id: int, suggestion: NewCategory
) -> Category | None:
    """Категорияи шахсиро аз пешниҳоди AI месозад."""
    if await count_custom(session, user_id) >= MAX_CUSTOM_CATEGORIES:
        return None

    existing = await list_for_user(session, user_id)
    if find_by_key(existing, suggestion.key):
        return None

    used_colors = {c.color for c in existing}
    color = next(
        (c for c in EXTRA_COLORS if c not in used_colors),
        EXTRA_COLORS[len(existing) % len(EXTRA_COLORS)],
    )

    # Агар AI номро дар як забон надод — аз забони дигар мегирем.
    name_ru = suggestion.name_ru or suggestion.name_en or suggestion.name_tg
    name_tg = suggestion.name_tg or name_ru
    name_en = suggestion.name_en or name_ru
    if not name_ru:
        return None

    category = Category(
        user_id=user_id,
        key=suggestion.key,
        emoji=suggestion.emoji,
        color=color,
        sort=200 + len(existing),
        name_tg=name_tg,
        name_ru=name_ru,
        name_en=name_en,
    )
    session.add(category)
    await session.flush()
    return category


async def remember(
    session: AsyncSession,
    user_id: int,
    phrase: str,
    category_id: int,
    *,
    declined: bool = False,
) -> None:
    """«такси» → 🚕 барои ҳамин корбар. Дафъаи оянда AI лозим нест."""
    if not phrase:
        return
    await session.execute(
        pg_insert(CategoryMemory)
        .values(
            user_id=user_id,
            phrase_norm=phrase,
            category_id=category_id,
            hits=1,
            declined=declined,
        )
        .on_conflict_do_update(
            index_elements=[CategoryMemory.user_id, CategoryMemory.phrase_norm],
            set_={
                "category_id": category_id,
                "declined": declined,
                "hits": CategoryMemory.hits + 1,
            },
        )
    )


async def recall(
    session: AsyncSession, user_id: int, phrase: str
) -> CategoryMemory | None:
    if not phrase:
        return None
    return await session.scalar(
        select(CategoryMemory).where(
            CategoryMemory.user_id == user_id,
            CategoryMemory.phrase_norm == phrase,
        )
    )


async def delete_custom(session: AsyncSession, user_id: int, category_id: int) -> bool:
    """Категорияи шахсиро нест мекунад; харҷҳояш ба «Дигар» мегузаранд."""
    category = await session.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    if category is None:
        return False

    other = await fallback(session)
    await session.execute(
        Expense.__table__.update()
        .where(Expense.user_id == user_id, Expense.category_id == category_id)
        .values(category_id=other.id)
    )
    await session.execute(
        CategoryMemory.__table__.delete().where(
            CategoryMemory.user_id == user_id,
            CategoryMemory.category_id == category_id,
        )
    )
    await session.delete(category)
    return True
