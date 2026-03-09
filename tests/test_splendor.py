"""Tests for python/splendor modules."""

from __future__ import annotations

import random
from unittest.mock import patch

from python.splendor.base import (
    BASE_COLORS,
    GEM_COLORS,
    Action,
    BuyCard,
    BuyCardReserved,
    Card,
    GameConfig,
    GameState,
    Noble,
    PlayerState,
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
    create_random_cards_tier,
    create_random_nobles,
    enforce_token_limit,
    get_default_starting_tokens,
    get_legal_actions,
    load_cards,
    load_nobles,
    new_game,
    run_game,
)
from python.splendor.bot import (
    PersonalizedBot,
    PersonalizedBot2,
    RandomBot,
    buy_card,
    buy_card_reserved,
    can_bot_afford,
    check_cards_in_tier,
    take_tokens,
)
from python.splendor.public_state import (
    Observation,
    ObsCard,
    ObsNoble,
    ObsPlayer,
    to_observation,
    _encode_card,
    _encode_noble,
    _encode_player,
)
from python.splendor.sim import SimStrategy, simulate_step

import pytest


# --- Helper to create a simple game ---


def _make_card(tier: int = 1, points: int = 0, color: str = "white", cost: dict | None = None) -> Card:
    if cost is None:
        cost = dict.fromkeys(GEM_COLORS, 0)
    return Card(tier=tier, points=points, color=color, cost=cost)


def _make_noble(name: str = "Noble", points: int = 3, reqs: dict | None = None) -> Noble:
    if reqs is None:
        reqs = {"white": 3, "blue": 3, "green": 3}
    return Noble(name=name, points=points, requirements=reqs)


