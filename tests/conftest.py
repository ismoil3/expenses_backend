"""Фикстураҳои умумӣ барои тестҳои API.

Тестҳо ба ҳамон пойгоҳи маълумоти таҳия мераванд, вале корбарони
худро бо `tg_id`-и беназир месозанд ва дар охир нест мекунанд —
маълумоти воқеӣ даст намехӯрад.
"""

import random

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.session import SessionLocal, engine
from app.main import app
from app.services import users
from app.services.auth import SESSION_COOKIE, issue_session


@pytest_asyncio.fixture(autouse=True)
async def _fresh_pool():
    """Ҳар тест event loop-и нав мегирад, вале пайвастҳои пул аз лупи
    қаблӣ мемонанд ва «Event loop is closed» медиҳанд. Пас аз ҳар тест
    пулро холӣ мекунем."""
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def session():
    async with SessionLocal() as db:
        yield db


async def _make_user(db, name: str):
    user = await users.get_or_create(
        db,
        random.randint(9_000_000_000, 9_999_999_999),
        first_name=name,
        language_code="ru",
    )
    await db.commit()
    return user


@pytest_asyncio.fixture
async def user_a(session):
    user = await _make_user(session, "Alice")
    yield user
    await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def user_b(session):
    user = await _make_user(session, "Bob")
    yield user
    await session.delete(user)
    await session.commit()


def _client_for(user) -> AsyncClient:
    client = AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    )
    client.cookies.set(SESSION_COOKIE, issue_session(user))
    return client


@pytest_asyncio.fixture
async def client_a(user_a):
    async with _client_for(user_a) as client:
        yield client


@pytest_asyncio.fixture
async def client_b(user_b):
    async with _client_for(user_b) as client:
        yield client


@pytest_asyncio.fixture
async def anon_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def coffee() -> dict:
    return {"text": "кофе 350"}
