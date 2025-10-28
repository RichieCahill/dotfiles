"""common."""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from os import getenv
from subprocess import PIPE, Popen

from apprise import Apprise

logger = logging.getLogger(__name__)


def configure_logger(level: str = "INFO") -> None:
    """Configure the logger.

    Args:
        level (str, optional): The logging level. Defaults to "INFO".
    """
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def bash_wrapper(command: str) -> tuple[str, int]:
    """Execute a bash command and capture the output.

    Args:
        command (str): The bash command to be executed.

    Returns:
        Tuple[str, int]: A tuple containing the output of the command (stdout) as a string,
        the error output (stderr) as a string (optional), and the return code as an integer.
    """
    # This is a acceptable risk
    process = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    output, error = process.communicate()
    if error:
        logger.error(f"{error=}")
        return error.decode(), process.returncode

    return output.decode(), process.returncode


def signal_alert(body: str, title: str = "") -> None:
    """Send a signal alert.

    Args:
        body (str): The body of the alert.
        title (str, optional): The title of the alert. Defaults to "".
    """
    apprise_client = Apprise()

    from_phone = getenv("SIGNAL_ALERT_FROM_PHONE")
    to_phone = getenv("SIGNAL_ALERT_TO_PHONE")
    if not from_phone or not to_phone:
        logger.info("SIGNAL_ALERT_FROM_PHONE or SIGNAL_ALERT_TO_PHONE not set")
        return

    apprise_client.add(f"signal://localhost:8989/{from_phone}/{to_phone}")

    apprise_client.notify(title=title, body=body)


def utcnow() -> datetime:
    """Get the current UTC time."""
    return datetime.now(tz=UTC)
