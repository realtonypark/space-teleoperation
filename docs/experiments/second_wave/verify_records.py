"""Verify completed schema-2 recordings with NumPy and stdlib only.

uv run python docs/experiments/second_wave/verify_records.py --self-check
uv run python docs/experiments/second_wave/verify_records.py --partial
uv run python docs/experiments/second_wave/verify_records.py --out docs/experiments/second_wave/record_verification.json
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    ("capture", "baseline", "zero"), ("capture", "baseline", "leo_relay"),
    ("peg", "baseline", "zero"), ("peg", "baseline", "leo_relay"),
    ("capture", "twin", "zero"),
    *(("capture", s, "sweep:400") for s in ("baseline", "twin", "gain")),
    *(("peg", s, "sweep:250") for s in ("baseline", "deadreckon")),
    *(("peg", s, "sweep:400") for s in ("baseline", "terminal", "terminal_ground")),
    *(("capture", "baseline", p) for p in ("leo_relay_drop1", "leo_relay_drop12")),
}
SOURCE_HASH = "89d5d7a656a6e95318a40bad29297e34b40a1aed325a359f03d06508d1b060aa"


def require(condition, message):
    if not np.all(condition):
        raise ValueError(message)


def load(path):
    with np.load(path, allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


def intervals(t_ns, mask):
    """Right-endpoint integration, matching the controller's hold-time convention."""
    return float(np.sum(np.diff(t_ns) / 1e9 * mask[1:]))


