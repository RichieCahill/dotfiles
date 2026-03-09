"""Tests for python/testing/logging modules."""

from __future__ import annotations

from python.testing.logging.bar import bar
from python.testing.logging.configure_logger import configure_logger
from python.testing.logging.foo import foo
from python.testing.logging.main import main


def test_bar() -> None:
    """Test bar function."""
    bar()


def test_configure_logger_default() -> None:
    """Test configure_logger with default level."""
    configure_logger()


def test_configure_logger_debug() -> None:
    """Test configure_logger with debug level."""
    configure_logger("DEBUG")


def test_configure_logger_with_test() -> None:
    """Test configure_logger with test name."""
    configure_logger("INFO", "TEST")


def test_foo() -> None:
    """Test foo function."""
    foo()


def test_main() -> None:
    """Test main function."""
    main()
