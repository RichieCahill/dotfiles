"""Location command for the Signal bot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from python.signal_bot.models import SignalMessage
    from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)


def _get_entity_state(ha_url: str, ha_token: str, entity_id: str) -> dict[str, Any]:
    """Fetch an entity's state from Home Assistant."""
    entity_url = f"{ha_url}/api/states/{entity_id}"
    logger.debug(f"Fetching {entity_url=}")
    response = requests.get(
        entity_url,
        headers={"Authorization": f"Bearer {ha_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _format_location(latitude: str, longitude: str) -> str:
    """Render a friendly location response."""
    return f"Van location: {latitude}, {longitude}\nhttps://maps.google.com/?q={latitude},{longitude}"


def handle_location_request(
    message: SignalMessage,
    signal: SignalClient,
    ha_url: str | None,
    ha_token: str | None,
) -> None:
    """Reply with van location from Home Assistant."""
    if ha_url is None or ha_token is None:
        signal.reply(message, "Location command is not configured (missing HA_URL or HA_TOKEN).")
        return

    lat_payload = None
    lon_payload = None
    try:
        lat_payload = _get_entity_state(ha_url, ha_token, "sensor.van_last_known_latitude")
        lon_payload = _get_entity_state(ha_url, ha_token, "sensor.van_last_known_longitude")
    except requests.RequestException:
        logger.exception("Couldn't fetch van location from Home Assistant right now.")
        logger.debug(f"{ha_url=} {lat_payload=} {lon_payload=}")
        signal.reply(message, "Couldn't fetch van location from Home Assistant right now.")
        return

    latitude = lat_payload.get("state", "")
    longitude = lon_payload.get("state", "")

    if not latitude or not longitude or latitude == "unavailable" or longitude == "unavailable":
        signal.reply(message, "Van location is unavailable in Home Assistant right now.")
        return

    signal.reply(message, _format_location(latitude, longitude))
