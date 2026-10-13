#%%
"""Play and evaluate knight vs dragon games.

Set the parameters in the configuration cell below and run it, or call
play() and evaluate() yourself:

    play(CustomKnight, ChaserDragon)                          # watch one game
    play(CustomKnight, GuardDragon, walls="random", seed=3)
    evaluate(CustomKnight, ChaserDragon, games=50, walls="random")

A knight or dragon is a strategy class, or an instance of one. Any setting
in CONFIG can be passed to play() and evaluate() as a keyword argument.
"""


CONFIG = {
    "size": 10,            # side of a square maze, or (rows, cols)
    "walls": None,         # None (no walls), "random", or a list of ((r, c), (r, c)) pairs
    "density": 0.8,        # for walls="random": share of walls kept (1 = no loops at all)
    "seed": None,          # random seed for walls="random"
    "knight_start": None,  # None: the top-left corner
    "dragon_start": None,  # None: the centre
    "goal": None,          # None: the bottom-right corner
    "max_turns": 200,
    "dragon_every": 1,     # the dragon moves once every this many turns (2 = half speed)
    "allow_stay": True,    # whether standing still counts as a move
}