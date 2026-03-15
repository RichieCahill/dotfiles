"""Location command for the Signal bot."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from python.signal_bot.models import SignalMessage
    from python.signal_bot.signal_client import SignalClient


def _get_location_payload(ha_url: str, ha_token: str, entity_id: str) -> dict[str, Any]:
    """Fetch location entity state from Home Assistant."""
    response = requests.get(
        f"{ha_url}/api/states/{entity_id}",
        headers={"Authorization": f"Bearer {ha_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _format_location(payload: dict[str, Any]) -> str:
    """Render a friendly location response."""
    attributes = payload.get("attributes", {})
    latitude = attributes.get("latitude")
    longitude = attributes.get("longitude")

    if latitude is None or longitude is None:
        state = payload.get("state", "unknown")
        if "," not in state:
            return "Van location is unavailable in Home Assistant right now."
        latitude_text, longitude_text = [part.strip() for part in state.split(",", maxsplit=1)]
    else:
        latitude_text = str(latitude)
        longitude_text = str(longitude)

    lines = [
        f"Van location: {latitude_text}, {longitude_text}",
        f"https://maps.google.com/?q={latitude_text},{longitude_text}",
    ]

    speed = attributes.get("speed")
    if speed not in (None, "", "unknown", "unavailable"):
        lines.append(f"Speed: {speed}")

    last_updated = attributes.get("last_updated")
    if last_updated:
        lines.append(f"Updated: {last_updated}")

    return "\n".join(lines)


def handle_location_request(
    message: SignalMessage,
    signal: SignalClient,
    ha_url: str | None,
    ha_token: str | None,
    ha_location_entity: str,
) -> None:
    """Reply with van location from Home Assistant."""
    if ha_url is None or ha_token is None:
        signal.reply(message, "Location command is not configured (missing HA_URL or HA_TOKEN).")
        return

    try:
        payload = _get_location_payload(ha_url, ha_token, ha_location_entity)
    except requests.RequestException:
        signal.reply(message, "Couldn't fetch van location from Home Assistant right now.")
        return

    signal.reply(message, _format_location(payload))
