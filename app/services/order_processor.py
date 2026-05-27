from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.schemas import OrderItem, OrderResponse
from app.services.product_service import get_product_by_name


def _build_llm():
    if settings.llm_provider == "ollama":
        from app.services.ollama_service import OllamaService
        return OllamaService()
    from app.services.bedrock import BedrockService
    return BedrockService()


_llm = _build_llm()


async def process_order(transcript: str, db: AsyncSession) -> OrderResponse:
    extracted = _llm.extract_order_items(transcript)

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
