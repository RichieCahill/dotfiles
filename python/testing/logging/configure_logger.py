"""configure_logger."""

import logging
import sys


def configure_logger(level: str = "INFO", test: str | None = None) -> None:
    """Configure the logger.

    Args:
        level (str, optional): The logging level. Defaults to "INFO".
        test (str | None, optional): The test name. Defaults to None.
    """
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s"  # this is nesiseary
        f" {test}",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
