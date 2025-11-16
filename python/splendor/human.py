from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Static

from .base import (
    BASE_COLORS,
    GEM_COLORS,
    Action,
    BuyCard,
    Card,
    GameState,
    GemColor,
    Noble,
    PlayerState,
    ReserveCard,
    Strategy,
    TakeDifferent,
    TakeDouble,
)

# Abbreviations used when rendering costs
COST_ABBR: dict[GemColor, str] = {
    "white": "W",
    "blue": "B",
    "green": "G",
    "red": "R",
    "black": "K",
    "gold": "O",
}

# Abbreviations players can type on the command line
COLOR_ABBR_TO_FULL: dict[str, GemColor] = {
    "w": "white",
    "b": "blue",
    "g": "green",
    "r": "red",
    "k": "black",
    "o": "gold",
}


def parse_color_token(raw: str) -> GemColor:
    """Convert user input into a GemColor.

    Supports:
      - full names:  white, blue, green, red, black, gold
      - abbreviations: w, b, g, r, k, o
    """
    key = raw.lower()

    # full color names first
    if key in BASE_COLORS:
        return key  # type: ignore[return-value]

    # abbreviations
    if key in COLOR_ABBR_TO_FULL:
        return COLOR_ABBR_TO_FULL[key]

    raise ValueError(f"Unknown color: {raw}")


def format_cost(cost: Mapping[GemColor, int]) -> str:
    """Format a cost/requirements dict as colored tokens like 'B:2, R:1'.

    Uses `color_token` internally so colors are guaranteed to match your bank.
    """
    parts: list[str] = []
    for color in GEM_COLORS:
        n = cost.get(color, 0)
        if not n:
            continue

        # color_token gives us e.g. "[blue]blue: 3[/]"
        token = color_token(color, n)

        # Turn the leading color name into the abbreviation (blue: 3 → B:3)
        # We only replace the first occurrence.
        full = f"{color}:"
        abbr = f"{COST_ABBR[color]}:"
        token = token.replace(full, abbr, 1)

        parts.append(token)

    return ", ".join(parts) if parts else "-"


def format_card(card: Card) -> str:
    """Readable card line using dataclass fields instead of __str__."""
    color_abbr = COST_ABBR[card.color]
    header = f"T{card.tier} {color_abbr} P{card.points}"
    cost_str = format_cost(card.cost)
    return f"{header} ({cost_str})"


def format_noble(noble: Noble) -> str:
    """Readable noble line using dataclass fields instead of __str__."""
    cost_str = format_cost(noble.requirements)
    return f"{noble.name} +{noble.points} ({cost_str})"


def format_tokens(tokens: Mapping[GemColor, int]) -> str:
    """Colored 'color: n' list for a token dict."""
    return " ".join(color_token(c, tokens.get(c, 0)) for c in GEM_COLORS)


def format_discounts(discounts: Mapping[GemColor, int]) -> str:
    """Colored discounts, skipping zeros."""
    parts: list[str] = []
    for c in GEM_COLORS:
        n = discounts.get(c, 0)
        if not n:
            continue
        abbr = COST_ABBR[c]
        fg, bg = COLOR_STYLE[c]
        parts.append(f"[{fg} on {bg}]{abbr}:{n}[/{fg} on {bg}]")
    return ", ".join(parts) if parts else "-"


COLOR_STYLE: dict[GemColor, tuple[str, str]] = {
    "white": ("black", "white"),  # fg, bg
    "blue": ("bright_white", "blue"),
    "green": ("bright_white", "sea_green4"),
    "red": ("white", "red3"),
    "black": ("white", "grey0"),
    "gold": ("black", "yellow3"),
}


def fmt_gem(color: GemColor) -> str:
    """Render gem name with fg/bg matching real token color."""
    fg, bg = COLOR_STYLE[color]
    return f"[{fg} on {bg}] {color} [/{fg} on {bg}]"


def fmt_number(value: int) -> str:
    return f"[bold cyan]{value}[/]"


def color_token(name: GemColor, amount: int) -> str:
    """Return a Rich-markup colored 'name: n' string."""
    # Map Splendor colors -> terminal colors
    color_map: Mapping[GemColor, str] = {
        "white": "white",
        "blue": "blue",
        "green": "green",
        "red": "red",
        "black": "grey70",  # 'black' is unreadable on dark backgrounds
        "gold": "yellow",
    }
    style = color_map.get(name, "white")
    return f"[{style}]{name}: {amount}[/]"


