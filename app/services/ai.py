"""Қабати OpenAI.

Се вазифа:
  * `classify`  — категорияи харҷ ё пешниҳоди категорияи нав
  * `extract`   — сумма ва тавсиф аз матни озод, вақте parser нафаҳмид
  * `read_receipt` — суммаи чек аз акс

Қоидаи асосӣ: **харҷ ҳеҷ гоҳ аз сабаби AI гум намешавад.** Ҳар хато,
timeout ё ҷавоби нодуруст → `None` бармегардад ва даъваткунанда роҳи
оддиро мегирад.
"""

import asyncio
import base64
import json
import logging
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.config import CURRENCIES, settings

log = logging.getLogger(__name__)

AI_TIMEOUT = 12.0
MIN_CONFIDENCE = 0.6

# Агар калид кредит надошта бошад ё нодуруст бошад, ҳар паём беҳуда
# чанд сония интизор мешавад. Дар чунин ҳолат AI-ро муваққатан хомӯш
# мекунем — бот бо луғат кор мекунад ва фаврӣ ҷавоб медиҳад.
QUOTA_COOLDOWN = 1800.0  # 30 дақиқа

_client = None
_disabled_until = 0.0


def available() -> bool:
    return settings.ai_enabled and time.monotonic() >= _disabled_until


def _disable(reason: str, seconds: float = QUOTA_COOLDOWN) -> None:
    global _disabled_until
    if time.monotonic() < _disabled_until:
        return
    _disabled_until = time.monotonic() + seconds
    log.warning(
        "AI барои %.0f дақиқа хомӯш шуд (%s). "
        "Бот бо луғат кор мекунад — харҷҳо гум намешаванд.",
        seconds / 60,
        reason,
    )


def _get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=AI_TIMEOUT,
            # такрори дохилии SDK интизориро ду баробар мекунад —
            # мо худамон timeout дорем
            max_retries=0,
        )
    return _client


async def _ask(messages: list[dict], schema: dict, tokens: int = 300) -> dict | None:
    """Як дархост бо ҷавоби сохторӣ. Ҳар хато → `None`."""
    if not available():
        return None

    try:
        response = await asyncio.wait_for(
            _get_client().chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                response_format={"type": "json_schema", "json_schema": schema},
                temperature=0,
                max_tokens=tokens,
            ),
            timeout=AI_TIMEOUT,
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception as exc:
        name = exc.__class__.__name__
        if name in {"RateLimitError", "AuthenticationError", "PermissionDeniedError"}:
            # Кредит тамом шуд ё калид нодуруст — такрор кардан бефоида аст
            _disable(name)
        else:
            log.warning("AI %s: %s", name, exc)
        return None


# --- 1. Категория --------------------------------------------------------


@dataclass(slots=True)
class NewCategory:
    key: str
    emoji: str
    name_tg: str
    name_ru: str
    name_en: str


@dataclass(slots=True)
class Classification:
    category_key: str | None
    confidence: float
    new_category: NewCategory | None


_CLASSIFY_SCHEMA = {
    "name": "expense_category",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["category_key", "confidence", "new_category"],
        "properties": {
            "category_key": {"type": ["string", "null"]},
            "confidence": {"type": "number"},
            "new_category": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "required": ["key", "emoji", "name_tg", "name_ru", "name_en"],
                "properties": {
                    "key": {"type": "string"},
                    "emoji": {"type": "string"},
                    "name_tg": {"type": "string"},
                    "name_ru": {"type": "string"},
                    "name_en": {"type": "string"},
                },
            },
        },
    },
}

