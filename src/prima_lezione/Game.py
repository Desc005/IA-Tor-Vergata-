"""Rules of the game.

Each turn the knight moves first, then the dragon (on the turns it is
allowed to move, see dragon_every). A move is a step to a neighbouring
open cell, or staying put if allow_stay is on.

The knight wins by reaching the goal. It loses if it and the dragon end
up on the same cell, or if it runs out of turns before reaching the goal.

Both sides are strategies with the same two methods: reset(state), called
once before each game, and next_move(state), called once per turn, which
returns the cell to move to. The dragons are in the next cell, the
knight's base class in the Knight cell.
"""

import Maze

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass



class IllegalMove(Exception):
    """A strategy returned a cell it cannot move to."""


@dataclass(frozen=True)
class GameState:
    """Everything a strategy can see on its turn."""
    maze: Maze
    knight: tuple            # (row, col)
    dragon: tuple
    goal: tuple              # the cell to reach
    turn: int                # turns played so far
    max_turns: int
    dragon_every: int        # the dragon moves once every this many turns
    allow_stay: bool
    history: tuple           # (knight, dragon) cells after each turn, starting position first

    def moves_from(self, cell):
        """Legal moves from `cell`: its open neighbours, plus `cell` itself
        if staying put is allowed (or if there is nowhere else to go)."""
        moves = self.maze.neighbours(cell)
        if self.allow_stay or not moves:
            moves.append(cell)
        return moves

    def dragon_acts_on(self, turn):
        """True if the dragon moves on the given turn (always, when dragon_every is 1)."""
        return turn % self.dragon_every == self.dragon_every - 1


@dataclass
class GameResult:
    outcome: str     # "won" or "lost", from the knight's point of view
    reason: str
    turns: int
    history: list    # (knight, dragon) cells after each turn


def maze_distances(maze, source):
    """Number of steps from `source` to every cell reachable from it."""
    dist, ring, steps = {source: 0}, {source}, 0
    while ring:
        steps += 1
        ring = {nb for cell in ring for nb in maze.neighbours(cell) if nb not in dist}
        dist.update(dict.fromkeys(ring, steps))
    return dist


# ======================================================================
# The game
# ======================================================================

class Game:
    def __init__(self, maze, knight, dragon, *, knight_start=None, dragon_start=None,
                 goal=None, max_turns=200, dragon_every=1, allow_stay=True):
        """A game between a knight strategy and a dragon strategy.

        Starting cells default to the top-left corner (knight) and the
        centre (dragon); the goal defaults to the bottom-right corner.
        """
        self.maze = maze
        self.knight_strategy, self.dragon_strategy = knight, dragon
        self.knight_start = tuple(knight_start or (0, 0))
        self.dragon_start = tuple(dragon_start or (maze.rows // 2, maze.cols // 2))
        self.goal = tuple(goal or (maze.rows - 1, maze.cols - 1))
        self.max_turns, self.dragon_every, self.allow_stay = max_turns, dragon_every, allow_stay
        self._check_setup()
        self.reset()

    def _check_setup(self):
        for name, cell in (("knight_start", self.knight_start),
                           ("dragon_start", self.dragon_start), ("goal", self.goal)):
            if not self.maze.in_bounds(cell):
                raise ValueError(f"{name} {cell} is outside the {self.maze.rows}x{self.maze.cols} maze")
        if self.knight_start == self.dragon_start:
            raise ValueError("the knight and the dragon can't start on the same cell")
        if self.goal == self.knight_start:
            raise ValueError("the knight can't start on the goal")
        if self.goal not in maze_distances(self.maze, self.knight_start):
            raise ValueError(f"the walls cut the goal {self.goal} off from the knight")
        if self.dragon_every < 1:
            raise ValueError("dragon_every must be at least 1")

    def reset(self):
        """Put both pieces back on their starting cells."""
        self.knight, self.dragon = self.knight_start, self.dragon_start
        self.turn = 0
        self.history = [(self.knight, self.dragon)]
        self.result = None
        self.knight_strategy.reset(self.state)
        self.dragon_strategy.reset(self.state)

    @property
    def state(self):
        return GameState(self.maze, self.knight, self.dragon, self.goal, self.turn,
                         self.max_turns, self.dragon_every, self.allow_stay,
                         tuple(self.history))

    def _ask(self, who, strategy, here):
        state = self.state
        move = strategy.next_move(state)
        try:
            move = tuple(int(x) for x in move)
        except (TypeError, ValueError):
            pass
        legal = state.moves_from(here)
        if move not in legal:
            raise IllegalMove(f"{strategy!r} tried to move the {who} from {here} to "
                              f"{move!r} on turn {self.turn}; legal moves were {legal}")
        return move

    def step(self):
        """Play one turn: the knight moves, then the dragon if it acts this turn.
        Returns the GameResult once the game is over, otherwise None."""
        if self.result:
            return self.result
        outcome = None
        self.knight = self._ask("knight", self.knight_strategy, self.knight)
        if self.knight == self.dragon:
            outcome = ("lost", "the knight walked into the dragon")
        elif self.knight == self.goal:
            outcome = ("won", "the knight reached the goal")
        elif self.state.dragon_acts_on(self.turn):
            self.dragon = self._ask("dragon", self.dragon_strategy, self.dragon)
            if self.dragon == self.knight:
                outcome = ("lost", "the dragon caught the knight")
        self.turn += 1
        self.history.append((self.knight, self.dragon))
        if outcome is None and self.turn >= self.max_turns:
            outcome = ("lost", "the knight ran out of turns")
        if outcome:
            self.result = GameResult(*outcome, self.turn, list(self.history))
        return self.result

    def run(self):
        """Play until the game is over and return the GameResult."""
        while not self.result:
            self.step()
        return self.result

    def __str__(self):
        marks = {self.goal: "G", self.dragon: "D"}
        marks[self.knight] = "X" if self.knight == self.dragon else "K"
        board = self.maze.render(marks, knight_path=[k for k, _ in self.history],
                                 dragon_path=[d for _, d in self.history])
        status = (f"turn {self.turn}/{self.max_turns}   knight {self.knight}   "
                  f"dragon {self.dragon}   ({self.knight_strategy!r} vs {self.dragon_strategy!r})")
        if self.result:
            status += f"\n{self.result.outcome.upper()}: {self.result.reason} ({self.result.turns} turns)"
        return board + "\n" + status

    __repr__ = __str__