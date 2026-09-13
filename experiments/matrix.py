"""Experiment matrix: selection.md section 3 encoded as data, plus a subprocess runner.

    uv run python experiments/matrix.py --dry-run --tier 1 --strategies baseline,twin
    uv run python experiments/matrix.py --tier 1 --blocks A,B --strategies baseline,twin \
        --seeds 30 --jobs 8 --out docs/experiments/raw

One cell = one `python -m spaceteleop.run` process (selection.md section 3: never `--arms`
for cross-cell parallelism, the GIL inflates dwell). Cells go to a thread pool of --jobs;
each thread only waits on its subprocess, so --jobs is the number of concurrent run.py
PROCESSES. Every cell of a run uses the same seed base, so arms are paired seed by seed.

Resumable: a cell whose `summary.json` exists and carries no error is skipped. A crashed
cell writes `summary.json` with the error and its stdout, and IS retried next time, which
is what you want for the Tier 1 blocks whose strategy or task has not landed yet.

Strategy names are data: they come from --strategies, never from this file. Blocks pick
arms by role -- "all" (every named strategy), "primary" (minus --ablations, the ablation
arms selection.md drops from block E) and "base" (the --baseline arm alone).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from spaceteleop.link.profiles import rtt_ms                            # noqa: E402

PRIMARY_TAU = 0.17          # SYNTHESIS section 8; 0.25 is the one variant (block E)
SWEEP = (0, 100, 250, 400, 500, 750, 1000)
ALL_PROFILES = ["zero", "direct_gs", "leo_relay", "geo_relay"] + [f"sweep:{r}" for r in SWEEP]

# selection.md section 3, Tier 1. `arms` is a role, resolved against --strategies.
TIER1 = {
    "A": dict(tasks=["capture"], arms="all", profiles=ALL_PROFILES, tau_h=PRIMARY_TAU),
    "B": dict(tasks=["peg"], arms="all", profiles=ALL_PROFILES, tau_h=PRIMARY_TAU),
    # H20: C = chained release-is-reset; Cr = same task, canonical teleoperated reset
    # charged to wall time. Both run under the baseline strategy (selection.md 3).
    "C": dict(tasks=["capture_chain", "capture_chain_teleop"], arms="base", tau_h=PRIMARY_TAU,
              profiles=["zero", "direct_gs", "leo_relay", "sweep:250", "sweep:500",
                        "sweep:1000"],
              extra={"capture_chain": ["--reset", "free"],
                     "capture_chain_teleop": ["--reset", "teleop"]}),
    "E": dict(tasks=["capture", "peg"], arms="primary", tau_h=0.25,
              profiles=["leo_relay", "sweep:400", "geo_relay"]),
    # S = the dropout block (audit T02). Poisson 1.7/h puts an outage inside a 20 s episode
    # 0.9 % of the time per direction, so blocks A/B never exercised hold or retract and
    # "zero unsafe motion on dropout" (PROGRAM.md acceptance) was vacuous: move_in_hold = 0
    # and vel_over = 0 because no hold ever started while an operator was driving. Both
    # profiles force one full outage at t = 6.0 s; drop1 (1 s) trips hold and returns,
    # drop12 (12 s) crosses the 10 s retract and the arm stows.
    "S": dict(tasks=["capture", "peg"], arms="all", tau_h=PRIMARY_TAU,
              profiles=["leo_relay_drop1", "leo_relay_drop12"]),
}

# Tier 2 confirm template, keyed by the selection.md arm label. Provisional by construction
# ("to be re-pointed once the knee is known"), so --arm-map decides which labels exist and
# unmapped labels are dropped. B is added to every cell: Tier 2 is paired against baseline.
TIER2 = {
    "T": [("capture", "sweep:400"), ("capture", "geo_relay"), ("peg", "sweep:400"),
          ("capture", "zero")],
    "D": [("capture", "sweep:250"), ("peg", "leo_relay")],
    "G": [("capture", "sweep:400"), ("capture", "geo_relay"), ("capture", "zero")],
    "P": [("peg", "leo_relay"), ("peg", "sweep:400"), ("capture", "sweep:500")],
    "Pg": [("peg", "leo_relay"), ("peg", "sweep:400"), ("capture", "sweep:500")],
    "C": [("capture_chain", "leo_relay"), ("capture_chain", "sweep:500")],
}


class Cell(NamedTuple):
    block: str
    task: str
    strategy: str
    profile: str
    tau_h: float
    seeds: int
    max_s: float
    extra_args: tuple = ()

    @property
    def name(self):
        return (f"{self.block}_{self.task}_{self.strategy}_"
                f"{self.profile.replace(':', '')}_tau{self.tau_h}")


def max_s(task, profile):
    """selection.md section 3: 20 s, 30 s for peg and for every cell at RTT >= 500 ms.

    Block S's `leo_relay_drop12` also gets 30 s: its forced outage alone is 12 s of the
    episode, and the operator cannot finish the task inside what a 20 s cap would leave."""
    return 30.0 if (task.startswith("peg") or rtt_ms(profile) >= 500
                    or profile.endswith("drop12")) else 20.0


def _arms(role, strategies, ablations, baseline):
    if role == "all":
        return list(strategies)
    if role == "primary":
        return [s for s in strategies if s not in ablations]
    return [baseline]


def cells(tier=1, blocks=None, strategies=("baseline",), seeds=30, profiles=None,
          ablations=(), baseline="baseline", arm_map=None):
    """The cell list for a tier. `profiles` overrides every block's profile list."""
    out = []
    if tier == 1:
        for b in (blocks or sorted(TIER1)):
            spec = TIER1[b]
            for task in spec["tasks"]:
                for s in _arms(spec["arms"], strategies, ablations, baseline):
                    for p in profiles or spec["profiles"]:
                        out.append(Cell(b, task, s, p, spec["tau_h"], seeds,
                                        max_s(task, p),
                                        tuple(spec.get("extra", {}).get(task, ()))))
        return out
    arm_map = arm_map or {}
    for label, cs in TIER2.items():
        if label not in arm_map:
            continue
        for task, p in cs:
            for s in dict.fromkeys([baseline, arm_map[label]]):
                for pr in profiles or [p]:
                    out.append(Cell("T2", task, s, pr, PRIMARY_TAU, seeds, max_s(task, pr)))
    return list(dict.fromkeys(out))


