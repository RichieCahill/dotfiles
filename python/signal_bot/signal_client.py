"""Client for the signal-cli-rest-api."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Self

import httpx
import websockets.sync.client

if TYPE_CHECKING:
    from collections.abc import Generator

from python.signal_bot.models import SignalMessage

logger = logging.getLogger(__name__)


def _parse_envelope(envelope: dict[str, Any]) -> SignalMessage | None:
    """Parse a signal-cli envelope into a SignalMessage, or None if not a data message."""
    data_message = envelope.get("dataMessage")
    if not data_message:
        return None

    attachment_ids = [att["id"] for att in data_message.get("attachments", []) if "id" in att]

    group_info = data_message.get("groupInfo")
    group_id = group_info.get("groupId") if group_info else None

    return SignalMessage(
        source=envelope.get("source", ""),
        timestamp=envelope.get("timestamp", 0),
        message=data_message.get("message", "") or "",
        attachments=attachment_ids,
        group_id=group_id,
    )


class SignalClient:
    """Communicate with signal-cli-rest-api.

    Args:
        base_url: URL of the signal-cli-rest-api (e.g. http://localhost:8989).
        phone_number: The registered phone number to send/receive as.
    """

    def __init__(self, base_url: str, phone_number: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.phone_number = phone_number
        self._client = httpx.Client(base_url=self.base_url, timeout=30)

    def _ws_url(self) -> str:
        """Build the WebSocket URL from the base HTTP URL."""
        url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{url}/v1/receive/{self.phone_number}"

    def listen(self) -> Generator[SignalMessage]:
        """Connect via WebSocket and yield messages as they arrive."""
        ws_url = self._ws_url()
        logger.info(f"Connecting to WebSocket: {ws_url}")

        with websockets.sync.client.connect(ws_url) as ws:
            for raw in ws:
                try:
                    data = json.loads(raw)
                    envelope = data.get("envelope", {})
                    message = _parse_envelope(envelope)
                    if message:
                        yield message
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON WebSocket frame: {raw[:200]}")

    def send(self, recipient: str, message: str) -> None:
        """Send a text message."""
        payload = {
            "message": message,
            "number": self.phone_number,
            "recipients": [recipient],
        }
        response = self._client.post("/v2/send", json=payload)
        response.raise_for_status()

    def send_to_group(self, group_id: str, message: str) -> None:
        """Send a message to a group."""
        payload = {
            "message": message,
            "number": self.phone_number,
            "recipients": [group_id],
        }
        response = self._client.post("/v2/send", json=payload)
        response.raise_for_status()

    def get_attachment(self, attachment_id: str) -> bytes:
        """Download an attachment by ID."""
        response = self._client.get(f"/v1/attachments/{attachment_id}")
        response.raise_for_status()
        return response.content

    def get_identities(self) -> list[dict[str, Any]]:
        """List known identities and their trust levels."""
        response = self._client.get(f"/v1/identities/{self.phone_number}")
        response.raise_for_status()
        return response.json()

    def trust_identity(self, number_to_trust: str, *, trust_all_known_keys: bool = False) -> None:
        """Trust an identity (verify safety number)."""
        payload: dict[str, Any] = {}
        if trust_all_known_keys:
            payload["trust_all_known_keys"] = True
        response = self._client.put(
            f"/v1/identities/{self.phone_number}/trust/{number_to_trust}",
            json=payload,
        )
        response.raise_for_status()

    def reply(self, message: SignalMessage, text: str) -> None:
        """Reply to a message, routing to group or individual."""
        if message.group_id:
            self.send_to_group(message.group_id, text)
        else:
            self.send(message.source, text)

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the HTTP client on exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
