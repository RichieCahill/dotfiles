"""Base logic for the Splendor game."""

from __future__ import annotations

import itertools
import json
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

GemColor = Literal["white", "blue", "green", "red", "black", "gold"]

GEM_COLORS: tuple[GemColor, ...] = (
    "white",
    "blue",
    "green",
    "red",
    "black",
    "gold",
)
BASE_COLORS: tuple[GemColor, ...] = (
    "white",
    "blue",
    "green",
    "red",
    "black",
)

GEM_ORDER: list[GemColor] = list(GEM_COLORS)
GEM_INDEX: dict[GemColor, int] = {c: i for i, c in enumerate(GEM_ORDER)}
BASE_INDEX: dict[GemColor, int] = {c: i for i, c in enumerate(BASE_COLORS)}


@dataclass(frozen=True)
class Card:
    """Development card: gives points + a permanent gem discount."""

    tier: int
    points: int
    color: GemColor
    cost: dict[GemColor, int]


@dataclass(frozen=True)
class Noble:
    """Noble tile: gives points if you have enough bonuses."""

    name: str
    points: int
    requirements: dict[GemColor, int]


@dataclass
class PlayerState:
    """State of a player in the game."""

    strategy: Strategy
    tokens: dict[GemColor, int] = field(default_factory=lambda: dict.fromkeys(GEM_COLORS, 0))
    discounts: dict[GemColor, int] = field(default_factory=lambda: dict.fromkeys(GEM_COLORS, 0))
    cards: list[Card] = field(default_factory=list)
    reserved: list[Card] = field(default_factory=list)
    nobles: list[Noble] = field(default_factory=list)
    card_score: int = 0
    noble_score: int = 0

    def total_tokens(self) -> int:
        """Total tokens in player's bank."""
        return sum(self.tokens.values())

    def add_noble(self, noble: Noble) -> None:
        """Add a noble to the player."""
        self.nobles.append(noble)
        self.noble_score = sum(noble.points for noble in self.nobles)

    def add_card(self, card: Card) -> None:
        """Add a card to the player."""
        self.cards.append(card)
        self.card_score = sum(card.points for card in self.cards)

    @property
    def score(self) -> int:
        """Total points in player's cards + nobles."""
        return self.card_score + self.noble_score

    def can_afford(self, card: Card) -> bool:
        """Check if player can afford card, using discounts + gold."""
        missing = 0
        gold = self.tokens["gold"]

        for color, cost in card.cost.items():
            missing += max(0, cost - self.discounts.get(color, 0) - self.tokens.get(color, 0))
            if missing > gold:
                return False

        return True

    def pay_for_card(self, card: Card) -> dict[GemColor, int]:
        """Pay tokens for card, move card to tableau, return payment for bank."""
        if not self.can_afford(card):
            msg = f"{self.name} cannot afford card {card}"
            raise ValueError(msg)

        payment: dict[GemColor, int] = dict.fromkeys(GEM_COLORS, 0)
        gold_available = self.tokens["gold"]

        for color in BASE_COLORS:
            cost = card.cost.get(color, 0)
            effective_cost = max(0, cost - self.discounts.get(color, 0))

            use = min(self.tokens[color], effective_cost)
            self.tokens[color] -= use
            payment[color] += use

            remaining = effective_cost - use
            if remaining > 0:
                use_gold = min(gold_available, remaining)
                gold_available -= use_gold
                self.tokens["gold"] -= use_gold
                payment["gold"] += use_gold

        self.add_card(card)
        self.discounts[card.color] += 1
        return payment


def get_default_starting_tokens(player_count: int) -> dict[GemColor, int]:
    """get_default_starting_tokens."""
    token_count = (player_count * player_count - 3 * player_count + 10) // 2
    return {
        "white": token_count,
        "blue": token_count,
        "green": token_count,
        "red": token_count,
        "black": token_count,
        "gold": 5,
    }


@dataclass
class GameConfig:
    """Game configuration: gems, bank, cards, nobles, etc."""

    win_score: int = 15
    table_cards_per_tier: int = 4
    reserve_limit: int = 3
    token_limit: int = 10
    turn_limit: int = 1000
    minimum_tokens_to_buy_2: int = 4
    max_token_take: int = 3

    cards: list[Card] = field(default_factory=list)
    nobles: list[Noble] = field(default_factory=list)


