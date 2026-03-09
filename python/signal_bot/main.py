"""Signal command and control bot — main entry point."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Annotated

import typer

from python.common import configure_logger
from python.orm.common import get_postgres_engine
from python.signal_bot.commands.inventory import handle_inventory_update
from python.signal_bot.device_registry import DeviceRegistry
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.models import BotConfig, SignalMessage
from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)


HELP_TEXT = (
    "Available commands:\n"
    "  !inventory <text list>  — update van inventory from a text list\n"
    "  !inventory (+ photo)    — update van inventory from a receipt photo\n"
    "  !status                 — show bot status\n"
    "  !help                   — show this help message\n"
    "Send a receipt photo with the message '!inventory' to scan it.\n"
)


def help_action(
    signal: SignalClient,
    message: SignalMessage,
    _llm: LLMClient,
    _registry: DeviceRegistry,
    _inventory_path: Path,
    _cmd: str,
) -> str:
    """Return the help text for the bot."""
    signal.reply(message, HELP_TEXT)


def status_action(
    signal: SignalClient,
    message: SignalMessage,
    llm: LLMClient,
    registry: DeviceRegistry,
    _inventory_path: Path,
    _cmd: str,
) -> str:
    """Return the status of the bot."""
    models = llm.list_models()
    model_list = ", ".join(models[:10])
    device_count = len(registry.list_devices())
    signal.reply(
        message,
        f"Bot online.\nLLM: {llm.model}\nAvailable models: {model_list}\nKnown devices: {device_count}",
    )


def unknown_action(
    signal: SignalClient,
    message: SignalMessage,
    _llm: LLMClient,
    _registry: DeviceRegistry,
    _inventory_path: Path,
    cmd: str,
) -> str:
    """Return an error message for an unknown command."""
    signal.reply(message, f"Unknown command: {cmd}\n\n{HELP_TEXT}")


def inventory_action(
    signal: SignalClient,
    message: SignalMessage,
    llm: LLMClient,
    _registry: DeviceRegistry,
    inventory_path: Path,
    _cmd: str,
) -> str:
    """Process an inventory update."""
    handle_inventory_update(message, signal, llm, inventory_path)


def dispatch(
    message: SignalMessage,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
    inventory_path: Path,
    config: BotConfig,
) -> None:
    """Route an incoming message to the right command handler."""
    source = message.source

    if not registry.is_verified(source) or not registry.has_safety_number(source):
        logger.info(f"Device {source} not verified, ignoring message")
        return

    text = message.message.strip()

    prefix = config.cmd_prefix
    if not text.startswith(prefix) and not message.attachments:
        return
    text.startswith(prefix)
    cmd = text.lstrip(prefix).split()[0].lower() if text.startswith(prefix) else ""

    commands = {
        "help": help_action,
        "status": status_action,
        "inventory": inventory_action,
    }

    action = commands.get(cmd, unknown_action)
    action(signal, message, llm, registry, inventory_path, cmd)


def run_loop(
    config: BotConfig,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
) -> None:
    """Listen for messages via WebSocket, reconnecting on failure."""
    inventory_path = Path(config.inventory_file)
    logger.info("Bot started — listening via WebSocket")

    retries = 0
    delay = config.reconnect_delay

    while retries < config.max_retries:
        try:
            for message in signal.listen():
                logger.info(f"Message from {message.source}: {message.message[:80]}")
                safety_number = signal.get_safety_number(message.source)
                registry.record_contact(message.source, safety_number)
                dispatch(message, signal, llm, registry, inventory_path, config)
                retries = 0
                delay = config.reconnect_delay
        except Exception:
            retries += 1
            logger.exception(f"WebSocket error ({retries}/{config.max_retries}), reconnecting in {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, config.max_reconnect_delay)

    logger.critical("Max retries exceeded, shutting down")


def main(
    signal_api_url: Annotated[str, typer.Option(envvar="SIGNAL_API_URL")],
    phone_number: Annotated[str, typer.Option(envvar="SIGNAL_PHONE_NUMBER")],
    llm_host: Annotated[str, typer.Option(envvar="LLM_HOST")],
    llm_model: Annotated[str, typer.Option(envvar="LLM_MODEL")] = "qwen3-vl:32b",
    llm_port: Annotated[int, typer.Option(envvar="LLM_PORT")] = 11434,
    inventory_file: Annotated[str, typer.Option(envvar="INVENTORY_FILE")] = "/var/lib/signal-bot/van_inventory.json",
    log_level: Annotated[str, typer.Option()] = "INFO",
) -> None:
    """Run the Signal command and control bot."""
    configure_logger(log_level)

    config = BotConfig(
        signal_api_url=signal_api_url,
        phone_number=phone_number,
        inventory_file=inventory_file,
    )

    engine = get_postgres_engine(name="RICHIE")

    with (
        SignalClient(config.signal_api_url, config.phone_number) as signal,
        LLMClient(model=llm_model, host=llm_host, port=llm_port) as llm,
    ):
        registry = DeviceRegistry(signal, engine)
        run_loop(config, signal, llm, registry)


if __name__ == "__main__":
    typer.run(main)
