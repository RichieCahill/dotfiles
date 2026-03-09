"""Tests for PersonalizedBot3 and PersonalizedBot4 edge cases."""

from __future__ import annotations

import random

from python.splendor.base import (
    BASE_COLORS,
    GEM_COLORS,
    BuyCard,
    Card,
    GameConfig,
    GameState,
    PlayerState,
    ReserveCard,
    TakeDifferent,
    create_random_cards,
    create_random_nobles,
    new_game,
    run_game,
)
from python.splendor.bot import (
    PersonalizedBot2,
    PersonalizedBot3,
    PersonalizedBot4,
    RandomBot,
)


def _make_card(tier: int = 1, points: int = 0, color: str = "white", cost: dict | None = None) -> Card:
    if cost is None:
        cost = dict.fromkeys(GEM_COLORS, 0)
    return Card(tier=tier, points=points, color=color, cost=cost)


def _make_game(bots: list) -> GameState:
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles, turn_limit=100)
    return new_game(bots, config)


def test_personalized_bot3_reserves_from_deck() -> None:
    """Test PersonalizedBot3 reserves from deck when no tokens."""
    random.seed(42)
    bot = PersonalizedBot3("pbot3")
    game = _make_game([bot, RandomBot("r")])
    p = game.players[0]
    p.strategy = bot

    # Clear bank to force reserve
    for c in BASE_COLORS:
        game.bank[c] = 0
    # Clear table to prevent buys
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []

    action = bot.choose_action(game, p)
    assert isinstance(action, (ReserveCard, TakeDifferent))


def test_personalized_bot3_fallback_take_different() -> None:
    """Test PersonalizedBot3 falls back to TakeDifferent."""
    random.seed(42)
    bot = PersonalizedBot3("pbot3")
    game = _make_game([bot, RandomBot("r")])
    p = game.players[0]
    p.strategy = bot

    # Empty everything
    for c in BASE_COLORS:
        game.bank[c] = 0
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []
        game.decks_by_tier[tier] = []

    action = bot.choose_action(game, p)
    assert isinstance(action, TakeDifferent)


def test_personalized_bot4_reserves_from_deck() -> None:
    """Test PersonalizedBot4 reserves from deck."""
    random.seed(42)
    bot = PersonalizedBot4("pbot4")
    game = _make_game([bot, RandomBot("r")])
    p = game.players[0]
    p.strategy = bot

    for c in BASE_COLORS:
        game.bank[c] = 0
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []

    action = bot.choose_action(game, p)
    assert isinstance(action, (ReserveCard, TakeDifferent))


def test_personalized_bot4_fallback() -> None:
    """Test PersonalizedBot4 fallback with empty everything."""
    random.seed(42)
    bot = PersonalizedBot4("pbot4")
    game = _make_game([bot, RandomBot("r")])
    p = game.players[0]
    p.strategy = bot

    for c in BASE_COLORS:
        game.bank[c] = 0
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []
        game.decks_by_tier[tier] = []

    action = bot.choose_action(game, p)
    assert isinstance(action, TakeDifferent)


def test_personalized_bot2_fallback_empty_colors() -> None:
    """Test PersonalizedBot2 with very few available colors."""
    random.seed(42)
    bot = PersonalizedBot2("pbot2")
    game = _make_game([bot, RandomBot("r")])
    p = game.players[0]
    p.strategy = bot

    # No table cards, no affordable reserved
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []
    # Set exactly 2 colors
    for c in BASE_COLORS:
        game.bank[c] = 0
    game.bank["white"] = 1
    game.bank["blue"] = 1

    action = bot.choose_action(game, p)
    assert action is not None


def test_full_game_with_bot3_and_bot4() -> None:
    """Test a full game with bot3 and bot4."""
    random.seed(42)
    bots = [PersonalizedBot3("b3"), PersonalizedBot4("b4")]
    game = _make_game(bots)
    winner, turns = run_game(game)
    assert winner is not None