_CLASSIFY_SYSTEM = (
    "Ты классифицируешь личные расходы. Текст бывает на таджикском, русском "
    "или английском, часто с опечатками и сокращениями.\n\n"
    "Верни ключ подходящей категории из списка allowed и confidence 0..1.\n"
    "Если по смыслу НИ ОДНА не подходит — верни category_key=null и предложи "
    "новую в new_category: короткий латинский key (a-z, 3-16 букв), одно "
    "уместное эмодзи и название на трёх языках, 1-2 слова каждое.\n\n"
    "Не притягивай расход к чужой категории — лучше предложи новую.\n\n"
    "Примеры:\n"
    "  «такси на работу» → transport\n"
    "  «хлеб молоко» → food\n"
    "  «латте» → cafe\n"
    "  «стрижка в барбершопе» → null + новая «Красота»\n"
    "  «корм для кота» → null + новая «Питомцы»\n"
    "  «взнос по кредиту» → null + новая «Кредиты»"
)


async def classify(description: str, allowed_keys: list[str]) -> Classification | None:
    """Категорияро муайян мекунад ё категорияи нав пешниҳод менамояд.

    `allowed_keys` набояд «other» дошта бошад: вагарна модел ҳамеша ба он
    мегурезад ва ҳеҷ гоҳ категорияи нав пешниҳод намекунад.
    """
    if not description.strip():
        return None

    data = await _ask(
        [
            {"role": "system", "content": _CLASSIFY_SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {"expense": description, "allowed": allowed_keys},
                    ensure_ascii=False,
                ),
            },
        ],
        _CLASSIFY_SCHEMA,
        tokens=200,
    )
    return _parse_classification(data, allowed_keys) if data else None


def _parse_classification(data: dict, allowed_keys: list[str]) -> Classification | None:
    key = data.get("category_key")
    if key is not None and key not in allowed_keys:
        key = None  # AI чизи нестро номбар кард

    raw_new = data.get("new_category")
    new_category = None
    if isinstance(raw_new, dict) and raw_new.get("key"):
        new_key = _clean_key(str(raw_new["key"]))
        if new_key and new_key not in allowed_keys:
            new_category = NewCategory(
                key=new_key,
                emoji=_clean_emoji(str(raw_new.get("emoji", ""))),
                name_tg=_clean_name(raw_new.get("name_tg")),
                name_ru=_clean_name(raw_new.get("name_ru")),
                name_en=_clean_name(raw_new.get("name_en")),
            )

    try:
        confidence = float(data.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0

    if key is None and new_category is None:
        return None

    return Classification(
        category_key=key,
        confidence=max(0.0, min(1.0, confidence)),
        new_category=new_category,
    )


# --- 2. Матни озод -------------------------------------------------------


@dataclass(slots=True)
class ExtractedItem:
    amount: Decimal
    currency: str | None
    description: str


_EXTRACT_SCHEMA = {
    "name": "expense_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["is_expense", "items"],
        "properties": {
            "is_expense": {"type": "boolean"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["amount", "currency", "description"],
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": ["string", "null"]},
                        "description": {"type": "string"},
                    },
                },
            },
        },
    },
}

_EXTRACT_SYSTEM = (
    "Ты вытаскиваешь траты из свободного текста на таджикском, русском или "
    "английском. Сумма может быть словами («триста», «сад сомонӣ», "
    "«two hundred»).\n\n"
    "is_expense=false, если человек не записывает трату (приветствие, вопрос, "
    "болтовня) — тогда items пустой.\n"
    "В одном сообщении может быть несколько трат — верни их все.\n"
    "description — коротко, 1-3 слова, без суммы.\n"
    "currency: TJS, USD, RUB или null, если валюта не названа.\n\n"
    "Примеры:\n"
    "  «потратил триста пятьдесят на кофе» → [350, null, «кофе»]\n"
    "  «нон сад сомонӣ» → [100, TJS, «нон»]\n"
    "  «отдал 20 баксов за такси» → [20, USD, «такси»]\n"
    "  «салом чӣ хел?» → is_expense=false"
)


