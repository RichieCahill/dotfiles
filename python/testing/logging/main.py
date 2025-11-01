"""main."""

import logging

from python.testing.logging.bar import bar
from python.testing.logging.configure_logger import configure_logger
from python.testing.logging.foo import foo

logger = logging.getLogger(__name__)


def main() -> None:
    """Main."""
    configure_logger("DEBUG")
    # handler = logging.StreamHandler()

    # Create and attach a formatter
    # formatter = logging.Formatter(
    #     "%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s FOO"
    # )
    # handler.setFormatter(formatter)

    # Attach handler to logger
    # foo_logger = logging.getLogger("python.testing.logging.foo")
    # foo_logger.addHandler(handler)
    # foo_logger.propagate = True
    logger.debug("main")
    foo()
    bar()


if __name__ == "__main__":
    main()
