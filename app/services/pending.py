"""Пешниҳодҳои категорияи нав, ки интизори ҷавоби корбаранд.

Дар хотираи process нигоҳ дошта мешаванд: агар бот аз нав сар шавад,
корбар танҳо тугмаро пахш карда, «дер шуд» мегирад — харҷ ҷои худаш аст.
"""

import time

from app.services.ai import NewCategory

TTL_SECONDS = 900  # 15 дақиқа
MAX_ITEMS = 500

_STORE: dict[int, tuple[float, NewCategory, str]] = {}


def _cleanup() -> None:
    now = time.monotonic()
    expired = [key for key, (ts, _, _) in _STORE.items() if now - ts > TTL_SECONDS]
    for key in expired:
        _STORE.pop(key, None)
    while len(_STORE) > MAX_ITEMS:
        _STORE.pop(next(iter(_STORE)), None)


def put(expense_id: int, suggestion: NewCategory, phrase: str) -> None:
    _cleanup()
    _STORE[expense_id] = (time.monotonic(), suggestion, phrase)


def pop(expense_id: int) -> tuple[NewCategory, str] | None:
    item = _STORE.pop(expense_id, None)
    if item is None:
        return None
    ts, suggestion, phrase = item
    if time.monotonic() - ts > TTL_SECONDS:
        return None
    return suggestion, phrase
