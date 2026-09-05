"""Лимитҳои моҳона аз рӯи категория."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.api.serializers import category_out
from app.schemas import LimitIn, LimitOut
from app.services import categories, limits as limits_service

router = APIRouter(prefix="/api/limits", tags=["limits"])


def _out(view, currency: str, lang: str) -> LimitOut:
    return LimitOut(
        category=category_out(view.category, lang),
        amount=view.amount,
        spent=view.spent,
        share=round(view.share, 4),
        currency=currency,
    )


@router.get("", response_model=list[LimitOut])
async def list_limits(user: CurrentUser, session: SessionDep) -> list[LimitOut]:
    views = await limits_service.list_for_user(session, user)
    return [_out(view, user.base_currency, user.lang) for view in views]


@router.put("", response_model=list[LimitOut])
async def set_limit(
    payload: LimitIn, user: CurrentUser, session: SessionDep
) -> list[LimitOut]:
    category = await categories.get_for_user(session, user.id, payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )

    ok = await limits_service.set_limit(
        session, user, payload.category_id, payload.amount
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Больше {limits_service.MAX_LIMITS} лимитов нельзя",
        )

    await session.commit()
    views = await limits_service.list_for_user(session, user)
    return [_out(view, user.base_currency, user.lang) for view in views]


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_limit(
    category_id: int, user: CurrentUser, session: SessionDep
) -> None:
    if not await limits_service.remove(session, user.id, category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Лимит не найден"
        )
    await session.commit()