class GameState:
    """Game state: players, bank, decks, table, available nobles, etc."""

    def __init__(
        self,
        config: GameConfig,
        players: list[PlayerState],
        bank: dict[GemColor, int],
        decks_by_tier: dict[int, list[Card]],
        table_by_tier: dict[int, list[Card]],
        available_nobles: list[Noble],
    ) -> None:
        """Game state."""
        self.config = config
        self.players = players
        self.bank = bank
        self.decks_by_tier = decks_by_tier
        self.table_by_tier = table_by_tier
        self.available_nobles = available_nobles
        self.noble_min_requirements = 0
        self.get_noble_min_requirements()
        self.current_player_index = 0
        self.finished = False

    def get_noble_min_requirements(self) -> None:
        """Find the minimum requirement for all available nobles."""
        test = 0

        for noble in self.available_nobles:
            test = max(test, min(foo for foo in noble.requirements.values()))

        self.noble_min_requirements = test

    def next_player(self) -> None:
        """Advance to the next player."""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    @property
    def current_player(self) -> PlayerState:
        """Current player."""
        return self.players[self.current_player_index]

    def refill_table(self) -> None:
        """Refill face-up cards from decks."""
        for tier, deck in self.decks_by_tier.items():
            table = self.table_by_tier[tier]
            while len(table) < self.config.table_cards_per_tier and deck:
                table.append(deck.pop())

    def check_winner_simple(self) -> PlayerState | None:
        """Simplified: end immediately when someone hits win_score."""
        eligible = [player for player in self.players if player.score >= self.config.win_score]
        if not eligible:
            return None
        eligible.sort(
            key=lambda p: (p.score, -len(p.cards)),
            reverse=True,
        )
        self.finished = True
        return eligible[0]


class Action:
    """Marker protocol for actions."""


@dataclass
class TakeDifferent(Action):
    """Take up to 3 different gem colors."""

    colors: list[GemColor]


@dataclass
class TakeDouble(Action):
    """Take two of the same color."""

    color: GemColor


@dataclass
class BuyCard(Action):
    """Buy a face-up card."""

    tier: int
    index: int


@dataclass
class BuyCardReserved(Action):
    """Buy a face-up card."""

    tier: int
    index: int


@dataclass
class ReserveCard(Action):
    """Reserve a face-up card."""

    tier: int
    index: int | None = None
    from_deck: bool = False


class Strategy(Protocol):
    """Implement this to make a bot or human controller."""

    def __init__(self, name: str) -> None:
        """Initialize a strategy."""
        self.name = name

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        """Return an Action, or None to concede/end."""
        raise NotImplementedError

    def choose_discard(
        self,
        game: GameState,  # noqa: ARG002
        player: PlayerState,
        excess: int,
    ) -> dict[GemColor, int]:
        """Called if player has more than token_limit tokens after an action.

        Default: naive auto-discard.
        """
        return auto_discard_tokens(player, excess)

    def choose_noble(
        self,
        game: GameState,  # noqa: ARG002
        player: PlayerState,  # noqa: ARG002
        nobles: list[Noble],
    ) -> Noble:
        """Called if player qualifies for multiple nobles. Default: first."""
        return nobles[0]


def auto_discard_tokens(player: PlayerState, excess: int) -> dict[GemColor, int]:
    """Very dumb discard logic: discard from colors you have the most of."""
    to_discard: dict[GemColor, int] = dict.fromkeys(GEM_COLORS, 0)
    remaining = excess
    while remaining > 0:
        color = max(player.tokens, key=lambda c: player.tokens[c])
        if player.tokens[color] == 0:
            break
        player.tokens[color] -= 1
        to_discard[color] += 1
        remaining -= 1
    return to_discard


def enforce_token_limit(
    game: GameState,
    strategy: Strategy,
    player: PlayerState,
) -> None:
    """If player has more than token_limit tokens, force discards."""
    limit = game.config.token_limit
    total = player.total_tokens()
    if total <= limit:
        return
    excess = total - limit
    discards = strategy.choose_discard(game, player, excess)
    for color, amount in discards.items():
        available = player.tokens[color]
        to_remove = min(amount, available)
        if to_remove <= 0:
            continue
        player.tokens[color] -= to_remove
        game.bank[color] += to_remove
    remaining = player.total_tokens() - limit
    if remaining > 0:
        auto = auto_discard_tokens(player, remaining)
        for color, amount in auto.items():
            game.bank[color] += amount


def _check_nobles_for_player(player: PlayerState, noble: Noble) -> bool:
    # this rule is slower
    for color, cost in noble.requirements.items():  # noqa: SIM110
        if player.discounts[color] < cost:
            return False
    return True