async def extract(text: str) -> list[ExtractedItem] | None:
    """Суммаҳоро аз матни озод мебарорад — вақте parser нафаҳмид.

    `None` → AI дастрас нест ё матн харҷ нест.
    """
    if not text.strip() or len(text) > 300:
        return None

    data = await _ask(
        [
            {"role": "system", "content": _EXTRACT_SYSTEM},
            {"role": "user", "content": text},
        ],
        _EXTRACT_SCHEMA,
        tokens=350,
    )
    if not data or not data.get("is_expense"):
        return None

    return _parse_items(data.get("items"))


def _parse_items(raw: object) -> list[ExtractedItem] | None:
    if not isinstance(raw, list):
        return None

    items: list[ExtractedItem] = []
    for entry in raw[:10]:
        if not isinstance(entry, dict):
            continue
        try:
            amount = Decimal(str(entry.get("amount"))).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if amount <= 0 or amount > Decimal("100000000"):
            continue

        currency = entry.get("currency")
        if currency not in CURRENCIES:
            currency = None

        items.append(
            ExtractedItem(
                amount=amount,
                currency=currency,
                description=_clean_name(entry.get("description"), limit=120),
            )
        )

    return items or None


# --- 3. Чек аз акс -------------------------------------------------------


@dataclass(slots=True)
class Receipt:
    total: Decimal
    currency: str | None
    merchant: str
    hint: str


_RECEIPT_SCHEMA = {
    "name": "receipt",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["found", "total", "currency", "merchant", "hint"],
        "properties": {
            "found": {"type": "boolean"},
            "total": {"type": ["number", "null"]},
            "currency": {"type": ["string", "null"]},
            "merchant": {"type": "string"},
            "hint": {"type": "string"},
        },
    },
}

_RECEIPT_SYSTEM = (
    "Ты читаешь фотографию платёжного документа: чек магазина, квитанцию, "
    "скриншот банковского перевода или оплаты в приложении.\n\n"
    "total — сумма списания: «итого», «всего», «total», «ҳамагӣ», "
    "«сумма операции». Не бери отдельные позиции, сдачу, комиссию и остаток "
    "на счёте.\n"
    "merchant — магазин, банк или получатель, если видно, иначе пустая строка.\n"
    "hint — 1-2 слова о том, за что платили («продукты», «аптека», «кафе»). "
    "Если по документу этого не понять — например обычный перевод по номеру "
    "телефона — оставь hint пустым, не выдумывай.\n"
    "currency: TJS, USD, RUB или null.\n"
    "found=false, только если это не платёжный документ или сумма не читается."
)


async def read_receipt(image: bytes, mime: str = "image/jpeg") -> Receipt | None:
    """Суммаро аз акси чек мехонад."""
    if not image or len(image) > 8 * 1024 * 1024:
        return None

    encoded = base64.b64encode(image).decode()
    data = await _ask(
        [
            {"role": "system", "content": _RECEIPT_SYSTEM},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{encoded}",
                            "detail": "low",
                        },
                    }
                ],
            },
        ],
        _RECEIPT_SCHEMA,
        tokens=200,
    )

    if not data or not data.get("found"):
        return None

    try:
        total = Decimal(str(data.get("total"))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if total <= 0 or total > Decimal("100000000"):
        return None

    currency = data.get("currency")
    if currency not in CURRENCIES:
        currency = None

    return Receipt(
        total=total,
        currency=currency,
        merchant=_clean_name(data.get("merchant"), limit=64),
        hint=_clean_name(data.get("hint"), limit=64),
    )


# --- тозакунӣ ------------------------------------------------------------


def _clean_key(value: str) -> str:
    key = "".join(c for c in value.lower() if c.isascii() and (c.isalnum() or c == "_"))
    return key[:16] if len(key) >= 3 else ""


def _clean_emoji(value: str) -> str:
    value = value.strip()
    return value[:4] if value else "🏷"


def _clean_name(value: object, limit: int = 32) -> str:
    name = str(value or "").strip()
    return name[:limit]
