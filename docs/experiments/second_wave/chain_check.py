"""Supplemental bookkeeping regression; four chains, not 20 IID observations."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "experiments"))
import matrix


if __name__ == "__main__":
    failures = 0
    for seed in (2000, 3000):
        cells = [matrix.Cell(f"C{seed}", "capture_chain" + ("_teleop" if mode == "teleop" else ""),
                             "baseline", "leo_relay", .17, 5, 20., ("--reset", mode))
                 for mode in ("free", "teleop")]
        failures += matrix.run(cells, "docs/experiments/raw_second_wave_chain", jobs=2, seed0=seed)
    raise SystemExit(failures)
