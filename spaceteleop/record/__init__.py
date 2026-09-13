"""Minimal LeRobot-v2-shaped episode writer (.npz instead of parquet).

Mapping to a real LeRobot v2.0 dataset:
  ours                         LeRobot v2.0
  ----                         ------------
  data/episode_%06d.npz        data/chunk-000/episode_%06d.parquet (one row per frame)
  meta/info.json               meta/info.json  (codebase_version, fps, features, shapes)
  meta/episodes.jsonl          meta/episodes.jsonl  ({episode_index, tasks, length})
  observation.state (7,)       observation.state   - joint positions as the ground saw them
  action (7,)                  action              - joint setpoint put on the wire
  timestamp, frame_index, episode_index, index, next.done   same names, same meaning
Extras outside the LeRobot schema (kept as plain columns, harmless to a loader that
ignores them): cmd_seq, rtt_ms, owd_up_ms, safety_hold.

Sidecar `data/episode_%06d_sat.npz` holds the SATELLITE side, one row per control cycle:
`t_ns` (the cycle), `t_applied_ns` (when the newest command first reached the arm),
`cmd_seq`, `hold`, `setpoint` (7). The main table pairs the newest telemetry the ground
held with the command it sent on the same tick, which on leo_relay is ~85 ms of
observation-action skew; anything that needs the true applied action at a true instant
re-pairs it from here instead of trusting that skew.
To convert: read the npz, build a pandas DataFrame per episode, write parquet. No
lerobot dependency here on purpose.
# ponytail: npz + jsonl, no parquet/pyarrow dependency. Add the converter when a training
# run actually needs it.
"""
import json
import os

import numpy as np

FPS = 50
COLS = ["observation.state", "action", "timestamp", "frame_index", "episode_index",
        "index", "next.done", "cmd_seq", "rtt_ms", "owd_up_ms", "safety_hold"]


def write_sat(out_dir, ep_index, satlog):
    """satlog: [(t_ns, t_applied_ns, cmd_seq, hold, setpoint7)] -> npz path (or None)."""
    if not satlog:
        return None
    path = f"{out_dir}/data/episode_{ep_index:06d}_sat.npz"
    np.savez_compressed(
        path, t_ns=np.array([r[0] for r in satlog], np.int64),
        t_applied_ns=np.array([r[1] for r in satlog], np.int64),
        cmd_seq=np.array([r[2] for r in satlog], np.int64),
        hold=np.array([r[3] for r in satlog], bool),
        setpoint=np.array([r[4] for r in satlog], np.float32))
    return path


def write_episode(out_dir, ep_index, rows, task="capture", index0=0, satlog=()):
    """rows: list of dicts with the COLS keys (minus index/episode_index). -> npz path."""
    os.makedirs(f"{out_dir}/data", exist_ok=True)
    os.makedirs(f"{out_dir}/meta", exist_ok=True)
    n = len(rows)
    arr = {
        "observation.state": np.array([r["observation.state"] for r in rows], np.float32),
        "action": np.array([r["action"] for r in rows], np.float32),
        "timestamp": np.array([r["timestamp"] for r in rows], np.float32),
        "frame_index": np.arange(n, dtype=np.int64),
        "episode_index": np.full(n, ep_index, np.int64),
        "index": np.arange(index0, index0 + n, dtype=np.int64),
        "next.done": np.array([i == n - 1 for i in range(n)], bool),
        "cmd_seq": np.array([r["cmd_seq"] for r in rows], np.int64),
        "rtt_ms": np.array([r["rtt_ms"] for r in rows], np.float32),
        "owd_up_ms": np.array([r["owd_up_ms"] for r in rows], np.float32),
        "safety_hold": np.array([r["safety_hold"] for r in rows], bool),
    }
    path = f"{out_dir}/data/episode_{ep_index:06d}.npz"
    np.savez_compressed(path, **arr)
    write_sat(out_dir, ep_index, satlog)
    with open(f"{out_dir}/meta/episodes.jsonl", "a") as f:
        f.write(json.dumps({"episode_index": ep_index, "tasks": [task], "length": n}) + "\n")
    json.dump({"codebase_version": "v2.0", "robot_type": "so_arm100", "fps": FPS,
               "total_episodes": ep_index + 1, "total_frames": index0 + n,
               "features": {k: {"dtype": str(v.dtype), "shape": list(v.shape[1:])}
                            for k, v in arr.items()}},
              open(f"{out_dir}/meta/info.json", "w"), indent=1)
    return path


def load_episode(path):
    with np.load(path) as z:
        return {k: z[k] for k in z.files}


def load_sat(path):
    """Sidecar next to `path`, or None if the episode carried no satellite log."""
    p = path.replace(".npz", "_sat.npz")
    return load_episode(p) if os.path.exists(p) else None
