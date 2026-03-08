"""Client for the signal-cli-rest-api."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from python.signal_bot.models import SignalMessage

logger = logging.getLogger(__name__)


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

    def receive(self) -> list[SignalMessage]:
        """Poll for new messages."""
        response = self._client.get(f"/v1/receive/{self.phone_number}")
        response.raise_for_status()
        envelopes: list[dict[str, Any]] = response.json()

        messages: list[SignalMessage] = []
        for raw in envelopes:
            envelope = raw.get("envelope", {})
            data_message = envelope.get("dataMessage")
            if not data_message:
                continue

            attachment_ids = [
                att["id"] for att in data_message.get("attachments", []) if "id" in att
            ]

            group_info = data_message.get("groupInfo")
            group_id = group_info.get("groupId") if group_info else None

            messages.append(
                SignalMessage(
                    source=envelope.get("source", ""),
                    timestamp=envelope.get("timestamp", 0),
                    message=data_message.get("message", "") or "",
                    attachments=attachment_ids,
                    group_id=group_id,
                ),
            )

        return messages

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

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
