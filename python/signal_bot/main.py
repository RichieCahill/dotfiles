"""Signal command and control bot — main entry point."""

from __future__ import annotations

import logging
from os import getenv
from typing import Annotated

import typer
from sqlalchemy.orm import Session
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from python.common import configure_logger, utcnow
from python.orm.common import get_postgres_engine
from python.orm.richie.dead_letter_message import DeadLetterMessage
from python.signal_bot.commands.inventory import handle_inventory_update
from python.signal_bot.commands.location import handle_location_request
from python.signal_bot.device_registry import DeviceRegistry
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.models import BotConfig, MessageStatus, SignalMessage
from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)


HELP_TEXT = (
    "Available commands:\n"
    "  inventory <text list>  — update van inventory from a text list\n"
    "  inventory (+ photo)    — update van inventory from a receipt photo\n"
    "  status                 — show bot status\n"
    "  location               — get current van location\n"
    "  help                   — show this help message\n"
    "Send a receipt photo with the message 'inventory' to scan it.\n"
)


def help_action(
    signal: SignalClient,
    message: SignalMessage,
    _llm: LLMClient,
    _registry: DeviceRegistry,
    _config: BotConfig,
    _cmd: str,
) -> None:
    """Return the help text for the bot."""
    signal.reply(message, HELP_TEXT)


def status_action(
    signal: SignalClient,
    message: SignalMessage,
    llm: LLMClient,
    registry: DeviceRegistry,
    _config: BotConfig,
    _cmd: str,
) -> None:
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
    _config: BotConfig,
    cmd: str,
) -> None:
    """Return an error message for an unknown command."""
    signal.reply(message, f"Unknown command: {cmd}\n\n{HELP_TEXT}")


def inventory_action(
    signal: SignalClient,
    message: SignalMessage,
    llm: LLMClient,
    _registry: DeviceRegistry,
    config: BotConfig,
    _cmd: str,
) -> None:
    """Process an inventory update."""
    handle_inventory_update(message, signal, llm, config.inventory_api_url)


def location_action(
    signal: SignalClient,
    message: SignalMessage,
    _llm: LLMClient,
    _registry: DeviceRegistry,
    config: BotConfig,
    _cmd: str,
) -> None:
    """Reply with current van location."""
    handle_location_request(message, signal, config.ha_url, config.ha_token, config.ha_location_entity)


def dispatch(
    message: SignalMessage,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
    config: BotConfig,
) -> None:
    """Route an incoming message to the right command handler."""
    source = message.source

    if not registry.is_verified(source) or not registry.has_safety_number(source):
        logger.info(f"Device {source} not verified, ignoring message")
        return

    text = message.message.strip()
    parts = text.split()

    if not parts and not message.attachments:
        return

    cmd = parts[0].lower() if parts else ""

    commands = {
        "help": help_action,
        "status": status_action,
        "inventory": inventory_action,
        "location": location_action,
    }
    logger.info(f"f{source=} running {cmd=} with {message=}")
    action = commands.get(cmd)
    if action is None:
        if message.attachments:
            action = inventory_action
            cmd = "inventory"
        else:
            return

    action(signal, message, llm, registry, config, cmd)


def _process_message(
    message: SignalMessage,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
    config: BotConfig,
) -> None:
    """Process a single message, sending it to the dead letter queue after repeated failures."""
    max_attempts = config.max_message_attempts
    for attempt in range(1, max_attempts + 1):
        try:
            safety_number = signal.get_safety_number(message.source)
            registry.record_contact(message.source, safety_number)
            dispatch(message, signal, llm, registry, config)
        except Exception:
            logger.exception(f"Failed to process message (attempt {attempt}/{max_attempts})")
        else:
            return

    logger.error(f"Message from {message.source} failed {max_attempts} times, sending to dead letter queue")
    with Session(config.engine) as session:
        session.add(
            DeadLetterMessage(
                source=message.source,
                message=message.message,
                received_at=utcnow(),
                status=MessageStatus.UNPROCESSED,
            )
        )
        session.commit()


def run_loop(
    config: BotConfig,
    signal: SignalClient,
    llm: LLMClient,
    registry: DeviceRegistry,
) -> None:
    """Listen for messages via WebSocket, reconnecting on failure."""
    logger.info("Bot started — listening via WebSocket")

    @retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=config.reconnect_delay, max=config.max_reconnect_delay),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _listen() -> None:
        for message in signal.listen():
            logger.info(f"Message from {message.source}: {message.message[:80]}")
            _process_message(message, signal, llm, registry, config)

    try:
        _listen()
    except Exception:
        logger.critical("Max retries exceeded, shutting down")
        raise


def main(
    log_level: Annotated[str, typer.Option()] = "INFO",
    llm_timeout: Annotated[int, typer.Option()] = 600,
) -> None:
    """Run the Signal command and control bot."""
    configure_logger(log_level)
    signal_api_url = getenv("SIGNAL_API_URL")
    phone_number = getenv("SIGNAL_PHONE_NUMBER")
    inventory_api_url = getenv("INVENTORY_API_URL")

    if signal_api_url is None:
        error = "SIGNAL_API_URL environment variable not set"
        raise ValueError(error)
    if phone_number is None:
        error = "SIGNAL_PHONE_NUMBER environment variable not set"
        raise ValueError(error)
    if inventory_api_url is None:
        error = "INVENTORY_API_URL environment variable not set"
        raise ValueError(error)

    engine = get_postgres_engine(name="SIGNALBOT")
    config = BotConfig(
        signal_api_url=signal_api_url,
        phone_number=phone_number,
        inventory_api_url=inventory_api_url,
        ha_url=getenv("HA_URL"),
        ha_token=getenv("HA_TOKEN"),
        ha_location_entity=getenv("HA_LOCATION_ENTITY", "sensor.gps_location"),
        engine=engine,
    )

    llm_host = getenv("LLM_HOST")
    llm_model = getenv("LLM_MODEL", "qwen3-vl:32b")
    llm_port = int(getenv("LLM_PORT", "11434"))
    if llm_host is None:
        error = "LLM_HOST environment variable not set"
        raise ValueError(error)

    with (
        SignalClient(config.signal_api_url, config.phone_number) as signal,
        LLMClient(model=llm_model, host=llm_host, port=llm_port, timeout=llm_timeout) as llm,
    ):
        registry = DeviceRegistry(signal, engine)
        run_loop(config, signal, llm, registry)


if __name__ == "__main__":
    typer.run(main)
