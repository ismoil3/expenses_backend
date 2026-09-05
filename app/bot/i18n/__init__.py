"""Тарҷумаҳои бот: tg · ru · en.

Истифода:
    t("expense.saved", lang, amount="350.00", sign="c.", cat="☕ Кафе")

Агар калид дар забони дархостшуда набошад, ба забони пешфарз (ru)
мегузарад — паём ҳеҷ гоҳ холӣ намемонад.
"""

from app.bot.i18n import en, ru, tg

TABLES: dict[str, dict[str, str]] = {
    "tg": tg.TEXTS,
    "ru": ru.TEXTS,
    "en": en.TEXTS,
}

FALLBACK_LANG = "ru"

# Ном ва парчами забонҳо барои /lang
LANG_LABELS: dict[str, str] = {
    "tg": "🇹🇯 Тоҷикӣ",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}


def normalize_lang(code: str | None) -> str:
    """`language_code`-и Telegram-ро ба забони мо табдил медиҳад."""
    if not code:
        return FALLBACK_LANG
    code = code.lower().split("-")[0]
    if code == "tg":
        return "tg"
    if code in {"ru", "uz", "ky", "kk", "be", "uk", "tk"}:
        return "ru"
    return "en"


def t(key: str, lang: str = FALLBACK_LANG, /, **kwargs: object) -> str:
    """`/` муҳим аст: он `key` ва `lang`-ро танҳо мавқеӣ мекунад, то
    ҷойгузори матн бо номи `{lang}` бо параметри худи функсия бархӯрд накунад.
    """
    table = TABLES.get(lang) or TABLES[FALLBACK_LANG]
    template = table.get(key) or TABLES[FALLBACK_LANG].get(key)
    if template is None:
        # Дар тестҳо ин хато мешавад; дар прод паём мешиканад, вале бот не.
        return key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
