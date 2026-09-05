"""Акси чек → харҷ.

Vision суммаи ниҳоиро мехонад, сипас ҳамон categorizer категорияро
муайян мекунад. Агар нахонад — корбар бе харҷ намемонад, балки
пешниҳоди дастӣ мегирад.
"""

import logging
from html import escape

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import format as fmt
from app.bot import keyboards as kb
from app.services import pending
from app.bot.i18n import t
from app.db.models import User
from app.services import categorizer, expenses, intake, limits

router = Router(name="photo")
log = logging.getLogger(__name__)

MAX_PHOTO_BYTES = 8 * 1024 * 1024


@router.message(F.photo)
async def on_photo(message: Message, session: AsyncSession, user: User) -> None:
    # Охирин андоза — калонтарин, барои хондани матн беҳтар аст
    photo = message.photo[-1]
    if photo.file_size and photo.file_size > MAX_PHOTO_BYTES:
        await message.answer(t("receipt.too_big", user.lang))
        return

    notice = await message.answer(t("receipt.reading", user.lang))

    try:
        buffer = await message.bot.download(photo.file_id)
        image = buffer.read() if buffer else b""
    except Exception as exc:
        log.warning("Акс боргирӣ нашуд: %s", exc)
        await notice.edit_text(t("receipt.failed", user.lang))
        return

    # Имзои акс маънои харҷро медиҳад: «kofe» зери квитансияи бонк
    parsed = await intake.from_receipt(image, caption=message.caption)
    if parsed is None:
        await notice.edit_text(t("receipt.failed", user.lang))
        return

    decision = await categorizer.resolve(session, user, parsed)
    expense = await expenses.create(session, user, parsed, decision, source="photo")
    total = await expenses.period_total(session, user, "today")

    text = t(
        "receipt.saved",
        user.lang,
        amount=fmt.amount_line(expense, user),
        cat=fmt.category_label(decision.category, user.lang),
        desc=escape(expense.description),
        period=t("label.today", user.lang),
        total=fmt.money_short(total, user.base_currency),
    )

    status = await limits.check(session, user, expense)
    if status is not None:
        text += fmt.limit_status(status, user, t)

    if decision.suggestion is not None:
        pending.put(expense.id, decision.suggestion, decision.phrase)
        text += t(
            "newcat.suggest",
            user.lang,
            phrase=escape(decision.phrase or parsed.description),
            emoji=decision.suggestion.emoji,
            name=escape(
                {
                    "tg": decision.suggestion.name_tg,
                    "ru": decision.suggestion.name_ru,
                    "en": decision.suggestion.name_en,
                }.get(user.lang)
                or decision.suggestion.name_ru
            ),
        )
        await notice.edit_text(
            text, reply_markup=kb.new_category_confirm(expense.id, user.lang)
        )
        return

    await notice.edit_text(
        text, reply_markup=kb.expense_actions(expense.id, user.lang)
    )