def check_nobles_for_player(
    game: GameState,
    strategy: Strategy,
    player: PlayerState,
) -> None:
    """Award at most one noble to player if they qualify."""
    if game.noble_min_requirements > max(player.discounts.values()):
        return

    candidates = [noble for noble in game.available_nobles if _check_nobles_for_player(player, noble)]

    if not candidates:
        return

    chosen = candidates[0] if len(candidates) == 1 else strategy.choose_noble(game, player, candidates)

    if chosen not in game.available_nobles:
        return
    game.available_nobles.remove(chosen)
    game.get_noble_min_requirements()

    player.add_noble(chosen)


def apply_take_different(game: GameState, strategy: Strategy, action: TakeDifferent) -> None:
    """Mutate game state according to action."""
    player = game.current_player

    colors = [color for color in action.colors if color in BASE_COLORS and game.bank[color] > 0]
    if not (1 <= len(colors) <= game.config.max_token_take):
        return

    for color in colors:
        game.bank[color] -= 1
        player.tokens[color] += 1

    enforce_token_limit(game, strategy, player)


def apply_take_double(game: GameState, strategy: Strategy, action: TakeDouble) -> None:
    """Mutate game state according to action."""
    player = game.current_player
    color = action.color
    if color not in BASE_COLORS:
        return
    if game.bank[color] < game.config.minimum_tokens_to_buy_2:
        return
    game.bank[color] -= 2
    player.tokens[color] += 2
    enforce_token_limit(game, strategy, player)


def apply_buy_card(game: GameState, _strategy: Strategy, action: BuyCard) -> None:
    """Mutate game state according to action."""
    player = game.current_player

    row = game.table_by_tier.get(action.tier)
    if row is None or not (0 <= action.index < len(row)):
        return
    card = row[action.index]
    if not player.can_afford(card):
        return
    row.pop(action.index)
    payment = player.pay_for_card(card)
    for color, amount in payment.items():
        game.bank[color] += amount
    game.refill_table()


def apply_buy_card_reserved(game: GameState, _strategy: Strategy, action: BuyCardReserved) -> None:
    """Mutate game state according to action."""
    player = game.current_player
    if not (0 <= action.index < len(player.reserved)):
        return
    card = player.reserved[action.index]
    if not player.can_afford(card):
        return
    player.reserved.pop(action.index)
    payment = player.pay_for_card(card)
    for color, amount in payment.items():
        game.bank[color] += amount


def apply_reserve_card(game: GameState, strategy: Strategy, action: ReserveCard) -> None:
    """Mutate game state according to action."""
    player = game.current_player

    if len(player.reserved) >= game.config.reserve_limit:
        return

    card: Card | None = None
    if action.from_deck:
        deck = game.decks_by_tier.get(action.tier)
        if deck:
            card = deck.pop()
    else:
        row = game.table_by_tier.get(action.tier)
        if row is None:
            return
        if action.index is None or not (0 <= action.index < len(row)):
            return
        card = row.pop(action.index)
        game.refill_table()

    if card is None:
        return
    player.reserved.append(card)

    if game.bank["gold"] > 0:
        game.bank["gold"] -= 1
        player.tokens["gold"] += 1
        enforce_token_limit(game, strategy, player)


def apply_action(game: GameState, strategy: Strategy, action: Action) -> None:
    """Mutate game state according to action."""
    actions = {
        TakeDifferent: apply_take_different,
        TakeDouble: apply_take_double,
        BuyCard: apply_buy_card,
        ReserveCard: apply_reserve_card,
        BuyCardReserved: apply_buy_card_reserved,
    }
    action_func = actions.get(type(action))
    if action_func is None:
        msg = f"Unknown action type: {type(action)}"
        raise ValueError(msg)
    action_func(game, strategy, action)


def legal_actions(
    game: GameState,
    player_index: int | None = None,
) -> list[Action]:
    """Enumerate all syntactically legal actions for the given player.

    This enforces:
    - token-taking rules
    - reserve limits
    - affordability for buys
    """
    if player_index is None:
        player_index = game.current_player_index
    player = game.players[player_index]

    actions: list[Action] = []

    colors_available = [c for c in BASE_COLORS if game.bank[c] > 0]
    for r in (1, 2, 3):
        actions.extend(TakeDifferent(colors=list(combo)) for combo in itertools.combinations(colors_available, r))

    actions.extend(
        TakeDouble(color=color) for color in BASE_COLORS if game.bank[color] >= game.config.minimum_tokens_to_buy_2
    )

    for tier, row in game.table_by_tier.items():
        for idx, card in enumerate(row):
            if player.can_afford(card):
                actions.append(BuyCard(tier=tier, index=idx))

    for idx, card in enumerate(player.reserved):
        if player.can_afford(card):
            actions.append(BuyCard(tier=0, index=idx, from_reserved=True))

    if len(player.reserved) < game.config.reserve_limit:
        for tier, row in game.table_by_tier.items():
            for idx, _ in enumerate(row):
                actions.append(
                    ReserveCard(tier=tier, index=idx, from_deck=False),
                )
        for tier, deck in game.decks_by_tier.items():
            if deck:
                actions.append(
                    ReserveCard(tier=tier, index=None, from_deck=True),
                )

    return actions


