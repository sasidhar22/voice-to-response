"""
Data ingestion pipeline: loads products.json → upserts into PostgreSQL.

Usage:
    python -m app.pipelines.ingestion --file data/products.json
"""
import asyncio
import argparse
import json
from pathlib import Path

from app.db.session import AsyncSessionLocal, engine, Base
from app.models import product as _product_model  # noqa: F401 — registers ORM model
from app.models.schemas import ProductCreate, ProductUpdate
import app.services.product_service as svc


async def ingest(file_path: str) -> None:
    raw = json.loads(Path(file_path).read_text())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = updated = failed = 0

    async with AsyncSessionLocal() as db:
        for entry in raw:
            product_name = entry.get("name", "<unknown>")
            try:
                data = ProductCreate(**entry)
                existing = await svc.get_product_by_name(data.name, db)

                if existing:
                    await svc.update_product(
                        existing.id,
                        ProductUpdate(
                            category=data.category,
                            unit=data.unit,
                            price_per_unit=data.price_per_unit,
                            aliases=data.aliases,
                        ),
                        db,
                    )
                    updated += 1
                    print(f"  updated : {product_name}")
                else:
                    await svc.create_product(data, db)
                    inserted += 1
                    print(f"  inserted: {product_name}")

            except Exception as exc:
                failed += 1
                print(f"  FAILED  : {product_name} — {exc}")

    print(f"\nDone — inserted: {inserted}, updated: {updated}, failed: {failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest product catalog into the DB")
    parser.add_argument("--file", default="data/products.json", help="Path to products JSON")
    args = parser.parse_args()
    asyncio.run(ingest(args.file))
