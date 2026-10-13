#%%
"""The dragon's strategies, roughly from easiest to hardest: StaticDragon,
GuardDragon, GreedyDragon and ChaserDragon.

A dragon has the same two methods as a knight: reset(state), called once
before each game, and next_move(state), called on the dragon's turns,
which returns the cell to move to.
"""
from abc import ABC, abstractmethod
from Maze import manhattan
from Game import maze_distances

class DragonStrategy(ABC):
    def reset(self, state):
        """Called once before each game with the starting state."""

    @abstractmethod
    def next_move(self, state):
        """Return the cell the dragon moves to: one of state.moves_from(state.dragon)."""

    def __repr__(self):
        return type(self).__name__


def _towards(state, target):
    """The dragon's move that brings it closest to `target` through the maze."""
    dist = maze_distances(state.maze, target)
    return min(state.moves_from(state.dragon), key=lambda cell: dist.get(cell, float("inf")))


class StaticDragon(DragonStrategy):
    """Sleeps where it stands."""

    def next_move(self, state):
        moves = state.moves_from(state.dragon)
        return state.dragon if state.dragon in moves else moves[0]


class GreedyDragon(DragonStrategy):
    """Steps towards the knight as the crow flies, ignoring walls, so it
    gets stuck behind them."""

    def next_move(self, state):
        return min(state.moves_from(state.dragon),
                   key=lambda cell: manhattan(cell, state.knight))


class ChaserDragon(DragonStrategy):
    """Follows the shortest path through the maze to the knight."""

    def next_move(self, state):
        return _towards(state, state.knight)


class GuardDragon(DragonStrategy):
    """Guards its lair (by default the cell it starts on). It chases the
    knight only while the knight is within `radius` steps of the lair, and
    otherwise goes back to it."""

    def __init__(self, radius=3, lair=None):
        self.radius, self.lair = radius, lair

    def reset(self, state):
        self._lair = tuple(self.lair) if self.lair is not None else state.dragon

    def next_move(self, state):
        to_lair = maze_distances(state.maze, self._lair)
        intruder = to_lair.get(state.knight, float("inf")) <= self.radius
        return _towards(state, state.knight if intruder else self._lair)
