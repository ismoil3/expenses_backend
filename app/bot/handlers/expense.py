"""Сабти харҷ аз матни оддӣ — роҳи асосии кор бо бот."""

import re
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
from app.services.parser import MAX_EXPENSES_PER_MESSAGE, ParsedExpense

router = Router(name="expense")

_BLANK_LINES = re.compile(r"\n{3,}")


def _tidy(text: str) -> str:
    """Тавсиф холӣ бошад, сатри холии зиёдатӣ намемонад."""
    return _BLANK_LINES.sub("\n\n", text).strip()


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: Message, session: AsyncSession, user: User) -> None:
    # Қоида → агар нафаҳмид, AI матни озодро мехонад
    parsed_list = await intake.from_text(message.text or "")

    if not parsed_list:
        await message.answer(t("expense.not_understood", user.lang))
        return

    if len(parsed_list) == 1:
        await _save_single(message, session, user, parsed_list[0])
    else:
        await _save_many(message, session, user, parsed_list)


async def _save_single(
    message: Message, session: AsyncSession, user: User, parsed: ParsedExpense
) -> None:
    decision = await categorizer.resolve(session, user, parsed)
    expense = await expenses.create(session, user, parsed, decision)
    total = await expenses.period_total(session, user, "today")

    text = _tidy(
        t(
            "expense.saved",
            user.lang,
            amount=fmt.amount_line(expense, user),
            cat=fmt.category_label(decision.category, user.lang),
            desc=fmt.description(expense),
            period=t("label.today", user.lang),
            total=fmt.money_short(total, user.base_currency),
        )
    )

    # Огоҳии лимит — танҳо ҳангоми гузаштан аз зина
    status = await limits.check(session, user, expense)
    if status is not None:
        text += fmt.limit_status(status, user, t)

    # Ҳеҷ категория мувофиқ наомад — AI категорияи нав пешниҳод мекунад
    if decision.suggestion is not None:
        pending.put(expense.id, decision.suggestion, decision.phrase)
        text += t(
            "newcat.suggest",
            user.lang,
            phrase=escape(decision.phrase or parsed.description),
            emoji=decision.suggestion.emoji,
            name=escape(_suggestion_name(decision.suggestion, user.lang)),
        )
        await message.answer(
            text, reply_markup=kb.new_category_confirm(expense.id, user.lang)
        )
        return

    await message.answer(text, reply_markup=kb.expense_actions(expense.id, user.lang))


async def _save_many(
    message: Message, session: AsyncSession, user: User, parsed_list: list[ParsedExpense]
) -> None:
    """D2 — якчанд харҷ дар як паём."""
    lines: list[str] = []
    ids: list[int] = []

    for parsed in parsed_list:
        decision = await categorizer.resolve(session, user, parsed)
        expense = await expenses.create(session, user, parsed, decision)
        ids.append(expense.id)
        lines.append(fmt.expense_row(expense, user))

    total = await expenses.period_total(session, user, "today")

    text = t("expense.multi_header", user.lang, count=len(ids))
    text += "\n\n" + "\n".join(lines) + "\n"
    text += t(
        "expense.multi_footer",
        user.lang,
        period=t("label.today", user.lang),
        total=fmt.money_short(total, user.base_currency),
    )

    if len(parsed_list) >= MAX_EXPENSES_PER_MESSAGE:
        text += t("expense.limit", user.lang, limit=MAX_EXPENSES_PER_MESSAGE)

    await message.answer(_tidy(text), reply_markup=kb.undo_many(ids, user.lang))


def _suggestion_name(suggestion, lang: str) -> str:
    return {
        "tg": suggestion.name_tg,
        "ru": suggestion.name_ru,
        "en": suggestion.name_en,
    }.get(lang) or suggestion.name_ru or suggestion.name_en
