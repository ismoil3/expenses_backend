"""Ислоҳи суммаи харҷ аз бот.

Талаботи ҳакатон: «трату можно исправить — и из бота, и из панели».
Категория ва нест кардан аллакай буданд, сумма — не.

Роутер якум сабт мешавад: ҳангоми интизори сумма ҳама паёмҳо ба ин ҷо
меоянд, то матн ба ҷои сумма ҳамчун харҷи нав сабт нашавад.
"""

from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import format as fmt
from app.bot import keyboards as kb
from app.bot.i18n import t
from app.db.models import User
from app.services import expenses
from app.services.parser import parse_message

router = Router(name="edit")


class EditExpense(StatesGroup):
    amount = State()


def _card(expense, user: User) -> str:
    return (
        f"✅ <b>{fmt.amount_line(expense, user)}</b> · "
        f"{fmt.category_label(expense.category, user.lang)}\n"
        f"{fmt.description(expense)}"
    ).strip()


@router.callback_query(F.data.startswith(f"{kb.CB_AMOUNT}:"))
async def ask_amount(
    query: CallbackQuery, session: AsyncSession, user: User, state: FSMContext
) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    expense = await expenses.get_alive(session, user.id, expense_id)
    if expense is None:
        await query.answer(t("expense.not_found", user.lang), show_alert=True)
        return

    await state.set_state(EditExpense.amount)
    await state.update_data(
        expense_id=expense_id,
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
    )

    await query.message.answer(
        t(
            "edit.ask_amount",
            user.lang,
            current=fmt.amount_line(expense, user),
        ),
        reply_markup=kb.cancel_only(user.lang),
    )
    await query.answer()


@router.callback_query(F.data == kb.CB_CANCEL)
async def cancel(query: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.clear()
    await query.message.edit_text(t("edit.cancelled", user.lang))
    await query.answer()


@router.message(EditExpense.amount, F.text)
async def apply_amount(
    message: Message, session: AsyncSession, user: User, state: FSMContext
) -> None:
    text = (message.text or "").strip()

    # Ҳангоми интизори сумма ин роутер ҳама паёмҳоро мегирад, аз ҷумла
    # командаҳоро — вагарна /today ҳамчун сумма хонда мешуд
    if text.startswith("/"):
        await state.clear()
        await message.answer(t("edit.cancelled_command", user.lang))
        return

    parsed = parse_message(text)
    if not parsed:
        await message.answer(
            t("edit.bad_amount", user.lang), reply_markup=kb.cancel_only(user.lang)
        )
        return

    data = await state.get_data()
    await state.clear()

    new = parsed[0]
    expense = await expenses.set_amount(
        session,
        user,
        int(data["expense_id"]),
        new.amount,
        new.currency,
        new.description or None,
    )
    if expense is None:
        await message.answer(t("expense.not_found", user.lang))
        return

    total = await expenses.period_total(session, user, "today")
    await message.answer(
        t(
            "edit.saved",
            user.lang,
            amount=fmt.amount_line(expense, user),
            cat=fmt.category_label(expense.category, user.lang),
            desc=escape(expense.description),
            period=t("label.today", user.lang),
            total=fmt.money_short(total, user.base_currency),
        ),
        reply_markup=kb.expense_actions(expense.id, user.lang),
    )

    # Корточкаи кӯҳна дигар рақами дурустро нишон намедиҳад
    try:
        await message.bot.edit_message_text(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            text=_card(expense, user),
            reply_markup=None,
        )
    except Exception:
        pass  # паём кӯҳна ё нест шудааст — фарқ надорад
