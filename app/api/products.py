from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.schemas import ProductCreate, ProductUpdate, ProductResponse
import app.services.product_service as svc

router = APIRouter(tags=["products"])


@router.get("/", response_model=List[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    return await svc.get_all_products(db)


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await svc.create_product(data, db)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    product = await svc.update_product(product_id, data, db)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    success = await svc.deactivate_product(product_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
