"""Категорияҳо: система (танҳо хондан) + шахсии корбар (CRUD)."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.api.serializers import category_out
from app.schemas import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import categories
from app.services.ai import NewCategory

router = APIRouter(prefix="/api/categories", tags=["categories"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
)


@router.get("", response_model=list[CategoryOut])
async def list_categories(user: CurrentUser, session: SessionDep) -> list[CategoryOut]:
    rows = await categories.list_for_user(session, user.id)
    return [category_out(row, user.lang) for row in rows]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate, user: CurrentUser, session: SessionDep
) -> CategoryOut:
    key = _slugify(payload.name)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Не удалось построить ключ из названия",
        )

    # Аз панел як ном меояд — ҳамон ном ба ҳар се забон меравад
    category = await categories.create_custom(
        session,
        user.id,
        NewCategory(
            key=key,
            emoji=payload.emoji,
            name_tg=payload.name,
            name_ru=payload.name,
            name_en=payload.name,
        ),
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Категория уже есть или достигнут предел "
            f"({categories.MAX_CUSTOM_CATEGORIES})",
        )

    await session.commit()
    return category_out(category, user.lang)


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int, payload: CategoryUpdate, user: CurrentUser, session: SessionDep
) -> CategoryOut:
    category = await categories.get_for_user(session, user.id, category_id)
    if category is None:
        raise NOT_FOUND
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Системную категорию менять нельзя",
        )

    if payload.name is not None:
        category.name_tg = category.name_ru = category.name_en = payload.name
    if payload.emoji is not None:
        category.emoji = payload.emoji
    if payload.color is not None:
        category.color = payload.color

    await session.commit()
    return category_out(category, user.lang)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int, user: CurrentUser, session: SessionDep
) -> None:
    """Харҷҳои ин категория ба «Дигар» мегузаранд, гум намешаванд."""
    if not await categories.delete_custom(session, user.id, category_id):
        raise NOT_FOUND
    await session.commit()


def _slugify(name: str) -> str:
    """«Ҳайвонот» → «hayvonot»; агар лотинӣ насозад — аз hash."""
    table = str.maketrans(
        {
            "а": "a", "б": "b", "в": "v", "г": "g", "ғ": "g", "д": "d", "е": "e",
            "ё": "yo", "ж": "j", "з": "z", "и": "i", "ӣ": "i", "й": "y", "к": "k",
            "қ": "q", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
            "с": "s", "т": "t", "у": "u", "ӯ": "u", "ф": "f", "х": "h", "ҳ": "h",
            "ц": "ts", "ч": "ch", "ҷ": "j", "ш": "sh", "щ": "sh", "ъ": "", "ы": "y",
            "ь": "", "э": "e", "ю": "yu", "я": "ya",
        }
    )
    slug = "".join(
        c for c in name.lower().translate(table) if c.isascii() and c.isalnum()
    )
    if len(slug) < 3:
        slug = f"cat{abs(hash(name)) % 100000}"
    return slug[:16]
