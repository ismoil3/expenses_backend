"""Моделҳои пойгоҳи маълумот.

Қоидаи асосӣ: ҳар сатри маълумоти корбар `user_id` дорад ва ҳар query
онро ҳатман филтр мекунад — маълумоти корбарон омехта намешавад.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))

    lang: Mapped[str] = mapped_column(String(2), default="ru")
    base_currency: Mapped[str] = mapped_column(String(3), default="TJS")
    tz: Mapped[str] = mapped_column(String(64), default="Asia/Dushanbe")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # `passive_deletes` — нест кардани корбарро ба ON DELETE CASCADE-и база
    # мегузорад, вагарна SQLAlchemy user_id-ро NULL мекунад ва хато медиҳад.
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class Category(Base):
    """`user_id IS NULL` → категорияи система (барои ҳама).

    `user_id = X` → категорияи шахсии корбари X (аз ҷониби AI пешниҳод ва
    аз ҷониби корбар тасдиқ шудааст).
    """

    __tablename__ = "categories"
    __table_args__ = (
        # Як корбар ду категорияи ҳамном сохта наметавонад.
        UniqueConstraint("user_id", "key", name="uq_category_user_key"),
        Index("ix_categories_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    key: Mapped[str] = mapped_column(String(48))
    emoji: Mapped[str] = mapped_column(String(8), default="📦")
    color: Mapped[str] = mapped_column(String(7), default="#7B8A8B")
    sort: Mapped[int] = mapped_column(Integer, default=100)

    name_tg: Mapped[str] = mapped_column(String(64))
    name_ru: Mapped[str] = mapped_column(String(64))
    name_en: Mapped[str] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @property
    def is_system(self) -> bool:
        return self.user_id is None

    def name(self, lang: str) -> str:
        return {"tg": self.name_tg, "ru": self.name_ru, "en": self.name_en}.get(
            lang, self.name_ru
        )

    def label(self, lang: str) -> str:
        return f"{self.emoji} {self.name(lang)}"


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        # Ҳисоботҳо ҳамеша «корбар + давра» мепурсанд.
        Index("ix_expenses_user_occurred", "user_id", "occurred_at"),
        Index("ix_expenses_user_deleted", "user_id", "deleted_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="RESTRICT")
    )

    # Сумма ва валютаи аслӣ — ҳамон тавре ки корбар навишт.
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))

    # Сумма дар валютаи асосии корбар + курс дар ЛАҲЗАИ САБТ.
    # Курс баъдтар тағйир ёбад ҳам, ҳисоботи гузашта дигар намешавад.
    amount_base: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("1"))

    description: Mapped[str] = mapped_column(Text, default="")
    raw_text: Mapped[str | None] = mapped_column(Text)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # аз куҷо омад: text | photo | panel
    source: Mapped[str] = mapped_column(String(10), default="text")
    # категория чӣ тавр муайян шуд: explicit | memory | rule | ai | new | default
    cat_source: Mapped[str] = mapped_column(String(10), default="default")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # soft delete — то тугмаи «↩️ Бозгардонӣ» кор кунад
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="expenses")
    category: Mapped["Category"] = relationship(lazy="joined")


class CategoryMemory(Base):
    """Хотираи шахсӣ: «такси» → 🚕 Нақлиёт барои ҳамин корбар.

    Ҳангоми ислоҳи категория аз ҷониби корбар пур мешавад. Дафъаи оянда
    ҳамон калима бе дархост ба AI ҳал мешавад.
    """

    __tablename__ = "category_memory"
    __table_args__ = (
        UniqueConstraint("user_id", "phrase_norm", name="uq_memory_user_phrase"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="CASCADE")
    )

    phrase_norm: Mapped[str] = mapped_column(String(120))
    hits: Mapped[int] = mapped_column(Integer, default=1)
    # `True` → корбар гуфт «категорияи нав лозим нест», дигар напурсем
    declined: Mapped[bool] = mapped_column(Boolean, default=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CategoryLimit(Base):
    """Лимити моҳона барои як категория.

    Дар валютаи асосии корбар нигоҳ дошта мешавад — ҳамон тавре ки
    ҳисоботҳо ҳисоб мешаванд.
    """

    __tablename__ = "category_limits"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="uq_limit_user_category"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="CASCADE")
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(lazy="joined")


class FxRate(Base):
    """Курси рӯзона. `pair` = "USD_TJS" яъне 1 USD = rate TJS."""

    __tablename__ = "fx_rates"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    pair: Mapped[str] = mapped_column(String(8), primary_key=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuthToken(Base):
    """Токени яккаратаи вуруд ба панел (аз команди /panel)."""

    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Худи токен нигоҳ дошта намешавад — танҳо sha256-и он.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
