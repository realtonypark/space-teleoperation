"""Audit four supplemental chains as bookkeeping regressions, not 20 IID trials."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from verify_records import ROOT, intervals, load, require

SOURCE_HASH = "22b6d1e5dfc8641c9ed0b74ef0f4ee4950c37de7811059aa0c6e80f0e2b43de0"
EXPECTED = {(seed, mode) for seed in (2000, 3000) for mode in ("free", "teleop")}


def terminal(outcome, episode, seed):
    require(outcome["seed"] == episode["seed"] == seed, "metadata/summary seed mismatch")
    require(outcome["success"] == episode["success"], "summary success mismatch")
    require(not outcome["success"] or outcome["released"], "chain success without release")
    require(outcome["no_link"] == episode["no_link"], "summary no-link mismatch")
    require(np.isfinite(outcome["done_wall"]) and outcome["duration_s"] > 0,
            "missing terminal time")
    require(abs(outcome["duration_s"] - episode["duration_s"]) <= .050001,
            "duration differs from rounded summary")
    for key, width in (("final_state", 6), ("final_velocity", 6), ("final_object", 7)):
        require(len(outcome[key]) == width and np.all(np.isfinite(outcome[key])),
                f"invalid terminal {key}")
    success = outcome["success_wall"]
    if success is not None:
        require(np.isfinite(success) and outcome["done_wall"] >= success,
                "release precedes capture success")
        reset = outcome["done_wall"] - success
        require(reset <= outcome["duration_s"], "duration excludes reset")
        return reset
    require(not outcome["success"], "success without capture-success time")
    return None


def verify(raw, partial=False):
    result = dict(passed=False, complete=False, cells=[], errors=[],
                  interpretation="Four dependent episode chains; bookkeeping regression, not 20 IID performance observations.",
                  limitations=["SAT state is sampled before physics; terminal state is separate metadata.",
                               "Newest-received command identity does not identify the sole interpolation source.",
                               "Command-envelope checks do not establish physical safety or pad-contact coverage."])
    identities = []
    for path in sorted(raw.glob("*/summary.json")):
        row = dict(name=path.parent.name, episodes=[])
        result["cells"].append(row)
        try:
            c = json.loads(path.read_text())
            seed0, mode = c["seed0"], c["extra_args"][1]
            identities.append((seed0, mode))
            require((seed0, mode) in EXPECTED and c["extra_args"] == ["--reset", mode], "unexpected chain")
            require(c["source_hash"] == SOURCE_HASH and c["error"] is None and c["linger_excluded"],
                    "source provenance or run completion mismatch")
            require(c["seeds"] == 5 and c["max_s"] == 20 and c["tau_h"] == .17
                    and c["strategy"] == "baseline" and c["profile"] == "leo_relay", "protocol mismatch")
            require(c["task"] == "capture_chain" + ("_teleop" if mode == "teleop" else ""), "task mismatch")
            folder = path.parent
            meta_path, info_path = folder / "meta/episodes.jsonl", folder / "meta/info.json"
            meta = [json.loads(line) for line in meta_path.read_text().splitlines()]
            info = json.loads(info_path.read_text())
            require([m["episode_index"] for m in meta] == list(range(5)), "duplicate/missing/obsolete metadata index")
            require([e["ep"] for e in c["episodes"]] == list(range(5)), "summary index mismatch")
            require(info["recording_schema"] == 2 and info["total_episodes"] == 5
                    and info["total_tasks"] == 1 and info["splits"] == {"train": "0:5"}, "metadata totals mismatch")
            require(info["features"]["observation.object"]["names"] == ["x", "y", "z", "qw", "qx", "qy", "qz"],
                    "object feature labels mismatch")
            tasks = [json.loads(line) for line in (folder / "meta/tasks.jsonl").read_text().splitlines()]
            require(tasks == [{"task_index": 0, "task": "capture_chain"}], "duplicate/obsolete task metadata")
            require({p.name for p in (folder / "data").glob("*.npz")} ==
                    {f"episode_{ep:06d}{suffix}.npz" for ep in range(5) for suffix in ("", "_sat")},
                    "missing or obsolete episode file")
            row.update(seed0=seed0, reset_mode=mode, source_hash=SOURCE_HASH,
                       input_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in (path, meta_path, info_path)})
            index0, previous, previous_sim = 0, None, None
            for m, e in zip(meta, c["episodes"]):
                ep, outcome = m["episode_index"], m["outcome"]
                reset_s = terminal(outcome, e, seed0 + ep)
                g = load(folder / f"data/episode_{ep:06d}.npz")
                s = load(folder / f"data/episode_{ep:06d}_sat.npz")
                n, ns = len(g["cmd_seq"]), len(s["t_ns"])
                require(ns > 1 and (n > 0 or outcome["no_link"]), "missing recorded frames")
                for data, count in ((g, n), (s, ns)):
                    require(all(len(v) == count for v in data.values()), "column count mismatch")
                    for key, value in data.items():
                        if key not in ("rtt_ms", "owd_up_ms") or not outcome["no_link"]:
                            require(np.isfinite(value), f"nonfinite {key}")
                require(m["tasks"] == ["capture_chain"] and e["arm"] == 0, "episode task/arm mismatch")
                require(m["length"] == e["frames"] == n, "frame count mismatch")
                for key in ("cmd_seq", "frame_index"):
                    require(g[key] == np.arange(n), f"{key} off by one")
                require(g["index"] == np.arange(index0, index0 + n), "global index mismatch")
                require(g["episode_index"] == ep, "array episode index mismatch")
                require(g["task_index"] == 0, "array task index mismatch")
                require(g["next.done"] == (np.arange(n) == n - 1), "terminal frame marker mismatch")
                command = g.get("command.t_send_ns", np.array([], np.int64))
                if n:
                    source, rx = g["observation.t_send_ns"], g["observation.t_rx_ns"]
                    require(np.diff(command) > 0, "nonmonotonic action time")
                    require(np.diff(g["timestamp"]) > 0, "nonmonotonic ground time")
                    require((source > 0) & (source <= rx + 1) & (rx <= command), "noncausal source/action")
                    require(np.diff(rx) >= 0, "source receive time goes backwards")
                    require(command - rx >= 170000000 - 2, "reaction delay too short")
                    require(~g["observation.predicted"], "baseline observation marked predicted")
                    require(g["observation.tel_seq"] > 0, "invalid telemetry sequence")
                    _, first, inverse = np.unique(g["observation.tel_seq"], return_index=True, return_inverse=True)
                    for key in ("observation.state", "observation.object", "observation.t_send_ns"):
                        require(g[key] == g[key][first][inverse], "raw telemetry sequence changes contents")
                t, applied, seq = s["t_ns"], s["t_applied_ns"], s["cmd_seq"]
                dt = np.diff(t) / 1e9
                require(dt > 0, "nonmonotonic satellite time")
                require(np.diff(applied) >= 0, "applied stamp goes backwards")
                require(np.diff(seq) >= 0, "newest sequence goes backwards")
                valid = applied > 0
                require((seq[valid] >= 0) & (seq[valid] < n), "newest sequence absent from ground")
                require(applied[valid] >= command[seq[valid]], "command received before send")
                require(applied[:-1] <= t[1:], "application timestamp outside cycle")
                require((np.diff(seq) == 0) | (np.diff(applied) > 0), "sequence changes without timestamp")
                require(~s["hold"][~valid], "hold before first received command")
                require(abs(t[-1] / 1e9 - outcome["done_wall"]) < 2e-9, "SAT includes linger or misses terminal cycle")
                sim = s["sim_time"]
                elapsed = (t - t[0]) / 1e9
                require(np.diff(sim) >= 0, "simulation time goes backwards")
                require(np.abs(sim / .002 - np.rint(sim / .002)) < 1e-6, "simulation time off physics grid")
                require(sim - sim[0] <= elapsed + .0021, "physics ahead of wall clock")
                require(sim[1:] - sim[0] >= elapsed[:-1] - .0021, "physics fails to catch up")
                require(outcome["duration_s"] >= elapsed[-1], "duration omits part of recorded chain")
                if previous is not None:
                    for key, final in (("state", "final_state"), ("velocity", "final_velocity"), ("object", "final_object")):
                        require(np.allclose(s[key][0], previous[final], atol=1e-6, rtol=1e-6), "chain state was reset between episodes")
                    require(sim[0] >= previous_sim, "chain simulation time reset")
                else:
                    require(sim[0] == 0, "first chain episode starts at nonzero sim time")
                require(not s["success"][0], "prior success carried into next episode")
                require(np.diff(s["success"].astype(int)) >= 0, "capture-success flag cleared mid-episode")
                if outcome["success"]:
                    require(s["success"][-1] and reset_s > 0, "release segment not recorded")
                speed = np.abs(np.diff(s["setpoint"].astype(float)[:, :6], axis=0)).max(axis=1) / dt
                require(e["stalls"] == int(np.sum(dt > .2)), "summary scheduler stall count mismatch")
                require(abs(e["max_dt_s"] - dt.max()) <= .005001, "summary cycle duration mismatch")
                row["episodes"].append(dict(ep=ep, seed=outcome["seed"], success=outcome["success"],
                    released=outcome["released"], duration_s=outcome["duration_s"], reset_s=reset_s,
                    ground_frames=n, satellite_cycles=ns, sim_start_s=float(sim[0]), sim_last_sample_s=float(sim[-1]),
                    observed_hold_s=intervals(t, s["hold"]), command_envelope_violations=int(np.sum(speed > 2.1))))
                index0 += n
                previous, previous_sim = outcome, sim[-1]
            require(info["total_frames"] == index0, "total indexed frame count mismatch")
        except (KeyError, ValueError, OSError, TypeError, IndexError) as exc:
            result["errors"].append(f'{row["name"]}: {exc}')
    result["complete"] = len(identities) == 4 and set(identities) == EXPECTED
    if not partial and not result["complete"]:
        result["errors"].append("expected four complete chains")
    result["verified_episodes"] = sum(len(c["episodes"]) for c in result["cells"])
    result["passed"] = bool(result["cells"]) and not result["errors"]
    return result


def self_check():
    outcome = dict(seed=2000, success=True, released=True, no_link=False, done_wall=10.,
                   success_wall=7., duration_s=5., final_state=[0.] * 6,
                   final_velocity=[0.] * 6, final_object=[0.] * 7)
    episode = dict(seed=2000, success=True, no_link=False, duration_s=5.)
    assert terminal(outcome, episode, 2000) == 3
    for replacement in ({"released": False}, {"seed": 2001}, {"duration_s": 2.}):
        try:
            terminal(dict(outcome, **replacement), episode, 2000)
        except ValueError:
            pass
        else:
            raise AssertionError("corrupt chain outcome accepted")
    print("chain self-check passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", nargs="?", type=Path, default=ROOT / "docs/experiments/raw_second_wave_chain")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("chain_verification.json"))
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
    else:
        result = verify(args.raw, args.partial)
        args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(f'{len(result["cells"])} chains, {result["verified_episodes"]} episodes, {len(result["errors"])} errors -> {args.out}')
        for error in result["errors"]:
            print(error)
        raise SystemExit(int(not result["passed"]))
