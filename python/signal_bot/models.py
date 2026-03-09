"""Models for the Signal command and control bot."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - pydantic needs this at runtime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class TrustLevel(StrEnum):
    """Device trust level."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"


class Device(BaseModel):
    """A registered device tracked by safety number."""

    phone_number: str
    safety_number: str
    trust_level: TrustLevel = TrustLevel.UNVERIFIED
    first_seen: datetime
    last_seen: datetime


class SignalMessage(BaseModel):
    """An incoming Signal message."""

    source: str
    timestamp: int
    message: str = ""
    attachments: list[str] = []
    group_id: str | None = None
    is_receipt: bool = False


class SignalEnvelope(BaseModel):
    """Raw envelope from signal-cli-rest-api."""

    envelope: dict[str, Any]
    account: str | None = None


class InventoryItem(BaseModel):
    """An item in the van inventory."""

    name: str
    quantity: float = 1
    unit: str = "each"
    category: str = ""
    notes: str = ""


class InventoryUpdate(BaseModel):
    """Result of processing an inventory update."""

    items: list[InventoryItem] = []
    raw_response: str = ""
    source_type: str = ""  # "receipt_photo" or "text_list"


class BotConfig(BaseModel):
    """Top-level bot configuration."""

    signal_api_url: str
    phone_number: str
    inventory_api_url: str
    cmd_prefix: str = "!"
    reconnect_delay: int = 5
    max_reconnect_delay: int = 300
    max_retries: int = 10
