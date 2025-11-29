"""Bot for Splendor game."""

from __future__ import annotations

import random

from .base import (
    BASE_COLORS,
    Action,
    BuyCard,
    BuyCardReserved,
    Card,
    GameState,
    GemColor,
    PlayerState,
    ReserveCard,
    Strategy,
    TakeDifferent,
    TakeDouble,
    auto_discard_tokens,
    get_legal_actions,
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

    def __init__(self, name: str) -> None:
        """Initialize the bot."""
        super().__init__(name=name)

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        """Choose an action for the current player."""
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
        game: GameState,  # noqa: ARG002
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        """Choose how many tokens to discard."""
        return auto_discard_tokens(player, excess)


def check_cards_in_tier(row: list[Card], player: PlayerState) -> list[int]:
    """Check if player can afford card, using discounts + gold."""
    return [index for index, card in enumerate(row) if can_bot_afford(player, card)]


class PersonalizedBot(Strategy):
    """PersonalizedBot."""

    """Dumb bot that follows rules but doesn't think."""

    def __init__(self, name: str) -> None:
        """Initialize the bot."""
        super().__init__(name=name)

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        """Choose an action for the current player."""
        for tier in (1, 2, 3):
            row = game.table_by_tier[tier]
            if affordable := check_cards_in_tier(row, player):
                index = random.choice(affordable)
                return BuyCard(tier=tier, index=index)

        colors_for_diff = [c for c in BASE_COLORS if game.bank[c] > 0]
        random.shuffle(colors_for_diff)
        return TakeDifferent(colors=colors_for_diff[:3])

    def choose_discard(
        self,
        game: GameState,  # noqa: ARG002
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        """Choose how many tokens to discard."""
        return auto_discard_tokens(player, excess)


class PersonalizedBot2(Strategy):
    """PersonalizedBot2."""

    """Dumb bot that follows rules but doesn't think."""

    def __init__(self, name: str) -> None:
        """Initialize the bot."""
        super().__init__(name=name)

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        """Choose an action for the current player."""
        tiers = (1, 2, 3)
        for tier in tiers:
            row = game.table_by_tier[tier]
            if affordable := check_cards_in_tier(row, player):
                index = random.choice(affordable)
                return BuyCard(tier=tier, index=index)

        if affordable := check_cards_in_tier(player.reserved, player):
            index = random.choice(affordable)
            return BuyCardReserved(index=index)

        colors_for_diff = [c for c in BASE_COLORS if game.bank[c] > 0]
        if len(colors_for_diff) >= 3:
            random.shuffle(colors_for_diff)
            return TakeDifferent(colors=colors_for_diff[:3])

        for tier in tiers:
            len_deck = len(game.decks_by_tier[tier])
            if len_deck:
                return ReserveCard(tier=tier, index=None, from_deck=True)

        return TakeDifferent(colors=colors_for_diff[:3])

    def choose_discard(
        self,
        game: GameState,  # noqa: ARG002
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        """Choose how many tokens to discard."""
        return auto_discard_tokens(player, excess)


def buy_card_reserved(player: PlayerState) -> Action | None:
    """Buy a card reserved."""
    if affordable := check_cards_in_tier(player.reserved, player):
        index = random.choice(affordable)
        return BuyCardReserved(index=index)
    return None


def buy_card(game: GameState, player: PlayerState) -> Action | None:
    """Buy a card."""
    for tier in (1, 2, 3):
        row = game.table_by_tier[tier]
        if affordable := check_cards_in_tier(row, player):
            index = random.choice(affordable)
            return BuyCard(tier=tier, index=index)
    return None


def take_tokens(game: GameState) -> Action | None:
    """Take tokens."""
    colors_for_diff = [color for color in BASE_COLORS if game.bank[color] > 0]
    if len(colors_for_diff) >= 3:
        random.shuffle(colors_for_diff)
        return TakeDifferent(colors=colors_for_diff[: game.config.max_token_take])
    return None


class PersonalizedBot3(Strategy):
    """PersonalizedBot3."""

    """Dumb bot that follows rules but doesn't think."""

    def __init__(self, name: str) -> None:
        """Initialize the bot."""
        super().__init__(name=name)

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        """Choose an action for the current player."""
        print(len(get_legal_actions(game, player)))
        print(get_legal_actions(game, player))
        if action := buy_card_reserved(player):
            return action
        if action := buy_card(game, player):
            return action

        colors_for_diff = [color for color in BASE_COLORS if game.bank[color] > 0]
        if len(colors_for_diff) >= 3:
            random.shuffle(colors_for_diff)
            return TakeDifferent(colors=colors_for_diff[:3])

        for tier in (1, 2, 3):
            len_deck = len(game.decks_by_tier[tier])
            if len_deck:
                return ReserveCard(tier=tier, index=None, from_deck=True)

        return TakeDifferent(colors=colors_for_diff[:3])

    def choose_discard(
        self,
        game: GameState,  # noqa: ARG002
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        """Choose how many tokens to discard."""
        return auto_discard_tokens(player, excess)


def estimate_value_of_card(game: GameState, player: PlayerState, color: GemColor) -> int:
    """Estimate value of a color in the player's bank."""
    return game.bank[color] - player.discounts.get(color, 0)


def estimate_value_of_token(game: GameState, player: PlayerState, color: GemColor) -> int:
    """Estimate value of a color in the player's bank."""
    return game.bank[color] - player.discounts.get(color, 0)


class PersonalizedBot4(Strategy):
    """PersonalizedBot4."""

    def __init__(self, name: str) -> None:
        """Initialize the bot."""
        super().__init__(name=name)

    def filter_actions(self, actions: list[Action]) -> list[Action]:
        """Filter actions to only take different."""
        return [
            action
            for action in actions
            if (isinstance(action, TakeDifferent) and len(action.colors) == 3) or not isinstance(action, TakeDifferent)
        ]

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        """Choose an action for the current player."""
        legal_actions = get_legal_actions(game, player)
        print(len(legal_actions))

        good_actions = self.filter_actions(legal_actions)
        print(len(good_actions))

        print(good_actions)

        print(len(get_legal_actions(game, player)))
        if action := buy_card_reserved(player):
            return action
        if action := buy_card(game, player):
            return action

        colors_for_diff = [color for color in BASE_COLORS if game.bank[color] > 0]
        if len(colors_for_diff) >= 3:
            random.shuffle(colors_for_diff)
            return TakeDifferent(colors=colors_for_diff[:3])

        for tier in (1, 2, 3):
            len_deck = len(game.decks_by_tier[tier])
            if len_deck:
                return ReserveCard(tier=tier, index=None, from_deck=True)

        return TakeDifferent(colors=colors_for_diff[:3])

    def choose_discard(
        self,
        game: GameState,  # noqa: ARG002
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        """Choose how many tokens to discard."""
        return auto_discard_tokens(player, excess)
