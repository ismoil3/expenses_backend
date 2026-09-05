"""Ҷамъоварии боти aiogram."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.bot.handlers import (
    callbacks,
    edit,
    expense,
    limits,
    photo,
    reports,
    start,
)
from app.bot.keyboards import is_public_https
from app.bot.middlewares import UserSessionMiddleware
from app.config import settings

log = logging.getLogger(__name__)


def build_bot() -> Bot:
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    dp.message.middleware(UserSessionMiddleware())
    dp.callback_query.middleware(UserSessionMiddleware())

    # Тартиб муҳим аст: `expense` ҳар матни оддиро мегирад,
    # барои ҳамин охирин меистад. `edit` якум аст — ҳангоми интизори
    # сумма паём набояд ба харҷи нав табдил ёбад.
    dp.include_router(edit.router)
    dp.include_router(limits.router)
    dp.include_router(start.router)
    dp.include_router(reports.router)
    dp.include_router(callbacks.router)
    dp.include_router(photo.router)
    dp.include_router(expense.router)

    return dp


async def set_menu_button(bot: Bot) -> None:
    """Тугмаи доимии Mini App дар назди майдони матн.

    Танҳо ҳангоми домени HTTPS кор мекунад — Telegram `localhost`-ро
    ҳамчун Web App қабул намекунад.
    """
    if not is_public_https(settings.PANEL_URL):
        log.info("PANEL_URL HTTPS нест — Mini App хомӯш аст")
        return

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Панель",
            web_app=WebAppInfo(url=settings.PANEL_URL),
        )
    )
    log.info("Mini App: %s", settings.PANEL_URL)


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="today", description="Итог за сегодня"),
            BotCommand(command="week", description="Итог за неделю"),
            BotCommand(command="month", description="Итог за месяц"),
            BotCommand(command="last", description="Последние расходы"),
            BotCommand(command="undo", description="Удалить последний"),
            BotCommand(command="limits", description="Лимиты по категориям"),
            BotCommand(command="export", description="Выгрузить CSV"),
            BotCommand(command="cats", description="Категории"),
            BotCommand(command="lang", description="Язык / Забон / Language"),
            BotCommand(command="currency", description="Валюта"),
            BotCommand(command="help", description="Помощь"),
        ]
    )