def verify_episode(g, s, meta, summary, cell, index0):
    n, ns = len(g["cmd_seq"]), len(s["t_ns"])
    no_link = meta["outcome"]["no_link"]
    require(ns > 1, "missing satellite frames")
    for data, count in ((g, n), (s, ns)):
        require(all(len(v) == count for v in data.values()), "unequal column lengths")
        for key, value in data.items():
            require(np.isfinite(value) | (np.isnan(value) if no_link and key in ("rtt_ms", "owd_up_ms") else False),
                    f"nonfinite {key}")
    for key, width in (("observation.state", 7), ("observation.object", 7), ("action", 7)):
        if not n and key == "observation.object":
            continue  # The writer emits schema-2 source columns only when rows exist.
        require(g[key].shape == (n, width), f"bad ground shape: {key}")
    for key, width in (("state", 6), ("velocity", 6), ("object", 7), ("setpoint", 7)):
        require(s[key].shape == (ns, width), f"bad satellite shape: {key}")
    if n:
        require(all(k in g for k in ("command.t_send_ns", "observation.t_send_ns",
                    "observation.t_rx_ns", "observation.tel_seq", "observation.predicted")),
                "missing schema-2 source columns")
    ep = meta["episode_index"]
    require(meta["tasks"] == [cell["task"]], "metadata task mismatch")
    require(meta["length"] == summary["frames"] == n, "frame count mismatch")
    require(summary["ep"] == ep and summary["arm"] == 0, "episode identity mismatch")
    require(summary["seed"] == 1000 + ep, "summary seed differs from planned seed")
    require(g["frame_index"] == np.arange(n), "frame index mismatch")
    require(g["index"] == np.arange(index0, index0 + n), "global index mismatch")
    require(g["episode_index"] == ep, "array episode index mismatch")
    require(g["task_index"] == 0, "array task index mismatch")
    require(g["cmd_seq"] == np.arange(n), "command sequence off by one or discontinuous")
    require(g["next.done"] == (np.arange(n) == n - 1), "bad terminal frame marker")
    require(np.diff(g["timestamp"]) > 0, "nonmonotonic ground time")
    command, source, received = (g.get(k, np.array([], dtype=np.int64)) for k in
        ("command.t_send_ns", "observation.t_send_ns", "observation.t_rx_ns"))
    require(np.diff(command) > 0, "nonmonotonic command timestamp")
    require((source > 0) & (source <= received + 1) & (received <= command),
            "noncausal observation/source/action timestamps")
    require(np.diff(received) >= 0, "source receive time goes backwards")
    require(command - received >= int(cell["tau_h"] * 1e9) - 2,
            "reaction delay shorter than configured tau_h")
    tel_seq = g.get("observation.tel_seq", np.array([], dtype=np.int64))
    predicted = g.get("observation.predicted", np.zeros(n, bool))
    require(tel_seq > 0, "invalid telemetry sequence")
    if cell["strategy"] != "twin":
        require(~predicted, "prediction marked for non-twin strategy")
    # Repeated source telemetry must retain its original timestamp and raw contents.
    _, first, inverse = np.unique(tel_seq, return_index=True, return_inverse=True)
    require(source == source[first][inverse], "telemetry sequence maps to multiple source stamps")
    if n and cell["strategy"] != "twin":
        for key in ("observation.state", "observation.object"):
            require(g[key] == g[key][first][inverse], f"raw telemetry changed: {key}")

    t, applied, seq = s["t_ns"], s["t_applied_ns"], s["cmd_seq"]
    dt = np.diff(t) / 1e9
    require(dt > 0, "nonmonotonic satellite cycle time")
    require(np.diff(applied) >= 0, "nonmonotonic applied timestamp")
    require(np.diff(seq) >= 0, "satellite command sequence goes backwards")
    require((np.diff(seq) == 0) | (np.diff(applied) > 0),
            "command sequence changes without a new application stamp")
    valid = applied > 0
    require(not no_link or not n or not np.any(valid), "no-link flag despite recorded command exposure")
    require(n > 0 or no_link, "empty ground recording not marked no-link")
    require((seq[valid] >= 0) & (seq[valid] < n), "satellite sequence has no recorded command")
    require(applied[valid] >= command[seq[valid]], "command applied before it was sent")
    require(applied[:-1] <= t[1:], "application stamp extends beyond its control cycle")
    changed = np.r_[valid[0], np.diff(applied) > 0]
    require(np.diff(seq[changed]) > 0, "new application does not advance command sequence")
    require(~s["hold"][~valid], "hold flagged before first command")
    sim = s["sim_time"]
    require(abs(sim[0]) < 1e-9 and np.all(np.diff(sim) >= 0), "invalid simulation clock")
    require(np.abs(sim / .002 - np.rint(sim / .002)) < 1e-6,
            "simulation time is not on the 2 ms physics grid")
    elapsed = (t - t[0]) / 1e9
    require(sim <= elapsed + .0021, "simulation advances ahead of wall clock")
    require(sim[1:] >= elapsed[:-1] - .0021, "simulation fails to catch up each cycle")
    outcome = meta["outcome"]
    require(outcome["success"] == summary["success"], "success differs from summary")
    require(outcome["no_link"] == summary["no_link"], "no-link mismatch")
    require(not no_link or not outcome["success"], "success recorded without command exposure")
    require(abs(outcome["duration_s"] - summary["duration_s"]) <= .050001,
            "duration differs from rounded summary")
    require(abs(outcome["done_wall"] - t[-1] / 1e9) < 2e-9,
            "satellite log does not end at terminal cycle")
    require(not np.any(s["success"]), "success state precedes terminal cycle")
    if outcome["success"]:
        require(outcome["success_wall"] == outcome["done_wall"], "late or missing success")
    else:
        require(outcome["success_wall"] is None, "failed outcome has success timestamp")
        require(outcome["duration_s"] >= cell["max_s"] - .002, "failed episode ended early")
    for key, width in (("final_state", 6), ("final_velocity", 6), ("final_object", 7)):
        require(len(outcome[key]) == width and np.all(np.isfinite(outcome[key])),
                f"invalid terminal {key}")
    final_object = np.array(outcome["final_object"])
    final_distance = float(np.linalg.norm(final_object[:3] - [.16, -.16, .22])) if cell["task"] == "capture" else float(np.linalg.norm(final_object[:2] - [.15, -.27]))
    require(not outcome["success"] or final_distance < (.05 if cell["task"] == "capture" else .014),
            "successful terminal object outside task goal geometry")

    dq = np.abs(np.diff(s["setpoint"].astype(float), axis=0))[:, :6]
    speed = dq.max(axis=1) / dt
    stale_s = np.maximum(0, (t - applied) / 1e9)
    hold_before_retract = s["hold"][1:] & (stale_s[1:] < 9.99)
    observed_newest = int(changed.sum())
    # Missing arrival stamps prevent exact interpolation replay or packet-loss counts.
    request_gap = np.abs(s["setpoint"][valid, :6] - g["action"][seq[valid], :6])
    velocity = np.abs(s["velocity"])
    peak_cycle, peak_joint = np.unravel_index(np.argmax(velocity), velocity.shape)
    final_velocity = np.abs(outcome["final_velocity"])
    forced_length = {"leo_relay_drop1": 1., "leo_relay_drop12": 12.}.get(cell["profile"])
    result = dict(
        ep=ep, seed=summary["seed"], success=outcome["success"], no_link=no_link, ground_frames=n,
        satellite_cycles=ns, duration_s=outcome["duration_s"],
        terminal_goal_distance_m=final_distance,
        observed_newest_commands=observed_newest,
        commands_not_observed_as_newest=n - observed_newest,
        commands_sent_after_terminal=int(np.sum(command > t[-1])),
        source_sequence_regressions=int(np.sum(np.diff(tel_seq) < 0)),
        predicted_observation_frames=int(np.sum(predicted)),
        source_age_max_s=float(np.max(command - source) / 1e9) if n else None,
        observed_hold_s=intervals(t, s["hold"]),
        hold_entries=int(np.sum(np.diff(s["hold"].astype(int)) == 1)),
        maximum_newest_command_age_s=float(np.max(stale_s[valid])) if valid.any() else None,
        hold_age_over_10s_s=intervals(t, s["hold"] & valid & (stale_s >= 10)),
        forced_window_overlap_sat_start_proxy_s=(
            max(0., min(float(elapsed[-1]), 6 + forced_length) - 6)
            if forced_length else None),
        command_envelope=dict(
            maximum_setpoint_speed_rad_s=float(speed.max()),
            cycles_over_2rad_s_with_5pct_tolerance=int(np.sum(speed > 2.1)),
            hold_before_retract_setpoint_change_cycles=int(np.sum(hold_before_retract & (dq.max(axis=1) > 1e-6))),
            mean_absolute_newest_request_setpoint_gap_rad=float(request_gap.mean()) if valid.any() else None),
        measured_motion=dict(
            maximum_abs_joint_velocity_rad_s=float(velocity.max()),
            terminal_maximum_abs_joint_velocity_rad_s=float(final_velocity.max()),
            terminal_peak_joint_index=int(final_velocity.argmax()),
            maximum_sampled_including_terminal_abs_joint_velocity_rad_s=float(max(velocity.max(), final_velocity.max())),
            peak_joint_index=int(peak_joint),
            peak_joint_name=("Rotation", "Pitch", "Elbow", "Wrist_Pitch", "Wrist_Roll", "Jaw")[peak_joint],
            peak_cycle_index=int(peak_cycle), peak_t_ns=int(t[peak_cycle]),
            peak_sim_time_s=float(sim[peak_cycle]),
            peak_sat_elapsed_s=float(elapsed[peak_cycle]),
            peak_in_hold=bool(s["hold"][peak_cycle]),
            cycles_above_2rad_s=int(np.sum(velocity.max(axis=1) > 2)),
            hold_cycles_with_joint_speed_above_0_05rad_s=int(np.sum(s["hold"] & (velocity.max(axis=1) > .05))),
            joint_travel_rad=float(np.abs(np.diff(s["state"].astype(float), axis=0)).sum()),
            object_translation_travel_m=float(np.linalg.norm(np.diff(s["object"][:, :3].astype(float), axis=0), axis=1).sum())),
        scheduler=dict(cycles_over_0_2s=int(np.sum(dt > .2)), maximum_cycle_s=float(dt.max())),
    )
    require(summary["stalls"] == result["scheduler"]["cycles_over_0_2s"], "stall count mismatch")
    require(abs(summary["max_dt_s"] - dt.max()) <= .005001, "max cycle differs from rounded summary")
    return result


