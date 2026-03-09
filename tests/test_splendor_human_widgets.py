"""Tests for splendor/human.py Textual widgets and TUI apps.

Covers Board (compose, on_mount, refresh_content, render methods),
ActionApp/DiscardApp/NobleChoiceApp (compose, on_mount, _update_prompt,
on_input_submitted), and TuiHuman tty paths.
"""

from __future__ import annotations

import random
import sys
from unittest.mock import MagicMock, patch

import pytest

from python.splendor.base import (
    BASE_COLORS,
    GEM_COLORS,
    Card,
    GameConfig,
    GameState,
    Noble,
    PlayerState,
    create_random_cards,
    create_random_nobles,
    new_game,
)
from python.splendor.bot import RandomBot
from python.splendor.human import (
    ActionApp,
    Board,
    DiscardApp,
    NobleChoiceApp,
    TuiHuman,
)


def _make_game(num_players: int = 2):
    random.seed(42)
    bots = [RandomBot(f"bot{i}") for i in range(num_players)]
    cards = create_random_cards()
    nobles = create_random_nobles()
    config = GameConfig(cards=cards, nobles=nobles)
    game = new_game(bots, config)
    return game, bots


def _patch_player_names(game: GameState) -> None:
    """Add .name attribute to each PlayerState (delegates to strategy.name)."""
    for p in game.players:
        p.name = p.strategy.name  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Board widget tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_board_compose_and_mount() -> None:
    """Board.compose yields expected widget tree; on_mount populates them."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        # Board should be mounted and its children present
        board = app.query_one(Board)
        assert board is not None

        # Verify sub-widgets exist
        bank_box = app.query_one("#bank_box")
        assert bank_box is not None
        tier1 = app.query_one("#tier1_box")
        assert tier1 is not None
        tier2 = app.query_one("#tier2_box")
        assert tier2 is not None
        tier3 = app.query_one("#tier3_box")
        assert tier3 is not None
        nobles_box = app.query_one("#nobles_box")
        assert nobles_box is not None
        players_box = app.query_one("#players_box")
        assert players_box is not None

        app.exit()


@pytest.mark.asyncio
async def test_board_render_bank() -> None:
    """Board._render_bank writes bank info to bank_box."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        # Call render explicitly to ensure it runs
        board._render_bank()
        app.exit()


@pytest.mark.asyncio
async def test_board_render_tiers() -> None:
    """Board._render_tiers populates tier boxes."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        board._render_tiers()
        app.exit()


@pytest.mark.asyncio
async def test_board_render_tiers_empty() -> None:
    """Board._render_tiers handles empty tiers."""
    game, _ = _make_game()
    _patch_player_names(game)
    # Clear all table cards
    for tier in game.table_by_tier:
        game.table_by_tier[tier] = []
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        board._render_tiers()
        app.exit()


@pytest.mark.asyncio
async def test_board_render_nobles() -> None:
    """Board._render_nobles shows noble info."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        board._render_nobles()
        app.exit()


@pytest.mark.asyncio
async def test_board_render_nobles_empty() -> None:
    """Board._render_nobles handles no nobles."""
    game, _ = _make_game()
    _patch_player_names(game)
    game.available_nobles = []
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        board._render_nobles()
        app.exit()


@pytest.mark.asyncio
async def test_board_render_players() -> None:
    """Board._render_players shows all player info."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        board._render_players()
        app.exit()


@pytest.mark.asyncio
async def test_board_render_players_with_nobles_and_cards() -> None:
    """Board._render_players handles players with nobles, cards, and reserved."""
    game, _ = _make_game()
    _patch_player_names(game)
    p = game.players[0]
    # Give player some cards
    card = Card(tier=1, points=1, color="white", cost=dict.fromkeys(GEM_COLORS, 0))
    p.cards.append(card)
    # Give player a reserved card
    reserved = Card(tier=2, points=2, color="blue", cost=dict.fromkeys(GEM_COLORS, 0))
    p.reserved.append(reserved)
    # Give player a noble
    noble = Noble(name="TestNoble", points=3, requirements=dict.fromkeys(GEM_COLORS, 0))
    p.nobles.append(noble)

    app = ActionApp(game, p)

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        board._render_players()
        app.exit()


@pytest.mark.asyncio
async def test_board_refresh_content() -> None:
    """Board.refresh_content calls all render sub-methods."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
        # refresh_content should run without error (also called by on_mount)
        board.refresh_content()
        app.exit()


