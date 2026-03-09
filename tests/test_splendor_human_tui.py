"""Tests for python/splendor/human.py TUI classes."""

from __future__ import annotations

import random

from python.splendor.base import (
    GEM_COLORS,
    GameConfig,
    PlayerState,
    create_random_cards,
    create_random_nobles,
    new_game,
)
from python.splendor.bot import RandomBot
from python.splendor.human import TuiHuman


def _make_game(num_players: int = 2):
    bots = [RandomBot(f"bot{i}") for i in range(num_players)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    return game, bots


def test_tui_human_choose_action_no_tty() -> None:
    """Test TuiHuman returns None when not a TTY."""
    random.seed(42)
    game, _ = _make_game(2)
    human = TuiHuman("test")
    # In test environment, stdout is not a TTY
    result = human.choose_action(game, game.players[0])
    assert result is None


def test_tui_human_choose_discard_no_tty() -> None:
    """Test TuiHuman returns empty discards when not a TTY."""
    random.seed(42)
    game, _ = _make_game(2)
    human = TuiHuman("test")
    result = human.choose_discard(game, game.players[0], 2)
    assert result == dict.fromkeys(GEM_COLORS, 0)


def test_tui_human_choose_noble_no_tty() -> None:
    """Test TuiHuman returns first noble when not a TTY."""
    random.seed(42)
    game, _ = _make_game(2)
    human = TuiHuman("test")
    nobles = game.available_nobles[:2]
    result = human.choose_noble(game, game.players[0], nobles)
    assert result == nobles[0]
