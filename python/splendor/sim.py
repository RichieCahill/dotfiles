from __future__ import annotations

import copy

from .base import Action, GameState, PlayerState, apply_action, check_nobles_for_player
from .bot import RandomBot


class SimStrategy(RandomBot):
    """Strategy used in simulate_step.

    We never call choose_action here (caller chooses actions),
    but we reuse discard/noble-selection logic.
    """

    def choose_action(self, game: GameState, player: PlayerState) -> Action | None:
        msg = "SimStrategy.choose_action should not be used in simulate_step"
        raise RuntimeError(msg)


def simulate_step(game: GameState, action: Action) -> GameState:
    """Return a deep-copied next state after applying action for the current player.

    Useful for tree search / MCTS:

        next_state = simulate_step(state, action)
    """
    next_state = copy.deepcopy(game)
    sim_strategy = SimStrategy()
    apply_action(next_state, sim_strategy, action)
    check_nobles_for_player(next_state, sim_strategy, next_state.current_player)
    next_state.next_player()
    return next_state
