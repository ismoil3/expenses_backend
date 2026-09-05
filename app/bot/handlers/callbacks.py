"""Тугмаҳои зери паёмҳо: категория, нест кардан, бозгардонӣ, категорияи нав."""

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import format as fmt
from app.bot import keyboards as kb
from app.services import pending
from app.bot.i18n import t
from app.db.models import User
from app.services import categories, expenses
from app.services.parser import normalize_phrase

router = Router(name="callbacks")


def _expense_card(expense, user: User, category=None) -> str:
    label = fmt.category_label(category or expense.category, user.lang)
    return (
        f"✅ <b>{fmt.amount_line(expense, user)}</b> · {label}\n"
        f"{fmt.description(expense)}"
    ).strip()


@router.callback_query(F.data.startswith(f"{kb.CB_CAT_MENU}:"))
async def category_menu(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    if await expenses.get_alive(session, user.id, expense_id) is None:
        await query.answer(t("expense.not_found", user.lang), show_alert=True)
        return

    available = await categories.list_for_user(session, user.id)
    await query.message.edit_reply_markup(
        reply_markup=kb.category_picker(expense_id, available, user.lang)
    )
    await query.answer(t("category.choose", user.lang))


@router.callback_query(F.data.startswith(f"{kb.CB_CAT_SET}:"))
async def category_set(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    _, raw_expense, raw_category = query.data.split(":", 2)
    expense_id, category_id = int(raw_expense), int(raw_category)

    category = await categories.get_for_user(session, user.id, category_id)
    if category is None:
        await query.answer(t("error.generic", user.lang), show_alert=True)
        return

    expense = await expenses.set_category(session, user.id, expense_id, category)
    if expense is None:
        await query.answer(t("expense.not_found", user.lang), show_alert=True)
        return

    # Бот меомӯзад: дафъаи оянда ҳамин калима фавран дуруст мешавад
    await categories.remember(
        session, user.id, normalize_phrase(expense.description), category.id
    )

    await query.message.edit_text(
        _expense_card(expense, user, category),
        reply_markup=kb.expense_actions(expense_id, user.lang),
    )
    await query.answer(t("category.changed", user.lang, cat=category.name(user.lang)))


@router.callback_query(F.data.startswith(f"{kb.CB_DELETE}:"))
async def delete(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    expense = await expenses.get_alive(session, user.id, expense_id)
    if expense is None:
        await query.answer(t("expense.not_found", user.lang), show_alert=True)
        return

    amount = fmt.amount_line(expense, user)
    label = fmt.category_label(expense.category, user.lang)
    await expenses.soft_delete(session, user.id, expense_id)

    await query.message.edit_text(
        t("expense.deleted", user.lang, amount=amount, cat=label),
        reply_markup=kb.restore_button(expense_id, user.lang),
    )
    await query.answer()


@router.callback_query(F.data.startswith(f"{kb.CB_RESTORE}:"))
async def restore(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    if not await expenses.restore(session, user.id, expense_id):
        await query.answer(t("error.generic", user.lang), show_alert=True)
        return

    expense = await expenses.get_alive(session, user.id, expense_id)
    await query.message.edit_text(
        t(
            "expense.restored",
            user.lang,
            amount=fmt.amount_line(expense, user),
            cat=fmt.category_label(expense.category, user.lang),
        ),
        reply_markup=kb.expense_actions(expense_id, user.lang),
    )
    await query.answer()


@router.callback_query(F.data.startswith(f"{kb.CB_UNDO_MANY}:"))
async def undo_many(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    """D2 — «↩️ Ҳамаро бекор кун» баъди якчанд харҷ дар як паём."""
    raw = query.data.split(":", 1)[1]
    ids = [int(part) for part in raw.split(",") if part.isdigit()]

    removed = sum(
        [await expenses.soft_delete(session, user.id, expense_id) for expense_id in ids]
    )
    total = await expenses.period_total(session, user, "today")

    await query.message.edit_text(
        t(
            "expense.deleted_many",
            user.lang,
            count=removed,
            period=t("label.today", user.lang),
            total=fmt.money_short(total, user.base_currency),
        )
    )
    await query.answer()


@router.callback_query(F.data.startswith(f"{kb.CB_NEWCAT_YES}:"))
async def new_category_yes(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    item = pending.pop(expense_id)
    if item is None:
        await query.answer(t("error.generic", user.lang), show_alert=True)
        return

    suggestion, phrase = item
    category = await categories.create_custom(session, user.id, suggestion)
    if category is None:
        await query.answer(
            t("newcat.limit", user.lang, limit=categories.MAX_CUSTOM_CATEGORIES),
            show_alert=True,
        )
        return

    expense = await expenses.set_category(session, user.id, expense_id, category)
    if expense is not None:
        expense.cat_source = "new"
    await categories.remember(session, user.id, phrase, category.id)

    await query.message.edit_text(
        t(
            "newcat.created",
            user.lang,
            amount=fmt.amount_line(expense, user),
            emoji=category.emoji,
            name=escape(category.name(user.lang)),
            phrase=escape(phrase),
        ),
        reply_markup=kb.expense_actions(expense_id, user.lang),
    )
    await query.answer()


@router.callback_query(F.data.startswith(f"{kb.CB_NEWCAT_NO}:"))
async def new_category_no(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    item = pending.pop(expense_id)
    phrase = item[1] if item else ""

    # Дигар барои ҳамин калима намепурсем — то бот безор накунад
    if phrase:
        other = await categories.fallback(session)
        await categories.remember(session, user.id, phrase, other.id, declined=True)

    await query.message.edit_text(
        t("newcat.declined", user.lang, phrase=escape(phrase)),
        reply_markup=kb.expense_actions(expense_id, user.lang),
    )
    await query.answer()
