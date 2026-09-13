"""Strategy registry: name -> class, used by run.py --strategy and experiments/."""
from .baseline import Baseline

STRATEGIES = {"baseline": Baseline}


def get(name):
    if name not in STRATEGIES:
        raise KeyError(f"unknown strategy {name!r}; known: {sorted(STRATEGIES)}")
    return STRATEGIES[name]
