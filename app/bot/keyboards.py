"""Клавиатураҳои бот."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from app.bot.i18n import LANG_LABELS, t
from app.config import CURRENCIES, CURRENCY_SIGN, settings
from app.db.models import Category

# --- callback data ---
# фишурда нигоҳ медорем: Telegram ба 64 байт маҳдуд аст
CB_CAT_MENU = "cat"  # cat:<expense_id>
CB_CAT_SET = "cs"  # cs:<expense_id>:<category_id>
CB_AMOUNT = "amt"  # amt:<expense_id>
CB_CANCEL = "esc"  # esc
CB_DELETE = "del"  # del:<expense_id>
CB_RESTORE = "res"  # res:<expense_id>
CB_UNDO_MANY = "undo"  # undo:<id>,<id>,...
CB_NEWCAT_YES = "ny"  # ny:<expense_id>:<token>
CB_NEWCAT_NO = "nn"  # nn:<expense_id>:<token>
CB_LANG = "lang"  # lang:<code>
CB_CURRENCY = "cur"  # cur:<code>
CB_PERIOD = "per"  # per:<period>
CB_LIMIT_ADD = "la"  # la
CB_LIMIT_PICK = "lp"  # lp:<category_id>
CB_LIMIT_DEL = "ld"  # ld:<category_id>


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Клавиатураи доимӣ — роҳи кӯтоҳтарин то графики аввал."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("kb.today", lang)), KeyboardButton(text=t("kb.week", lang))],
            [KeyboardButton(text=t("kb.month", lang)), KeyboardButton(text=t("kb.panel", lang))],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def expense_actions(expense_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn.amount", lang), callback_data=f"{CB_AMOUNT}:{expense_id}"
                ),
                InlineKeyboardButton(
                    text=t("btn.category", lang),
                    callback_data=f"{CB_CAT_MENU}:{expense_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("btn.delete", lang), callback_data=f"{CB_DELETE}:{expense_id}"
                )
            ],
        ]
    )


def cancel_only(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn.cancel", lang), callback_data=CB_CANCEL)]
        ]
    )


def undo_many(expense_ids: list[int], lang: str) -> InlineKeyboardMarkup:
    ids = ",".join(str(i) for i in expense_ids)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn.undo_all", lang), callback_data=f"{CB_UNDO_MANY}:{ids}"
                )
            ]
        ]
    )


def restore_button(expense_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn.restore", lang), callback_data=f"{CB_RESTORE}:{expense_id}"
                )
            ]
        ]
    )


def category_picker(
    expense_id: int, categories: list[Category], lang: str
) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=f"{c.emoji} {c.name(lang)}",
            callback_data=f"{CB_CAT_SET}:{expense_id}:{c.id}",
        )
        for c in categories
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def new_category_confirm(expense_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn.newcat_yes", lang), callback_data=f"{CB_NEWCAT_YES}:{expense_id}")],
            [InlineKeyboardButton(text=t("btn.newcat_no", lang), callback_data=f"{CB_NEWCAT_NO}:{expense_id}")],
        ]
    )


def limits_menu(lang: str, limited: list[Category]) -> InlineKeyboardMarkup:
    """Тугмаи иловаи лимит + нест кардани лимитҳои мавҷуда."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=t("btn.limit_add", lang), callback_data=CB_LIMIT_ADD
            )
        ]
    ]
    for category in limited:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {category.emoji} {category.name(lang)}",
                    callback_data=f"{CB_LIMIT_DEL}:{category.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def limit_category_picker(
    categories: list[Category], lang: str
) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=f"{c.emoji} {c.name(lang)}", callback_data=f"{CB_LIMIT_PICK}:{c.id}"
        )
        for c in categories
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    )


def is_public_https(url: str) -> bool:
    """Telegram дар тугмаҳо танҳо HTTPS-и оммавиро қабул мекунад.

    Барои `localhost` даъват бо `BUTTON_URL_INVALID` меафтад — ҳангоми
    таҳия ба ҷои тугма линки одӣ фиристода мешавад.
    """
    return url.startswith("https://") and not any(
        host in url for host in ("localhost", "127.0.0.1")
    )


def panel_link_button(url: str, lang: str) -> InlineKeyboardMarkup | None:
    """Ду роҳи кушодани панел: дар браузер ва дар худи Telegram."""
    if not is_public_https(url):
        return None

    rows = [[InlineKeyboardButton(text=t("btn.open_panel", lang), url=url)]]

    # Mini App панелро дар худи Telegram мекушояд — вуруд бо `initData`,
    # барои ҳамин линки яккарата ин ҷо лозим нест
    if is_public_https(settings.PANEL_URL):
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("btn.open_miniapp", lang),
                    web_app=WebAppInfo(url=settings.PANEL_URL),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_picker() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"{CB_LANG}:{code}")]
            for code, label in LANG_LABELS.items()
        ]
    )


def currency_picker() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{code} {CURRENCY_SIGN.get(code, '')}",
                    callback_data=f"{CB_CURRENCY}:{code}",
                )
                for code in CURRENCIES
            ]
        ]
    )


def report_nav(lang: str, exclude: str = "") -> InlineKeyboardMarkup:
    items = [
        ("today", t("kb.today", lang)),
        ("week", t("kb.week", lang)),
        ("month", t("kb.month", lang)),
    ]
    buttons = [
        InlineKeyboardButton(text=label, callback_data=f"{CB_PERIOD}:{period}")
        for period, label in items
        if period != exclude
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
