import json
import boto3
from typing import List
from app.config import settings
from app.models.schemas import ExtractedItem

_EXTRACTION_TOOL = {
    "name": "extract_order_items",
    "description": "Extract grocery items from a customer order transcript.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "Product name as spoken by the customer",
                        },
                        "quantity": {
                            "type": "number",
                            "description": "Numeric quantity (e.g. 'a dozen' → 12, 'half a kilo' → 0.5)",
                        },
                        "unit": {
                            "type": "string",
                            "description": "Unit of measure: kg, piece, pack, liter, dozen",
                        },
                    },
                    "required": ["product_name", "quantity", "unit"],
                },
            }
        },
        "required": ["items"],
    },
}

_SYSTEM_PROMPT = (
    "You are a grocery order assistant. Extract every product the customer wants to buy "
    "from the transcript. Normalize quantities: 'a dozen' → 12 pieces, "
    "'half a kilo' → 0.5 kg, 'a pack' → 1 pack, 'a liter' → 1 liter. "
    "Always call the extract_order_items tool — never respond in plain text."
)


class BedrockService:
    def __init__(self):
        kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        self._client = boto3.client("bedrock-runtime", **kwargs)

    def extract_order_items(self, transcript: str) -> List[ExtractedItem]:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": _SYSTEM_PROMPT,
            "tools": [_EXTRACTION_TOOL],
            "tool_choice": {"type": "tool", "name": "extract_order_items"},
            "messages": [
                {"role": "user", "content": f"Customer order: {transcript}"}
            ],
        }
        response = self._client.invoke_model(
            modelId=settings.bedrock_llm_model_id,
            body=json.dumps(body),
        )
        result = json.loads(response["body"].read())

        for block in result.get("content", []):
            if (
                block.get("type") == "tool_use"
                and block.get("name") == "extract_order_items"
            ):
                return [ExtractedItem(**item) for item in block["input"]["items"]]

        return []
