"""Bot for Splendor game."""

from __future__ import annotations

import random

from .base import (
    BASE_COLORS,
    Action,
    BuyCard,
    Card,
    GameState,
    GemColor,
    PlayerState,
    ReserveCard,
    Strategy,
    TakeDifferent,
    TakeDouble,
    auto_discard_tokens,
)


def can_bot_afford(player: PlayerState, card: Card) -> bool:
    """Check if player can afford card, using discounts + gold."""
    missing = 0
    gold = player.tokens["gold"]
    for color, cost in card.cost.items():
        missing += max(0, cost - player.discounts.get(color, 0) - player.tokens.get(color, 0))
        if missing > gold:
            return False

    return True


class RandomBot(Strategy):
    """Dumb bot that follows rules but doesn't think."""

    def __init__(self, name: str = "Bot") -> None:
        super().__init__(name=name)

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        affordable: list[tuple[int, int]] = []
        for tier, row in game.table_by_tier.items():
            for idx, card in enumerate(row):
                if can_bot_afford(player, card):
                    affordable.append((tier, idx))
        if affordable and random.random() < 0.5:
            tier, idx = random.choice(affordable)
            return BuyCard(tier=tier, index=idx)

        if random.random() < 0.2:
            tier = random.choice([1, 2, 3])
            row = game.table_by_tier.get(tier, [])
            if row:
                idx = random.randrange(len(row))
                return ReserveCard(tier=tier, index=idx, from_deck=False)

        if random.random() < 0.5:
            colors_for_double = [c for c in BASE_COLORS if game.bank[c] >= 4]
            if colors_for_double:
                return TakeDouble(color=random.choice(colors_for_double))

        colors_for_diff = [c for c in BASE_COLORS if game.bank[c] > 0]
        random.shuffle(colors_for_diff)
        return TakeDifferent(colors=colors_for_diff[:3])

    def choose_discard(
        self,
        game: GameState,
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        return auto_discard_tokens(player, excess)
