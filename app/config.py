"""Танзимоти лоиҳа — ҳама аз муҳити иҷро (.env) хонда мешаванд."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/config.py → app → backend
BACKEND_DIR = Path(__file__).resolve().parents[1]

# Забонҳо ва валютаҳои дастгиришаванда
LANGS: tuple[str, ...] = ("tg", "ru", "en")
CURRENCIES: tuple[str, ...] = ("TJS", "USD", "RUB")

# Аломати валюта барои намоиш
CURRENCY_SIGN: dict[str, str] = {"TJS": "c.", "USD": "$", "RUB": "₽"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Роҳи мутлақ — фарқ надорад, ки серверро аз кадом папка мебароранд.
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram ---
    BOT_TOKEN: str = ""
    BOT_MODE: str = "polling"  # polling | webhook
    PUBLIC_URL: str = "http://localhost:8000"
    WEBHOOK_SECRET: str = "change-me"

    # --- OpenAI ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # --- Пойгоҳи маълумот ---
    DATABASE_URL: str = "postgresql+asyncpg://amiri:amiri@db:5432/amiri"

    # --- Амният ---
    JWT_SECRET: str = "change-me"
    JWT_TTL_DAYS: int = 7
    MAGIC_TOKEN_TTL_MINUTES: int = 5

    # --- Панел ---
    PANEL_URL: str = "http://localhost:5173"

    # --- Пешфарзҳо ---
    DEFAULT_LANG: str = "ru"
    DEFAULT_CURRENCY: str = "TJS"
    DEFAULT_TZ: str = "Asia/Dushanbe"

    # --- Курси валюта ---
    FX_API_URL: str = "https://open.er-api.com/v6/latest"

    @property
    def bot_enabled(self) -> bool:
        """Бе токен ботро намебарорем — API бояд бе он ҳам кор кунад."""
        return bool(self.BOT_TOKEN) and not self.BOT_TOKEN.startswith("123456789:")

    @property
    def ai_enabled(self) -> bool:
        key = self.OPENAI_API_KEY
        # калиди намунавӣ аз .env.example ба ҳисоб намеравад
        return bool(key) and key.startswith("sk-") and "xxxx" not in key.lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