EP_RE = re.compile(r"arm (\d+) ep (\d+) seed (\d+) success=(True|False) ([\d.]+)s "
                   r"rtt_p50=([\d.]+)ms hold=([\d.]+)s unsafe=(\d+) cage=(\d+) "
                   r"stalls=(\d+) max_dt=([\d.]+)s frames=(\d+)")
UNSAFE_RE = re.compile(r"^(\d+)\s+\((.*)\)$")

# `cage` is reported apart from the unsafe (link-caused) counters, and `stalls`/`max_dt_s`
# flag a cell that ran under CPU contention (audit T06, T07).
TABLE_KEYS = {"profile", "episodes", "success_rate", "mean_duration_s", "demos_per_hour",
              "demos_per_hour_gross", "rtt_p50_ms", "rtt_p95_ms", "rtt_max_ms", "cmd_loss",
              "safety_hold_s", "jerk_sum_sq", "sal", "ldlj", "stall_frac", "unsafe_events",
              "cage", "stalls", "max_dt_s",
              "diagnostics", "task", "wire_up_Bps", "wire_down_Bps", "nominal_rtt_ms"}


def _num(v):
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return v


def parse_stdout(text):
    """run.py stdout -> (per-episode dicts, aggregate dict). Both formats are fixed by
    run.run_arm's print and metrics.table, so this is cheaper than re-deriving the
    aggregate from the npz files (which carry no success flag or wall time)."""
    eps = [dict(arm=int(m[1]), ep=int(m[2]), seed=int(m[3]), success=m[4] == "True",
                duration_s=float(m[5]), rtt_p50=float(m[6]), hold_s=float(m[7]),
                unsafe=int(m[8]), cage=int(m[9]), stalls=int(m[10]),
                max_dt_s=float(m[11]), frames=int(m[12]))
           for m in EP_RE.finditer(text)]
    agg = {}
    for line in text.splitlines():
        k, _, v = line.partition(" ")
        v = v.strip()
        if not v or k not in TABLE_KEYS:
            continue
        if k == "unsafe_events" and (m := UNSAFE_RE.match(v)):
            agg["unsafe"] = int(m[1])
            agg["events"] = _kv(m[2])
        elif k == "diagnostics":
            agg.setdefault("events", {}).update(_kv(v))
        else:
            agg[k] = _num(v)
    return eps, agg


def _kv(s):
    return {p.split("=")[0].strip(): _num(p.split("=")[1])
            for p in s.split(",") if "=" in p}


def done(cell, root):
    """True if this cell already has a clean summary.json (resume)."""
    p = f"{root}/{cell.name}/summary.json"
    try:
        with open(p) as f:
            return not json.load(f).get("error")
    except (OSError, ValueError):
        return False


