"""foo"""

import logging

from python.testing.logging.bar import bar
from python.testing.logging.configure_logger import configure_logger

logger = logging.getLogger(__name__)


def foo() -> None:
    """Foo."""

    configure_logger("DEBUG", "FOO")
    logger.debug(f"foo {__name__}")
    logger.debug("foo")

    bar()
