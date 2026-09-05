"""Муайянкунии категория — панҷ қадам, аз арзон ба гарон.

    1. #tag ё номи возеҳи категория      — фаврӣ
    2. хотираи ҳамин корбар              — фаврӣ
    3. луғати сезабона                   — фаврӣ
    4. OpenAI                            — ~1 сония
    5. AI категорияи НАВ пешниҳод мекунад → бот аз корбар мепурсад

Ҳар қадам метавонад ноком шавад — дар охир ҳамеша «Дигар» мемонад, яъне
харҷ ҳеҷ гоҳ гум намешавад.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, User
from app.services import ai, categories
from app.services.keywords import match_category_key
from app.services.parser import ParsedExpense, normalize_phrase


@dataclass(slots=True)
class CategoryDecision:
    category: Category
    source: str  # explicit | memory | rule | ai | default
    phrase: str  # калиди хотира (метавонад холӣ бошад)
    suggestion: ai.NewCategory | None = None  # пешниҳоди категорияи нав


async def resolve(
    session: AsyncSession, user: User, parsed: ParsedExpense
) -> CategoryDecision:
    available = await categories.list_for_user(session, user.id)
    other = categories.find_by_key(available, "other") or await categories.fallback(
        session
    )
    phrase = normalize_phrase(parsed.description)

    # 1 — категорияи возеҳ: «#cafe» ё калимаи «кафе»
    if parsed.explicit_category:
        match = categories.find_by_key(
            available, parsed.explicit_category
        ) or categories.find_by_name(available, parsed.explicit_category)
        if match:
            return CategoryDecision(match, "explicit", phrase)

    if parsed.description:
        match = categories.find_by_name(available, parsed.description)
        if match:
            return CategoryDecision(match, "explicit", phrase)

    # 2 — хотираи ҳамин корбар
    memory = await categories.recall(session, user.id, phrase)
    if memory is not None:
        if memory.declined:
            # Корбар аллакай гуфт: «категорияи нав лозим нест»
            return CategoryDecision(other, "default", phrase)
        match = next((c for c in available if c.id == memory.category_id), None)
        if match:
            return CategoryDecision(match, "memory", phrase)

    # 3 — луғати сезабона
    key = match_category_key(parsed.description)
    if key:
        match = categories.find_by_key(available, key)
        if match:
            return CategoryDecision(match, "rule", phrase)

    # 4 ва 5 — AI.
    # «other» ба AI дода намешавад: вагарна модел ҳамеша ба он мегурезад
    # ва ҳеҷ гоҳ категорияи нав пешниҳод намекунад.
    allowed = [c.key for c in available if c.key != "other"]
    result = await ai.classify(parsed.description, allowed)
    if result is not None:
        if result.category_key and result.confidence >= ai.MIN_CONFIDENCE:
            match = categories.find_by_key(available, result.category_key)
            if match:
                return CategoryDecision(match, "ai", phrase)

        if result.new_category and phrase:
            # Харҷ дар «Дигар» сабт мешавад ва бот пешниҳод мекунад
            return CategoryDecision(other, "default", phrase, result.new_category)

    return CategoryDecision(other, "default", phrase)
