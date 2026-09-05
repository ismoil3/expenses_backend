"""Ҳар се забон бояд ҳамон калидҳо ва ҳамон ҷойгузорҳоро дошта бошанд.

Набудани як калид дар як забон = бот дар ҳамон забон паёми хароб медиҳад,
барои ҳамин ин тест ҳатмист.
"""

import re

import pytest

from app.bot.i18n import LANG_LABELS, TABLES, normalize_lang, t

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def test_all_languages_present():
    assert set(TABLES) == {"tg", "ru", "en"} == set(LANG_LABELS)


def test_same_keys_everywhere():
    reference = set(TABLES["ru"])
    for lang, table in TABLES.items():
        missing = reference - set(table)
        extra = set(table) - reference
        assert not missing, f"{lang}: калидҳои нокифоя {sorted(missing)}"
        assert not extra, f"{lang}: калидҳои зиёдатӣ {sorted(extra)}"


@pytest.mark.parametrize("lang", ["tg", "en"])
def test_same_placeholders(lang):
    for key, template in TABLES["ru"].items():
        expected = set(PLACEHOLDER_RE.findall(template))
        actual = set(PLACEHOLDER_RE.findall(TABLES[lang][key]))
        assert expected == actual, f"{lang}/{key}: {expected} != {actual}"


@pytest.mark.parametrize(
    "code, expected",
    [
        ("tg", "tg"),
        ("ru", "ru"),
        ("ru-RU", "ru"),
        ("uz", "ru"),
        ("en", "en"),
        ("en-US", "en"),
        ("fr", "en"),
        (None, "ru"),
        ("", "ru"),
    ],
)
def test_normalize_lang(code, expected):
    assert normalize_lang(code) == expected


def test_t_formats():
    assert "Кафе" in t("category.changed", "ru", cat="☕ Кафе")
    assert "Кафе" in t("category.changed", "tg", cat="☕ Кафе")
    assert "Кафе" in t("category.changed", "en", cat="☕ Кафе")


def test_t_unknown_lang_falls_back():
    assert t("label.total", "fr") == TABLES["ru"]["label.total"]


def test_t_unknown_key_returns_key():
    assert t("no.such.key", "ru") == "no.such.key"


def test_placeholder_named_lang_does_not_collide():
    """Регрессия: `{lang}` дар матн набояд ба параметри худи `t()` бархӯрад."""
    result = t("lang.changed", "en", lang="🇬🇧 English")
    assert "🇬🇧 English" in result
    assert "{lang}" not in result
