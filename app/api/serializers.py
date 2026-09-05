"""Табдили моделҳо ба ҷавоби API (бо забони корбар)."""

from app.db.models import Category, Expense
from app.schemas import CategoryOut, ExpenseOut


def category_out(category: Category, lang: str) -> CategoryOut:
    return CategoryOut(
        id=category.id,
        key=category.key,
        emoji=category.emoji,
        color=category.color,
        name=category.name(lang),
        is_system=category.is_system,
    )


def expense_out(expense: Expense, lang: str) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        amount=expense.amount,
        currency=expense.currency,
        amount_base=expense.amount_base,
        description=expense.description,
        occurred_at=expense.occurred_at,
        source=expense.source,
        category=category_out(expense.category, lang),
    )
