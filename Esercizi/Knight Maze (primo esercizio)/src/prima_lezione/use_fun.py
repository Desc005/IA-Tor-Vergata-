import time
import Maze
import Game
from collections import Counter
from Maze import random_walls
from config import CONFIG

def as_strategy(spec, who):
    """A strategy class is instantiated; an instance is used as it is."""
    strategy = spec() if isinstance(spec, type) else spec
    if not hasattr(strategy, "next_move"):
        raise TypeError(f"the {who} must be a strategy class or an instance of one, got {spec!r}")
    return strategy


def make_maze(size=10, walls=None, density=0.8, seed=None):
    rows, cols = (size, size) if isinstance(size, int) else size
    if walls is None:
        return Maze.Maze(rows, cols)
    if walls == "random":
        return Maze.Maze(rows, cols, random_walls(rows, cols, density, seed))
    if isinstance(walls, str):
        raise ValueError(f"unknown walls {walls!r}: use None, 'random', or a list of wall pairs")
    return Maze.Maze(rows, cols, walls)


def make_game(knight, dragon, **settings):
    unknown = set(settings) - set(CONFIG)
    if unknown:
        raise TypeError(f"unknown settings {sorted(unknown)}; the settings are {list(CONFIG)}")
    cfg = {**CONFIG, **settings}
    maze = make_maze(cfg["size"], cfg["walls"], cfg["density"], cfg["seed"])
    return Game.Game(maze, as_strategy(knight, "knight"), as_strategy(dragon, "dragon"),
                     knight_start=cfg["knight_start"], dragon_start=cfg["dragon_start"],
                     goal=cfg["goal"], max_turns=cfg["max_turns"],
                     dragon_every=cfg["dragon_every"], allow_stay=cfg["allow_stay"])


def _drawer(game):
    """A function that redraws the game in place: in the output cell under
    Jupyter, otherwise by clearing the terminal."""
    try:
        from IPython import get_ipython
        shell = get_ipython()
    except ImportError:
        shell = None
    if shell is not None and "IPKernelApp" in shell.config:
        from IPython.display import display
        handle = None

        def draw():
            nonlocal handle
            if handle is None:
                handle = display(game, display_id=True)
            else:
                handle.update(game)
        return draw
    return lambda: print("\033[H\033[2J" + str(game), flush=True)


def play(knight, dragon, delay=0.2, show=True, **settings):
    """Play one game, drawing every turn, and return the GameResult."""
    game = make_game(knight, dragon, **settings)
    if not show:
        return game.run()
    draw = _drawer(game)
    draw()
    while not game.result:
        time.sleep(delay)
        game.step()
        draw()
    return game.result


def evaluate(knight, dragon, games=20, **settings):
    """Play several games without drawing them, print a summary and return
    the results. With walls="random", each game gets its own maze."""
    first_seed = settings.pop("seed", None) or 0
    results, names = [], None
    for i in range(games):
        game = make_game(knight, dragon, seed=first_seed + i, **settings)
        names = names or f"{game.knight_strategy!r} vs {game.dragon_strategy!r}"
        results.append(game.run())
    wins = [r for r in results if r.outcome == "won"]
    print(f"{names}: won {len(wins)} of {games} ({100 * len(wins) / games:.0f}%)")
    for reason, count in Counter(r.reason for r in results).most_common():
        print(f"  {count:4d}  {reason}")
    if wins:
        print(f"  average turns in a win: {sum(r.turns for r in wins) / len(wins):.1f}")
    return results

