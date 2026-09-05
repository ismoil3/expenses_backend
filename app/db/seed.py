"""10 категорияи система + палитраи рангҳо барои категорияҳои шахсӣ.

Идемпотент аст: ҳар дафъа беэътино иҷро мешавад, такрор намекунад.
Иҷро:  python -m app.db.seed
"""

import asyncio

from sqlalchemy import select

from app.db.models import Category
from app.db.session import SessionLocal, engine

# key, emoji, ранг, tg, ru, en
SYSTEM_CATEGORIES: list[tuple[str, str, str, str, str, str]] = [
    ("food", "🍔", "#E07A3F", "Хӯрока", "Еда", "Food"),
    ("transport", "🚕", "#3E7CC4", "Нақлиёт", "Транспорт", "Transport"),
    ("cafe", "☕", "#9B6B4A", "Кафе", "Кафе", "Cafe"),
    ("shopping", "🛍", "#C0508F", "Харид", "Покупки", "Shopping"),
    ("health", "💊", "#D14B4B", "Саломатӣ", "Здоровье", "Health"),
    ("home", "🏠", "#4FA07A", "Хона", "Дом", "Home"),
    ("connection", "📱", "#4BA3C7", "Алоқа", "Связь", "Connection"),
    ("fun", "🎬", "#8A6BC4", "Фароғат", "Развлечения", "Fun"),
    ("education", "📚", "#C9A227", "Таҳсил", "Образование", "Education"),
    ("other", "📦", "#7B8A8B", "Дигар", "Другое", "Other"),
]

# Категорияи охирин — ҷои афтодани ҳар чизи нофаҳмо.
FALLBACK_KEY = "other"

# Рангҳо барои категорияҳои шахсӣ (аз рӯи навбат дода мешаванд).
EXTRA_COLORS: list[str] = [
    "#2FA0A0", "#B5651D", "#6F8F2F", "#B0417A", "#4C6EF5",
    "#C77D2E", "#7A5AC7", "#3E9E6B", "#CC5C5C", "#5C8AA6",
    "#A0762F", "#8E5AA0", "#3D8F8F", "#C05A3A", "#6B7FA0", "#9A7B3F",
]


async def seed_categories() -> int:
    """Категорияҳои системаро месозад. Шумораи иловашударо бармегардонад."""
    added = 0
    async with SessionLocal() as session:
        for sort, (key, emoji, color, tg, ru, en) in enumerate(SYSTEM_CATEGORIES):
            exists = await session.scalar(
                select(Category.id).where(
                    Category.user_id.is_(None), Category.key == key
                )
            )
            if exists:
                continue
            session.add(
                Category(
                    user_id=None,
                    key=key,
                    emoji=emoji,
                    color=color,
                    sort=sort,
                    name_tg=tg,
                    name_ru=ru,
                    name_en=en,
                )
            )
            added += 1
        await session.commit()
    return added


async def _main() -> None:
    added = await seed_categories()
    print(f"  ✓ категорияҳо: {added} нав, {len(SYSTEM_CATEGORIES)} ҳамагӣ")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
