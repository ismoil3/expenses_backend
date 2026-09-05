"""Amiri — як сервис: REST API барои панел + боти Telegram.

Бот дар ҳамон process ҳамчун asyncio task кор мекунад (BOT_MODE=polling)
ё тавассути webhook (BOT_MODE=webhook).
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth as auth_routes
from app.api.routes import categories as categories_routes
from app.api.routes import expenses as expenses_routes
from app.api.routes import export as export_routes
from app.api.routes import limits as limits_routes
from app.api.routes import me as me_routes
from app.api.routes import stats as stats_routes
from app.config import settings

# Консоли Windows пешфарз cp1251 аст ва ҳарфҳои тоҷикӣ (ӣ, ҷ, ҳ) -ро
# намефаҳмад — бе ин логҳо ҳангоми оғози локалӣ хато медиҳанд.
for _stream in (sys.stdout, sys.stderr):
    with suppress(Exception):
        _stream.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-5.5s [%(name)s] %(message)s",
)
log = logging.getLogger("amiri")

bot = None
dp = None
_polling_task: asyncio.Task | None = None


async def _run_polling() -> None:
    """Polling-и бот. Ҳангоми хатои шабака аз нав мекӯшад, вале
    сервисро намекушад — API мустақил кор мекунад."""
    delay = 5
    while True:
        try:
            await dp.start_polling(bot, handle_signals=False)
            return  # оромона қатъ шуд
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.error("Polling шикаст (%s) — баъди %s сония аз нав", exc, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, _polling_task

    if not settings.bot_enabled:
        log.warning("BOT_TOKEN гузошта нашудааст — танҳо API кор мекунад")
        yield
        return

    from app.bot.dispatcher import (
        build_bot,
        build_dispatcher,
        set_commands,
        set_menu_button,
    )

    bot = build_bot()
    dp = build_dispatcher()

    with suppress(Exception):
        await set_commands(bot)
    with suppress(Exception):
        await set_menu_button(bot)

    # Хатои шабакаи Telegram набояд тамоми сервисро кушад:
    # панел ва API бояд кор кунанд, ҳатто агар бот наздик нашуда бошад.
    if settings.BOT_MODE == "webhook":
        url = f"{settings.PUBLIC_URL.rstrip('/')}/webhook/{settings.WEBHOOK_SECRET}"
        try:
            await bot.set_webhook(url, drop_pending_updates=True)
            log.info("Бот дар реҷаи webhook: %s", url)
        except Exception as exc:
            log.error("Webhook гузошта нашуд (%s) — танҳо API кор мекунад", exc)
    else:
        with suppress(Exception):
            await bot.delete_webhook(drop_pending_updates=True)
        _polling_task = asyncio.create_task(_run_polling())
        log.info("Бот дар реҷаи polling")

    yield

    if _polling_task is not None:
        _polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await _polling_task
    with suppress(Exception):
        await bot.session.close()


app = FastAPI(
    title="Amiri API",
    description="Трекери харҷҳо дар Telegram",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.PANEL_URL],
    allow_credentials=True,  # cookie-и сессия
    allow_methods=["*"],
    allow_headers=["*"],
)

for _router in (
    auth_routes.router,
    me_routes.router,
    categories_routes.router,
    limits_routes.router,
    expenses_routes.router,
    stats_routes.router,
    export_routes.router,
):
    app.include_router(_router)


@app.get("/health", tags=["service"])
async def health() -> dict[str, object]:
    from app.services import ai

    if not settings.ai_enabled:
        ai_state = "disabled"
    elif ai.available():
        ai_state = settings.OPENAI_MODEL
    else:
        # калид кор намекунад (кредит ё дастрасӣ) — бот бо луғат кор мекунад
        ai_state = "cooldown"

    return {
        "status": "ok",
        "bot": settings.BOT_MODE if settings.bot_enabled else "disabled",
        "ai": ai_state,
    }


@app.post("/webhook/{secret}", include_in_schema=False)
async def telegram_webhook(secret: str, request: Request) -> Response:
    if secret != settings.WEBHOOK_SECRET or dp is None or bot is None:
        return Response(status_code=404)

    from aiogram.types import Update

    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=200)
