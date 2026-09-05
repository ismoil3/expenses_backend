"""Содироти CSV аз панел."""

from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import CurrentUser, SessionDep
from app.services.csv_export import build_csv

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export.csv")
async def export_csv(
    user: CurrentUser,
    session: SessionDep,
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
) -> Response:
    content, _ = await build_csv(session, user, date_from, date_to)
    stamp = datetime.now().strftime("%Y-%m-%d")
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="amiri-{stamp}.csv"'},
    )
