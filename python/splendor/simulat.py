from __future__ import annotations

from .base import GameConfig, create_random_nobles, create_random_cards, new_game, run_game
from .bot import RandomBot


def main() -> None:
    """Main entry point."""
    turn_limit = 10000
    for _ in range(1000):
        bot_a = RandomBot("bot_a")
        bot_b = RandomBot("bot_b")
        bot_c = RandomBot("bot_c")
        bot_d = RandomBot("bot_d")
        config = GameConfig(
            cards=create_random_cards(),
            nobles=create_random_nobles(),
            turn_limit=turn_limit,
        )
        players = (bot_a, bot_b, bot_c, bot_d)
        game_state = new_game(players, config)
        winner, turns = run_game(game_state)
        print(f"Winner is {winner.strategy.name} with {winner.score} points after {turns} turns.")


if __name__ == "__main__":
    main()
