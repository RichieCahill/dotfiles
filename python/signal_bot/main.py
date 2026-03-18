"""Signal command and control bot — main entry point."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from os import getenv
from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from collections.abc import Callable

import typer
from alembic.command import upgrade
from sqlalchemy.orm import Session
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from python.common import configure_logger, utcnow
from python.database_cli import DATABASES
from python.orm.common import get_postgres_engine
from python.orm.signal_bot.models import DeadLetterMessage
from python.signal_bot.commands.inventory import handle_inventory_update
from python.signal_bot.commands.location import handle_location_request
from python.signal_bot.device_registry import DeviceRegistry, sync_roles
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.models import BotConfig, MessageStatus, Role, SignalMessage
from python.signal_bot.signal_client import SignalClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Command:
    """A registered bot command."""

    action: Callable[[SignalMessage, str], None]
    help_text: str
    role: Role | None  # None = no role required (always allowed)


class Bot:
    """Holds shared resources and dispatches incoming messages to command handlers."""

    def __init__(
        self,
        signal: SignalClient,
        llm: LLMClient,
        registry: DeviceRegistry,
        config: BotConfig,
    ) -> None:
        self.signal = signal
        self.llm = llm
        self.registry = registry
        self.config = config
        self.commands: dict[str, Command] = {
            "help": Command(action=self._help, help_text="show this help message", role=None),
            "status": Command(action=self._status, help_text="show bot status", role=Role.STATUS),
            "inventory": Command(
                action=self._inventory,
                help_text="update van inventory from a text list or receipt photo",
                role=Role.INVENTORY,
            ),
            "location": Command(
                action=self._location,
                help_text="get current van location",
                role=Role.LOCATION,
            ),
        }

    # -- actions --------------------------------------------------------------

    def _help(self, message: SignalMessage, _cmd: str) -> None:
        """Return help text filtered to the sender's roles."""
        self.signal.reply(message, self._build_help(self.registry.get_roles(message.source)))

    def _status(self, message: SignalMessage, _cmd: str) -> None:
        """Return the status of the bot."""
        models = self.llm.list_models()
        model_list = ", ".join(models[:10])
        device_count = len(self.registry.list_devices())
        self.signal.reply(
            message,
            f"Bot online.\nLLM: {self.llm.model}\nAvailable models: {model_list}\nKnown devices: {device_count}",
        )

    def _inventory(self, message: SignalMessage, _cmd: str) -> None:
        """Process an inventory update."""
        handle_inventory_update(message, self.signal, self.llm, self.config.inventory_api_url)

    def _location(self, message: SignalMessage, _cmd: str) -> None:
        """Reply with current van location."""
        handle_location_request(message, self.signal, self.config.ha_url, self.config.ha_token)

    # -- dispatch -------------------------------------------------------------

    def _build_help(self, roles: list[Role]) -> str:
        """Build help text showing only the commands the user can access."""
        is_admin = Role.ADMIN in roles
        lines = ["Available commands:"]
        for name, cmd in self.commands.items():
            if cmd.role is None or is_admin or cmd.role in roles:
                lines.append(f"  {name:20s} — {cmd.help_text}")
        return "\n".join(lines)

    def dispatch(self, message: SignalMessage) -> None:
        """Route an incoming message to the right command handler."""
        source = message.source

        if not self.registry.is_verified(source):
            logger.info(f"Device {source} not verified, ignoring message")
            return

        if not self.registry.has_safety_number(source) and self.registry.has_role(source, Role.ADMIN):
            logger.warning(f"Admin device {source} missing safety number, ignoring message")
            return

        text = message.message.strip()
        parts = text.split()

        if not parts and not message.attachments:
            return

        cmd = parts[0].lower() if parts else ""

        logger.info(f"f{source=} running {cmd=} with {message=}")

        command = self.commands.get(cmd)
        if command is None:
            if message.attachments:
                command = self.commands["inventory"]
                cmd = "inventory"
            else:
                return

        if command.role is not None and not self.registry.has_role(source, command.role):
            logger.warning(f"Device {source} denied access to {cmd!r}")
            self.signal.reply(message, f"Permission denied: you do not have the '{command.role}' role.")
            return

        command.action(message, cmd)

    def process_message(self, message: SignalMessage) -> None:
        """Process a single message, sending it to the dead letter queue after repeated failures."""
        max_attempts = self.config.max_message_attempts
        for attempt in range(1, max_attempts + 1):
            try:
                safety_number = self.signal.get_safety_number(message.source)
                self.registry.record_contact(message.source, safety_number)
                self.dispatch(message)
            except Exception:
                logger.exception(f"Failed to process message (attempt {attempt}/{max_attempts})")
            else:
                return

        logger.error(f"Message from {message.source} failed {max_attempts} times, sending to dead letter queue")
        with Session(self.config.engine) as session:
            session.add(
                DeadLetterMessage(
                    source=message.source,
                    message=message.message,
                    received_at=utcnow(),
                    status=MessageStatus.UNPROCESSED,
                )
            )
            session.commit()

    def run(self) -> None:
        """Listen for messages via WebSocket, reconnecting on failure."""
        logger.info("Bot started — listening via WebSocket")

        @retry(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(multiplier=self.config.reconnect_delay, max=self.config.max_reconnect_delay),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def _listen() -> None:
            for message in self.signal.listen():
                logger.info(f"Message from {message.source}: {message.message[:80]}")
                self.process_message(message)

        try:
            _listen()
        except Exception:
            logger.critical("Max retries exceeded, shutting down")
            raise


def main(
    log_level: Annotated[str, typer.Option()] = "DEBUG",
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

    signal_bot_config = DATABASES["signal_bot"].alembic_config()
    upgrade(signal_bot_config, "head")
    engine = get_postgres_engine(name="SIGNALBOT")
    sync_roles(engine)
    config = BotConfig(
        signal_api_url=signal_api_url,
        phone_number=phone_number,
        inventory_api_url=inventory_api_url,
        ha_url=getenv("HA_URL"),
        ha_token=getenv("HA_TOKEN"),
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
        bot = Bot(signal, llm, registry, config)
        bot.run()


if __name__ == "__main__":
    typer.run(main)
