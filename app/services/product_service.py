import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.models.schemas import ProductCreate, ProductUpdate


async def get_product_by_name(name: str, db: AsyncSession) -> Optional[Product]:
    name_lower = name.lower()

    # 1. Exact name match (case-insensitive)
    result = await db.execute(
        select(Product).where(
            func.lower(Product.name) == name_lower,
            Product.active.is_(True),
        )
    )
    product = result.scalar_one_or_none()
    if product:
        return product

    # 2. Alias match — scan active products and compare aliases in Python.
    #    Grocery catalogs are small enough that this is efficient.
    result = await db.execute(select(Product).where(Product.active.is_(True)))
    for product in result.scalars().all():
        if name_lower in [a.lower() for a in (product.aliases or [])]:
            return product
    return None


async def get_all_products(db: AsyncSession) -> List[Product]:
    result = await db.execute(
        select(Product).where(Product.active.is_(True)).order_by(Product.name)
    )
    return list(result.scalars().all())


async def create_product(data: ProductCreate, db: AsyncSession) -> Product:
    product = Product(
        id=uuid.uuid4(),
        name=data.name,
        category=data.category,
        unit=data.unit,
        price_per_unit=data.price_per_unit,
        aliases=[a.lower() for a in data.aliases],
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    product_id: uuid.UUID, data: ProductUpdate, db: AsyncSession
) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return None

    updates = data.model_dump(exclude_none=True)
    if "aliases" in updates:
        updates["aliases"] = [a.lower() for a in updates["aliases"]]

    for field, value in updates.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


async def deactivate_product(product_id: uuid.UUID, db: AsyncSession) -> bool:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return False
    product.active = False
    await db.commit()
    return True
