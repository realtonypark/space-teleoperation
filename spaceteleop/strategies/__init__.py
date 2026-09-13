"""Strategy registry: name -> class, used by run.py --strategy and experiments/."""
from .adaptive_gain import Gain
from .baseline import Baseline
from .deadreckon import DeadReckon, DeadReckon30
from .twin import Twin

STRATEGIES = {"baseline": Baseline, "twin": Twin, "deadreckon": DeadReckon,
              "deadreckon30": DeadReckon30, "gain": Gain}


def get(name):
    if name not in STRATEGIES:
        raise KeyError(f"unknown strategy {name!r}; known: {sorted(STRATEGIES)}")
    return STRATEGIES[name]