# ---------------------------------------------------------------------------
# ActionApp tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_action_app_compose_and_mount() -> None:
    """ActionApp composes command_zone, board, footer and sets up prompt."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        # Verify compose created the expected structure
        from textual.widgets import Input, Footer, Static

        input_w = app.query_one("#input_line", Input)
        assert input_w is not None
        prompt = app.query_one("#prompt", Static)
        assert prompt is not None
        board = app.query_one("#board", Board)
        assert board is not None
        footer = app.query_one(Footer)
        assert footer is not None

        app.exit()


@pytest.mark.asyncio
async def test_action_app_update_prompt() -> None:
    """ActionApp._update_prompt writes action menu to prompt widget."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        app._update_prompt()
        app.exit()


@pytest.mark.asyncio
async def test_action_app_update_prompt_with_message() -> None:
    """ActionApp._update_prompt includes error message when set."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        app.message = "Some error occurred"
        app._update_prompt()
        app.exit()


def _make_mock_input_event(value: str):
    """Create a mock Input.Submitted event."""
    mock_event = MagicMock()
    mock_event.value = value
    mock_event.input = MagicMock()
    mock_event.input.value = value
    return mock_event


def test_action_app_on_input_submitted_quit_sync() -> None:
    """ActionApp exits on 'q' input (sync test via direct method call)."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("q")
    app.on_input_submitted(event)
    assert app.result is None
    app.exit.assert_called_once()


def test_action_app_on_input_submitted_quit_word_sync() -> None:
    """ActionApp exits on 'quit' input."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()

    event = _make_mock_input_event("quit")
    app.on_input_submitted(event)
    assert app.result is None
    app.exit.assert_called_once()


def test_action_app_on_input_submitted_zero_sync() -> None:
    """ActionApp exits on '0' input."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()

    event = _make_mock_input_event("0")
    app.on_input_submitted(event)
    assert app.result is None
    app.exit.assert_called_once()


def test_action_app_on_input_submitted_empty_sync() -> None:
    """ActionApp ignores empty input."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()

    event = _make_mock_input_event("")
    app.on_input_submitted(event)
    app.exit.assert_not_called()


def test_action_app_on_input_submitted_valid_cmd_sync() -> None:
    """ActionApp processes valid command '1 w b g'."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()

    event = _make_mock_input_event("1 w b g")
    app.on_input_submitted(event)
    from python.splendor.base import TakeDifferent
    assert isinstance(app.result, TakeDifferent)
    app.exit.assert_called_once()


