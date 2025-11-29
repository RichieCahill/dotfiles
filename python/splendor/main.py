"""Main entry point for Splendor game."""

from __future__ import annotations

from .base import new_game, run_game
from .bot import RandomBot
from .human import TuiHuman


def main() -> None:
    """Main entry point."""
    human = TuiHuman()
    bot = RandomBot()
    game_state = new_game(["You", "Bot A"])
    run_game(game_state, [human, bot])


if __name__ == "__main__":
    main()
