import logging
import sys


def configure_logger(level: str = "INFO", test: str = None) -> None:
    """Configure the logger.
    Args:
        level (str, optional): The logging level. Defaults to "INFO".
    """
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s"
        f" {test}",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