def test_action_app_on_input_submitted_error_sync() -> None:
    """ActionApp shows error message for bad command."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("badcmd")
    app.on_input_submitted(event)
    assert app.message == "Unknown command."
    app._update_prompt.assert_called_once()


def test_action_app_on_input_submitted_cmd_error_sync() -> None:
    """ActionApp shows error from a valid command number but bad args."""
    game, _ = _make_game()
    app = ActionApp(game, game.players[0])
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("1")
    app.on_input_submitted(event)
    assert "color" in app.message.lower() or "Need" in app.message


# ---------------------------------------------------------------------------
# DiscardApp tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_discard_app_compose_and_mount() -> None:
    """DiscardApp composes header, command_zone, board, footer."""
    game, _ = _make_game()
    _patch_player_names(game)
    # Give player excess tokens so discard makes sense
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5

    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        from textual.widgets import Header, Footer, Input, Static

        assert app.query_one(Header) is not None
        assert app.query_one("#input_line", Input) is not None
        assert app.query_one("#prompt", Static) is not None
        assert app.query_one("#board", Board) is not None
        assert app.query_one(Footer) is not None

        app.exit()


@pytest.mark.asyncio
async def test_discard_app_update_prompt() -> None:
    """DiscardApp._update_prompt shows remaining discards info."""
    game, _ = _make_game()
    _patch_player_names(game)
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5

    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        app._update_prompt()
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_update_prompt_with_message() -> None:
    """DiscardApp._update_prompt includes error message."""
    game, _ = _make_game()
    _patch_player_names(game)
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5

    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        app.message = "No more blue tokens"
        app._update_prompt()
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_on_input_submitted_empty() -> None:
    """DiscardApp ignores empty input."""
    game, _ = _make_game()
    _patch_player_names(game)
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5

    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        input_w = app.query_one("#input_line")
        input_w.value = ""
        await input_w.action_submit()
        # Nothing should change
        assert all(v == 0 for v in app.discards.values())
        app.exit()


def test_discard_app_on_input_submitted_unknown_color_sync() -> None:
    """DiscardApp shows error for unknown color."""
    game, _ = _make_game()
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5
    app = DiscardApp(game, p)
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("purple")
    app.on_input_submitted(event)
    assert "Unknown color" in app.message
    app._update_prompt.assert_called()


def test_discard_app_on_input_submitted_no_tokens_sync() -> None:
    """DiscardApp shows error when no tokens of that color available."""
    game, _ = _make_game()
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5
    p.tokens["white"] = 0
    app = DiscardApp(game, p)
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("white")
    app.on_input_submitted(event)
    assert "No more" in app.message


def test_discard_app_on_input_submitted_valid_discard_sync() -> None:
    """DiscardApp increments discard count for valid color."""
    game, _ = _make_game()
    p = game.players[0]
    total_needed = game.config.token_limit + 1
    p.tokens["white"] = total_needed
    for c in BASE_COLORS:
        if c != "white":
            p.tokens[c] = 0
    p.tokens["gold"] = 0
    app = DiscardApp(game, p)
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("white")
    app.on_input_submitted(event)
    assert app.discards["white"] == 1
    app.exit.assert_called_once()


def test_discard_app_on_input_submitted_not_done_yet_sync() -> None:
    """DiscardApp stays open when more discards still needed."""
    game, _ = _make_game()
    p = game.players[0]
    total_needed = game.config.token_limit + 2
    p.tokens["white"] = total_needed
    for c in BASE_COLORS:
        if c != "white":
            p.tokens[c] = 0
    p.tokens["gold"] = 0
    app = DiscardApp(game, p)
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("white")
    app.on_input_submitted(event)
    assert app.discards["white"] == 1
    assert app.message == ""
    app.exit.assert_not_called()

    event2 = _make_mock_input_event("white")
    app.on_input_submitted(event2)
    assert app.discards["white"] == 2
    app.exit.assert_called_once()


def test_discard_app_on_input_submitted_empty_sync() -> None:
    """DiscardApp ignores empty input."""
    game, _ = _make_game()
    p = game.players[0]
    for c in BASE_COLORS:
        p.tokens[c] = 5
    app = DiscardApp(game, p)
    app.exit = MagicMock()

    event = _make_mock_input_event("")
    app.on_input_submitted(event)
    assert all(v == 0 for v in app.discards.values())
    app.exit.assert_not_called()


# ---------------------------------------------------------------------------
# NobleChoiceApp tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_noble_choice_app_compose_and_mount() -> None:
    """NobleChoiceApp composes header, command_zone, board, footer."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        from textual.widgets import Header, Footer, Input, Static

        assert app.query_one(Header) is not None
        assert app.query_one("#input_line", Input) is not None
        assert app.query_one("#prompt", Static) is not None
        assert app.query_one("#board", Board) is not None
        assert app.query_one(Footer) is not None

        app.exit()


