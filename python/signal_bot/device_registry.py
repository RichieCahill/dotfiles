"""Device registry — tracks verified/unverified devices by safety number."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from python.common import utcnow
from python.signal_bot.models import Device, TrustLevel

if TYPE_CHECKING:
    from pathlib import Path

    from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """Manage device trust based on Signal safety numbers.

    Devices start as UNVERIFIED. An admin verifies them over SSH by calling
    ``verify(phone_number)`` which marks the device VERIFIED and also tells
    signal-cli to trust the identity.

    Only VERIFIED devices may execute commands.

    Args:
        signal_client: The Signal API client (used to sync identities).
        registry_path: Path to the JSON file that persists device state.
    """

    def __init__(self, signal_client: SignalClient, registry_path: Path) -> None:
        self.signal_client = signal_client
        self.registry_path = registry_path
        self._devices: dict[str, Device] = {}
        self._load()

    def is_verified(self, phone_number: str) -> bool:
        """Check if a phone number is verified."""
        device = self._devices.get(phone_number)
        return device is not None and device.trust_level == TrustLevel.VERIFIED

    def is_blocked(self, phone_number: str) -> bool:
        """Check if a phone number is blocked."""
        device = self._devices.get(phone_number)
        return device is not None and device.trust_level == TrustLevel.BLOCKED

    def record_contact(self, phone_number: str, safety_number: str) -> Device:
        """Record seeing a device. Creates entry if new, updates last_seen."""
        now = utcnow()
        if phone_number in self._devices:
            device = self._devices[phone_number]
            if device.safety_number != safety_number:
                logger.warning(f"Safety number changed for {phone_number}, resetting to UNVERIFIED")
                device.safety_number = safety_number
                device.trust_level = TrustLevel.UNVERIFIED
            device.last_seen = now
        else:
            device = Device(
                phone_number=phone_number,
                safety_number=safety_number,
                trust_level=TrustLevel.UNVERIFIED,
                first_seen=now,
                last_seen=now,
            )
            self._devices[phone_number] = device
            logger.info(f"New device registered: {phone_number}")

        self._save()
        return device

    def verify(self, phone_number: str) -> bool:
        """Mark a device as verified. Called by admin over SSH.

        Returns True if the device was found and verified.
        """
        device = self._devices.get(phone_number)
        if not device:
            logger.warning(f"Cannot verify unknown device: {phone_number}")
            return False

        device.trust_level = TrustLevel.VERIFIED
        self.signal_client.trust_identity(phone_number, trust_all_known_keys=True)
        self._save()
        logger.info(f"Device verified: {phone_number}")
        return True

    def block(self, phone_number: str) -> bool:
        """Block a device."""
        device = self._devices.get(phone_number)
        if not device:
            return False
        device.trust_level = TrustLevel.BLOCKED
        self._save()
        logger.info(f"Device blocked: {phone_number}")
        return True

    def unverify(self, phone_number: str) -> bool:
        """Reset a device to unverified."""
        device = self._devices.get(phone_number)
        if not device:
            return False
        device.trust_level = TrustLevel.UNVERIFIED
        self._save()
        return True

    def list_devices(self) -> list[Device]:
        """Return all known devices."""
        return list(self._devices.values())

    def sync_identities(self) -> None:
        """Pull identity list from signal-cli and record any new ones."""
        identities = self.signal_client.get_identities()
        for identity in identities:
            number = identity.get("number", "")
            safety = identity.get("safety_number", identity.get("fingerprint", ""))
            if number:
                self.record_contact(number, safety)

    def _load(self) -> None:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return
        data: list[dict[str, Any]] = json.loads(self.registry_path.read_text())
        for entry in data:
            device = Device.model_validate(entry)
            self._devices[device.phone_number] = device

    def _save(self) -> None:
        """Persist registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = [device.model_dump(mode="json") for device in self._devices.values()]
        self.registry_path.write_text(json.dumps(data, indent=2) + "\n")
