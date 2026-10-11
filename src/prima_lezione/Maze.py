"""The maze: a rows x cols grid graph, drawn as text.

Each cell (row, col) is a node, and two neighbouring cells are connected
unless there is a wall between them. A new maze has no walls. You can add
them through the `walls` parameter, with add_wall(), or with random_walls().

    maze = Maze(4, 6, walls=[((0, 0), (0, 1)), ((1, 2), (2, 2))])
    print(maze)

Walls are drawn as solid blocks, and cells are separated by faint dots so
the grid stays visible even with no walls. Paths are drawn as arrows
pointing to the next cell: single arrows for the knight, double arrows
for the dragon, and a cross where both passed.
"""
import random

DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))  # up, down, left, right

WALL, DOT, BOTH = "█", "·", "✕"
ARROWS = {
    "knight": {(-1, 0): "↑", (1, 0): "↓", (0, -1): "←", (0, 1): "→"},
    "dragon": {(-1, 0): "⇑", (1, 0): "⇓", (0, -1): "⇐", (0, 1): "⇒"},
}


def manhattan(a, b):
    """Grid distance between two cells, ignoring walls."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def path_arrows(path, arrows):
    """{cell: arrow pointing to the next cell on the path}. A cell visited
    more than once keeps its latest arrow; the last cell gets none."""
    out = {}
    for a, b in zip(path, path[1:]):
        if a != b:
            out[tuple(a)] = arrows[(b[0] - a[0], b[1] - a[1])]
    return out


class Maze:
    def __init__(self, rows=10, cols=None, walls=()):
        """A rows x cols maze (square if cols is omitted).

        `walls` is a list of pairs of neighbouring cells with a wall between
        them, e.g. [((0, 0), (0, 1))] puts a wall between the two top-left
        cells.
        """
        self.rows = rows
        self.cols = rows if cols is None else cols
        self.walls = set()
        for a, b in walls:
            self.add_wall(a, b)

    # ---------- cells and walls ----------

    def in_bounds(self, cell):
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def cells(self):
        """All cells, row by row."""
        return [(r, c) for r in range(self.rows) for c in range(self.cols)]

    def _edge(self, a, b):
        a, b = tuple(a), tuple(b)
        if not (self.in_bounds(a) and self.in_bounds(b)) or manhattan(a, b) != 1:
            raise ValueError(
                f"a wall must separate two neighbouring cells inside the "
                f"{self.rows}x{self.cols} maze, got {a} and {b}")
        return frozenset((a, b))

    def add_wall(self, a, b):
        self.walls.add(self._edge(a, b))

    def is_open(self, a, b):
        """True if you can step directly from cell a to cell b."""
        return (self.in_bounds(a) and self.in_bounds(b) and manhattan(a, b) == 1
                and frozenset((a, b)) not in self.walls)

    # ---------- graph view ----------

    def neighbours(self, cell):
        """Cells you can step to from `cell` (up, down, left, right)."""
        r, c = cell
        return [(r + dr, c + dc) for dr, dc in DIRECTIONS
                if self.is_open(cell, (r + dr, c + dc))]

    def adjacency(self):
        """The whole maze as an adjacency list: {cell: [neighbours]}."""
        return {cell: self.neighbours(cell) for cell in self.cells()}

    # ---------- drawing ----------

    def _wall_above(self, r, c):
        """Wall on the top edge of cell (r, c); r == rows is the bottom border."""
        return r in (0, self.rows) or not self.is_open((r - 1, c), (r, c))

    def _wall_left(self, r, c):
        """Wall on the left edge of cell (r, c); c == cols is the right border."""
        return c in (0, self.cols) or not self.is_open((r, c - 1), (r, c))

    def _wall_at_corner(self, r, c):
        """True if any wall segment touches the corner point (r, c)."""
        return ((c < self.cols and self._wall_above(r, c))
                or (c > 0 and self._wall_above(r, c - 1))
                or (r < self.rows and self._wall_left(r, c))
                or (r > 0 and self._wall_left(r - 1, c)))

    def render(self, marks=None, knight_path=(), dragon_path=()):
        """The maze as text.

        `marks` maps cells to single characters, e.g. {(0, 0): "K"}, and is
        drawn on top of the paths; `knight_path` and `dragon_path` are
        lists of cells, drawn as arrows.
        """
        km = path_arrows(list(knight_path), ARROWS["knight"])
        dm = path_arrows(list(dragon_path), ARROWS["dragon"])
        symbols = {cell: BOTH if cell in km and cell in dm else km.get(cell) or dm[cell]
                   for cell in set(km) | set(dm)}
        symbols.update({tuple(cell): ch for cell, ch in (marks or {}).items()})

        lines = []
        for r in range(self.rows + 1):
            line = ""
            for c in range(self.cols + 1):
                line += WALL if self._wall_at_corner(r, c) else DOT
                if c < self.cols:
                    line += WALL * 3 if self._wall_above(r, c) else "   "
            lines.append(line)
            if r < self.rows:
                line = ""
                for c in range(self.cols + 1):
                    line += WALL if self._wall_left(r, c) else " "
                    if c < self.cols:
                        line += " " + symbols.get((r, c), " ") + " "
                lines.append(line)
        return "\n".join(lines)

    def __str__(self):
        return self.render()

    __repr__ = __str__  # Jupyter shows this when a maze ends a cell


def random_walls(rows, cols=None, density=0.8, seed=None):
    """Walls for a random maze in which every cell can be reached.

    It first builds a "perfect" maze, with exactly one path between any two
    cells, by randomised depth-first search, then keeps each of its walls
    with probability `density`. density=1 gives the perfect maze, which has
    no loops, so a dragon can always corner the knight in a dead end; lower
    values knock walls down and open up loops; density=0 gives no walls.
    """
    cols = rows if cols is None else cols
    rng = random.Random(seed)
    seen, stack, passages = {(0, 0)}, [(0, 0)], set()
    while stack:
        r, c = stack[-1]
        options = [(r + dr, c + dc) for dr, dc in DIRECTIONS
                   if 0 <= r + dr < rows and 0 <= c + dc < cols
                   and (r + dr, c + dc) not in seen]
        if options:
            nxt = rng.choice(options)
            seen.add(nxt)
            stack.append(nxt)
            passages.add(frozenset(((r, c), nxt)))
        else:
            stack.pop()

    walls = []
    for r in range(rows):
        for c in range(cols):
            for nb in ((r, c + 1), (r + 1, c)):
                if nb[0] < rows and nb[1] < cols:
                    if frozenset(((r, c), nb)) not in passages and rng.random() < density:
                        walls.append(((r, c), nb))
    return walls