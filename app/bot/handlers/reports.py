"""Ҳисоботҳо: /today · /week · /month · /last · /undo · /panel"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import format as fmt
from app.bot import keyboards as kb
from app.bot.i18n import TABLES, t
from app.db.models import User
from app.services import auth, expenses, stats
from app.services.csv_export import build_csv
from app.services.period import (
    day_buckets,
    format_period_title,
    now_local,
    period_bounds,
)

router = Router(name="reports")

CB_PICK = "pick"
LAST_LIMIT = 10


def _texts(key: str) -> set[str]:
    """Матни тугмаи клавиатура дар ҳар се забон."""
    return {table[key] for table in TABLES.values()}


async def build_report(session: AsyncSession, user: User, period: str) -> str:
    start, end = period_bounds(user.tz, period)
    rows, total = await stats.by_category(session, user, start, end)
    period_label = t(f"label.{period}", user.lang)

    if not rows:
        return t("report.empty", user.lang, period=period_label)

    _, count = await stats.totals(session, user, start, end)

    blocks = [
        t(
            "report.header",
            user.lang,
            period=period_label,
            date=format_period_title(user.tz, user.lang, period),
        ),
        fmt.report_body(rows, total, user),
    ]

    # Барои имрӯз тақсими рӯзона маъно надорад — як рӯз аст
    if period != "today":
        daily = dict(await stats.by_day(session, user, start, end))
        buckets = day_buckets(user.tz, user.lang, period, daily)
        timeline = fmt.timeline_body(buckets, user)
        if timeline:
            blocks.append(
                t(f"report.by_{'days' if period == 'week' else 'weeks'}", user.lang)
                + "\n"
                + timeline
            )

    blocks.append(
        t(
            "report.footer",
            user.lang,
            label=t("label.total", user.lang),
            total=fmt.money_short(total, user.base_currency),
            count=count,
        )
    )
    return "\n\n".join(blocks)


async def _answer_report(
    message: Message, session: AsyncSession, user: User, period: str
) -> None:
    text = await build_report(session, user, period)
    await message.answer(text, reply_markup=kb.report_nav(user.lang, exclude=period))


@router.message(Command("today"))
@router.message(F.text.in_(_texts("kb.today")))
async def today(message: Message, session: AsyncSession, user: User) -> None:
    await _answer_report(message, session, user, "today")


@router.message(Command("week"))
@router.message(F.text.in_(_texts("kb.week")))
async def week(message: Message, session: AsyncSession, user: User) -> None:
    await _answer_report(message, session, user, "week")


@router.message(Command("month"))
@router.message(F.text.in_(_texts("kb.month")))
async def month(message: Message, session: AsyncSession, user: User) -> None:
    await _answer_report(message, session, user, "month")


@router.callback_query(F.data.startswith(f"{kb.CB_PERIOD}:"))
async def switch_period(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    period = query.data.split(":", 1)[1]
    if period not in {"today", "week", "month"}:
        await query.answer()
        return

    text = await build_report(session, user, period)
    await query.message.edit_text(
        text, reply_markup=kb.report_nav(user.lang, exclude=period)
    )
    await query.answer()


# --- панел ---------------------------------------------------------------


async def send_panel_link(
    message: Message, session: AsyncSession, user: User
) -> None:
    """Линки яккарата. Дар прод — тугма, дар localhost — матн.

    Telegram суроғаи `localhost`-ро дар тугмаи URL қабул намекунад,
    барои ҳамин ҳангоми таҳия линк ҳамчун матн меояд.
    """
    token = await auth.create_magic_token(session, user)
    url = auth.panel_link(token)
    keyboard = kb.panel_link_button(url, user.lang)

    await message.answer(
        t("panel.link" if keyboard else "panel.link_plain", user.lang, url=url),
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


@router.message(Command("panel"))
@router.message(F.text.in_(_texts("kb.panel")))
async def panel(message: Message, session: AsyncSession, user: User) -> None:
    await send_panel_link(message, session, user)


# --- содироти CSV ---------------------------------------------------------

CB_EXPORT = "exp"

EXPORT_PERIODS = ("month", "week", "all")


def _export_nav(lang: str, exclude: str) -> InlineKeyboardMarkup:
    labels = {
        "month": t("label.month", lang),
        "week": t("label.week", lang),
        "all": t("label.all_time", lang),
    }
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=labels[period], callback_data=f"{CB_EXPORT}:{period}"
                )
                for period in EXPORT_PERIODS
                if period != exclude
            ]
        ]
    )


async def _send_csv(
    message: Message, session: AsyncSession, user: User, period: str
) -> None:
    if period == "all":
        start = end = None
        label = t("label.all_time", user.lang)
    else:
        start, end = period_bounds(user.tz, period)
        label = t(f"label.{period}", user.lang)

    content, count = await build_csv(session, user, start, end)
    if count == 0:
        await message.answer(t("export.empty", user.lang))
        return

    stamp = now_local(user.tz).strftime("%Y-%m-%d")
    document = BufferedInputFile(
        content.encode("utf-8"), filename=f"amiri-{period}-{stamp}.csv"
    )

    await message.answer_document(
        document,
        caption=t("export.caption", user.lang, period=label, count=count),
        reply_markup=_export_nav(user.lang, exclude=period),
    )


@router.message(Command("export"))
async def export(message: Message, session: AsyncSession, user: User) -> None:
    await _send_csv(message, session, user, "month")


@router.callback_query(F.data.startswith(f"{CB_EXPORT}:"))
async def export_period(
    query: CallbackQuery, session: AsyncSession, user: User
) -> None:
    period = query.data.split(":", 1)[1]
    if period not in EXPORT_PERIODS:
        await query.answer()
        return

    await _send_csv(query.message, session, user, period)
    await query.answer()


# --- рӯйхати охирин -------------------------------------------------------


@router.message(Command("last"))
async def last(message: Message, session: AsyncSession, user: User) -> None:
    rows = await expenses.last(session, user.id, LAST_LIMIT)
    if not rows:
        await message.answer(t("last.empty", user.lang))
        return

    lines = [t("last.title", user.lang)]
    buttons: list[InlineKeyboardButton] = []

    for index, expense in enumerate(rows, start=1):
        lines.append(fmt.expense_row(expense, user, prefix=f"{index}."))
        buttons.append(
            InlineKeyboardButton(text=str(index), callback_data=f"{CB_PICK}:{expense.id}")
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[buttons[i : i + 5] for i in range(0, len(buttons), 5)]
    )
    await message.answer("\n".join(lines), reply_markup=keyboard)


@router.callback_query(F.data.startswith(f"{CB_PICK}:"))
async def pick(query: CallbackQuery, session: AsyncSession, user: User) -> None:
    expense_id = int(query.data.split(":", 1)[1])
    expense = await expenses.get_alive(session, user.id, expense_id)
    if expense is None:
        await query.answer(t("expense.not_found", user.lang), show_alert=True)
        return

    text = (
        f"<b>{fmt.amount_line(expense, user)}</b> · "
        f"{fmt.category_label(expense.category, user.lang)}\n"
        f"{fmt.description(expense)}"
    ).strip()
    await query.message.answer(
        text, reply_markup=kb.expense_actions(expense.id, user.lang)
    )
    await query.answer()


@router.message(Command("undo"))
async def undo(message: Message, session: AsyncSession, user: User) -> None:
    expense_id = await expenses.last_alive_id(session, user.id)
    if expense_id is None:
        await message.answer(t("expense.nothing_to_undo", user.lang))
        return

    expense = await expenses.get_alive(session, user.id, expense_id)
    amount = fmt.amount_line(expense, user)
    label = fmt.category_label(expense.category, user.lang)
    await expenses.soft_delete(session, user.id, expense_id)

    await message.answer(
        t("expense.deleted", user.lang, amount=amount, cat=label),
        reply_markup=kb.restore_button(expense_id, user.lang),
    )