def create_random_cards_tier(
    tier: int,
    card_count: int,
    cost_choices: list[int],
    point_choices: list[int],
) -> list[Card]:
    """Create a random set of cards for a given tier."""
    cards: list[Card] = []

    for color in BASE_COLORS:
        for _ in range(card_count):
            cost = dict.fromkeys(GEM_COLORS, 0)
            for c in BASE_COLORS:
                if c == color:
                    continue
                cost[c] = random.choice(cost_choices)
            points = random.choice(point_choices)
            cards.append(Card(tier=tier, points=points, color=color, cost=cost))

    return cards


def create_random_cards() -> list[Card]:
    """Generate a generic but Splendor-ish set of cards.

    This is not the official deck, but structured similarly enough for play.
    """
    cards: list[Card] = []
    cards.extend(
        create_random_cards_tier(
            tier=1,
            card_count=5,
            cost_choices=[0, 1, 1, 2],
            point_choices=[0, 0, 1],
        )
    )
    cards.extend(
        create_random_cards_tier(
            tier=2,
            card_count=4,
            cost_choices=[2, 3, 4],
            point_choices=[1, 2, 2, 3],
        )
    )
    cards.extend(
        create_random_cards_tier(
            tier=3,
            card_count=3,
            cost_choices=[4, 5, 6],
            point_choices=[3, 4, 5],
        )
    )

    random.shuffle(cards)
    return cards


def create_random_nobles() -> list[Noble]:
    """A small set of noble tiles, roughly Splendor-ish."""
    nobles: list[Noble] = []

    base_requirements: list[dict[GemColor, int]] = [
        {"white": 3, "blue": 3, "green": 3},
        {"blue": 3, "green": 3, "red": 3},
        {"green": 3, "red": 3, "black": 3},
        {"red": 3, "black": 3, "white": 3},
        {"black": 3, "white": 3, "blue": 3},
        {"white": 4, "blue": 4},
        {"green": 4, "red": 4},
        {"blue": 4, "black": 4},
    ]

    for idx, req in enumerate(base_requirements, start=1):
        nobles.append(
            Noble(
                name=f"Noble {idx}",
                points=3,
                requirements=dict(req.items()),
            ),
        )
    return nobles


def load_nobles(file: Path) -> list[Noble]:
    """Load nobles from a file."""
    nobles = json.loads(file.read_text())
    return [Noble(**noble) for noble in nobles]


def load_cards(file: Path) -> list[Card]:
    """Load cards from a file."""
    cards = json.loads(file.read_text())
    return [Card(**card) for card in cards]


def new_game(
    strategies: Sequence[Strategy],
    config: GameConfig,
) -> GameState:
    """Create a new game state from a config + list of players."""
    num_players = len(strategies)
    bank = get_default_starting_tokens(num_players)

    decks_by_tier: dict[int, list[Card]] = {1: [], 2: [], 3: []}
    for card in config.cards:
        decks_by_tier.setdefault(card.tier, []).append(card)
    for deck in decks_by_tier.values():
        random.shuffle(deck)

    table_by_tier: dict[int, list[Card]] = {1: [], 2: [], 3: []}
    players = [PlayerState(strategy=strategy) for strategy in strategies]

    nobles = list(config.nobles)
    random.shuffle(nobles)
    nobles = nobles[: num_players + 1]

    game = GameState(
        config=config,
        players=players,
        bank=bank,
        decks_by_tier=decks_by_tier,
        table_by_tier=table_by_tier,
        available_nobles=nobles,
    )
    game.refill_table()
    return game


def run_game(game: GameState) -> tuple[PlayerState, int]:
    """Run a full game loop until someone wins or a player returns None."""
    turn_count = 0
    while not game.finished:
        turn_count += 1
        player = game.current_player
        strategy = player.strategy
        action = strategy.choose_action(game, player)
        if action is None:
            game.finished = True
            break

        apply_action(game, strategy, action)
        check_nobles_for_player(game, strategy, player)

        winner = game.check_winner_simple()
        if winner is not None:
            return winner, turn_count

        game.next_player()
        if turn_count >= game.config.turn_limit:
            break

    fallback = max(game.players, key=lambda player: player.score)
    return fallback, turn_count
