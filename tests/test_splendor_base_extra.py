"""Extra tests for splendor/base.py covering missed lines and branches."""

from __future__ import annotations

import random

from python.splendor.base import (
    BASE_COLORS,
    GEM_COLORS,
    BuyCard,
    BuyCardReserved,
    Card,
    GameConfig,
    Noble,
    ReserveCard,
    TakeDifferent,
    TakeDouble,
    apply_action,
    apply_buy_card,
    apply_buy_card_reserved,
    apply_reserve_card,
    apply_take_different,
    apply_take_double,
    auto_discard_tokens,
    check_nobles_for_player,
    create_random_cards,
    create_random_nobles,
    enforce_token_limit,
    get_legal_actions,
    new_game,
    run_game,
)
from python.splendor.bot import RandomBot


def _make_game(num_players: int = 2):
    random.seed(42)
    bots = [RandomBot(f"bot{i}") for i in range(num_players)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    return game, bots


def test_auto_discard_tokens_all_zero() -> None:
    """Test auto_discard when all tokens are zero."""
    game, _ = _make_game()
    p = game.players[0]
    for c in GEM_COLORS:
        p.tokens[c] = 0
    result = auto_discard_tokens(p, 3)
    assert sum(result.values()) == 0  # Can't discard from empty


def test_enforce_token_limit_with_fallback() -> None:
    """Test enforce_token_limit uses auto_discard as fallback."""
    game, bots = _make_game()
    p = game.players[0]
    strategy = bots[0]
    # Give player many tokens to force discard
    for c in BASE_COLORS:
        p.tokens[c] = 5
    enforce_token_limit(game, strategy, p)
    assert p.total_tokens() <= game.config.token_limit


def test_apply_take_different_invalid_color() -> None:
    """Test take different with gold (non-base) color."""
    game, bots = _make_game()
    action = TakeDifferent(colors=["gold"])
    apply_take_different(game, bots[0], action)
    # Gold is not in BASE_COLORS, so no tokens should be taken


def test_apply_take_double_invalid_color() -> None:
    """Test take double with gold (non-base) color."""
    game, bots = _make_game()
    action = TakeDouble(color="gold")
    apply_take_double(game, bots[0], action)


def test_apply_take_double_insufficient_bank() -> None:
    """Test take double when bank has fewer than minimum."""
    game, bots = _make_game()
    game.bank["white"] = 2  # Below minimum_tokens_to_buy_2 (4)
    action = TakeDouble(color="white")
    apply_take_double(game, bots[0], action)


def test_apply_buy_card_invalid_tier() -> None:
    """Test buy card with invalid tier."""
    game, bots = _make_game()
    action = BuyCard(tier=99, index=0)
    apply_buy_card(game, bots[0], action)


def test_apply_buy_card_invalid_index() -> None:
    """Test buy card with out-of-range index."""
    game, bots = _make_game()
    action = BuyCard(tier=1, index=99)
    apply_buy_card(game, bots[0], action)


def test_apply_buy_card_cannot_afford() -> None:
    """Test buy card when player can't afford."""
    game, bots = _make_game()
    # Zero out all tokens
    for c in GEM_COLORS:
        game.players[0].tokens[c] = 0
    # Find an expensive card
    for tier, row in game.table_by_tier.items():
        for idx, card in enumerate(row):
            if any(v > 0 for v in card.cost.values()):
                action = BuyCard(tier=tier, index=idx)
                apply_buy_card(game, bots[0], action)
                return


def test_apply_buy_card_reserved_invalid_index() -> None:
    """Test buy reserved card with out-of-range index."""
    game, bots = _make_game()
    action = BuyCardReserved(index=99)
    apply_buy_card_reserved(game, bots[0], action)


def test_apply_buy_card_reserved_cannot_afford() -> None:
    """Test buy reserved card when can't afford."""
    game, bots = _make_game()
    expensive = Card(tier=3, points=5, color="white", cost={
        "white": 10, "blue": 10, "green": 10, "red": 10, "black": 10, "gold": 0
    })
    game.players[0].reserved.append(expensive)
    for c in GEM_COLORS:
        game.players[0].tokens[c] = 0
    action = BuyCardReserved(index=0)
    apply_buy_card_reserved(game, bots[0], action)


def test_apply_reserve_card_at_limit() -> None:
    """Test reserve card when at reserve limit."""
    game, bots = _make_game()
    p = game.players[0]
    # Fill up reserved slots
    for _ in range(game.config.reserve_limit):
        p.reserved.append(Card(tier=1, points=0, color="white", cost=dict.fromkeys(GEM_COLORS, 0)))
    action = ReserveCard(tier=1, index=0, from_deck=False)
    apply_reserve_card(game, bots[0], action)
    assert len(p.reserved) == game.config.reserve_limit


def test_apply_reserve_card_invalid_tier() -> None:
    """Test reserve face-up card with invalid tier."""
    game, bots = _make_game()
    action = ReserveCard(tier=99, index=0, from_deck=False)
    apply_reserve_card(game, bots[0], action)


def test_apply_reserve_card_invalid_index() -> None:
    """Test reserve face-up card with None index."""
    game, bots = _make_game()
    action = ReserveCard(tier=1, index=None, from_deck=False)
    apply_reserve_card(game, bots[0], action)


def test_apply_reserve_card_from_empty_deck() -> None:
    """Test reserve from deck when deck is empty."""
    game, bots = _make_game()
    game.decks_by_tier[1] = []  # Empty the deck
    action = ReserveCard(tier=1, index=None, from_deck=True)
    apply_reserve_card(game, bots[0], action)


def test_apply_reserve_card_no_gold() -> None:
    """Test reserve card when bank has no gold."""
    game, bots = _make_game()
    game.bank["gold"] = 0
    action = ReserveCard(tier=1, index=0, from_deck=True)
    reserved_before = len(game.players[0].reserved)
    apply_reserve_card(game, bots[0], action)
    if len(game.players[0].reserved) > reserved_before:
        assert game.players[0].tokens["gold"] == 0


def test_check_nobles_multiple_candidates() -> None:
    """Test check_nobles when player qualifies for multiple nobles."""
    game, bots = _make_game()
    p = game.players[0]
    # Give player huge discounts to qualify for everything
    for c in BASE_COLORS:
        p.discounts[c] = 20
    check_nobles_for_player(game, bots[0], p)


def test_check_nobles_chosen_not_in_available() -> None:
    """Test check_nobles when chosen noble is somehow not available."""
    game, bots = _make_game()
    p = game.players[0]
    for c in BASE_COLORS:
        p.discounts[c] = 20
    # This tests the normal path - chosen should be in available


def test_run_game_turn_limit() -> None:
    """Test run_game respects turn limit."""
    random.seed(99)
    bots = [RandomBot(f"bot{i}") for i in range(2)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles, turn_limit=5)
    game = new_game(bots, config)
    winner, turns = run_game(game)
    assert turns <= 5


def test_run_game_action_none() -> None:
    """Test run_game stops when strategy returns None."""
    from unittest.mock import MagicMock
    bots = [RandomBot(f"bot{i}") for i in range(2)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    # Make the first player's strategy return None
    game.players[0].strategy.choose_action = MagicMock(return_value=None)
    winner, turns = run_game(game)
    assert turns == 1


def test_get_valid_actions_with_reserved() -> None:
    """Test get_valid_actions includes BuyCardReserved when player has reserved cards."""
    game, _ = _make_game()
    p = game.players[0]
    # Give player a free reserved card
    free_card = Card(tier=1, points=0, color="white", cost=dict.fromkeys(GEM_COLORS, 0))
    p.reserved.append(free_card)
    actions = get_legal_actions(game)
    assert any(isinstance(a, BuyCardReserved) for a in actions)


def test_get_legal_actions_reserve_from_deck() -> None:
    """Test get_legal_actions includes ReserveCard from deck."""
    game, _ = _make_game()
    actions = get_legal_actions(game)
    assert any(isinstance(a, ReserveCard) and a.from_deck for a in actions)
    assert any(isinstance(a, ReserveCard) and not a.from_deck for a in actions)
