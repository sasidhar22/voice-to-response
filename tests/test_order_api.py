from decimal import Decimal
from unittest.mock import patch
import pytest
from httpx import AsyncClient

from app.models.schemas import ExtractedItem
from app.services.product_service import create_product
from app.models.schemas import ProductCreate

pytestmark = pytest.mark.asyncio

_TOMATOES = {"name": "Tomatoes",   "unit": "kg",    "price_per_unit": "1.50", "aliases": ["tomato"]}
_EGGS     = {"name": "Eggs",       "unit": "piece", "price_per_unit": "0.30", "aliases": ["egg", "eggs"]}
_MILK     = {"name": "Whole Milk", "unit": "liter", "price_per_unit": "1.20", "aliases": ["milk"]}


async def test_order_text_known_products(client: AsyncClient, db):
    for p in [_TOMATOES, _EGGS, _MILK]:
        await create_product(ProductCreate(**p), db)

    extracted = [
        ExtractedItem(product_name="tomato", quantity=2,  unit="kg"),
        ExtractedItem(product_name="eggs",   quantity=12, unit="piece"),
        ExtractedItem(product_name="milk",   quantity=1,  unit="liter"),
    ]

    with patch("app.services.order_processor._llm.extract_order_items", return_value=extracted):
        resp = await client.post("/order/text", json={"text": "2 kg tomatoes, dozen eggs, 1 liter milk"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["transcript"] == "2 kg tomatoes, dozen eggs, 1 liter milk"
    assert len(body["items"]) == 3
    assert float(body["grand_total"]) == pytest.approx(3.00 + 3.60 + 1.20)

    names = {i["product"] for i in body["items"]}
    assert names == {"Tomatoes", "Eggs", "Whole Milk"}


async def test_order_text_mixed_known_unknown(client: AsyncClient, db):
    await create_product(ProductCreate(**_TOMATOES), db)

    extracted = [
        ExtractedItem(product_name="tomato",      quantity=1, unit="kg"),
        ExtractedItem(product_name="dragon fruit", quantity=2, unit="piece"),
    ]

    with patch("app.services.order_processor._llm.extract_order_items", return_value=extracted):
        resp = await client.post("/order/text", json={"text": "1 kg tomatoes and 2 dragon fruits"})

    assert resp.status_code == 200
    body = resp.json()

    unknown = next(i for i in body["items"] if i["product"] == "dragon fruit")
    assert unknown["status"] == "No info found on the specified item."
    assert unknown.get("unit_price") is None

    known = next(i for i in body["items"] if i["product"] == "Tomatoes")
    assert float(known["total"]) == pytest.approx(1.50)

    assert float(body["grand_total"]) == pytest.approx(1.50)


async def test_order_text_empty_transcript(client: AsyncClient, db):
    extracted = []
    with patch("app.services.order_processor._llm.extract_order_items", return_value=extracted):
        resp = await client.post("/order/text", json={"text": "umm nothing thanks"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert float(body["grand_total"]) == 0.0


async def test_order_text_missing_body(client: AsyncClient, db):
    resp = await client.post("/order/text", json={})
    assert resp.status_code == 422
