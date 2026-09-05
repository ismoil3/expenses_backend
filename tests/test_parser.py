"""Ҳар сатри ҷадвали нақша — як тест."""

from decimal import Decimal

import pytest

from app.services.parser import normalize_phrase, parse_message


def one(text: str):
    result = parse_message(text)
    assert len(result) == 1, f"интизор 1 харҷ, омад {len(result)}: {text!r}"
    return result[0]


@pytest.mark.parametrize(
    "text, amount, currency, description",
    [
        ("кофе 350", "350.00", None, "кофе"),
        ("350 кофе", "350.00", None, "кофе"),
        ("такси 900 работа", "900.00", None, "такси работа"),
        ("нон 12.5", "12.50", None, "нон"),
        ("нон 12,5", "12.50", None, "нон"),
        ("1к такси", "1000.00", None, "такси"),
        ("1k такси", "1000.00", None, "такси"),
        ("1.5к такси", "1500.00", None, "такси"),
        ("5$ обуна", "5.00", "USD", "обуна"),
        ("$5 обуна", "5.00", "USD", "обуна"),
        ("500р курс", "500.00", "RUB", "курс"),
        ("500 руб курс", "500.00", "RUB", "курс"),
        ("500руб курс", "500.00", "RUB", "курс"),
        ("350с нон", "350.00", "TJS", "нон"),
        ("350 сомонӣ нон", "350.00", "TJS", "нон"),
        ("200", "200.00", None, ""),
    ],
)
def test_single(text, amount, currency, description):
    parsed = one(text)
    assert parsed.amount == Decimal(amount)
    assert parsed.currency == currency
    assert parsed.description == description


def test_explicit_tag():
    parsed = one("кофе 350 #cafe")
    assert parsed.amount == Decimal("350.00")
    assert parsed.explicit_category == "cafe"
    assert parsed.description == "кофе"


@pytest.mark.parametrize(
    "text",
    [
        "кофе 350, такси 900, нон 20",
        "кофе 350; такси 900; нон 20",
        "кофе 350\nтакси 900\nнон 20",
    ],
)
def test_multi_expense(text):
    """D2 — якчанд харҷ дар як паём."""
    result = parse_message(text)
    assert [str(p.amount) for p in result] == ["350.00", "900.00", "20.00"]
    assert [p.description for p in result] == ["кофе", "такси", "нон"]


def test_multi_expense_keeps_decimal_comma():
    """Вергули дохили рақам харҷро намебурад."""
    result = parse_message("нон 12,5, кофе 350")
    assert [str(p.amount) for p in result] == ["12.50", "350.00"]


def test_multi_expense_skips_chunks_without_amount():
    result = parse_message("кофе 350, ва боз чизе, такси 900")
    assert [str(p.amount) for p in result] == ["350.00", "900.00"]


@pytest.mark.parametrize("text", ["кофе", "", "   ", "салом чӣ хел?", "#cafe"])
def test_no_amount(text):
    assert parse_message(text) == []


def test_limit_per_message():
    text = ", ".join(f"чиз{i} {i + 1}" for i in range(25))
    assert len(parse_message(text)) == 10


def test_negative_and_zero_ignored():
    assert parse_message("кофе 0") == []


@pytest.mark.parametrize(
    "description, expected",
    [
        ("кофе", "кофе"),
        ("Кофе 2 шт!", "кофе шт"),
        ("такси работа", "такси работа"),
        ("ТАКСИ  Работа", "такси работа"),
    ],
)
def test_normalize_phrase(description, expected):
    assert normalize_phrase(description) == expected
