"""Validate {server_name}."""

import logging
import sys
import tomllib
from os import environ
from pathlib import Path
from socket import gethostname

import typer

from python.common import configure_logger, signal_alert
from python.system_tests.components import systemd_tests, zpool_tests

logger = logging.getLogger(__name__)


def load_config_data(config_file: Path) -> dict[str, list[str]]:
    """Load a TOML configuration file.

    Args:
        config_file (Path): The path to the configuration file.

    Returns:
        dict: The configuration data.
    """
    return tomllib.loads(config_file.read_text())


def main(config_file: Path) -> None:
    """Main."""
    configure_logger(level=environ.get("LOG_LEVEL", "INFO"))

    server_name = gethostname()
    logger.info(f"Starting {server_name} validation")

    config_data = load_config_data(config_file)

    errors: list[str] = []
    try:
        if config_data.get("zpools") and (zpool_errors := zpool_tests(config_data["zpools"])):
            errors.extend(zpool_errors)

        if config_data.get("services") and (systemd_errors := systemd_tests(config_data["services"])):
            errors.extend(systemd_errors)

    except Exception as error:
        logger.exception(f"{server_name} validation failed")
        errors.append(f"{server_name} validation failed: {error}")

    if errors:
        logger.error(f"{server_name} validation failed: \n{'\n'.join(errors)}")
        signal_alert(f"{server_name} validation failed {errors}")

        sys.exit(1)

    logger.info(f"{server_name} validation passed")


def cli() -> None:
    """CLI."""
    typer.run(main)


if __name__ == "__main__":
    cli()
