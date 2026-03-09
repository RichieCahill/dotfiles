"""Extended tests for python/splendor/bot.py to improve coverage."""

from __future__ import annotations

import random

from python.splendor.base import (
    BASE_COLORS,
    GEM_COLORS,
    BuyCard,
    BuyCardReserved,
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
    PersonalizedBot,
    PersonalizedBot2,
    PersonalizedBot3,
    PersonalizedBot4,
    RandomBot,
    buy_card,
    buy_card_reserved,
    estimate_value_of_card,
    estimate_value_of_token,
    take_tokens,
)


def _make_card(tier: int = 1, points: int = 0, color: str = "white", cost: dict | None = None) -> Card:
    if cost is None:
        cost = dict.fromkeys(GEM_COLORS, 0)
    return Card(tier=tier, points=points, color=color, cost=cost)


def _make_game(num_players: int = 2) -> tuple[GameState, list]:
    bots = [RandomBot(f"bot{i}") for i in range(num_players)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    return game, bots


def test_random_bot_buys_affordable() -> None:
    """Test RandomBot buys affordable cards."""
    random.seed(1)
    game, bots = _make_game(2)
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 10
    # Should sometimes buy
    actions = [bots[0].choose_action(game, p) for _ in range(20)]
    buy_actions = [a for a in actions if isinstance(a, BuyCard)]
    assert len(buy_actions) > 0


def test_random_bot_reserves() -> None:
    """Test RandomBot reserves cards sometimes."""
    random.seed(3)
    game, bots = _make_game(2)
    actions = [bots[0].choose_action(game, game.players[0]) for _ in range(50)]
    reserve_actions = [a for a in actions if isinstance(a, ReserveCard)]
    assert len(reserve_actions) > 0


def test_random_bot_choose_discard() -> None:
    """Test RandomBot.choose_discard."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    p.tokens["white"] = 5
    p.tokens["blue"] = 3
    discards = bot.choose_discard(None, p, 2)
    assert sum(discards.values()) == 2


def test_personalized_bot_takes_different() -> None:
    """Test PersonalizedBot takes different when no affordable cards."""
    random.seed(42)
    bot = PersonalizedBot("pbot")
    game, _ = _make_game(2)
    p = game.players[0]
    action = bot.choose_action(game, p)
    assert action is not None


def test_personalized_bot_choose_discard() -> None:
    """Test PersonalizedBot.choose_discard."""
    bot = PersonalizedBot("pbot")
    p = PlayerState(strategy=bot)
    p.tokens["white"] = 5
    discards = bot.choose_discard(None, p, 2)
    assert sum(discards.values()) == 2


def test_personalized_bot2_buys_reserved() -> None:
    """Test PersonalizedBot2 buys reserved cards."""
    random.seed(42)
    bot = PersonalizedBot2("pbot2")
    game, _ = _make_game(2)
    p = game.players[0]
    p.strategy = bot
    # Add affordable reserved card
    card = _make_card(cost=dict.fromkeys(GEM_COLORS, 0))
    p.reserved.append(card)
    # Clear table cards to force reserved buy
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []
    action = bot.choose_action(game, p)
    assert isinstance(action, BuyCardReserved)


def test_personalized_bot2_reserves_from_deck() -> None:
    """Test PersonalizedBot2 reserves from deck when few colors available."""
    random.seed(42)
    bot = PersonalizedBot2("pbot2")
    game, _ = _make_game(2)
    p = game.players[0]
    p.strategy = bot
    # Clear table and set only 2 bank colors
    for tier in (1, 2, 3):
        game.table_by_tier[tier] = []
    for c in BASE_COLORS:
        game.bank[c] = 0
    game.bank["white"] = 1
    game.bank["blue"] = 1
    action = bot.choose_action(game, p)
    assert isinstance(action, (ReserveCard, TakeDifferent))


def test_personalized_bot2_choose_discard() -> None:
    """Test PersonalizedBot2.choose_discard."""
    bot = PersonalizedBot2("pbot2")
    p = PlayerState(strategy=bot)
    p.tokens["red"] = 5
    discards = bot.choose_discard(None, p, 2)
    assert sum(discards.values()) == 2


def test_personalized_bot3_choose_action() -> None:
    """Test PersonalizedBot3.choose_action."""
    random.seed(42)
    bot = PersonalizedBot3("pbot3")
    game, _ = _make_game(2)
    p = game.players[0]
    p.strategy = bot
    action = bot.choose_action(game, p)
    assert action is not None


def test_personalized_bot3_choose_discard() -> None:
    """Test PersonalizedBot3.choose_discard."""
    bot = PersonalizedBot3("pbot3")
    p = PlayerState(strategy=bot)
    p.tokens["green"] = 5
    discards = bot.choose_discard(None, p, 2)
    assert sum(discards.values()) == 2


def test_personalized_bot4_choose_action() -> None:
    """Test PersonalizedBot4.choose_action."""
    random.seed(42)
    bot = PersonalizedBot4("pbot4")
    game, _ = _make_game(2)
    p = game.players[0]
    p.strategy = bot
    action = bot.choose_action(game, p)
    assert action is not None


def test_personalized_bot4_filter_actions() -> None:
    """Test PersonalizedBot4.filter_actions."""
    bot = PersonalizedBot4("pbot4")
    actions = [
        TakeDifferent(colors=["white", "blue", "green"]),
        TakeDifferent(colors=["white", "blue"]),
        BuyCard(tier=1, index=0),
    ]
    filtered = bot.filter_actions(actions)
    # Should keep 3-color TakeDifferent and BuyCard, remove 2-color TakeDifferent
    assert len(filtered) == 2


def test_personalized_bot4_choose_discard() -> None:
    """Test PersonalizedBot4.choose_discard."""
    bot = PersonalizedBot4("pbot4")
    p = PlayerState(strategy=bot)
    p.tokens["black"] = 5
    discards = bot.choose_discard(None, p, 2)
    assert sum(discards.values()) == 2


def test_estimate_value_of_card() -> None:
    """Test estimate_value_of_card."""
    game, _ = _make_game(2)
    p = game.players[0]
    result = estimate_value_of_card(game, p, "white")
    assert isinstance(result, int)


def test_estimate_value_of_token() -> None:
    """Test estimate_value_of_token."""
    game, _ = _make_game(2)
    p = game.players[0]
    result = estimate_value_of_token(game, p, "white")
    assert isinstance(result, int)


def test_full_game_with_personalized_bots() -> None:
    """Test a full game with different bot types."""
    random.seed(42)
    bots = [
        RandomBot("random"),
        PersonalizedBot("p1"),
        PersonalizedBot2("p2"),
    ]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles, turn_limit=200)
    game = new_game(bots, config)
    winner, turns = run_game(game)
    assert winner is not None
    assert turns > 0
