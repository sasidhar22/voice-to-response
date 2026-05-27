from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    unit: str
    price_per_unit: Decimal
    aliases: List[str] = []


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    price_per_unit: Optional[Decimal] = None
    aliases: Optional[List[str]] = None


class ProductResponse(ProductBase):
    id: UUID
    active: bool

    model_config = {"from_attributes": True}


class ExtractedItem(BaseModel):
    product_name: str
    quantity: float
    unit: str


class TextOrderRequest(BaseModel):
    text: str


class OrderItem(BaseModel):
    product: str
    quantity: float
    unit: str
    unit_price: Optional[Decimal] = None
    total: Optional[Decimal] = None
    status: Optional[str] = None


class OrderResponse(BaseModel):
    transcript: str
    items: List[OrderItem]
    grand_total: Decimal
