"""Талаботи ҳатмии ҳакатон: маълумоти корбарон намеомезад.

Корбари B набояд харҷи корбари A-ро бинад, хонад, тағйир диҳад ё нест кунад.
Ҷавоб ҳамеша **404** аст, на 403 — вагарна аз рӯи фарқи ҷавобҳо фаҳмидан
мумкин мешуд, ки чунин сатр умуман вуҷуд дорад.
"""

import pytest


async def _create_many(client, text: str) -> list[dict]:
    response = await client.post("/api/expenses", json={"text": text})
    assert response.status_code == 201, response.text
    return response.json()


async def _create(client, text: str = "кофе 350") -> dict:
    created = await _create_many(client, text)
    assert len(created) == 1
    return created[0]


async def test_expense_is_created_for_its_owner(client_a):
    expense = await _create(client_a)
    assert expense["amount"] == "350.00"
    assert expense["category"]["key"] == "cafe"

    listing = await client_a.get("/api/expenses")
    assert [item["id"] for item in listing.json()["items"]] == [expense["id"]]


async def test_other_user_does_not_see_it(client_a, client_b):
    expense = await _create(client_a)

    listing = await client_b.get("/api/expenses")
    assert listing.json()["total"] == 0
    assert expense["id"] not in [item["id"] for item in listing.json()["items"]]


@pytest.mark.parametrize("method", ["patch", "delete"])
async def test_other_user_cannot_modify(client_a, client_b, method):
    expense = await _create(client_a)
    url = f"/api/expenses/{expense['id']}"

    call = getattr(client_b, method)
    response = await call(url, json={"description": "hack"}) if method == "patch" else await call(url)
    assert response.status_code == 404

    # Харҷ ҳамон тавре мемонад, ки буд
    still = await client_a.get("/api/expenses")
    assert still.json()["total"] == 1


async def test_one_message_creates_several_expenses(client_a):
    """D2 — ҳамон қоидаи бот бояд дар панел ҳам кор кунад."""
    created = await _create_many(client_a, "кофе 350, такси 900, хлеб 20")

    assert [item["amount"] for item in created] == ["350.00", "900.00", "20.00"]
    assert [item["category"]["key"] for item in created] == [
        "cafe",
        "transport",
        "food",
    ]

    listing = await client_a.get("/api/expenses")
    assert listing.json()["total"] == 3


async def test_other_user_cannot_use_foreign_category(client_a, client_b):
    created = await client_a.post(
        "/api/categories", json={"name": "Ҳайвонот", "emoji": "🦒"}
    )
    assert created.status_code == 201
    category_id = created.json()["id"]

    # B категорияи A-ро дар рӯйхати худ намебинад
    listing = await client_b.get("/api/categories")
    assert category_id not in [item["id"] for item in listing.json()]

    # ва онро ба харҷи худ часпонда наметавонад
    response = await client_b.post(
        "/api/expenses", json={"amount": "100", "category_id": category_id}
    )
    assert response.status_code == 404

    # ва онро таҳрир ё нест карда наметавонад
    assert (await client_b.patch(f"/api/categories/{category_id}", json={"name": "x"})).status_code == 404
    assert (await client_b.delete(f"/api/categories/{category_id}")).status_code == 404


async def test_stats_are_per_user(client_a, client_b):
    await _create(client_a, "кофе 350")
    await _create(client_a, "такси 900")

    summary_a = (await client_a.get("/api/stats/summary?period=month")).json()
    summary_b = (await client_b.get("/api/stats/summary?period=month")).json()

    assert summary_a["count"] == 2
    assert summary_b["count"] == 0
    assert summary_b["total"] == "0"


async def test_export_contains_only_own_rows(client_a, client_b):
    await _create(client_a, "кофе 350")

    csv_a = (await client_a.get("/api/export.csv")).text
    csv_b = (await client_b.get("/api/export.csv")).text

    assert "кофе" in csv_a
    assert "кофе" not in csv_b


async def test_anonymous_is_rejected(anon_client):
    for url in ("/api/me", "/api/expenses", "/api/stats/summary", "/api/export.csv"):
        assert (await anon_client.get(url)).status_code == 401


async def test_broken_session_cookie_is_rejected(anon_client):
    anon_client.cookies.set("amiri_session", "not-a-real-jwt")
    assert (await anon_client.get("/api/me")).status_code == 401
