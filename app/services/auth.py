"""Вуруд ба панел бе парол.

Ду роҳ, ҳарду ба ҳамон cookie мерасанд:

  1. Линки яккарата аз команди `/panel` — токени тасодуфӣ, 5 дақиқа,
     як маротиба. Дар база танҳо sha256-и он нигоҳ дошта мешавад.
  2. Telegram Mini App — имзои `initData` бо HMAC санҷида мешавад.
"""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AuthToken, User

SESSION_COOKIE = "amiri_session"
ALGORITHM = "HS256"

# `initData`-и кӯҳнатар аз ин қабул намешавад
MINIAPP_MAX_AGE = timedelta(hours=24)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# --- линки яккарата --------------------------------------------------------


async def create_magic_token(session: AsyncSession, user: User) -> str:
    token = secrets.token_urlsafe(32)
    session.add(
        AuthToken(
            user_id=user.id,
            token_hash=_hash(token),
            expires_at=_now() + timedelta(minutes=settings.MAGIC_TOKEN_TTL_MINUTES),
        )
    )
    await session.flush()
    return token


def panel_link(token: str) -> str:
    return f"{settings.PANEL_URL.rstrip('/')}/auth?token={token}"


async def consume_magic_token(session: AsyncSession, token: str) -> User | None:
    """Токенро як маротиба истифода мекунад ва корбарро бармегардонад."""
    if not token:
        return None

    row = await session.scalar(
        select(AuthToken).where(AuthToken.token_hash == _hash(token))
    )
    if row is None or row.used_at is not None or row.expires_at <= _now():
        return None

    row.used_at = _now()
    return await session.get(User, row.user_id)


async def purge_expired_tokens(session: AsyncSession) -> None:
    await session.execute(
        AuthToken.__table__.delete().where(AuthToken.expires_at < _now())
    )


# --- Telegram Mini App -----------------------------------------------------


def verify_init_data(init_data: str) -> dict | None:
    """Имзои `initData`-ро тафтиш мекунад ва маълумоти корбарро бармегардонад.

    Алгоритми расмии Telegram: калиди махфӣ = HMAC(«WebAppData», токени бот),
    сипас HMAC-и ҳамон калид аз сатри санҷишӣ бо `hash` муқоиса мешавад.
    """
    if not init_data or not settings.BOT_TOKEN:
        return None

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(
        b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    expected = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        return None

    # Имзо дуруст аст — акнун синну соли онро месанҷем
    try:
        auth_date = datetime.fromtimestamp(int(pairs.get("auth_date", 0)), timezone.utc)
    except (TypeError, ValueError):
        return None
    if _now() - auth_date > MINIAPP_MAX_AGE:
        return None

    try:
        return json.loads(pairs.get("user", "{}"))
    except json.JSONDecodeError:
        return None


# --- сессия ----------------------------------------------------------------


def issue_session(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(days=settings.JWT_TTL_DAYS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def read_session(token: str | None) -> int | None:
    """`user_id` аз cookie ё `None`, агар нодуруст/кӯҳна бошад."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
