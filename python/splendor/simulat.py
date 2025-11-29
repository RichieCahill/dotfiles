"""Simulator for Splendor game."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean

from .base import GameConfig, load_cards, load_nobles, new_game, run_game
from .bot import PersonalizedBot4, RandomBot


def main() -> None:
    """Main entry point."""
    turn_limit = 1000
    good_games = 0
    games = 1
    winners: dict[str, list] = defaultdict(list)
    game_data = Path(__file__).parent / "game_data"

    cards = load_cards(game_data / "cards/default.json")
    nobles = load_nobles(game_data / "nobles/default.json")

    for _ in range(games):
        bot_a = RandomBot("bot_a")
        bot_b = RandomBot("bot_b")
        bot_c = RandomBot("bot_c")
        bot_d = PersonalizedBot4("my_bot")
        config = GameConfig(
            cards=cards,
            nobles=nobles,
            turn_limit=turn_limit,
        )
        players = (bot_a, bot_b, bot_c, bot_d)
        game_state = new_game(players, config)
        winner, turns = run_game(game_state)
        if turns < turn_limit:
            good_games += 1
            winners[winner.strategy.name].append(turns)

    print(
        f"out of {games} {turn_limit} turn games with {len(players)}"
        f"random bots there where {good_games} games where a bot won"
    )
    for name, turns in winners.items():
        print(f"{name} won {len(turns)} games in {mean(turns):.2f} turns")


if __name__ == "__main__":
    main()
