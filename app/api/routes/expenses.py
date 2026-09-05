"""Харҷҳо: рӯйхат, илова, таҳрир, нест кардан.

Ҳар query бо `user.id` филтр мешавад. Дархости харҷи бегона `404` медиҳад
(на `403`), то мавҷудияти сатри бегона фош нашавад.
"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.serializers import expense_out
from app.config import CURRENCIES
from app.db.models import Expense
from app.schemas import (
    ExpenseCreate,
    ExpenseCreated,
    ExpenseList,
    ExpenseOut,
    ExpenseUpdate,
    SuggestionDecision,
    SuggestionOut,
)
from app.services import (
    categories,
    categorizer,
    expenses as expense_service,
    fx,
    intake,
    pending,
)
from app.services.parser import ParsedExpense

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Расход не найден")


@router.get("", response_model=ExpenseList)
async def list_expenses(
    user: CurrentUser,
    session: SessionDep,
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
    category_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ExpenseList:
    filters = [Expense.user_id == user.id, Expense.deleted_at.is_(None)]
    if date_from:
        filters.append(Expense.occurred_at >= date_from)
    if date_to:
        filters.append(Expense.occurred_at < date_to)
    if category_id:
        filters.append(Expense.category_id == category_id)

    totals = (
        await session.execute(
            select(
                func.count(Expense.id),
                func.coalesce(func.sum(Expense.amount_base), 0),
            ).where(*filters)
        )
    ).one()

    rows = await session.scalars(
        select(Expense)
        .where(*filters)
        .order_by(desc(Expense.occurred_at), desc(Expense.id))
        .limit(limit)
        .offset(offset)
    )

    return ExpenseList(
        items=[expense_out(row, user.lang) for row in rows],
        total=int(totals[0] or 0),
        sum=Decimal(totals[1] or 0),
        currency=user.base_currency,
    )


@router.post(
    "", response_model=list[ExpenseCreated], status_code=status.HTTP_201_CREATED
)
async def create_expense(
    payload: ExpenseCreate, user: CurrentUser, session: SessionDep
) -> list[ExpenseCreated]:
    """Ду роҳ: матни хом («кофе 350») ё майдонҳои алоҳида.

    Матн метавонад якчанд харҷ дошта бошад — «кофе 350, такси 900, нон 20».
    Ҳамон қоидаи бот: як паём → чанд харҷ. Барои ҳамин ҷавоб ҳамеша рӯйхат аст.
    """
    if payload.text:
        parsed_list = await intake.from_text(payload.text)
        if not parsed_list:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не нашёл сумму. Пример: кофе 350",
            )
        plan = [
            (parsed, await categorizer.resolve(session, user, parsed))
            for parsed in parsed_list
        ]
    else:
        if payload.amount is None or payload.category_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Нужны amount и category_id либо text",
            )
        category = await categories.get_for_user(session, user.id, payload.category_id)
        if category is None:
            raise NOT_FOUND

        parsed = ParsedExpense(
            amount=payload.amount,
            currency=_check_currency(payload.currency),
            description=payload.description,
            explicit_category=None,
            raw=payload.description,
        )
        plan = [(parsed, categorizer.CategoryDecision(category, "explicit", ""))]

    created = []
    for parsed, decision in plan:
        expense = await expense_service.create(
            session,
            user,
            parsed,
            decision,
            source="panel",
            occurred_at=payload.occurred_at,
        )
        created.append((expense, decision))

    await session.commit()

    result: list[ExpenseCreated] = []
    for expense, decision in created:
        await session.refresh(expense)
        item = ExpenseCreated(
            **expense_out(expense, user.lang).model_dump(), suggestion=None
        )

        # AI категорияи нав пешниҳод кард — панел аз корбар мепурсад
        if decision.suggestion is not None:
            pending.put(expense.id, decision.suggestion, decision.phrase)
            item.suggestion = SuggestionOut(
                key=decision.suggestion.key,
                emoji=decision.suggestion.emoji,
                name=_localized(decision.suggestion, user.lang),
                phrase=decision.phrase,
            )

        result.append(item)

    return result


@router.post("/{expense_id}/suggestion", response_model=ExpenseOut)
async def resolve_suggestion(
    expense_id: int,
    payload: SuggestionDecision,
    user: CurrentUser,
    session: SessionDep,
) -> ExpenseOut:
    """Ҷавоби корбар ба пешниҳоди AI — ҳамон мантиқи тугмаҳои бот."""
    item = pending.pop(expense_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Предложение устарело — добавьте расход заново",
        )

    suggestion, phrase = item
    expense = await expense_service.get_alive(session, user.id, expense_id)
    if expense is None:
        raise NOT_FOUND

    if not payload.accept:
        # Дигар барои ҳамин калима намепурсем
        other = await categories.fallback(session)
        await categories.remember(session, user.id, phrase, other.id, declined=True)
        await session.commit()
        await session.refresh(expense)
        return expense_out(expense, user.lang)

    category = await categories.create_custom(session, user.id, suggestion)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Достигнут предел в {categories.MAX_CUSTOM_CATEGORIES} категорий",
        )

    expense = await expense_service.set_category(session, user.id, expense_id, category)
    if expense is not None:
        expense.cat_source = "new"
    await categories.remember(session, user.id, phrase, category.id)

    await session.commit()
    await session.refresh(expense)
    return expense_out(expense, user.lang)


def _localized(suggestion, lang: str) -> str:
    return (
        {
            "tg": suggestion.name_tg,
            "ru": suggestion.name_ru,
            "en": suggestion.name_en,
        }.get(lang)
        or suggestion.name_ru
        or suggestion.name_en
    )


@router.patch("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: int, payload: ExpenseUpdate, user: CurrentUser, session: SessionDep
) -> ExpenseOut:
    expense = await expense_service.get_alive(session, user.id, expense_id)
    if expense is None:
        raise NOT_FOUND

    if payload.category_id is not None:
        category = await categories.get_for_user(session, user.id, payload.category_id)
        if category is None:
            raise NOT_FOUND
        expense.category_id = category.id
        expense.cat_source = "explicit"

    if payload.description is not None:
        expense.description = payload.description
    if payload.occurred_at is not None:
        expense.occurred_at = payload.occurred_at

    # Сумма ё валюта иваз шуд — курсро аз нав ҳисоб мекунем
    if payload.amount is not None or payload.currency is not None:
        expense.amount = payload.amount or expense.amount
        expense.currency = _check_currency(payload.currency) or expense.currency
        expense.amount_base, expense.fx_rate = await fx.convert(
            session, expense.amount, expense.currency, user.base_currency
        )

    await session.commit()
    await session.refresh(expense)
    return expense_out(expense, user.lang)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int, user: CurrentUser, session: SessionDep
) -> None:
    if not await expense_service.soft_delete(session, user.id, expense_id):
        raise NOT_FOUND
    await session.commit()


def _check_currency(code: str | None) -> str | None:
    if code is None:
        return None
    code = code.upper()
    if code not in CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Валюта должна быть одной из: {', '.join(CURRENCIES)}",
        )
    return code
