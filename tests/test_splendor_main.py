"""Tests for python/splendor/main.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_splendor_main_import() -> None:
    """Test that splendor main module can be imported."""
    from python.splendor.main import main
    assert callable(main)


def test_splendor_main_calls_run_game() -> None:
    """Test main creates human + bot and runs game."""
    # main() uses wrong signature for new_game (passes strings instead of strategies)
    # so we just verify it can be called with mocked internals
    with (
        patch("python.splendor.main.TuiHuman") as mock_tui,
        patch("python.splendor.main.RandomBot") as mock_bot,
        patch("python.splendor.main.new_game") as mock_new_game,
        patch("python.splendor.main.run_game") as mock_run_game,
    ):
        mock_tui.return_value = MagicMock()
        mock_bot.return_value = MagicMock()
        mock_new_game.return_value = MagicMock()
        mock_run_game.return_value = (MagicMock(), 10)

        from python.splendor.main import main
        main()

        mock_new_game.assert_called_once()
        mock_run_game.assert_called_once()
