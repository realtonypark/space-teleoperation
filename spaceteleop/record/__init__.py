"""Minimal LeRobot-v2.1-shaped episode writer (.npz instead of parquet).

Mapping to a real LeRobot v2.1 dataset:
  ours                         LeRobot v2.1
  ----                         ------------
  data/episode_%06d.npz        data/chunk-000/episode_%06d.parquet (one row per frame)
  meta/info.json               meta/info.json  (all of the v2.1 keys, see below)
  meta/episodes.jsonl          meta/episodes.jsonl  ({episode_index, tasks, length})
  meta/tasks.jsonl             meta/tasks.jsonl  ({task_index, task})
  observation.state (7,)       observation.state   - joint positions as the ground saw them
  action (7,)                  action              - joint setpoint put on the wire
  timestamp, frame_index, episode_index, index, next.done, task_index   same names/meaning
Extras outside the LeRobot schema (kept as plain columns, harmless to a loader that
ignores them): cmd_seq, rtt_ms, owd_up_ms, safety_hold, assist.

`info.json` carries the keys a v2.x `LeRobotDataset` actually parses (audit T11):
`codebase_version`, `robot_type`, `fps`, `total_episodes`, `total_frames`, `total_tasks`,
`total_videos`, `total_chunks`, `chunks_size`, `splits`, `data_path`, `video_path`, and
per-feature `dtype`/`shape`/`names`. The ONE remaining structural deviation is deliberate
and documented here: `data_path` points at `.npz`, not `.parquet`, and there is no
`meta/episodes_stats.jsonl`, because nothing in this program reads the data through
`lerobot` and parquet would cost a pyarrow dependency. `data_path` names the real,
un-chunked npz location rather than a chunk directory that does not exist. A loader
therefore finds every key it looks for and then fails opening the file, instead of failing
on the metadata. See the ponytail note at the bottom.

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
        "index", "next.done", "task_index", "cmd_seq", "rtt_ms", "owd_up_ms",
        "safety_hold", "assist"]
CHUNK = 1000            # LeRobot `chunks_size`: episodes per data/chunk-%03d directory
# SO-100 joints + the spare wire slot: LeRobot wants a name per element of every vector
JOINTS = ["Rotation", "Pitch", "Elbow", "Wrist_Pitch", "Wrist_Roll", "Jaw", "spare"]


def _task_index(out_dir, task):
    """meta/tasks.jsonl, LeRobot v2.x: one {task_index, task} line per distinct task."""
    p = f"{out_dir}/meta/tasks.jsonl"
    tasks = []
    if os.path.exists(p):
        with open(p) as f:
            tasks = [json.loads(l)["task"] for l in f if l.strip()]
    if task not in tasks:
        tasks.append(task)
        with open(p, "a") as f:
            f.write(json.dumps({"task_index": len(tasks) - 1, "task": task}) + "\n")
    return tasks.index(task), len(tasks)


def write_sat(out_dir, ep_index, satlog):
    """satlog: [(t_ns, t_applied_ns, cmd_seq, hold, setpoint7[, assist, taut])] -> npz path.

    `assist` is proto.F_ASSIST per control cycle (H11): the mask a training run needs to
    tell a robot-executed segment from a human-executed one. `taut` is H20's tether."""
    if not satlog:
        return None
    col = lambda i, t: np.array([r[i] if len(r) > i else 0 for r in satlog], t)
    path = f"{out_dir}/data/episode_{ep_index:06d}_sat.npz"
    np.savez_compressed(
        path, t_ns=np.array([r[0] for r in satlog], np.int64),
        t_applied_ns=np.array([r[1] for r in satlog], np.int64),
        cmd_seq=np.array([r[2] for r in satlog], np.int64),
        hold=np.array([r[3] for r in satlog], bool),
        setpoint=np.array([r[4] for r in satlog], np.float32),
        assist=col(5, bool), taut=col(6, bool))
    return path


def write_episode(out_dir, ep_index, rows, task="capture", index0=0, satlog=()):
    """rows: list of dicts with the COLS keys (minus index/episode_index). -> npz path."""
    os.makedirs(f"{out_dir}/data", exist_ok=True)
    os.makedirs(f"{out_dir}/meta", exist_ok=True)
    n = len(rows)
    ti, ntasks = _task_index(out_dir, task)
    arr = {
        "observation.state": np.array([r["observation.state"] for r in rows], np.float32),
        "action": np.array([r["action"] for r in rows], np.float32),
        "timestamp": np.array([r["timestamp"] for r in rows], np.float32),
        "frame_index": np.arange(n, dtype=np.int64),
        "episode_index": np.full(n, ep_index, np.int64),
        "index": np.arange(index0, index0 + n, dtype=np.int64),
        "next.done": np.array([i == n - 1 for i in range(n)], bool),
        "task_index": np.full(n, ti, np.int64),
        "cmd_seq": np.array([r["cmd_seq"] for r in rows], np.int64),
        "rtt_ms": np.array([r["rtt_ms"] for r in rows], np.float32),
        "owd_up_ms": np.array([r["owd_up_ms"] for r in rows], np.float32),
        "safety_hold": np.array([r["safety_hold"] for r in rows], bool),
        # H11: which frames a primitive drove, from whichever side ran it (P or Pg)
        "assist": np.array([r.get("assist", False) for r in rows], bool),
    }
    path = f"{out_dir}/data/episode_{ep_index:06d}.npz"
    np.savez_compressed(path, **arr)
    write_sat(out_dir, ep_index, satlog)
    with open(f"{out_dir}/meta/episodes.jsonl", "a") as f:
        f.write(json.dumps({"episode_index": ep_index, "tasks": [task], "length": n}) + "\n")
    neps = ep_index + 1
    json.dump({"codebase_version": "v2.1", "robot_type": "so_arm100", "fps": FPS,
               "total_episodes": neps, "total_frames": index0 + n, "total_tasks": ntasks,
               "total_videos": 0, "total_chunks": (neps - 1) // CHUNK + 1,
               "chunks_size": CHUNK, "splits": {"train": f"0:{neps}"},
               # the documented deviation: the real path, .npz and un-chunked, where v2.1
               # says data/chunk-{episode_chunk:03d}/...parquet (see the module docstring)
               "data_path": "data/episode_{episode_index:06d}.npz",
               "video_path": None,
               "features": {k: {"dtype": str(v.dtype), "shape": list(v.shape[1:]) or [1],
                                "names": JOINTS[:v.shape[1]] if v.ndim > 1 else None}
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
