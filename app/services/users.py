"""Корбарон — аккаунт худи Telegram аст, рӯйхатнома нест."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import normalize_lang
from app.config import settings
from app.db.models import User


async def get_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    return await session.scalar(select(User).where(User.tg_id == tg_id))


async def get_or_create(
    session: AsyncSession,
    tg_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
    language_code: str | None = None,
) -> User:
    """Корбарро меёбад ё месозад. Ҳангоми сохтан забон худкор муайян мешавад."""
    user = await get_by_tg_id(session, tg_id)
    if user is not None:
        # ном метавонад дигар шуда бошад
        if username != user.username or first_name != user.first_name:
            user.username = username
            user.first_name = first_name
        return user

    user = User(
        tg_id=tg_id,
        username=username,
        first_name=first_name,
        lang=normalize_lang(language_code or settings.DEFAULT_LANG),
        base_currency=settings.DEFAULT_CURRENCY,
        tz=settings.DEFAULT_TZ,
    )
    session.add(user)
    await session.flush()
    return user
