"""Device registry — tracks verified/unverified devices by safety number."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from python.common import utcnow
from python.orm.richie.signal_device import RoleRecord, SignalDevice
from python.signal_bot.models import Role, TrustLevel

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)

_BLOCKED_TTL = timedelta(minutes=60)
_DEFAULT_TTL = timedelta(minutes=5)


class _CacheEntry(NamedTuple):
    expires: datetime
    trust_level: TrustLevel
    has_safety_number: bool
    safety_number: str | None
    roles: list[Role]


class DeviceRegistry:
    """Manage device trust based on Signal safety numbers.

    Devices start as UNVERIFIED. An admin verifies them over SSH by calling
    ``verify(phone_number)`` which marks the device VERIFIED and also tells
    signal-cli to trust the identity.

    Only VERIFIED devices may execute commands.
    """

    def __init__(self, signal_client: SignalClient, engine: Engine) -> None:
        self.signal_client = signal_client
        self.engine = engine
        self._contact_cache: dict[str, _CacheEntry] = {}

    def is_verified(self, phone_number: str) -> bool:
        """Check if a phone number is verified."""
        if entry := self._cached(phone_number):
            return entry.trust_level == TrustLevel.VERIFIED
        device = self._load_device(phone_number)
        return device is not None and device.trust_level == TrustLevel.VERIFIED

    def record_contact(self, phone_number: str, safety_number: str | None = None) -> None:
        """Record seeing a device. Creates entry if new, updates last_seen."""
        now = utcnow()

        entry = self._cached(phone_number)
        if entry and entry.safety_number == safety_number:
            return

        with Session(self.engine) as session:
            device = (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

            if device:
                if device.safety_number != safety_number and device.trust_level != TrustLevel.BLOCKED:
                    logger.warning(f"Safety number changed for {phone_number}, resetting to UNVERIFIED")
                    device.safety_number = safety_number
                    device.trust_level = TrustLevel.UNVERIFIED
                device.last_seen = now
            else:
                device = SignalDevice(
                    phone_number=phone_number,
                    safety_number=safety_number,
                    trust_level=TrustLevel.UNVERIFIED,
                    last_seen=now,
                )
                session.add(device)
                logger.info(f"New device registered: {phone_number}")

            session.commit()
            self._update_cache(phone_number, device)

    def has_safety_number(self, phone_number: str) -> bool:
        """Check if a device has a safety number on file."""
        if entry := self._cached(phone_number):
            return entry.has_safety_number
        device = self._load_device(phone_number)
        return device is not None and device.safety_number is not None

    def verify(self, phone_number: str) -> bool:
        """Mark a device as verified. Called by admin over SSH.

        Returns True if the device was found and verified.
        """
        with Session(self.engine) as session:
            device = (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

            if not device:
                logger.warning(f"Cannot verify unknown device: {phone_number}")
                return False

            device.trust_level = TrustLevel.VERIFIED
            self.signal_client.trust_identity(phone_number, trust_all_known_keys=True)
            session.commit()
            self._update_cache(phone_number, device)
            logger.info(f"Device verified: {phone_number}")
            return True

    def block(self, phone_number: str) -> bool:
        """Block a device."""
        return self._set_trust(phone_number, TrustLevel.BLOCKED, "Device blocked")

    def unverify(self, phone_number: str) -> bool:
        """Reset a device to unverified."""
        return self._set_trust(phone_number, TrustLevel.UNVERIFIED)

    # -- role management ------------------------------------------------------

    def get_roles(self, phone_number: str) -> list[Role]:
        """Return the roles for a device, defaulting to empty."""
        if entry := self._cached(phone_number):
            return entry.roles
        device = self._load_device(phone_number)
        return _extract_roles(device) if device else []

    def has_role(self, phone_number: str, role: Role) -> bool:
        """Check if a device has a specific role or is admin."""
        roles = self.get_roles(phone_number)
        return Role.ADMIN in roles or role in roles

    def grant_role(self, phone_number: str, role: Role) -> bool:
        """Add a role to a device. Called by admin over SSH."""
        with Session(self.engine) as session:
            device = (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

            if not device:
                logger.warning(f"Cannot grant role for unknown device: {phone_number}")
                return False

            if any(rr.name == role for rr in device.roles):
                return True

            role_record = session.execute(
                select(RoleRecord).where(RoleRecord.name == role)
            ).scalar_one_or_none()

            if not role_record:
                logger.warning(f"Unknown role: {role}")
                return False

            device.roles.append(role_record)
            session.commit()
            self._update_cache(phone_number, device)
            logger.info(f"Device {phone_number} granted role {role}")
            return True

    def revoke_role(self, phone_number: str, role: Role) -> bool:
        """Remove a role from a device. Called by admin over SSH."""
        with Session(self.engine) as session:
            device = (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

            if not device:
                logger.warning(f"Cannot revoke role for unknown device: {phone_number}")
                return False

            device.roles = [rr for rr in device.roles if rr.name != role]
            session.commit()
            self._update_cache(phone_number, device)
            logger.info(f"Device {phone_number} revoked role {role}")
            return True

    def set_roles(self, phone_number: str, roles: list[Role]) -> bool:
        """Replace all roles for a device. Called by admin over SSH."""
        with Session(self.engine) as session:
            device = (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

            if not device:
                logger.warning(f"Cannot set roles for unknown device: {phone_number}")
                return False

            role_names = [str(r) for r in roles]
            records = list(
                session.execute(select(RoleRecord).where(RoleRecord.name.in_(role_names))).scalars().all()
            )
            device.roles = records
            session.commit()
            self._update_cache(phone_number, device)
            logger.info(f"Device {phone_number} roles set to {role_names}")
            return True

    # -- queries --------------------------------------------------------------

    def list_devices(self) -> list[SignalDevice]:
        """Return all known devices."""
        with Session(self.engine) as session:
            return list(session.execute(select(SignalDevice)).scalars().all())

    def sync_identities(self) -> None:
        """Pull identity list from signal-cli and record any new ones."""
        identities = self.signal_client.get_identities()
        for identity in identities:
            number = identity.get("number", "")
            safety = identity.get("safety_number", identity.get("fingerprint", ""))
            if number:
                self.record_contact(number, safety)

    # -- internals ------------------------------------------------------------

    def _cached(self, phone_number: str) -> _CacheEntry | None:
        """Return the cache entry if it exists and hasn't expired."""
        entry = self._contact_cache.get(phone_number)
        if entry and utcnow() < entry.expires:
            return entry
        return None

    def _load_device(self, phone_number: str) -> SignalDevice | None:
        """Fetch a device by phone number (with joined roles)."""
        with Session(self.engine) as session:
            return (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

    def _update_cache(self, phone_number: str, device: SignalDevice) -> None:
        """Refresh the cache entry for a device."""
        ttl = _BLOCKED_TTL if device.trust_level == TrustLevel.BLOCKED else _DEFAULT_TTL
        self._contact_cache[phone_number] = _CacheEntry(
            expires=utcnow() + ttl,
            trust_level=device.trust_level,
            has_safety_number=device.safety_number is not None,
            safety_number=device.safety_number,
            roles=_extract_roles(device),
        )

    def _set_trust(self, phone_number: str, level: str, log_msg: str | None = None) -> bool:
        """Update the trust level for a device."""
        with Session(self.engine) as session:
            device = (
                session.execute(select(SignalDevice).where(SignalDevice.phone_number == phone_number))
                .scalar_one_or_none()
            )

            if not device:
                return False

            device.trust_level = level
            session.commit()
            self._update_cache(phone_number, device)
            if log_msg:
                logger.info(f"{log_msg}: {phone_number}")
            return True


def _extract_roles(device: SignalDevice) -> list[Role]:
    """Convert a device's RoleRecord objects to a list of Role enums."""
    return [Role(rr.name) for rr in device.roles]
