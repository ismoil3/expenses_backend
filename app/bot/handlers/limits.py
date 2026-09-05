"""Лимитҳои моҳона аз рӯи категория: `/limits`.

Огоҳӣ ҳангоми сабти харҷ дар `handlers/expense.py` ва `photo.py` меояд —
ин ҷо танҳо идоракунии худи лимитҳо.
"""

from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import format as fmt
from app.bot import keyboards as kb
from app.bot.i18n import t
from app.db.models import User
from app.services import categories, limits
from app.services.parser import parse_message

router = Router(name="limits")


class SetLimit(StatesGroup):
    amount = State()


async def _render(session: AsyncSession, user: User) -> tuple[str, list]:
    views = await limits.list_for_user(session, user)
    if not views:
        return t("limits.empty", user.lang), []

    lines = [t("limits.title", user.lang)]
    for view in views:
        share = min(float(view.share), 1.0)
        mark = "🔴" if view.share >= 1 else "🟡" if view.share >= 0.8 else "🟢"
        lines.append(
            f"{mark} {view.category.emoji} {escape(view.category.name(user.lang))}\n"
            f"<code>{fmt.bar(share)}</code> "
            f"{fmt.money_short(view.spent, user.base_currency)} / "
            f"{fmt.money_short(view.amount, user.base_currency)}"
        )

    return "\n\n".join(lines), [view.category for view in views]


@router.message(Command("limits"))
async def show(message: Message, session: AsyncSession, user: User) -> None:
    text, limited = await _render(session, user)
    await message.answer(text, reply_markup=kb.limits_menu(user.lang, limited))


@router.callback_query(F.data == kb.CB_LIMIT_ADD)
async def add(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    available = await categories.list_for_user(session, user.id)
    await query.message.answer(
        t("limits.choose_category", user.lang),
        reply_markup=kb.limit_category_picker(available, user.lang),
    )
    await query.answer()


@router.callback_query(F.data.startswith(f"{kb.CB_LIMIT_PICK}:"))
async def ask_amount(
    query: CallbackQuery, session: AsyncSession, user: User, state: FSMContext
) -> None:
    category_id = int(query.data.split(":", 1)[1])
    category = await categories.get_for_user(session, user.id, category_id)
    if category is None:
        await query.answer(t("error.generic", user.lang), show_alert=True)
        return

    await state.set_state(SetLimit.amount)
    await state.update_data(category_id=category_id)

    await query.message.edit_text(
        t(
            "limits.ask_amount",
            user.lang,
            cat=fmt.category_label(category, user.lang),
            currency=user.base_currency,
        ),
        reply_markup=kb.cancel_only(user.lang),
    )
    await query.answer()


@router.message(SetLimit.amount, F.text)
async def save(
    message: Message, session: AsyncSession, user: User, state: FSMContext
) -> None:
    text = (message.text or "").strip()
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

    ok = await limits.set_limit(
        session, user, int(data["category_id"]), parsed[0].amount
    )
    if not ok:
        await message.answer(
            t("limits.too_many", user.lang, limit=limits.MAX_LIMITS)
        )
        return

    await session.flush()
    body, limited = await _render(session, user)
    await message.answer(
        t("limits.saved", user.lang) + "\n\n" + body,
        reply_markup=kb.limits_menu(user.lang, limited),
    )


@router.callback_query(F.data.startswith(f"{kb.CB_LIMIT_DEL}:"))
async def remove(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    category_id = int(query.data.split(":", 1)[1])
    await limits.remove(session, user.id, category_id)
    await session.flush()

    text, limited = await _render(session, user)
    await query.message.edit_text(
        text, reply_markup=kb.limits_menu(user.lang, limited)
    )
    await query.answer(t("limits.removed", user.lang))
