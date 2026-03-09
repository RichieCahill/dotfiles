"""Van inventory command — parse receipts and item lists via LLM, push to API."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from python.signal_bot.models import InventoryItem, InventoryUpdate

if TYPE_CHECKING:
    from python.signal_bot.llm_client import LLMClient
    from python.signal_bot.models import SignalMessage
    from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an inventory assistant. Extract items from the input and return ONLY
a JSON array. Each element must have these fields:
  - "name": item name (string)
  - "quantity": numeric count or amount (default 1)
  - "unit": unit of measure (e.g. "each", "lb", "oz", "gallon", "bag", "box")
  - "category": category like "food", "tools", "supplies", etc.
  - "notes": any extra detail (empty string if none)

Example output:
[{"name": "water bottles", "quantity": 6, "unit": "gallon", "category": "supplies", "notes": "1 gallon each"}]

Return ONLY the JSON array, no other text.\
"""

IMAGE_PROMPT = "Extract all items from this receipt or inventory photo."
TEXT_PROMPT = "Extract all items from this inventory list."


def parse_llm_response(raw: str) -> list[InventoryItem]:
    """Parse the LLM JSON response into InventoryItem list."""
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.startswith("```")]
        text = "\n".join(lines)

    items_data: list[dict[str, Any]] = json.loads(text)
    return [InventoryItem.model_validate(item) for item in items_data]


def _upsert_item(api_url: str, item: InventoryItem) -> None:
    """Create or update an item via the van_inventory API.

    Fetches existing items, and if one with the same name exists,
    patches its quantity (summing). Otherwise creates a new item.
    """
    base = api_url.rstrip("/")
    response = httpx.get(f"{base}/api/items", timeout=10)
    response.raise_for_status()
    existing: list[dict[str, Any]] = response.json()

    match = next((e for e in existing if e["name"].lower() == item.name.lower()), None)

    if match:
        new_qty = match["quantity"] + item.quantity
        patch = {"quantity": new_qty}
        if item.category:
            patch["category"] = item.category
        response = httpx.patch(f"{base}/api/items/{match['id']}", json=patch, timeout=10)
        response.raise_for_status()
        return
    payload = {
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "category": item.category or None,
    }
    response = httpx.post(f"{base}/api/items", json=payload, timeout=10)
    response.raise_for_status()


def handle_inventory_update(
    message: SignalMessage,
    signal: SignalClient,
    llm: LLMClient,
    api_url: str,
) -> InventoryUpdate:
    """Process an inventory update from a Signal message.

    Accepts either an image (receipt photo) or text list.
    Uses the LLM to extract structured items, then pushes to the van_inventory API.
    """
    try:
        if message.attachments:
            image_data = signal.get_attachment(message.attachments[0])
            raw_response = llm.chat_with_image(
                IMAGE_PROMPT,
                image_data,
                system=SYSTEM_PROMPT,
            )
            source_type = "receipt_photo"
        elif message.message.strip():
            raw_response = llm.chat(
                f"{TEXT_PROMPT}\n\n{message.message}",
                system=SYSTEM_PROMPT,
            )
            source_type = "text_list"
        else:
            signal.reply(message, "Send a photo of a receipt or a text list of items to update inventory.")
            return InventoryUpdate()

        new_items = parse_llm_response(raw_response)

        for item in new_items:
            _upsert_item(api_url, item)

        summary = _format_summary(new_items)
        signal.reply(message, f"Inventory updated with {len(new_items)} item(s):\n{summary}")

        return InventoryUpdate(items=new_items, raw_response=raw_response, source_type=source_type)

    except Exception:
        logger.exception("Failed to process inventory update")
        signal.reply(message, "Failed to process inventory update. Check logs for details.")
        return InventoryUpdate()


def _format_summary(items: list[InventoryItem]) -> str:
    """Format items into a readable summary."""
    lines = [f"  - {item.name} x{item.quantity} {item.unit} [{item.category}]" for item in items]
    return "\n".join(lines)
