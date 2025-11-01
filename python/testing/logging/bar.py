"""Bar."""

import logging

logger = logging.getLogger(__name__)


def bar() -> None:
    """Bar."""
    logger.debug(f"bar {__name__}")
    logger.debug("bar")