def verify(raw, partial=False):
    paths = sorted(raw.glob("*/summary.json"))
    result = dict(complete=False, passed=False, cells=[], errors=[], limitations=[
        "Seeds are checked against summary and planned 1000..1029; recording metadata has no seed.",
        "SAT samples are pre-step; terminal state and outcome live in metadata, not a terminal SAT row.",
        "next.done marks the final ground row, not success or the exact physics terminal instant.",
        "Source telemetry can reorder. Source receive times, not source sequences, must be monotonic.",
        "Applied sequence means newest command seen by a cycle, not the interpolator's sole source. Multiple commands may drain per cycle; exact accepted/lost counts and interpolation replay are unavailable.",
        "Runner no_link counts received commands through linger; observed_newest_commands counts only the recorded pre-terminal cycles.",
        "Hold and command-age exposure use recorded timestamps. Forced-window overlap uses first SAT cycle as a link-start proxy; exact Link.start timestamp and drop events are not recorded.",
        "Command-envelope diagnostics are not measured motion, contact coverage, or proof of zero physical risk.",
        "Measured velocity maxima are maxima of recorded samples plus terminal metadata; unsampled physics steps can have larger peaks.",
    ])
    identities = []
    for path in paths:
        c = json.loads(path.read_text())
        identity = (c["task"], c["strategy"], c["profile"])
        identities.append(identity)
        row = dict(name=c["name"], source_hash=c.get("source_hash"), episodes=[],
                   summary_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        result["cells"].append(row)
        try:
            require(identity in EXPECTED, "unexpected cell")
            require(c["error"] is None and c["linger_excluded"], "failed or legacy cell")
            require(c["source_hash"] == SOURCE_HASH, "source hash differs from frozen study")
            require(c["tau_h"] == .17 and c["seeds"] == 30 and c["seed0"] == 1000,
                    "protocol mismatch")
            require(c["max_s"] == (30 if c["task"] == "peg" or c["profile"].endswith("drop12") else 20),
                    "episode budget differs from protocol")
            folder = path.parent
            info = json.loads((folder / "meta/info.json").read_text())
            meta = [json.loads(line) for line in (folder / "meta/episodes.jsonl").read_text().splitlines()]
            require(info["recording_schema"] == 2 and info["total_episodes"] == len(meta) == len(c["episodes"]) == 30,
                    "schema or episode count mismatch")
            require([m["episode_index"] for m in meta] == list(range(30)), "metadata episode sequence mismatch")
            index = 0
            for m, e in zip(meta, c["episodes"]):
                try:
                    p = folder / f'data/episode_{m["episode_index"]:06d}'
                    row["episodes"].append(verify_episode(load(p.with_suffix(".npz")),
                        load(p.with_name(p.name + "_sat.npz")), m, e, c, index))
                except (KeyError, ValueError, OSError, TypeError) as exc:
                    result["errors"].append(f'{c["name"]} episode {m["episode_index"]}: {exc}')
                index += m["length"]
            require(info["total_frames"] == index, "total frame count mismatch")
        except (KeyError, ValueError, OSError, TypeError) as exc:
            result["errors"].append(f'{c["name"]}: {exc}')
    result["complete"] = len(identities) == 15 and set(identities) == EXPECTED
    if not partial and not result["complete"]:
        result["errors"].append(f"incomplete protocol: {len(paths)}/15 completed cell summaries")
    if not paths:
        result["errors"].append("no completed cells")
    result["verified_episodes"] = sum(len(c["episodes"]) for c in result["cells"])
    result["passed"] = not result["errors"]
    return result


def self_check():
    t = np.array([0, 1, 3, 6], dtype=np.int64) * 10**9
    assert intervals(t, np.array([False, True, True, False])) == 3
    assert intervals(t, np.zeros(4, bool)) == 0
    # One tiny episode exercises loading, then rejects off-by-one, causality and NaN defects.
    import tempfile
    n = 3
    command = np.array([1001000000, 1003000000, 1005000000], np.int64)
    g = {k: np.arange(n) for k in ("cmd_seq", "frame_index", "index")}
    g.update({k: np.zeros(n, np.int64) for k in ("episode_index", "task_index")})
    g.update({k: np.zeros((n, 7)) for k in ("action", "observation.state", "observation.object")})
    g.update({"next.done": np.array([False, False, True]), "timestamp": np.array([.001, .003, .005]),
              "command.t_send_ns": command, "observation.t_send_ns": command - 201000000,
              "observation.t_rx_ns": command - 200000000,
              "observation.tel_seq": np.arange(1, 4), "observation.predicted": np.zeros(n, bool)})
    s = dict(t_ns=np.array([1000000000, 1002000000, 1004000000, 1006000000], np.int64),
             t_applied_ns=np.array([0, 1002000100, 1004000100, 1006000100], np.int64),
             cmd_seq=np.array([0, 0, 1, 2]), hold=np.zeros(4, bool), success=np.zeros(4, bool),
             sim_time=np.arange(4) * .002)
    s.update({k: np.zeros((4, width)) for k, width in
              (("state", 6), ("velocity", 6), ("object", 7), ("setpoint", 7))})
    outcome = dict(success=False, no_link=False, duration_s=.006, done_wall=1.006, success_wall=None,
                   final_state=[0.] * 6, final_velocity=[0.] * 6, final_object=[0.] * 7)
    meta = dict(episode_index=0, tasks=["capture"], length=3, outcome=outcome)
    summary = dict(ep=0, arm=0, seed=1000, frames=3, success=False, no_link=False,
                   duration_s=.006, stalls=0, max_dt_s=.002)
    cell = dict(task="capture", strategy="baseline", profile="zero", tau_h=.17, max_s=.006)
    with tempfile.TemporaryDirectory() as directory:
        p = Path(directory) / "sample.npz"
        np.savez(p, **g)
        g = load(p)
        assert verify_episode(g, s, meta, summary, cell, 0)["observed_newest_commands"] == 3
        blackout_s = dict(s, t_applied_ns=np.zeros(4, np.int64), cmd_seq=np.zeros(4, np.int64))
        blackout_meta = dict(meta, length=0, outcome=dict(outcome, no_link=True))
        blackout_summary = dict(summary, frames=0, no_link=True)
        blackout_g = {key: value[:0] for key, value in g.items() if not key.startswith("observation.") or key == "observation.state"}
        blackout_g.pop("command.t_send_ns")
        assert verify_episode(blackout_g, blackout_s, blackout_meta, blackout_summary, cell, 0)["observed_newest_commands"] == 0
        lost_uplink = dict(g, rtt_ms=np.full(3, np.nan), owd_up_ms=np.full(3, np.nan))
        assert verify_episode(lost_uplink, blackout_s, dict(meta, outcome=dict(outcome, no_link=True)),
                              dict(summary, no_link=True), cell, 0)["no_link"]
        for key, value, message in (
                ("cmd_seq", np.arange(1, 4), "command sequence off by one"),
                ("observation.t_send_ns", command + 1, "noncausal observation"),
                ("action", np.full((3, 7), np.nan), "nonfinite action")):
            try:
                verify_episode(dict(g, **{key: value}), s, meta, summary, cell, 0)
            except ValueError as exc:
                assert message in str(exc)
            else:
                raise AssertionError(f"corrupt {key} accepted")
    print("self-check passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", nargs="?", type=Path, default=ROOT / "docs/experiments/raw_second_wave")
    parser.add_argument("--partial", action="store_true", help="allow fewer than 15 completed cells")
    parser.add_argument("--out", type=Path, help="write evidence JSON; otherwise print it")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    result = verify(args.raw, args.partial)
    output = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(output)
        print(f'{len(result["cells"])} cells, {result["verified_episodes"]} verified episodes, '
              f'{len(result["errors"])} errors -> {args.out}')
        for error in result["errors"]:
            print(error)
    else:
        print(output, end="")
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