class Board(Widget):
    """Big board widget with the layout you sketched."""

    def __init__(self, game: GameState, me: PlayerState, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game = game
        self.me = me

    def compose(self) -> ComposeResult:
        # Structure:
        # ┌ bank row
        # ├ middle row (tiers | nobles)
        # └ players row
        with Vertical(id="board_root"):
            yield Static(id="bank_box")
            with Horizontal(id="middle_row"):
                with Vertical(id="tiers_box"):
                    yield Static(id="tier1_box")
                    yield Static(id="tier2_box")
                    yield Static(id="tier3_box")
                yield Static(id="nobles_box")
            yield Static(id="players_box")

    def on_mount(self) -> None:
        self.refresh_content()

    def refresh_content(self) -> None:
        self._render_bank()
        self._render_tiers()
        self._render_nobles()
        self._render_players()

    # --- sections ----------------------------------------------------

    def _render_bank(self) -> None:
        bank = self.game.bank
        parts: list[str] = ["[b]Bank:[/b]"]
        # One line, all tokens colored
        parts.append(format_tokens(bank))
        self.query_one("#bank_box", Static).update("\n".join(parts))

    def _render_tiers(self) -> None:
        for tier in (1, 2, 3):
            box = self.query_one(f"#tier{tier}_box", Static)
            cards: list[Card] = self.game.table_by_tier.get(tier, [])
            lines: list[str] = [f"[b]Tier {tier} cards:[/b]"]
            if not cards:
                lines.append("  (none)")
            else:
                for idx, card in enumerate(cards):
                    lines.append(f"  [{idx}] {format_card(card)}")
            box.update("\n".join(lines))

    def _render_nobles(self) -> None:
        nobles_box = self.query_one("#nobles_box", Static)
        lines: list[str] = ["[b]Nobles[/b]"]
        if not self.game.available_nobles:
            lines.append("  (none)")
        else:
            for noble in self.game.available_nobles:
                lines.append("  - " + format_noble(noble))
        nobles_box.update("\n".join(lines))

    def _render_players(self) -> None:
        players_box = self.query_one("#players_box", Static)
        lines: list[str] = ["[b]Players:[/b]", ""]
        for player in self.game.players:
            mark = "*" if player is self.me else " "
            token_str = format_tokens(player.tokens)
            discount_str = format_discounts(player.discounts)

            lines.append(
                f"{mark} {player.name:10}  Score={player.score:2d}  Discounts={discount_str}",
            )
            lines.append(f"    Tokens: {token_str}")

            if player.nobles:
                noble_names = ", ".join(n.name for n in player.nobles)
                lines.append(f"    Nobles: {noble_names}")

            # Optional: show counts of cards / reserved
            if player.cards:
                lines.append(f"    Cards: {len(player.cards)}")
            if player.reserved:
                lines.append(f"    Reserved: {len(player.reserved)}")

            lines.append("")
        players_box.update("\n".join(lines))


class ActionApp(App[None]):
    """Textual app that asks for a single action command and returns an Action."""

    CSS = """
    Screen {
        /* 3 rows: command zone, board, footer */
        layout: grid;
        grid-size: 1 3;
        grid-rows: auto 1fr auto;
    }

    /* Top area with input + instructions */
    #command_zone {
        grid-columns: 1;
        grid-rows: 1;
        padding: 1 1;
    }

    /* Board sits in the middle row and can grow */
    #board {
        grid-columns: 1;
        grid-rows: 2;
        padding: 0 1 1 1;
    }

    Footer {
        grid-columns: 1;
        grid-rows: 3;
    }

    Input {
        border: round $accent;
    }

    /* === Board layout === */

    #board_root {
        /* outer frame around the whole board area */
        border: heavy white;
        padding: 0 1;
    }

    /* Bank row: full width */
    #bank_box {
        border: heavy white;
        padding: 0 1;
    }

    /* Middle row: tiers (left) + nobles (right) */
    #middle_row {
        layout: horizontal;
    }

    #tiers_box {
        border: heavy white;
        padding: 0 1;
        width: 70%;
    }

    #tier1_box,
    #tier2_box,
    #tier3_box {
        border-bottom: heavy white;
        padding: 0 0 1 0;
        margin-bottom: 1;
    }

    #nobles_box {
        border: heavy white;
        padding: 0 1;
        width: 30%;
    }

    /* Players row: full width at bottom */
    #players_box {
        border: heavy white;
        padding: 0 1;
    }
    """

    def __init__(self, game: GameState, player: PlayerState) -> None:
        super().__init__()
        self.game = game
        self.player = player
        self.result: Action | None = None
        self.message: str = ""

    def compose(self) -> ComposeResult:  # type: ignore[override]
        # Row 1: input + Actions text
        with Vertical(id="command_zone"):
            yield Input(
                placeholder="Enter command, e.g. '1 white blue red' or '1 w b r' or 'q'",
                id="input_line",
            )
            yield Static("", id="prompt")

        # Row 2: board
        yield Board(self.game, self.player, id="board")

        # Row 3: footer
        yield Footer()

    def on_mount(self) -> None:  # type: ignore[override]
        self._update_prompt()
        self.query_one(Input).focus()

    def _update_prompt(self) -> None:
        lines: list[str] = []
        lines.append("[bold underline]Actions:[/]")
        lines.append(
            " [bold green]1[/] <colors...>  - Take up to 3 different gem colors "
            "(e.g. [cyan]1 white blue red[/] or [cyan]1 w b r[/])",
        )
        lines.append(
            f" [bold green]2[/] <color>      - Take 2 of the same color (needs {fmt_number(4)} in bank, "
            "e.g. [cyan]2 blue[/] or [cyan]2 b[/])",
        )
        lines.append(
            " [bold green]3[/] <tier> <idx> - Buy a face-up card (e.g. [cyan]3 1 0[/] for tier 1, index 0)",
        )
        lines.append(" [bold green]4[/] <idx>        - Buy a reserved card")
        lines.append(" [bold green]5[/] <tier> <idx> - Reserve a face-up card")
        lines.append(" [bold green]6[/] <tier>       - Reserve top card of a deck")
        lines.append(" [bold red]q[/]                - Quit game")
        if self.message:
            lines.append("")
            lines.append(f"[bold red]Message:[/] {self.message}")
        self.query_one("#prompt", Static).update("\n".join(lines))

    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        text = (event.value or "").strip()
        event.input.value = ""
        if not text:
            return
        if text.lower() in {"q", "quit", "0"}:
            self.result = None
            self.exit()
            return

        parts = text.split()
        cmd = parts[0]

        try:
            if cmd == "1":
                # Take up to 3 different gem colors: 1 white blue red  OR  1 w b r
                color_names = parts[1:]
                if not color_names:
                    raise ValueError("Need at least one color (full name or abbreviation).")
                colors: list[GemColor] = []
                for name in color_names:
                    color = parse_color_token(name)
                    if self.game.bank[color] <= 0:
                        raise ValueError(f"No tokens left for color: {color}")
                    colors.append(color)
                self.result = TakeDifferent(colors=colors[:3])
                self.exit()
                return

            if cmd == "2":
                # TakeDouble: 2 color  (full name or abbreviation)
                if len(parts) < 2:
                    raise ValueError("Usage: 2 <color>")
                raw_color = parts[1]
                color = parse_color_token(raw_color)
                if self.game.bank[color] < 4:
                    raise ValueError("Bank must have at least 4 of that color.")
                self.result = TakeDouble(color=color)
                self.exit()
                return

            if cmd == "3":
                # Buy face-up card: 3 tier index
                if len(parts) < 3:
                    raise ValueError("Usage: 3 <tier> <index>")
                tier = int(parts[1])
                idx = int(parts[2])
                self.result = BuyCard(tier=tier, index=idx)
                self.exit()
                return

            if cmd == "4":
                # Buy reserved card: 4 index
                if len(parts) < 2:
                    raise ValueError("Usage: 4 <reserved_index>")
                idx = int(parts[1])
                if not (0 <= idx < len(self.player.reserved)):
                    raise ValueError("Reserved index out of range.")
                self.result = BuyCard(tier=0, index=idx, from_reserved=True)
                self.exit()
                return

            if cmd == "5":
                # Reserve face-up card: 5 tier index
                if len(parts) < 3:
                    raise ValueError("Usage: 5 <tier> <index>")
                tier = int(parts[1])
                idx = int(parts[2])
                self.result = ReserveCard(tier=tier, index=idx, from_deck=False)
                self.exit()
                return

            if cmd == "6":
                # Reserve top of deck: 6 tier
                if len(parts) < 2:
                    raise ValueError("Usage: 6 <tier>")
                tier = int(parts[1])
                self.result = ReserveCard(tier=tier, index=None, from_deck=True)
                self.exit()
                return

            raise ValueError("Unknown command.")

        except ValueError as exc:
            self.message = str(exc)
            self._update_prompt()
            return


class DiscardApp(App[None]):
    """Textual app to choose discards when over token limit."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #command_zone {
        padding: 1 1;
    }

    #board {
        padding: 0 1 1 1;
    }

    Input {
        border: round $accent;
    }
    """

    def __init__(self, game: GameState, player: PlayerState) -> None:
        super().__init__()
        self.game = game
        self.player = player
        self.discards: dict[GemColor, int] = dict.fromkeys(GEM_COLORS, 0)
        self.message: str = ""

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header(show_clock=False)

        with Vertical(id="command_zone"):
            yield Input(
                placeholder="Enter color to discard, e.g. 'blue' or 'b'",
                id="input_line",
            )
            yield Static("", id="prompt")

        # Board directly under the command zone
        yield Board(self.game, self.player, id="board")

        yield Footer()

    def on_mount(self) -> None:  # type: ignore[override]
        self._update_prompt()
        self.query_one(Input).focus()

    def _remaining_to_discard(self) -> int:
        return self.player.total_tokens() - sum(self.discards.values()) - self.game.config.token_limit

    def _update_prompt(self) -> None:
        remaining = max(self._remaining_to_discard(), 0)
        lines: list[str] = []
        lines.append(
            "You must discard "
            f"{fmt_number(remaining)} token(s) "
            f"to get down to {fmt_number(self.game.config.token_limit)}.",
        )
        disc_str = ", ".join(f"{fmt_gem(c)}={fmt_number(self.discards[c])}" for c in GEM_COLORS)
        lines.append(f"Current planned discards: {{ {disc_str} }}")
        lines.append(
            "Type a color name or abbreviation (e.g. 'blue' or 'b') to discard one token.",
        )
        if self.message:
            lines.append("")
            lines.append(f"[bold red]Message:[/] {self.message}")
        self.query_one("#prompt", Static).update("\n".join(lines))

    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        raw = (event.value or "").strip()
        event.input.value = ""
        if not raw:
            return

        try:
            color = parse_color_token(raw)
        except ValueError:
            self.message = f"Unknown color: {raw}"
            self._update_prompt()
            return

        available = self.player.tokens[color] - self.discards[color]
        if available <= 0:
            self.message = f"No more {color} tokens available to discard."
            self._update_prompt()
            return

        self.discards[color] += 1
        if self._remaining_to_discard() <= 0:
            self.exit()
            return

        self.message = ""
        self._update_prompt()


# ---------------------------------------------------------------------------
# Noble choice app
# ---------------------------------------------------------------------------


class NobleChoiceApp(App[None]):
    """Textual app to choose one noble."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #command_zone {
        padding: 1 1;
    }

    #board {
        padding: 0 1 1 1;
    }

    Input {
        border: round $accent;
    }
    """

    def __init__(
        self,
        game: GameState,
        player: PlayerState,
        nobles: list[Noble],
    ) -> None:
        super().__init__()
        self.game = game
        self.player = player
        self.nobles = nobles
        self.result: Noble | None = None
        self.message: str = ""

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header(show_clock=False)

        with Vertical(id="command_zone"):
            yield Input(
                placeholder="Enter noble index, e.g. '0'",
                id="input_line",
            )
            yield Static("", id="prompt")

        # Board directly under the command zone
        yield Board(self.game, self.player, id="board")

        yield Footer()

    def on_mount(self) -> None:  # type: ignore[override]
        self._update_prompt()
        self.query_one(Input).focus()

    def _update_prompt(self) -> None:
        lines: list[str] = []
        lines.append("[bold underline]You qualify for nobles:[/]")
        for i, noble in enumerate(self.nobles):
            lines.append(f" [bright_cyan]{i})[/] {format_noble(noble)}")
        lines.append("Enter the index of the noble you want.")
        if self.message:
            lines.append("")
            lines.append(f"[bold red]Message:[/] {self.message}")
        self.query_one("#prompt", Static).update("\n".join(lines))

    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        raw = (event.value or "").strip()
        event.input.value = ""
        if not raw:
            return
        try:
            idx = int(raw)
        except ValueError:
            self.message = "Please enter a valid integer index."
            self._update_prompt()
            return
        if not (0 <= idx < len(self.nobles)):
            self.message = "Index out of range."
            self._update_prompt()
            return
        self.result = self.nobles[idx]
        self.exit()


class TuiHuman(Strategy):
    """Textual-based human player Strategy with colorful board."""

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        if not sys.stdout.isatty():
            return None
        app = ActionApp(game, player)
        app.run()
        return app.result

    def choose_discard(
        self,
        game: GameState,
        player: PlayerState,
        excess: int,  # noqa: ARG002
    ) -> dict[GemColor, int]:
        if not sys.stdout.isatty():
            return dict.fromkeys(GEM_COLORS, 0)
        app = DiscardApp(game, player)
        app.run()
        return app.discards

    def choose_noble(
        self,
        game: GameState,
        player: PlayerState,
        nobles: list[Noble],
    ) -> Noble:
        if not sys.stdout.isatty():
            return nobles[0]
        app = NobleChoiceApp(game, player, nobles)
        app.run()
        assert app.result is not None
        return app.result
