"""Signal command and control bot — main entry point."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Annotated

import typer

from python.common import configure_logger
from python.signal_bot.commands.inventory import handle_inventory_update
from python.signal_bot.device_registry import DeviceRegistry
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.models import BotConfig, LLMConfig, SignalMessage
from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)

# Command prefix — messages must start with this to be treated as commands.
CMD_PREFIX = "!"

HELP_TEXT = """\
Available commands:
  !inventory <text list>  — update van inventory from a text list
  !inventory (+ photo)    — update van inventory from a receipt photo
  !status                 — show bot status
  !help                   — show this help message

Send a receipt photo with the message "!inventory" to scan it.\
"""

RECONNECT_DELAY = 5


def dispatch(
    message: SignalMessage,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
    inventory_path: Path,
) -> None:
    """Route an incoming message to the right command handler."""
    source = message.source

    if registry.is_blocked(source):
        return

    if not registry.is_verified(source):
        signal.reply(
            message,
            "Your device is not verified. Ask the admin to verify your safety number over SSH.",
        )
        return

    text = message.message.strip()

    if not text.startswith(CMD_PREFIX) and not message.attachments:
        return

    cmd = text.lstrip(CMD_PREFIX).split()[0].lower() if text.startswith(CMD_PREFIX) else ""

    if cmd == "help":
        signal.reply(message, HELP_TEXT)

    elif cmd == "status":
        models = llm.list_models()
        model_list = ", ".join(models[:10])
        device_count = len(registry.list_devices())
        signal.reply(
            message,
            f"Bot online.\nLLM: {llm.config.model}\nAvailable models: {model_list}\nKnown devices: {device_count}",
        )

    elif cmd == "inventory" or (message.attachments and not text.startswith(CMD_PREFIX)):
        handle_inventory_update(message, signal, llm, inventory_path)

    else:
        signal.reply(message, f"Unknown command: {cmd}\n\n{HELP_TEXT}")


def run_loop(
    config: BotConfig,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
) -> None:
    """Listen for messages via WebSocket, reconnecting on failure."""
    inventory_path = Path(config.inventory_file)
    logger.info("Bot started — listening via WebSocket")

    while True:
        try:
            for message in signal.listen():
                logger.info(f"Message from {message.source}: {message.message[:80]}")
                registry.record_contact(message.source, "")
                dispatch(message, signal, llm, registry, inventory_path)
        except Exception:
            logger.exception(f"WebSocket error, reconnecting in {RECONNECT_DELAY}s")
            time.sleep(RECONNECT_DELAY)


def main(
    signal_api_url: Annotated[str, typer.Option(envvar="SIGNAL_API_URL")],
    phone_number: Annotated[str, typer.Option(envvar="SIGNAL_PHONE_NUMBER")],
    llm_host: Annotated[str, typer.Option(envvar="LLM_HOST")],
    llm_model: Annotated[str, typer.Option(envvar="LLM_MODEL")] = "qwen3-vl:32b",
    llm_port: Annotated[int, typer.Option(envvar="LLM_PORT")] = 11434,
    inventory_file: Annotated[str, typer.Option(envvar="INVENTORY_FILE")] = "/var/lib/signal-bot/van_inventory.json",
    registry_file: Annotated[str, typer.Option(envvar="REGISTRY_FILE")] = "/var/lib/signal-bot/device_registry.json",
    log_level: Annotated[str, typer.Option()] = "INFO",
) -> None:
    """Run the Signal command and control bot."""
    configure_logger(log_level)

    llm_config = LLMConfig(model=llm_model, host=llm_host, port=llm_port)
    config = BotConfig(
        signal_api_url=signal_api_url,
        phone_number=phone_number,
        llm=llm_config,
        inventory_file=inventory_file,
    )

    signal = SignalClient(config.signal_api_url, config.phone_number)
    llm = LLMClient(llm_config)
    registry = DeviceRegistry(signal, Path(registry_file))

    try:
        run_loop(config, signal, llm, registry)
    finally:
        signal.close()
        llm.close()


if __name__ == "__main__":
    typer.run(main)
