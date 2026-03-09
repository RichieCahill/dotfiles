"""Tests for capasitor main function."""

from __future__ import annotations

from python.stuff.capasitor import main


def test_capasitor_main(capsys: object) -> None:
    """Test capasitor main function runs."""
    main()
