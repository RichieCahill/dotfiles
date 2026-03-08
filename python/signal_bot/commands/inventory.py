"""Van inventory command — parse receipts and item lists via LLM."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from python.signal_bot.models import InventoryItem, InventoryUpdate

if TYPE_CHECKING:
    from pathlib import Path

    from python.signal_bot.llm_client import LLMClient
    from python.signal_bot.models import SignalMessage
    from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an inventory assistant. Extract items from the input and return ONLY
a JSON array. Each element must have these fields:
  - "name": item name (string)
  - "quantity": integer count (default 1)
  - "category": category like "food", "tools", "supplies", etc.
  - "notes": any extra detail (empty string if none)

Example output:
[{"name": "water bottles", "quantity": 6, "category": "supplies", "notes": "1 gallon each"}]

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


def load_inventory(path: Path) -> list[InventoryItem]:
    """Load existing inventory from disk."""
    if not path.exists():
        return []
    data: list[dict[str, Any]] = json.loads(path.read_text())
    return [InventoryItem.model_validate(item) for item in data]


def save_inventory(path: Path, items: list[InventoryItem]) -> None:
    """Save inventory to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [item.model_dump() for item in items]
    path.write_text(json.dumps(data, indent=2) + "\n")


def handle_inventory_update(
    message: SignalMessage,
    signal: SignalClient,
    llm: LLMClient,
    inventory_path: Path,
) -> InventoryUpdate:
    """Process an inventory update from a Signal message.

    Accepts either an image (receipt photo) or text list.
    Uses the LLM to extract structured items, then merges into inventory.
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
        existing = load_inventory(inventory_path)
        merged = _merge_items(existing, new_items)
        save_inventory(inventory_path, merged)

        summary = _format_summary(new_items)
        signal.reply(message, f"Inventory updated with {len(new_items)} item(s):\n{summary}")

        return InventoryUpdate(items=new_items, raw_response=raw_response, source_type=source_type)

    except Exception:
        logger.exception("Failed to process inventory update")
        signal.reply(message, "Failed to process inventory update. Check logs for details.")
        return InventoryUpdate()


def _merge_items(existing: list[InventoryItem], new: list[InventoryItem]) -> list[InventoryItem]:
    """Merge new items into existing inventory, summing quantities for matches."""
    by_name: dict[str, InventoryItem] = {item.name.lower(): item for item in existing}
    for item in new:
        key = item.name.lower()
        if key in by_name:
            current = by_name[key]
            by_name[key] = current.model_copy(
                update={
                    "quantity": current.quantity + item.quantity,
                    "category": item.category or current.category,
                    "notes": item.notes or current.notes,
                },
            )
        else:
            by_name[key] = item
    return list(by_name.values())


def _format_summary(items: list[InventoryItem]) -> str:
    """Format items into a readable summary."""
    lines = [f"  - {item.name} x{item.quantity} [{item.category}]" for item in items]
    return "\n".join(lines)
