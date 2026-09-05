"""Схемаҳои дархост ва ҷавоби API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.config import CURRENCIES, LANGS


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    emoji: str
    color: str
    name: str
    is_system: bool


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    currency: str
    amount_base: Decimal
    description: str
    occurred_at: datetime
    source: str
    category: CategoryOut


class SuggestionOut(BaseModel):
    """AI категорияи нав пешниҳод мекунад — корбар тасдиқ мекунад."""

    key: str
    emoji: str
    name: str
    phrase: str


class ExpenseCreated(ExpenseOut):
    """Ҳангоми илова: агар ҳеҷ категория мувофиқ наомада бошад,
    ин ҷо пешниҳоди AI меистад."""

    suggestion: SuggestionOut | None = None


class SuggestionDecision(BaseModel):
    accept: bool


class ExpenseCreate(BaseModel):
    """Ду роҳ: ё матни хом (ҳамон parser-и бот), ё майдонҳои алоҳида."""

    text: str | None = Field(default=None, max_length=500)
    amount: Decimal | None = Field(default=None, gt=0, le=Decimal("100000000"))
    currency: str | None = None
    category_id: int | None = None
    description: str = Field(default="", max_length=300)
    occurred_at: datetime | None = None


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, le=Decimal("100000000"))
    currency: str | None = None
    category_id: int | None = None
    description: str | None = Field(default=None, max_length=300)
    occurred_at: datetime | None = None


class ExpenseList(BaseModel):
    items: list[ExpenseOut]
    total: int  # шумораи ҳамаи сатрҳои филтр, на танҳо саҳифаи ҷорӣ
    sum: Decimal  # ҷамъи ҳамон филтр дар валютаи асосӣ
    currency: str


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    emoji: str = Field(default="🏷", max_length=4)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=32)
    emoji: str | None = Field(default=None, max_length=4)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class LimitOut(BaseModel):
    category: CategoryOut
    amount: Decimal
    spent: Decimal
    share: float
    currency: str


class LimitIn(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0, le=Decimal("100000000"))


class MeOut(BaseModel):
    id: int
    tg_id: int
    first_name: str | None
    username: str | None
    lang: str
    base_currency: str
    tz: str


class LoginOut(MeOut):
    """Ҳамон профил + худи токен.

    Сессия асосан дар cookie-и httpOnly меистад. Вале баъзе браузерҳо
    (танзимоти қатъӣ, васеъкуниҳо) cookie-и localhost-ро намегузоранд —
    он гоҳ панел ҳамин токенро истифода мебарад, то корбар бе панел намонад.
    """

    session_token: str
    expires_in_days: int


class MeUpdate(BaseModel):
    lang: str | None = None
    base_currency: str | None = None

    def validated(self) -> "MeUpdate":
        if self.lang is not None and self.lang not in LANGS:
            self.lang = None
        if self.base_currency is not None and self.base_currency not in CURRENCIES:
            self.base_currency = None
        return self


class SummaryOut(BaseModel):
    period: str
    total: Decimal
    previous_total: Decimal
    change_percent: float | None
    currency: str
    count: int


class CategorySlice(BaseModel):
    category: CategoryOut
    total: Decimal
    share: float


class DayPoint(BaseModel):
    day: str
    total: Decimal


class AuthTokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=128)


class InitDataIn(BaseModel):
    init_data: str = Field(min_length=8, max_length=4096)
