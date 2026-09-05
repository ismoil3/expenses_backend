#!/bin/sh
set -e

echo "→ Интизори пойгоҳи маълумот…"
python - <<'PY'
import asyncio, sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

async def wait():
    for attempt in range(1, 31):
        try:
            engine = create_async_engine(settings.DATABASE_URL)
            async with engine.connect():
                pass
            await engine.dispose()
            print("  ✓ пойгоҳ омода")
            return
        except Exception as exc:
            print(f"  … {attempt}/30 ({exc.__class__.__name__})")
            await asyncio.sleep(1)
    sys.exit("✗ пойгоҳи маълумот дастрас нашуд")

asyncio.run(wait())
PY

echo "→ Миграцияҳо…"
alembic upgrade head

echo "→ Категорияҳои система…"
python -m app.db.seed

echo "→ Оғози сервер…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