def run_cell(cell, root, seed0=0):
    d = f"{root}/{cell.name}"
    os.makedirs(d, exist_ok=True)
    cmd = ["uv", "run", "python", "-m", "spaceteleop.run",
           "--profile", cell.profile, "--task", cell.task.replace("_teleop", ""),
           "--strategy", cell.strategy,
           "--episodes", str(cell.seeds), "--seed", str(seed0), "--out", d,
           "--max-s", str(cell.max_s), "--tau-h", str(cell.tau_h), *cell.extra_args]
    t0 = time.monotonic()
    r = subprocess.run(cmd, capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
    with open(f"{d}/stdout.txt", "w") as f:
        f.write(out)
    eps, agg = parse_stdout(r.stdout)
    err = None
    if r.returncode != 0:
        err = f"exit {r.returncode}: " + ((r.stderr or out).strip().splitlines() or [""])[-1]
    elif not eps:
        err = "no episodes parsed from stdout"
    # schema flags the aggregator reads: `duration_s` already ends at the success/done
    # instant (audit T09/F2, run.py), and SAL/LDLJ/stall_frac already come from the
    # satellite applied-setpoint sidecar (T05). Without these it would apply both
    # corrections a second time.
    s = dict(cell._asdict(), name=cell.name, seed0=seed0, cmd=" ".join(cmd),
             rtt_ms=rtt_ms(cell.profile), linger_excluded=True,
             wall_s=round(time.monotonic() - t0, 1), error=err,
             aggregate=dict(agg, smoothness_source="sat"), episodes=eps)
    with open(f"{d}/summary.json", "w") as f:
        json.dump(s, f, indent=1)
    return s


def _fmt(s):
    return f"{int(s // 3600)}h{int(s % 3600 // 60):02d}m" if s >= 3600 else f"{s / 60:.1f}m"


def est_s(cell):
    """Wall time guess: episodes end on success, selection.md measured ~12 s at max_s 20."""
    return 2.0 + cell.seeds * 0.6 * cell.max_s


def run(cs, root, jobs, seed0=0):
    os.makedirs(root, exist_ok=True)
    pend = [c for c in cs if not done(c, root)]
    print(f"{len(cs)} cells, {len(cs) - len(pend)} already done, {len(pend)} to run "
          f"on {jobs} processes (estimate {_fmt(sum(map(est_s, pend)) / jobs)})")
    t0, times, bad = time.monotonic(), [], 0
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = {ex.submit(run_cell, c, root, seed0): c for c in pend}
        for i, f in enumerate(as_completed(futs), 1):
            c = futs[f]
            try:
                s = f.result()
            except Exception as e:                          # a cell never kills the run
                s = {"error": repr(e)}
            times.append(time.monotonic() - t0)
            bad += bool(s.get("error"))
            eta = (times[-1] / i) * (len(pend) - i)
            print(f"[{i}/{len(pend)}] {c.name} "
                  f"{'ERROR ' + str(s['error'])[:80] if s.get('error') else 'ok'} "
                  f"{s.get('wall_s', 0)}s  eta {_fmt(eta)}", flush=True)
    print(f"done in {_fmt(time.monotonic() - t0)}, {bad} cells errored -> {root}")
    return bad


def main(argv=None):
    p = argparse.ArgumentParser(prog="matrix")
    p.add_argument("--tier", type=int, default=1, choices=(1, 2))
    p.add_argument("--blocks", default=None, help="comma list, default all of the tier")
    p.add_argument("--strategies", default="baseline", help="comma list, arms to run")
    p.add_argument("--ablations", default="", help="strategies block E leaves out")
    p.add_argument("--baseline", default="baseline", help="the paired reference arm")
    p.add_argument("--arm-map", default="", help="tier 2: label=strategy,... e.g. T=twin")
    p.add_argument("--profiles", default=None, help="override every block's profile list")
    p.add_argument("--seeds", type=int, default=30, help="episodes per cell")
    p.add_argument("--seed0", type=int, default=0, help="base seed, identical across arms")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--out", default="docs/experiments/raw")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    split = lambda s: [x for x in (s or "").split(",") if x]
    cs = cells(a.tier, split(a.blocks) or None, split(a.strategies), a.seeds,
               split(a.profiles) or None, split(a.ablations), a.baseline,
               dict(kv.split("=") for kv in split(a.arm_map)))
    if a.dry_run:
        for c in cs:
            print(f"{c.name:<52} profile={c.profile:<12} max_s={c.max_s:<5} "
                  f"seeds={c.seeds} extra={' '.join(c.extra_args)}")
        tot = sum(map(est_s, cs))
        print(f"\n{len(cs)} cells, {sum(c.seeds for c in cs)} episodes; "
              f"estimate {_fmt(tot)} serial, {_fmt(tot / a.jobs)} on {a.jobs} jobs")
        return cs
    run(cs, a.out, a.jobs, a.seed0)
    return cs


if __name__ == "__main__":
    main()
