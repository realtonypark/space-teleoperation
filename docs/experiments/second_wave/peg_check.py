"""Final-pose regression: three ten-episode cells; no new mechanism-effect estimate."""
import argparse
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments import matrix
from spaceteleop import sim

RAW = ROOT / "docs/experiments/raw_second_wave_peg_endpoint"
OUT = Path(__file__).resolve().parent
CELLS = [matrix.Cell("P3", "peg", strategy, profile, .17, 10, 30.)
         for strategy, profile in (("baseline", "zero"), ("baseline", "leo_relay"),
                                   ("terminal", "sweep:400"))]


def verify():
    manifest = json.loads((OUT / "peg_manifest.json").read_text())
    assert matrix.source_hash() == manifest["source_hash"], "audit source changed"
    rows = []
    for cell in CELLS:
        path = RAW / cell.name
        summary = json.loads((path / "summary.json").read_text())
        assert not summary["error"] and summary["source_hash"] == manifest["source_hash"]
        assert matrix.complete(summary["episodes"], 10, 4000)
        meta = [json.loads(line) for line in (path / "meta/episodes.jsonl").read_text().splitlines()]
        assert [e["episode_index"] for e in meta] == list(range(10))
        m, d = sim.build("peg")
        for episode, entry in zip(summary["episodes"], meta):
            outcome = entry["outcome"]
            assert outcome["seed"] == episode["seed"]
            assert outcome["success"] == episode["success"]
            st = sim.reset(m, d, outcome["seed"], "peg")
            d.qpos[:sim.NJ] = outcome["final_state"]
            a = st["ids"]["qadr"]
            d.qpos[a:a + 7] = outcome["final_object"]
            assert np.all(np.isfinite(d.qpos))
            mujoco.mj_forward(m, d)
            lateral = float(np.linalg.norm(d.qpos[a:a + 2] - sim.HOLE[:2]))
            depth_margin = float(sim.FIX_TOP - sim.DEPTH - (d.qpos[a + 2] - sim.PEG_H))
            contact = bool(sim._touching(d, st["ids"]["fix"], st["ids"]["objg"]))
            meets = lateral < sim.BOX + sim.CLEAR and depth_margin >= 0 and not contact
            assert not outcome["success"] or meets, f"invalid endpoint: {cell.name} {outcome['seed']}"
            rows.append(dict(cell=cell.name, seed=outcome["seed"], success=outcome["success"],
                             lateral_m=lateral, insertion_depth_margin_m=depth_margin,
                             fixture_contact=contact, terminal_predicate=meets))
    result = dict(passed=True, verified_episodes=len(rows), source_hash=manifest["source_hash"],
                  method="Reconstruct final joint/object pose; check lateral position, depth and fixture contact.",
                  limitation="Endpoint regression only; no trajectory replay, physical validation or paired effect estimate.",
                  episodes=rows)
    (OUT / "peg_verification.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"{len(rows)} endpoints verified; {sum(r['success'] for r in rows)} successful")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only:
        failures = matrix.run(CELLS, str(RAW), jobs=3, seed0=4000)
        if failures:
            raise SystemExit(failures)
    verify()
