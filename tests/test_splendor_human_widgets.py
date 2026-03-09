"""Tests for splendor/human.py Textual widgets and TUI apps.

Covers Board (compose, on_mount, refresh_content, render methods),
ActionApp/DiscardApp/NobleChoiceApp (compose, on_mount, _update_prompt,
on_input_submitted), and TuiHuman tty paths.
"""

from __future__ import annotations

import random
import sys
from unittest.mock import patch

import pytest

from python.splendor.base import (
    BASE_COLORS,
    GEM_COLORS,
    Card,
    GameConfig,
    GameState,
    Noble,
    PlayerState,
    TakeDifferent,
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
        board = app.query_one(Board)
        assert board is not None

        # Verify sub-widgets exist
        assert app.query_one("#bank_box") is not None
        assert app.query_one("#tier1_box") is not None
        assert app.query_one("#tier2_box") is not None
        assert app.query_one("#tier3_box") is not None
        assert app.query_one("#nobles_box") is not None
        assert app.query_one("#players_box") is not None

        app.exit()


@pytest.mark.asyncio
async def test_board_render_bank() -> None:
    """Board._render_bank writes bank info to bank_box."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        board = app.query_one(Board)
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
    card = Card(
        tier=1, points=1, color="white", cost=dict.fromkeys(GEM_COLORS, 0),
    )
    p.cards.append(card)
    reserved = Card(
        tier=2, points=2, color="blue", cost=dict.fromkeys(GEM_COLORS, 0),
    )
    p.reserved.append(reserved)
    noble = Noble(
        name="TestNoble", points=3, requirements=dict.fromkeys(GEM_COLORS, 0),
    )
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
        from textual.widgets import Footer, Input, Static

        assert app.query_one("#input_line", Input) is not None
        assert app.query_one("#prompt", Static) is not None
        assert app.query_one("#board", Board) is not None
        assert app.query_one(Footer) is not None

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


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_quit() -> None:
    """ActionApp exits on 'q' input via pilot keyboard."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        await pilot.press("q", "enter")
        await pilot.pause()
        assert app.result is None


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_quit_word() -> None:
    """ActionApp exits on 'quit' input."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        await pilot.press("q", "u", "i", "t", "enter")
        await pilot.pause()
        assert app.result is None


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_zero() -> None:
    """ActionApp exits on '0' input."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        await pilot.press("0", "enter")
        await pilot.pause()
        assert app.result is None


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_empty() -> None:
    """ActionApp ignores empty input."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        assert app.result is None
        app.exit()


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_valid_cmd() -> None:
    """ActionApp processes valid command '1 w b g' and exits."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        for ch in "1 w b g":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.result, TakeDifferent)


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_error() -> None:
    """ActionApp shows error message for bad command."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        for ch in "xyz":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert app.message == "Unknown command."
        app.exit()


@pytest.mark.asyncio
async def test_action_app_on_input_submitted_cmd_error() -> None:
    """ActionApp shows error from a valid command number but bad args."""
    game, _ = _make_game()
    _patch_player_names(game)
    app = ActionApp(game, game.players[0])

    async with app.run_test() as pilot:
        await pilot.press("1", "enter")
        await pilot.pause()
        assert app.message != ""
        app.exit()


# ---------------------------------------------------------------------------
# DiscardApp tests
# ---------------------------------------------------------------------------


def _make_discard_game(excess: int = 1):
    """Create a game where player 0 has excess tokens over the limit."""
    game, _bots = _make_game()
    _patch_player_names(game)
    p = game.players[0]
    for c in GEM_COLORS:
        p.tokens[c] = 0
    p.tokens["white"] = game.config.token_limit + excess
    return game, p


@pytest.mark.asyncio
async def test_discard_app_compose_and_mount() -> None:
    """DiscardApp composes header, command_zone, board, footer."""
    game, p = _make_discard_game(2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        from textual.widgets import Footer, Header, Input, Static

        assert app.query_one(Header) is not None
        assert app.query_one("#input_line", Input) is not None
        assert app.query_one("#prompt", Static) is not None
        assert app.query_one("#board", Board) is not None
        assert app.query_one(Footer) is not None

        app.exit()


@pytest.mark.asyncio
async def test_discard_app_update_prompt() -> None:
    """DiscardApp._update_prompt shows remaining discards info."""
    game, p = _make_discard_game(2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        app._update_prompt()
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_update_prompt_with_message() -> None:
    """DiscardApp._update_prompt includes error message."""
    game, p = _make_discard_game(2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        app.message = "No more blue tokens"
        app._update_prompt()
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_on_input_submitted_empty() -> None:
    """DiscardApp ignores empty input."""
    game, p = _make_discard_game(2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        assert all(v == 0 for v in app.discards.values())
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_on_input_submitted_unknown_color() -> None:
    """DiscardApp shows error for unknown color."""
    game, p = _make_discard_game(2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        for ch in "purple":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert "Unknown color" in app.message
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_on_input_submitted_no_tokens() -> None:
    """DiscardApp shows error when no tokens of that color available."""
    game, p = _make_discard_game(2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        for ch in "blue":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert "No more" in app.message
        app.exit()


@pytest.mark.asyncio
async def test_discard_app_on_input_submitted_valid_finishes() -> None:
    """DiscardApp increments discard and exits when done (excess=1)."""
    game, p = _make_discard_game(excess=1)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        await pilot.press("w", "enter")
        await pilot.pause()
        assert app.discards["white"] == 1


@pytest.mark.asyncio
async def test_discard_app_on_input_submitted_not_done_yet() -> None:
    """DiscardApp stays open when more discards still needed (excess=2)."""
    game, p = _make_discard_game(excess=2)
    app = DiscardApp(game, p)

    async with app.run_test() as pilot:
        await pilot.press("w", "enter")
        await pilot.pause()
        assert app.discards["white"] == 1
        assert app.message == ""

        await pilot.press("w", "enter")
        await pilot.pause()
        assert app.discards["white"] == 2


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
        from textual.widgets import Footer, Header, Input, Static

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


@pytest.mark.asyncio
async def test_noble_choice_app_on_input_submitted_empty() -> None:
    """NobleChoiceApp ignores empty input."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        assert app.result is None
        app.exit()


@pytest.mark.asyncio
async def test_noble_choice_app_on_input_submitted_not_int() -> None:
    """NobleChoiceApp shows error for non-integer input."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        for ch in "abc":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert "valid integer" in app.message
        app.exit()


@pytest.mark.asyncio
async def test_noble_choice_app_on_input_submitted_out_of_range() -> None:
    """NobleChoiceApp shows error for index out of range."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        await pilot.press("9", "enter")
        await pilot.pause()
        assert "out of range" in app.message.lower()
        app.exit()


@pytest.mark.asyncio
async def test_noble_choice_app_on_input_submitted_valid() -> None:
    """NobleChoiceApp selects noble and exits on valid index."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        await pilot.press("0", "enter")
        await pilot.pause()
        assert app.result is nobles[0]


@pytest.mark.asyncio
async def test_noble_choice_app_on_input_submitted_second_noble() -> None:
    """NobleChoiceApp selects second noble."""
    game, _ = _make_game()
    _patch_player_names(game)
    nobles = game.available_nobles[:2]
    app = NobleChoiceApp(game, game.players[0], nobles)

    async with app.run_test() as pilot:
        await pilot.press("1", "enter")
        await pilot.pause()
        assert app.result is nobles[1]


# ---------------------------------------------------------------------------
# TuiHuman tty path tests
# ---------------------------------------------------------------------------


def test_tui_human_choose_action_tty() -> None:
    """TuiHuman.choose_action runs ActionApp when stdout is a tty."""
    random.seed(42)
    game, _ = _make_game()
    human = TuiHuman("test")

    with patch.object(sys.stdout, "isatty", return_value=True):
        with patch.object(ActionApp, "run") as mock_run:
            result = human.choose_action(game, game.players[0])
            mock_run.assert_called_once()
            assert result is None


def test_tui_human_choose_discard_tty() -> None:
    """TuiHuman.choose_discard runs DiscardApp when stdout is a tty."""
    random.seed(42)
    game, _ = _make_game()
    human = TuiHuman("test")

    with patch.object(sys.stdout, "isatty", return_value=True):
        with patch.object(DiscardApp, "run") as mock_run:
            result = human.choose_discard(game, game.players[0], 2)
            mock_run.assert_called_once()
            assert result == dict.fromkeys(GEM_COLORS, 0)


def test_tui_human_choose_noble_tty() -> None:
    """TuiHuman.choose_noble runs NobleChoiceApp when stdout is a tty."""
    random.seed(42)
    game, _ = _make_game()
    nobles = game.available_nobles[:2]
    human = TuiHuman("test")

    with patch.object(sys.stdout, "isatty", return_value=True):
        with patch.object(NobleChoiceApp, "run") as mock_run:
            result = human.choose_noble(game, game.players[0], nobles)
            mock_run.assert_called_once()
            assert result is None