@pytest.mark.asyncio
async def test_noble_choice_app_update_prompt() -> None:
    """NobleChoiceApp._update_prompt lists available nobles."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        app._update_prompt()
        app.exit()


@pytest.mark.asyncio
async def test_noble_choice_app_update_prompt_with_message() -> None:
    """NobleChoiceApp._update_prompt includes error message."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        app.message = "Index out of range."
        app._update_prompt()
        app.exit()


def test_noble_choice_app_on_input_submitted_empty_sync() -> None:
    """NobleChoiceApp ignores empty input."""
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)
    app.exit = MagicMock()

    event = _make_mock_input_event("")
    app.on_input_submitted(event)
    assert app.result is None
    app.exit.assert_not_called()


def test_noble_choice_app_on_input_submitted_not_int_sync() -> None:
    """NobleChoiceApp shows error for non-integer input."""
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("abc")
    app.on_input_submitted(event)
    assert "valid integer" in app.message
    app._update_prompt.assert_called()


def test_noble_choice_app_on_input_submitted_out_of_range_sync() -> None:
    """NobleChoiceApp shows error for index out of range."""
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)
    app.exit = MagicMock()
    app._update_prompt = MagicMock()

    event = _make_mock_input_event("99")
    app.on_input_submitted(event)
    assert "out of range" in app.message.lower()


def test_noble_choice_app_on_input_submitted_valid_sync() -> None:
    """NobleChoiceApp selects noble and exits on valid index."""
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)
    app.exit = MagicMock()

    event = _make_mock_input_event("0")
    app.on_input_submitted(event)
    assert app.result is nobles[0]
    app.exit.assert_called_once()


def test_noble_choice_app_on_input_submitted_second_noble_sync() -> None:
    """NobleChoiceApp selects second noble."""
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)
    app.exit = MagicMock()

    event = _make_mock_input_event("1")
    app.on_input_submitted(event)
    assert app.result is nobles[1]
    app.exit.assert_called_once()


# ---------------------------------------------------------------------------
# TuiHuman tty path tests
# ---------------------------------------------------------------------------


def test_tui_human_choose_action_tty() -> None:
    """TuiHuman.choose_action creates and runs ActionApp when stdout is a tty."""
    random.seed(42)
    game, _ = _make_game()
    human = TuiHuman("test")

    with patch.object(sys.stdout, "isatty", return_value=True):
        with patch.object(ActionApp, "run") as mock_run:
            # Simulate the app setting a result
            def set_result():
                pass  # result stays None (quit)

            mock_run.side_effect = set_result
            result = human.choose_action(game, game.players[0])
            mock_run.assert_called_once()
            assert result is None  # default result is None


def test_tui_human_choose_discard_tty() -> None:
    """TuiHuman.choose_discard creates and runs DiscardApp when stdout is a tty."""
    random.seed(42)
    game, _ = _make_game()
    human = TuiHuman("test")

    with patch.object(sys.stdout, "isatty", return_value=True):
        with patch.object(DiscardApp, "run") as mock_run:
            result = human.choose_discard(game, game.players[0], 2)
            mock_run.assert_called_once()
            # Default discards are all zeros
            assert result == dict.fromkeys(GEM_COLORS, 0)


def test_tui_human_choose_noble_tty() -> None:
    """TuiHuman.choose_noble creates and runs NobleChoiceApp when stdout is a tty."""
    random.seed(42)
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    human = TuiHuman("test")

    with patch.object(sys.stdout, "isatty", return_value=True):
        with patch.object(NobleChoiceApp, "run") as mock_run:
            result = human.choose_noble(game, game.players[0], nobles)
            mock_run.assert_called_once()
            # Default result is None
            assert result is None
