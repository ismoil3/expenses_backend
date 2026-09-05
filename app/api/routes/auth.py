"""Вуруд ба панел: линки яккарата ё Telegram Mini App."""

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, SessionDep
from app.config import settings
from app.db.models import User
from app.schemas import AuthTokenIn, InitDataIn, LoginOut, MeOut
from app.services import auth, users

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue(response: Response, user: User) -> LoginOut:
    """Сессияро мекушояд: cookie мегузорад ва ҳамон токенро бармегардонад."""
    token = auth.issue_session(user)
    secure = settings.PANEL_URL.startswith("https://")

    response.set_cookie(
        key=auth.SESSION_COOKIE,
        value=token,
        max_age=settings.JWT_TTL_DAYS * 24 * 3600,
        httponly=True,  # JavaScript ба он намерасад
        samesite="lax",
        secure=secure,
        path="/",
    )

    return LoginOut(
        **MeOut.model_validate(user, from_attributes=True).model_dump(),
        session_token=token,
        expires_in_days=settings.JWT_TTL_DAYS,
    )


@router.post("/telegram-token", response_model=LoginOut)
async def login_with_token(
    payload: AuthTokenIn, response: Response, session: SessionDep
) -> LoginOut:
    """Линки яккарата аз команди `/panel`."""
    user = await auth.consume_magic_token(session, payload.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ссылка недействительна или уже использована",
        )

    await auth.purge_expired_tokens(session)
    await session.commit()
    return _issue(response, user)


@router.post("/miniapp", response_model=LoginOut)
async def login_with_miniapp(
    payload: InitDataIn, response: Response, session: SessionDep
) -> LoginOut:
    """Кушодани панел аз дохили Telegram."""
    data = auth.verify_init_data(payload.init_data)
    if not data or not data.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Подпись не совпала"
        )

    user = await users.get_or_create(
        session,
        int(data["id"]),
        username=data.get("username"),
        first_name=data.get("first_name"),
        language_code=data.get("language_code"),
    )
    await session.commit()
    return _issue(response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(auth.SESSION_COOKIE, path="/")


@router.get("/me", response_model=MeOut)
async def whoami(user: CurrentUser) -> MeOut:
    return MeOut.model_validate(user, from_attributes=True)
