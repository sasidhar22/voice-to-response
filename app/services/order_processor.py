from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import OrderItem, OrderResponse
from app.services.bedrock import BedrockService
from app.services.product_service import get_product_by_name

_bedrock = BedrockService()


async def process_order(transcript: str, db: AsyncSession) -> OrderResponse:
    extracted = _bedrock.extract_order_items(transcript)

    items: list[OrderItem] = []
    grand_total = Decimal("0.00")

    for extracted_item in extracted:
        product = await get_product_by_name(extracted_item.product_name, db)

        if product is None:
            items.append(
                OrderItem(
                    product=extracted_item.product_name,
                    quantity=extracted_item.quantity,
                    unit=extracted_item.unit,
                    status="No info found on the specified item.",
                )
            )
        else:
            line_total = Decimal(str(extracted_item.quantity)) * product.price_per_unit
            grand_total += line_total
            items.append(
                OrderItem(
                    product=product.name,
                    quantity=extracted_item.quantity,
                    unit=product.unit,
                    unit_price=product.price_per_unit,
                    total=line_total,
                )
            )

    return OrderResponse(
        transcript=transcript,
        items=items,
        grand_total=grand_total,
    )
