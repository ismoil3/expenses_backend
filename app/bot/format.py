"""Форматкунии рақамҳо ва паёмҳои бот.

Ду қоидаи дизайн:

  1. **Рақам чизи асосӣ аст** — ғафс, бе тини беҳуда (`350 c.`, на `350.00 c.`).
  2. **Сутунҳо бо эмоҷи ҳамвор намешаванд.** Дар Telegram эмоҷи паҳнои
     дукарата дорад, барои ҳамин ҷадвали `<pre>` каҷ мешавад. Ба ҷои он
     диаграмма дар аввали сатр меистад — блокҳо ҳамеша як паҳноӣ доранд.
"""

from decimal import Decimal
from html import escape

from app.config import CURRENCY_SIGN
from app.db.models import Category, Expense, User

BAR_WIDTH = 10
BAR_FULL = "▰"
BAR_EMPTY = "▱"

_CENT = Decimal("0.01")


def sign(currency: str) -> str:
    return CURRENCY_SIGN.get(currency, currency)


def _group(value: Decimal) -> str:
    return f"{int(value):,}".replace(",", " ")


def money(amount: Decimal, currency: str) -> str:
    """`350` → `350 c.` · `12.5` → `12.50 c.` · `1234` → `1 234 c.`

    Тинҳо танҳо ҳангоми зарурат нишон дода мешаванд — «350.00» садои беҳуда аст.
    """
    value = Decimal(amount).quantize(_CENT)
    whole = value.to_integral_value(rounding="ROUND_DOWN")

    if value == whole:
        return f"{_group(whole)} {sign(currency)}"

    frac = f"{value:.2f}".split(".")[1]
    return f"{_group(whole)}.{frac} {sign(currency)}"


def money_short(amount: Decimal, currency: str) -> str:
    """Бе тини — барои ҷамъҳо ва ҳисоботҳо."""
    return f"{_group(Decimal(amount).quantize(Decimal('1')))} {sign(currency)}"


def amount_line(expense: Expense, user: User) -> str:
    """`350 c.` ё `5 $ ≈ 46 c.` агар валюта фарқ кунад."""
    original = money(expense.amount, expense.currency)
    if expense.currency == user.base_currency:
        return original
    return f"{original} ≈ {money(expense.amount_base, user.base_currency)}"


def category_label(category: Category, lang: str) -> str:
    return f"{category.emoji} {escape(category.name(lang))}"


def description(expense: Expense) -> str:
    """Тавсиф дар паҳлӯи сумма: «350 c. — кофе».

    Сумма ва он чи харида шуд як чиз аст, барои ҳамин дар як сатр
    меистанд; категория сатри алоҳида мегирад.
    """
    if not expense.description:
        return ""
    return f" — {escape(expense.description)}"


def bar(share: float) -> str:
    filled = min(BAR_WIDTH, max(1, round(share * BAR_WIDTH))) if share > 0 else 0
    return BAR_FULL * filled + BAR_EMPTY * (BAR_WIDTH - filled)


def report_body(
    rows: list[tuple[Category, Decimal]], total: Decimal, user: User
) -> str:
    """Диаграмма дар аввали сатр — ҳамвориро эмоҷи вайрон намекунад."""
    if not rows or total <= 0:
        return ""

    lines = [
        f"{bar(float(amount) / float(total))} {category.emoji} "
        f"{escape(category.name(user.lang))} · "
        f"<b>{money_short(amount, user.base_currency)}</b>"
        for category, amount in rows
    ]
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def timeline_body(buckets: list[tuple[str, Decimal]], user: User) -> str:
    """Диаграммаи «аз рӯи рӯзҳо» — ҳамон забони визуалӣ, ки категорияҳо.

    Сутуни холӣ ҳам нишон дода мешавад: рӯзи бе харҷ худаш маълумот аст.
    """
    if not buckets:
        return ""

    peak = max((amount for _, amount in buckets), default=Decimal(0))
    if peak <= 0:
        return ""

    width = max(len(label) for label, _ in buckets)
    lines = []
    for label, amount in buckets:
        value = (
            f"<b>{money_short(amount, user.base_currency)}</b>" if amount > 0 else "—"
        )
        lines.append(f"{bar(float(amount) / float(peak))} {label:<{width}} · {value}")

    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def limit_status(status, user: User, lang_text) -> str:
    """Ҳолати лимит зери харҷ.

    Дар лаҳзаи гузаштани зина — блоки калон бо диаграмма. Вагарна як
    сатри кӯтоҳ: корбар ҳамеша мебинад, ки дар кадом ҳолат аст, вале
    ҳар харҷ огоҳии баланг намегирад.
    """
    spent = money_short(status.spent, user.base_currency)
    limit = money_short(status.amount, user.base_currency)

    # Категория дар сатри болоии худи харҷ ҳаст — ин ҷо такрор лозим нест
    if status.crossed is None:
        return "\n" + lang_text(
            "limits.status", user.lang, mark=status.mark, spent=spent, limit=limit
        )

    key = "limits.exceeded" if status.crossed == "exceeded" else "limits.near"
    return "\n\n" + lang_text(
        key,
        user.lang,
        bar=bar(min(status.share, 1.0)),
        spent=spent,
        limit=limit,
    )


def expense_row(expense: Expense, user: User, *, prefix: str = "•") -> str:
    """Як сатри рӯйхат: `• 350 c. · ☕ Кафе — кофе`"""
    row = (
        f"{prefix} <b>{amount_line(expense, user)}</b> · "
        f"{category_label(expense.category, user.lang)}"
    )
    if expense.description:
        row += f" — {escape(expense.description)}"
    return row
