import json
from typing import List
import ollama as ollama_client
from app.config import settings
from app.models.schemas import ExtractedItem

_SYSTEM_PROMPT = """You are a grocery order assistant. Extract every product the customer wants to buy.

Return ONLY valid JSON in this exact format (no extra text):
{"items": [{"product_name": "string", "quantity": number, "unit": "string"}]}

Normalization rules:
- "a dozen" or "dozen" → 12, unit = "piece"
- "half a kilo" → 0.5, unit = "kg"
- "a pack" / "one pack" → 1, unit = "pack"
- "a liter" / "one liter" → 1, unit = "liter"
- unit must be one of: kg, piece, pack, liter"""


class OllamaService:
    def extract_order_items(self, transcript: str) -> List[ExtractedItem]:
        response = ollama_client.chat(
            model=settings.ollama_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Customer order: {transcript}"},
            ],
            format="json",
            options={"temperature": 0},
        )
        raw = response["message"]["content"]
        data = json.loads(raw)

        # Handle both {"items": [...]} and direct [...]
        items = data.get("items", data) if isinstance(data, dict) else data
        return [ExtractedItem(**item) for item in items]