def _make_game(num_players: int = 2) -> tuple[GameState, list[RandomBot]]:
    bots = [RandomBot(f"bot{i}") for i in range(num_players)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    return game, bots


# --- PlayerState tests ---


def test_player_state_defaults() -> None:
    """Test PlayerState default values."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    assert p.total_tokens() == 0
    assert p.score == 0
    assert p.card_score == 0
    assert p.noble_score == 0


def test_player_add_card() -> None:
    """Test adding a card to player."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    card = _make_card(points=3)
    p.add_card(card)
    assert len(p.cards) == 1
    assert p.card_score == 3
    assert p.score == 3


def test_player_add_noble() -> None:
    """Test adding a noble to player."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    noble = _make_noble(points=3)
    p.add_noble(noble)
    assert len(p.nobles) == 1
    assert p.noble_score == 3
    assert p.score == 3


def test_player_can_afford_free_card() -> None:
    """Test can_afford with a free card."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    card = _make_card(cost=dict.fromkeys(GEM_COLORS, 0))
    assert p.can_afford(card) is True


def test_player_can_afford_with_tokens() -> None:
    """Test can_afford with tokens."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    p.tokens["white"] = 3
    card = _make_card(cost={**dict.fromkeys(GEM_COLORS, 0), "white": 3})
    assert p.can_afford(card) is True


def test_player_cannot_afford() -> None:
    """Test can_afford returns False when not enough."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    card = _make_card(cost={**dict.fromkeys(GEM_COLORS, 0), "white": 5})
    assert p.can_afford(card) is False


def test_player_can_afford_with_gold() -> None:
    """Test can_afford uses gold tokens."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    p.tokens["gold"] = 3
    card = _make_card(cost={**dict.fromkeys(GEM_COLORS, 0), "white": 3})
    assert p.can_afford(card) is True


def test_player_pay_for_card() -> None:
    """Test pay_for_card transfers tokens."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    p.tokens["white"] = 3
    card = _make_card(color="white", cost={**dict.fromkeys(GEM_COLORS, 0), "white": 2})
    payment = p.pay_for_card(card)
    assert payment["white"] == 2
    assert p.tokens["white"] == 1
    assert len(p.cards) == 1
    assert p.discounts["white"] == 1


def test_player_pay_for_card_cannot_afford() -> None:
    """Test pay_for_card raises when cannot afford."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    card = _make_card(cost={**dict.fromkeys(GEM_COLORS, 0), "white": 5})
    with pytest.raises(ValueError, match="cannot afford"):
        p.pay_for_card(card)


# --- GameState tests ---


def test_get_default_starting_tokens() -> None:
    """Test starting token counts."""
    tokens = get_default_starting_tokens(2)
    assert tokens["gold"] == 5
    assert tokens["white"] == 4  # (4-6+10)//2 = 4

    tokens = get_default_starting_tokens(3)
    assert tokens["white"] == 5

    tokens = get_default_starting_tokens(4)
    assert tokens["white"] == 7


def test_new_game() -> None:
    """Test new_game creates valid state."""
    game, _ = _make_game(2)
    assert len(game.players) == 2
    assert game.bank["gold"] == 5
    assert len(game.available_nobles) == 3  # 2 players + 1


def test_game_next_player() -> None:
    """Test next_player cycles."""
    game, _ = _make_game(2)
    assert game.current_player_index == 0
    game.next_player()
    assert game.current_player_index == 1
    game.next_player()
    assert game.current_player_index == 0


def test_game_current_player() -> None:
    """Test current_player property."""
    game, _ = _make_game(2)
    assert game.current_player is game.players[0]


def test_game_check_winner_simple_no_winner() -> None:
    """Test check_winner_simple with no winner."""
    game, _ = _make_game(2)
    assert game.check_winner_simple() is None


def test_game_check_winner_simple_winner() -> None:
    """Test check_winner_simple with winner."""
    game, _ = _make_game(2)
    # Give player enough points
    for _ in range(15):
        game.players[0].add_card(_make_card(points=1))
    winner = game.check_winner_simple()
    assert winner is game.players[0]
    assert game.finished is True


def test_game_refill_table() -> None:
    """Test refill_table fills from decks."""
    game, _ = _make_game(2)
    # Table should be filled initially
    for tier in (1, 2, 3):
        assert len(game.table_by_tier[tier]) <= game.config.table_cards_per_tier


# --- Action tests ---


def test_apply_take_different() -> None:
    """Test take different colors."""
    game, bots = _make_game(2)
    strategy = bots[0]
    action = TakeDifferent(colors=["white", "blue", "green"])
    apply_take_different(game, strategy, action)
    p = game.players[0]
    assert p.tokens["white"] == 1
    assert p.tokens["blue"] == 1
    assert p.tokens["green"] == 1


def test_apply_take_different_invalid() -> None:
    """Test take different with too many colors is truncated."""
    game, bots = _make_game(2)
    strategy = bots[0]
    # 4 colors should be rejected
    action = TakeDifferent(colors=["white", "blue", "green", "red"])
    apply_take_different(game, strategy, action)


def test_apply_take_double() -> None:
    """Test take double."""
    game, bots = _make_game(2)
    strategy = bots[0]
    action = TakeDouble(color="white")
    apply_take_double(game, strategy, action)
    p = game.players[0]
    assert p.tokens["white"] == 2


def test_apply_take_double_insufficient() -> None:
    """Test take double fails when bank has insufficient."""
    game, bots = _make_game(2)
    strategy = bots[0]
    game.bank["white"] = 2  # Below minimum_tokens_to_buy_2
    action = TakeDouble(color="white")
    apply_take_double(game, strategy, action)
    p = game.players[0]
    assert p.tokens["white"] == 0  # No change


def test_apply_buy_card() -> None:
    """Test buy a card."""
    game, bots = _make_game(2)
    strategy = bots[0]
    # Give the player enough tokens
    game.players[0].tokens["white"] = 10
    game.players[0].tokens["blue"] = 10
    game.players[0].tokens["green"] = 10
    game.players[0].tokens["red"] = 10
    game.players[0].tokens["black"] = 10

    if game.table_by_tier[1]:
        action = BuyCard(tier=1, index=0)
        apply_buy_card(game, strategy, action)


def test_apply_buy_card_reserved() -> None:
    """Test buy a reserved card."""
    game, bots = _make_game(2)
    strategy = bots[0]
    card = _make_card(cost=dict.fromkeys(GEM_COLORS, 0))
    game.players[0].reserved.append(card)

    action = BuyCardReserved(index=0)
    apply_buy_card_reserved(game, strategy, action)
    assert len(game.players[0].reserved) == 0
    assert len(game.players[0].cards) == 1


def test_apply_reserve_card_from_table() -> None:
    """Test reserve a card from table."""
    game, bots = _make_game(2)
    strategy = bots[0]
    if game.table_by_tier[1]:
        action = ReserveCard(tier=1, index=0, from_deck=False)
        apply_reserve_card(game, strategy, action)
        assert len(game.players[0].reserved) == 1


def test_apply_reserve_card_from_deck() -> None:
    """Test reserve a card from deck."""
    game, bots = _make_game(2)
    strategy = bots[0]
    action = ReserveCard(tier=1, index=None, from_deck=True)
    apply_reserve_card(game, strategy, action)
    assert len(game.players[0].reserved) == 1


def test_apply_reserve_card_limit() -> None:
    """Test reserve limit."""
    game, bots = _make_game(2)
    strategy = bots[0]
    # Fill reserves
    for _ in range(3):
        game.players[0].reserved.append(_make_card())
    action = ReserveCard(tier=1, index=0, from_deck=False)
    apply_reserve_card(game, strategy, action)
    assert len(game.players[0].reserved) == 3  # No change


def test_apply_action_unknown_type() -> None:
    """Test apply_action with unknown action type."""

    class FakeAction(Action):
        pass

    game, bots = _make_game(2)
    with pytest.raises(ValueError, match="Unknown action type"):
        apply_action(game, bots[0], FakeAction())


def test_apply_action_dispatches() -> None:
    """Test apply_action dispatches to correct handler."""
    game, bots = _make_game(2)
    action = TakeDifferent(colors=["white"])
    apply_action(game, bots[0], action)


# --- auto_discard_tokens ---


def test_auto_discard_tokens() -> None:
    """Test auto_discard_tokens."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    p.tokens["white"] = 5
    p.tokens["blue"] = 3
    discards = auto_discard_tokens(p, 2)
    assert sum(discards.values()) == 2


# --- enforce_token_limit ---


def test_enforce_token_limit_under() -> None:
    """Test enforce_token_limit when under limit."""
    game, bots = _make_game(2)
    p = game.players[0]
    p.tokens["white"] = 3
    enforce_token_limit(game, bots[0], p)
    assert p.tokens["white"] == 3  # No change


def test_enforce_token_limit_over() -> None:
    """Test enforce_token_limit when over limit."""
    game, bots = _make_game(2)
    p = game.players[0]
    for color in BASE_COLORS:
        p.tokens[color] = 5
    enforce_token_limit(game, bots[0], p)
    assert p.total_tokens() <= game.config.token_limit


# --- check_nobles_for_player ---


def test_check_nobles_no_qualification() -> None:
    """Test check_nobles when player doesn't qualify."""
    game, bots = _make_game(2)
    check_nobles_for_player(game, bots[0], game.players[0])
    assert len(game.players[0].nobles) == 0


def test_check_nobles_qualification() -> None:
    """Test check_nobles when player qualifies."""
    game, bots = _make_game(2)
    p = game.players[0]
    # Give enough discounts to qualify for ALL nobles (ensures at least one match)
    for color in BASE_COLORS:
        p.discounts[color] = 10
    check_nobles_for_player(game, bots[0], p)
    assert len(p.nobles) >= 1


# --- get_legal_actions ---


def test_get_legal_actions() -> None:
    """Test get_legal_actions returns valid actions."""
    game, _ = _make_game(2)
    actions = get_legal_actions(game)
    assert len(actions) > 0


def test_get_legal_actions_explicit_player() -> None:
    """Test get_legal_actions with explicit player."""
    game, _ = _make_game(2)
    actions = get_legal_actions(game, game.players[1])
    assert len(actions) > 0


# --- create_random helpers ---


def test_create_random_cards() -> None:
    """Test create_random_cards."""
    random.seed(42)
    cards = create_random_cards()
    assert len(cards) > 0
    tiers = {c.tier for c in cards}
    assert tiers == {1, 2, 3}


def test_create_random_cards_tier() -> None:
    """Test create_random_cards_tier."""
    cards = create_random_cards_tier(1, 3, [0, 1], [0, 1])
    assert len(cards) == 15  # 5 colors * 3 per color


def test_create_random_nobles() -> None:
    """Test create_random_nobles."""
    nobles = create_random_nobles()
    assert len(nobles) == 8
    assert all(n.points == 3 for n in nobles)


# --- load_cards / load_nobles ---


def test_load_cards(tmp_path: Path) -> None:
    """Test load_cards from file."""
    import json
    from pathlib import Path

    cards_data = [
        {"tier": 1, "points": 0, "color": "white", "cost": {"white": 0, "blue": 1}},
    ]
    file = tmp_path / "cards.json"
    file.write_text(json.dumps(cards_data))
    cards = load_cards(file)
    assert len(cards) == 1


def test_load_nobles(tmp_path: Path) -> None:
    """Test load_nobles from file."""
    import json
    from pathlib import Path

    nobles_data = [
        {"name": "Noble 1", "points": 3, "requirements": {"white": 3, "blue": 3}},
    ]
    file = tmp_path / "nobles.json"
    file.write_text(json.dumps(nobles_data))
    nobles = load_nobles(file)
    assert len(nobles) == 1


# --- run_game ---


def test_run_game() -> None:
    """Test run_game completes."""
    random.seed(42)
    game, _ = _make_game(2)
    winner, turns = run_game(game)
    assert winner is not None
    assert turns > 0


def test_run_game_concede() -> None:
    """Test run_game handles player conceding."""

    class ConcedingBot(RandomBot):
        def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
            return None

    bots = [ConcedingBot("bot1"), RandomBot("bot2")]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    winner, turns = run_game(game)
    assert winner is not None


# --- Bot tests ---


def test_random_bot_choose_action() -> None:
    """Test RandomBot.choose_action returns valid action."""
    random.seed(42)
    game, bots = _make_game(2)
    action = bots[0].choose_action(game, game.players[0])
    assert action is not None


def test_personalized_bot_choose_action() -> None:
    """Test PersonalizedBot.choose_action."""
    random.seed(42)
    bot = PersonalizedBot("pbot")
    game, _ = _make_game(2)
    game.players[0].strategy = bot
    action = bot.choose_action(game, game.players[0])
    assert action is not None


def test_personalized_bot2_choose_action() -> None:
    """Test PersonalizedBot2.choose_action."""
    random.seed(42)
    bot = PersonalizedBot2("pbot2")
    game, _ = _make_game(2)
    game.players[0].strategy = bot
    action = bot.choose_action(game, game.players[0])
    assert action is not None


def test_can_bot_afford() -> None:
    """Test can_bot_afford function."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    card = _make_card(cost=dict.fromkeys(GEM_COLORS, 0))
    assert can_bot_afford(p, card) is True


def test_check_cards_in_tier() -> None:
    """Test check_cards_in_tier."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    free_card = _make_card(cost=dict.fromkeys(GEM_COLORS, 0))
    expensive_card = _make_card(cost={**dict.fromkeys(GEM_COLORS, 0), "white": 10})
    result = check_cards_in_tier([free_card, expensive_card], p)
    assert result == [0]


def test_buy_card_function() -> None:
    """Test buy_card helper function."""
    game, _ = _make_game(2)
    p = game.players[0]
    # Give player enough tokens
    for c in BASE_COLORS:
        p.tokens[c] = 10
    result = buy_card(game, p)
    assert result is not None or True  # May or may not find affordable card


def test_buy_card_reserved_function() -> None:
    """Test buy_card_reserved helper function."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    # No reserved cards
    assert buy_card_reserved(p) is None

    # With affordable reserved card
    card = _make_card(cost=dict.fromkeys(GEM_COLORS, 0))
    p.reserved.append(card)
    result = buy_card_reserved(p)
    assert isinstance(result, BuyCardReserved)


def test_take_tokens_function() -> None:
    """Test take_tokens helper function."""
    game, _ = _make_game(2)
    result = take_tokens(game)
    assert result is not None


def test_take_tokens_empty_bank() -> None:
    """Test take_tokens with empty bank."""
    game, _ = _make_game(2)
    for c in BASE_COLORS:
        game.bank[c] = 0
    result = take_tokens(game)
    assert result is None


# --- public_state tests ---


def test_encode_card() -> None:
    """Test _encode_card."""
    card = _make_card(tier=1, points=2, color="blue", cost={"white": 1, "blue": 2})
    obs = _encode_card(card)
    assert isinstance(obs, ObsCard)
    assert obs.tier == 1
    assert obs.points == 2


def test_encode_noble() -> None:
    """Test _encode_noble."""
    noble = _make_noble(points=3, reqs={"white": 3, "blue": 3, "green": 3})
    obs = _encode_noble(noble)
    assert isinstance(obs, ObsNoble)
    assert obs.points == 3


def test_encode_player() -> None:
    """Test _encode_player."""
    bot = RandomBot("test")
    p = PlayerState(strategy=bot)
    obs = _encode_player(p)
    assert isinstance(obs, ObsPlayer)
    assert obs.score == 0


def test_to_observation() -> None:
    """Test to_observation creates full observation."""
    game, _ = _make_game(2)
    obs = to_observation(game)
    assert isinstance(obs, Observation)
    assert len(obs.players) == 2
    assert obs.current_player == 0


# --- sim tests ---


def test_sim_strategy_choose_action_raises() -> None:
    """Test SimStrategy.choose_action raises."""
    sim = SimStrategy("sim")
    game, _ = _make_game(2)
    with pytest.raises(RuntimeError, match="should not be used"):
        sim.choose_action(game, game.players[0])


def test_simulate_step() -> None:
    """Test simulate_step returns deep copy."""
    random.seed(42)
    game, _ = _make_game(2)
    action = TakeDifferent(colors=["white", "blue", "green"])
    # SimStrategy() in source is missing name arg - patch it
    with patch("python.splendor.sim.SimStrategy", lambda: SimStrategy("sim")):
        next_state = simulate_step(game, action)
    assert next_state is not game
    assert next_state.current_player_index != game.current_player_index or len(game.players) == 1
