from decimal import Decimal
from unittest.mock import patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ExtractedItem
from app.services.order_processor import process_order
from app.services.product_service import create_product
from app.models.schemas import ProductCreate

pytestmark = pytest.mark.asyncio


async def _seed(db: AsyncSession, *products):
    for p in products:
        await create_product(ProductCreate(**p), db)


async def test_order_known_products(db: AsyncSession):
    await _seed(
        db,
        {"name": "Tomatoes", "unit": "kg", "price_per_unit": "1.50", "aliases": ["tomato"]},
        {"name": "Eggs", "unit": "piece", "price_per_unit": "0.30", "aliases": ["egg"]},
    )

    extracted = [
        ExtractedItem(product_name="tomato", quantity=2, unit="kg"),
        ExtractedItem(product_name="eggs", quantity=12, unit="piece"),
    ]

    with patch(
        "app.services.order_processor._llm.extract_order_items",
        return_value=extracted,
    ):
        order = await process_order("2 kg of tomatoes and a dozen eggs", db)

    assert order.transcript == "2 kg of tomatoes and a dozen eggs"
    assert len(order.items) == 2

    tomato_item = next(i for i in order.items if i.product == "Tomatoes")
    assert tomato_item.unit_price == Decimal("1.50")
    assert tomato_item.total == Decimal("3.00")

    egg_item = next(i for i in order.items if i.product == "Eggs")
    assert egg_item.total == Decimal("3.60")

    assert order.grand_total == Decimal("6.60")


async def test_order_unknown_product(db: AsyncSession):
    await _seed(db, {"name": "Apples", "unit": "kg", "price_per_unit": "2.20", "aliases": []})

    extracted = [
        ExtractedItem(product_name="Apples", quantity=1, unit="kg"),
        ExtractedItem(product_name="Dragon Fruit", quantity=2, unit="piece"),
    ]

    with patch(
        "app.services.order_processor._llm.extract_order_items",
        return_value=extracted,
    ):
        order = await process_order("1 kg apples and 2 dragon fruits", db)

    unknown = next(i for i in order.items if i.product == "Dragon Fruit")
    assert unknown.status == "No info found on the specified item."
    assert unknown.unit_price is None

    known = next(i for i in order.items if i.product == "Apples")
    assert known.total == Decimal("2.20")

    assert order.grand_total == Decimal("2.20")


async def test_order_all_unknown(db: AsyncSession):
    extracted = [ExtractedItem(product_name="Unicorn Milk", quantity=1, unit="liter")]

    with patch(
        "app.services.order_processor._llm.extract_order_items",
        return_value=extracted,
    ):
        order = await process_order("1 liter of unicorn milk", db)

    assert order.grand_total == Decimal("0.00")
    assert order.items[0].status == "No info found on the specified item."


async def test_alias_match(db: AsyncSession):
    await _seed(
        db,
        {"name": "Potatoes", "unit": "kg", "price_per_unit": "0.89", "aliases": ["spud", "spuds"]},
    )

    extracted = [ExtractedItem(product_name="spuds", quantity=3, unit="kg")]

    with patch(
        "app.services.order_processor._llm.extract_order_items",
        return_value=extracted,
    ):
        order = await process_order("3 kg of spuds", db)

    assert order.items[0].product == "Potatoes"
    assert order.items[0].total == Decimal("2.67")
