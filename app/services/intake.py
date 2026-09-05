"""Як дарвоза барои ҳама роҳҳои вуруд: матн, матни озод, акси чек.

Тартиб муҳим аст: аввал parser-и қоидавӣ (0 мс, ройгон), баъд AI.
«кофе 350» ҳеҷ гоҳ ба AI намерасад — танҳо он чи қоида нафаҳмид.
"""

import logging

from app.services import ai
from app.services.parser import ParsedExpense, parse_message  # noqa: F401

log = logging.getLogger(__name__)


async def from_text(text: str) -> list[ParsedExpense]:
    """Матнро ба харҷҳо табдил медиҳад. Рӯйхати холӣ = харҷ нест."""
    parsed = parse_message(text)
    if parsed:
        return parsed

    # Parser рақам наёфт: «потратил триста на кофе», «нон сад сомонӣ»
    items = await ai.extract(text)
    if not items:
        return []

    log.info("AI аз матни озод %d харҷ бароварда", len(items))
    return [
        ParsedExpense(
            amount=item.amount,
            currency=item.currency,
            description=item.description,
            explicit_category=None,
            raw=text,
        )
        for item in items
    ]


async def from_receipt(
    image: bytes, mime: str = "image/jpeg", caption: str | None = None
) -> ParsedExpense | None:
    """Акси чекро ба харҷ табдил медиҳад.

    Агар акс имзо дошта бошад («kofe»), маҳз он тавсиф мешавад: чек
    суммаро медиҳад, одам маънои онро. Квитансияи бонкӣ худаш танҳо
    «интиқоли пул» аст ва ба ягон категория намеафтад.
    """
    receipt = await ai.read_receipt(image, mime)

    caption = (caption or "").strip()
    if receipt is None:
        # Чек хонда нашуд, вале шояд имзо худаш харҷ бошад: «kofe 50»
        return None if not caption else _first(await from_text(caption))

    if caption:
        # Имзо метавонад суммаи худро дошта бошад — онро дур мекунем,
        # сумма ҳамеша аз худи чек гирифта мешавад
        parsed_caption = parse_message(caption)
        description = (
            parsed_caption[0].description if parsed_caption else caption
        ) or caption
        explicit = parsed_caption[0].explicit_category if parsed_caption else None
    else:
        # Имзо нест — мағоза ва ишораи AI мемонанд
        description = " ".join(p for p in (receipt.merchant, receipt.hint) if p)
        explicit = None

    return ParsedExpense(
        amount=receipt.total,
        currency=receipt.currency,
        description=description.strip()[:120],
        explicit_category=explicit,
        raw=f"receipt: {receipt.merchant or '—'}",
    )


def _first(items: list[ParsedExpense]) -> ParsedExpense | None:
    return items[0] if items else None
