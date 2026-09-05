"""Аз як паёми оддӣ сумма, валюта ва тавсифро мебарорад.

Мисолҳо:
    кофе 350                  → 350.00, валютаи асосӣ, "кофе"
    350 кофе                  → 350.00, валютаи асосӣ, "кофе"
    такси 900 работа          → 900.00, валютаи асосӣ, "такси работа"
    нон 12,5                  → 12.50
    1к такси                  → 1000.00
    5$ обуна                  → 5.00 USD
    500р курс                 → 500.00 RUB
    350с нон                  → 350.00 TJS
    кофе 350 #cafe            → категорияи возеҳ "cafe"
    кофе 350, такси 900       → ДУ харҷи алоҳида
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

MAX_AMOUNT = Decimal("100000000")  # муҳофизат аз рақами бемаънӣ
MAX_EXPENSES_PER_MESSAGE = 10  # то як паём базаро пур накунад


@dataclass(slots=True)
class ParsedExpense:
    amount: Decimal
    currency: str | None  # None → валютаи асосии корбар
    description: str
    explicit_category: str | None  # аз #tag
    raw: str


# --- валютаҳо ------------------------------------------------------------
# Аломатҳои дукарата маънидор (с, р) танҳо дар паҳлӯи рақам эътибор доранд,
# вагарна «с дустам» ба валюта табдил меёфт.
_SYMBOLS = {"$": "USD", "₽": "RUB"}
_SYMBOL_RE = re.compile(r"[$₽]")

_UNAMBIGUOUS = {
    "TJS": ["сомонӣ", "сомони", "somoni", "смн", "tjs", "сом"],
    "USD": ["долларов", "доллар", "долл", "dollar", "usd", "бакс"],
    "RUB": ["рублей", "рубль", "рубл", "руб", "rub"],
}
_AMBIGUOUS = {
    "TJS": ["с", "c"],
    "RUB": ["р", "p"],
}


def _word_pattern(tokens: list[str]) -> re.Pattern[str]:
    # `(?<![^\W\d_])` = пеш аз он ҳарф нест — вале рақам мумкин («500руб»)
    alts = "|".join(re.escape(t) for t in sorted(tokens, key=len, reverse=True))
    return re.compile(rf"(?<![^\W\d_])({alts})\.?(?!\w)", re.IGNORECASE)


_UNAMBIGUOUS_RE = [(code, _word_pattern(tokens)) for code, tokens in _UNAMBIGUOUS.items()]
_AMBIGUOUS_RE = [
    (code, re.compile(r"(?<=\d)\s?(" + "|".join(tokens) + r")\.?(?!\w)", re.IGNORECASE))
    for code, tokens in _AMBIGUOUS.items()
]

# рақам: 350 · 12.5 · 12,5 (аммо на қисми "12.5.3")
_NUMBER_RE = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d{1,2})?)(?![\d])")
# ҳазор: 1к · 1k · 1.5к
_THOUSAND_RE = re.compile(r"\s?[кk](?!\w)", re.IGNORECASE)
# категорияи возеҳ: #cafe
_TAG_RE = re.compile(r"#([\w\-]{2,32})", re.UNICODE)

# паёмро ба чанд харҷ ҷудо мекунад: `;`, сатри нав ё вергул, вале НЕ дар "12,5"
_SPLIT_RE = re.compile(r"[;\n]+|,(?!\d)|(?<!\d),")

_TRIM = " \t\r\n.,:;!?-–—·•"


def _to_decimal(raw: str) -> Decimal | None:
    try:
        value = Decimal(raw.replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        return None
    if value <= 0 or value > MAX_AMOUNT:
        return None
    return value


def _extract_currency(text: str) -> tuple[str | None, str]:
    """Валютаро меёбад ва аз матн мебарорад."""
    symbol = _SYMBOL_RE.search(text)
    if symbol:
        code = _SYMBOLS[symbol.group(0)]
        return code, text[: symbol.start()] + " " + text[symbol.end() :]

    for code, pattern in _UNAMBIGUOUS_RE:
        match = pattern.search(text)
        if match:
            return code, text[: match.start()] + " " + text[match.end() :]
    for code, pattern in _AMBIGUOUS_RE:
        match = pattern.search(text)
        if match:
            return code, text[: match.start()] + " " + text[match.end() :]
    return None, text


def _extract_amount(text: str) -> tuple[Decimal | None, str]:
    """Аввалин рақамро ҳамчун сумма мегирад (бо назардошти `к` = ҳазор)."""
    match = _NUMBER_RE.search(text)
    if not match:
        return None, text

    value = _to_decimal(match.group(1))
    if value is None:
        return None, text

    rest = text[match.end() :]
    thousand = _THOUSAND_RE.match(rest)
    if thousand:
        value *= 1000
        rest = rest[thousand.end() :]

    if value > MAX_AMOUNT:
        return None, text

    return value, text[: match.start()] + " " + rest


def _extract_tag(text: str) -> tuple[str | None, str]:
    match = _TAG_RE.search(text)
    if not match:
        return None, text
    return match.group(1).lower(), text[: match.start()] + " " + text[match.end() :]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(_TRIM)


def parse_one(chunk: str) -> ParsedExpense | None:
    """Як порчаро ба харҷ табдил медиҳад. Агар сумма набошад — None."""
    raw = chunk.strip()
    if not raw:
        return None

    tag, text = _extract_tag(raw)
    currency, text = _extract_currency(text)
    amount, text = _extract_amount(text)

    if amount is None:
        return None

    return ParsedExpense(
        amount=amount.quantize(Decimal("0.01")),
        currency=currency,
        description=_clean(text),
        explicit_category=tag,
        raw=raw,
    )


def parse_message(text: str) -> list[ParsedExpense]:
    """Паёмро ба рӯйхати харҷҳо табдил медиҳад.

    Як паём метавонад якчанд харҷ дошта бошад:
        «кофе 350, такси 900, нон 20» → се харҷ.
    Порчаҳои бе рақам сарфи назар мешаванд.
    """
    if not text or not text.strip():
        return []

    chunks = [c for c in _SPLIT_RE.split(text) if c and c.strip()]
    if not chunks:
        return []

    parsed = [p for c in chunks for p in (parse_one(c),) if p is not None]

    # Агар ҷудокунӣ натиҷа надод, тамоми паёмро ҳамчун як харҷ месанҷем
    # (масалан «нон 12,5» — вергул рақамро бурида буд).
    if not parsed:
        single = parse_one(text)
        return [single] if single else []

    return parsed[:MAX_EXPENSES_PER_MESSAGE]


def normalize_phrase(description: str) -> str:
    """Калиди хотираи категория: «Кофе 2 шт!» → «кофе шт».

    Рақамҳо ва аломатҳо партофта мешаванд, то «кофе 350» ва «кофе 500»
    як калид дошта бошанд.
    """
    text = description.lower().replace("ё", "е")
    text = re.sub(r"[^\w\sЀ-ӿ]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\d+", " ", text)
    words = [w for w in text.split() if len(w) > 1]
    return " ".join(words[:4])[:120]
