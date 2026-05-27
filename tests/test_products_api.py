import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_products_empty(client: AsyncClient):
    resp = await client.get("/products/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_product(client: AsyncClient):
    payload = {
        "name": "Tomatoes",
        "category": "Vegetables",
        "unit": "kg",
        "price_per_unit": "1.50",
        "aliases": ["tomato", "tomatoes"],
    }
    resp = await client.post("/products/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Tomatoes"
    assert data["unit"] == "kg"
    assert float(data["price_per_unit"]) == 1.50
    assert data["active"] is True
    return data["id"]


async def test_list_products_after_create(client: AsyncClient):
    await client.post(
        "/products/",
        json={"name": "Eggs", "unit": "piece", "price_per_unit": "0.30", "aliases": ["egg"]},
    )
    resp = await client.get("/products/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_update_product(client: AsyncClient):
    create_resp = await client.post(
        "/products/",
        json={"name": "Butter", "unit": "pack", "price_per_unit": "3.49", "aliases": []},
    )
    product_id = create_resp.json()["id"]

    resp = await client.put(f"/products/{product_id}", json={"price_per_unit": "3.99"})
    assert resp.status_code == 200
    assert float(resp.json()["price_per_unit"]) == 3.99


async def test_update_product_not_found(client: AsyncClient):
    resp = await client.put(
        "/products/00000000-0000-0000-0000-000000000000",
        json={"price_per_unit": "1.00"},
    )
    assert resp.status_code == 404


async def test_delete_product(client: AsyncClient):
    create_resp = await client.post(
        "/products/",
        json={"name": "Rice", "unit": "kg", "price_per_unit": "1.80", "aliases": []},
    )
    product_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/products/{product_id}")
    assert del_resp.status_code == 204

    list_resp = await client.get("/products/")
    assert all(p["id"] != product_id for p in list_resp.json())


async def test_delete_product_not_found(client: AsyncClient):
    resp = await client.delete("/products/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
