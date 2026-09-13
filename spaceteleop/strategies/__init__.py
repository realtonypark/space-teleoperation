"""Strategy registry: name -> class, used by run.py --strategy and experiments/."""
from .baseline import Baseline
from .terminal import Terminal, TerminalGround

STRATEGIES = {"baseline": Baseline, "terminal": Terminal,
              "terminal_ground": TerminalGround}


def get(name):
    if name not in STRATEGIES:
        raise KeyError(f"unknown strategy {name!r}; known: {sorted(STRATEGIES)}")
    return STRATEGIES[name]
