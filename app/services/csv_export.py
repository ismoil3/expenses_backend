"""Содирот ба CSV.

Ду тафсили амалӣ, ки файлро дар Excel хонданӣ мекунанд:

  * **UTF-8 BOM** — бе он Excel ҳарфҳои кириллиро вайрон мекунад.
  * **Ҷудокунанда `;`** — Excel дар маҳалли русӣ маҳз онро интизор аст;
    бо вергул тамоми сатр ба як хона меафтад. Google Sheets ва pandas
    ҳарду вариантро худашон мефаҳманд.
"""

import csv
import io
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Expense, User
from app.services.period import user_tz

BOM = "﻿"
DELIMITER = ";"

HEADERS: dict[str, list[str]] = {
    "tg": [
        "Сана",
        "Вақт",
        "Сумма",
        "Валюта",
        "Дар валютаи асосӣ",
        "Валютаи асосӣ",
        "Категория",
        "Тавсиф",
        "Манбаъ",
    ],
    "ru": [
        "Дата",
        "Время",
        "Сумма",
        "Валюта",
        "В основной валюте",
        "Основная валюта",
        "Категория",
        "Описание",
        "Источник",
    ],
    "en": [
        "Date",
        "Time",
        "Amount",
        "Currency",
        "In base currency",
        "Base currency",
        "Category",
        "Description",
        "Source",
    ],
}

# `text` / `photo` / `panel` барои одам чизе намегӯянд
SOURCES: dict[str, dict[str, str]] = {
    "tg": {"text": "бот", "photo": "акси чек", "panel": "панел"},
    "ru": {"text": "бот", "photo": "фото чека", "panel": "панель"},
    "en": {"text": "bot", "photo": "receipt", "panel": "dashboard"},
}


def _headers(lang: str) -> list[str]:
    return HEADERS.get(lang) or HEADERS["ru"]


def _source(lang: str, value: str) -> str:
    table = SOURCES.get(lang) or SOURCES["ru"]
    return table.get(value, value)


async def build_csv(
    session: AsyncSession,
    user: User,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[str, int]:
    """`(матни CSV, шумораи сатрҳо)`."""
    filters = [Expense.user_id == user.id, Expense.deleted_at.is_(None)]
    if start:
        filters.append(Expense.occurred_at >= start)
    if end:
        filters.append(Expense.occurred_at < end)

    rows = await session.scalars(
        select(Expense).where(*filters).order_by(desc(Expense.occurred_at))
    )

    tz = user_tz(user.tz)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=DELIMITER, lineterminator="\r\n")
    writer.writerow(_headers(user.lang))

    count = 0
    for expense in rows:
        local = expense.occurred_at.astimezone(tz)
        writer.writerow(
            [
                local.strftime("%d.%m.%Y"),
                local.strftime("%H:%M"),
                f"{expense.amount:.2f}".replace(".", ","),
                expense.currency,
                f"{expense.amount_base:.2f}".replace(".", ","),
                user.base_currency,
                expense.category.name(user.lang),
                expense.description,
                _source(user.lang, expense.source),
            ]
        )
        count += 1

    return BOM + buffer.getvalue(), count
