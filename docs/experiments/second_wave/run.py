"""Fixed second-wave protocol; run from repository root with uv run python PATH."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "experiments"))
import matrix


def cells():
    rows = []
    for task, profiles, strategies in [
        ("capture", ["zero", "leo_relay"], ["baseline"]),
        ("peg", ["zero", "leo_relay"], ["baseline"]),
        ("capture", ["zero"], ["twin"]),
        ("capture", ["sweep:400"], ["baseline", "twin", "gain"]),
        ("peg", ["sweep:250"], ["baseline", "deadreckon"]),
        ("peg", ["sweep:400"], ["baseline", "terminal", "terminal_ground"]),
        ("capture", ["leo_relay_drop1", "leo_relay_drop12"], ["baseline"]),
    ]:
        for profile in profiles:
            for strategy in strategies:
                block = "S" if "drop" in profile else "W2"
                rows.append(matrix.Cell(block, task, strategy, profile, 0.17, 30,
                                        matrix.max_s(task, profile)))
    assert len(rows) == 15 and len({c.name for c in rows}) == 15
    return rows


if __name__ == "__main__":
    raise SystemExit(matrix.run(cells(), "docs/experiments/raw_second_wave", jobs=4, seed0=1000))
