"""/start · /help · /lang · /currency · /cats"""

from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import keyboards as kb
from app.bot.handlers.reports import send_panel_link
from app.bot.i18n import LANG_LABELS, t
from app.config import CURRENCIES
from app.db.models import User
from app.services import categories, expenses

router = Router(name="start")


@router.message(CommandStart())
async def start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    user: User,
) -> None:
    # Тугмаи «Кушодани бот» дар саҳифаи вуруд `?start=panel` мефиристад —
    # корбар барои панел омадааст, на барои салом
    if (command.args or "").strip() == "panel":
        await send_panel_link(message, session, user)
        return

    await message.answer(
        t("start.greeting", user.lang, name=escape(user.first_name or "")),
        reply_markup=kb.main_keyboard(user.lang),
    )


@router.message(Command("help"))
async def help_command(message: Message, user: User) -> None:
    await message.answer(t("help.text", user.lang), reply_markup=kb.main_keyboard(user.lang))


@router.message(Command("lang"))
async def lang_command(message: Message, user: User) -> None:
    await message.answer(t("lang.choose", user.lang), reply_markup=kb.language_picker())


@router.callback_query(F.data.startswith(f"{kb.CB_LANG}:"))
async def lang_set(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    code = query.data.split(":", 1)[1]
    if code not in LANG_LABELS:
        await query.answer()
        return

    user.lang = code
    await session.flush()

    await query.message.edit_text(
        t("lang.changed", code, lang=LANG_LABELS[code])
    )
    # клавиатураи доимӣ бо забони нав
    await query.message.answer(
        t("help.text", code), reply_markup=kb.main_keyboard(code)
    )
    await query.answer()


@router.message(Command("currency"))
async def currency_command(message: Message, user: User) -> None:
    await message.answer(
        t("currency.choose", user.lang), reply_markup=kb.currency_picker()
    )


@router.callback_query(F.data.startswith(f"{kb.CB_CURRENCY}:"))
async def currency_set(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    code = query.data.split(":", 1)[1]
    if code not in CURRENCIES:
        await query.answer()
        return

    # Ҳама рақамҳо ба валютаи нав мегузаранд, вагарна ҷамъҳо омехта мешаванд
    moved = await expenses.rebase(session, user, code)

    await query.message.edit_text(
        t("currency.changed", user.lang, currency=code, count=moved)
    )
    await query.answer()


@router.message(Command("cats"))
async def cats(message: Message, session: AsyncSession, user: User) -> None:
    available = await categories.list_for_user(session, user.id)
    lines = [t("category.list", user.lang)]
    for category in available:
        star = "" if category.is_system else " ⭐"
        lines.append(f"{category.emoji} {escape(category.name(user.lang))}{star}")
    await message.answer("\n".join(lines))
