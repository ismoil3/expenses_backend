"""Вобастагиҳои умумии API.

`get_current_user` ягона дарвозаи вуруд аст: ҳар роут аз он мегузарад ва
сипас ҳар query бо `user.id` филтр мешавад.
"""

from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_session
from app.services.auth import SESSION_COOKIE, read_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Требуется вход через бота",
)


def _from_header(value: str | None) -> str | None:
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


async def get_current_user(
    session: SessionDep,
    amiri_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Сессия аз cookie, вагарна аз `Authorization: Bearer`.

    Cookie роҳи асосӣ аст (JavaScript ба он намерасад). Header захиравист:
    баъзе браузерҳо cookie-и localhost-ро намегузоранд.
    """
    user_id = read_session(amiri_session) or read_session(_from_header(authorization))
    if user_id is None:
        raise UNAUTHORIZED

    user = await session.get(User, user_id)
    if user is None:
        raise UNAUTHORIZED
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
