"""Профили корбар: забон ва валютаи асосӣ."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas import MeOut, MeUpdate
from app.services import expenses

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=MeOut)
async def read_me(user: CurrentUser) -> MeOut:
    return MeOut.model_validate(user, from_attributes=True)


@router.patch("", response_model=MeOut)
async def update_me(
    payload: MeUpdate, user: CurrentUser, session: SessionDep
) -> MeOut:
    """Ҳангоми ивази валютаи асосӣ ҳама харҷҳо ва лимитҳо ба он
    гузаронида мешаванд — вагарна ҳисоботҳо ду валютаро якҷоя ҷамъ мекарданд."""
    clean = payload.validated()
    if clean.lang:
        user.lang = clean.lang
    if clean.base_currency:
        await expenses.rebase(session, user, clean.base_currency)

    await session.commit()
    return MeOut.model_validate(user, from_attributes=True)
