"""Public state for RL/search."""

from __future__ import annotations

from dataclasses import dataclass

from .base import (
    BASE_COLORS,
    BASE_INDEX,
    GEM_ORDER,
    Card,
    GameState,
    Noble,
    PlayerState,
)


@dataclass(frozen=True)
class ObsCard:
    """Numeric-ish card view for RL/search."""

    tier: int
    points: int
    color_index: int
    cost: list[int]


@dataclass(frozen=True)
class ObsNoble:
    """Numeric-ish noble view for RL/search."""

    points: int
    requirements: list[int]


@dataclass(frozen=True)
class ObsPlayer:
    """Numeric-ish player view for RL/search."""

    tokens: list[int]
    discounts: list[int]
    score: int
    cards: list[ObsCard]
    reserved: list[ObsCard]
    nobles: list[ObsNoble]


@dataclass(frozen=True)
class Observation:
    """Full public state for RL/search."""

    current_player: int
    bank: list[int]
    players: list[ObsPlayer]
    table_by_tier: dict[int, list[ObsCard]]
    decks_remaining: dict[int, int]
    available_nobles: list[ObsNoble]


def _encode_card(card: Card) -> ObsCard:
    color_index = BASE_INDEX.get(card.color, -1)
    cost_vec = [card.cost.get(c, 0) for c in BASE_COLORS]
    return ObsCard(
        tier=card.tier,
        points=card.points,
        color_index=color_index,
        cost=cost_vec,
    )


def _encode_noble(noble: Noble) -> ObsNoble:
    req_vec = [noble.requirements.get(c, 0) for c in BASE_COLORS]
    return ObsNoble(
        points=noble.points,
        requirements=req_vec,
    )


def _encode_player(player: PlayerState) -> ObsPlayer:
    tokens_vec = [player.tokens[c] for c in GEM_ORDER]
    discounts_vec = [player.discounts[c] for c in GEM_ORDER]
    cards_enc = [_encode_card(c) for c in player.cards]
    reserved_enc = [_encode_card(c) for c in player.reserved]
    nobles_enc = [_encode_noble(n) for n in player.nobles]
    return ObsPlayer(
        tokens=tokens_vec,
        discounts=discounts_vec,
        score=player.score,
        cards=cards_enc,
        reserved=reserved_enc,
        nobles=nobles_enc,
    )


def to_observation(game: GameState) -> Observation:
    """Create a structured observation of the full public state."""
    bank_vec = [game.bank[c] for c in GEM_ORDER]
    players_enc = [_encode_player(p) for p in game.players]
    table_enc: dict[int, list[ObsCard]] = {
        tier: [_encode_card(c) for c in row] for tier, row in game.table_by_tier.items()
    }
    decks_remaining = {tier: len(deck) for tier, deck in game.decks_by_tier.items()}
    nobles_enc = [_encode_noble(n) for n in game.available_nobles]
    return Observation(
        current_player=game.current_player_index,
        bank=bank_vec,
        players=players_enc,
        table_by_tier=table_enc,
        decks_remaining=decks_remaining,
        available_nobles=nobles_enc,
    )
