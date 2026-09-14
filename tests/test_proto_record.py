"""Self-check: wire format round-trips and rejects junk; recorder + metrics round-trip."""
import json

import numpy as np
import pytest

from spaceteleop.metrics import aggregate, episode_metrics, ldlj, sal, table
from spaceteleop.proto import (F_SAFETY_HOLD, pack_cmd, pack_tel, unpack_cmd, unpack_tel)
from spaceteleop.record import load_episode, load_sat, write_episode


def test_proto_roundtrip_and_junk():
    sp = [0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7]
    c = unpack_cmd(pack_cmd(7, 123456789, sp, F_SAFETY_HOLD))
    assert c["seq"] == 7 and c["t_send"] == 123456789 and c["flags"] == F_SAFETY_HOLD
    assert np.allclose(c["setpoints"], sp, atol=1e-6)
    t = unpack_tel(pack_tel(1, 2, 3, 4, 5, sp, sp, [0, 0, 0, 1, 0, 0, 0], 0, b"\0" * 900))
    assert t["last_cmd_seq"] == 3 and t["t_cmd_applied"] == 5 and len(t["frame"]) == 900
    assert unpack_cmd(b"") is None and unpack_cmd(b"x" * 45) is None
    assert unpack_tel(b"x" * 200) is None
    assert unpack_tel(pack_tel(1, 2, 3, 4, 5, sp, sp, [0] * 7)[:-1]) is None   # truncated
    for bad in (float("nan"), float("inf"), -float("inf")):
        assert unpack_cmd(pack_cmd(0, 1, [bad] + [0.0] * 6)) is None
        for field in range(3):
            vectors = [[0.0] * 7 for _ in range(3)]
            vectors[field][0] = bad
            assert unpack_tel(pack_tel(1, 2, 3, 4, 5, *vectors)) is None


def test_record_and_metrics(tmp_path):
    rows = [dict(**{"observation.state": [0.0] * 7, "action": [0.01 * i] * 7,
                    "timestamp": 0.02 * i}, cmd_seq=i, rtt_ms=40 + i % 5,
                 owd_up_ms=20, safety_hold=(i > 90))
            for i in range(100)]
    p = write_episode(str(tmp_path), 0, rows)
    ep = load_episode(p)
    assert ep["index"][-1] == 99 and ep["next.done"][-1] and not ep["next.done"][0]
    em = episode_metrics(ep, True, 2.0, cmds_sent=100, cmds_rx=95,
                         events=dict(keepout=1, cage=2, hold=7))
    assert em["success"] and abs(em["cmd_loss"] - 0.05) < 1e-9
    assert 40 <= em["rtt_p50"] <= 44 and em["hold_frames"] == 9
    assert abs(em["hold_s"] - 0.18) < 1e-6
    # `hold` is a diagnostic, and `cage` is reported apart from the link-caused
    # counters, not summed into `unsafe` (audit T07)
    assert em["unsafe"] == 1 and em["events"]["vel_over"] == 0
    assert em["cage"] == 2 and em["stalls"] == 0
    agg = aggregate([em, dict(em, success=False)])
    assert agg["success_rate"] == 0.5 and abs(agg["demos_per_hour"] - 1800) < 1
    assert agg["unsafe"] == 2 and agg["cage"] == 4 and agg["events"]["cage"] == 4
    t = table("t", agg)
    assert "cage             4" in t and "hold=14" in t
    assert "unsafe_events    2" in t and "stalls           0" in t


def test_smoothness_comes_from_the_sidecar_not_the_sampled_observation(tmp_path):
    """T05: `observation.state` is a 50 Hz sample-and-hold of 30 Hz telemetry, which on its
    own puts a floor of ~0.4 under stall_frac. The same motion read off the satellite's
    applied-setpoint log must not show that floor."""
    t = np.linspace(0, 4, 2000)                       # 500 Hz control log, one moving joint
    q = 0.5 * (1 - np.cos(np.pi * np.clip(t / 4.0, 0, 1)))
    sat_rows = [(int(ti * 1e9), 0, i // 10, False, [qi] + [0.0] * 6)
                for i, (ti, qi) in enumerate(zip(t, q))]
    held = q[(np.arange(200) * 10) // 16 * 16 // 10]  # the same motion, sampled and held
    rows = [dict(**{"observation.state": [x] + [0.0] * 6, "action": [x] + [0.0] * 6,
                    "timestamp": 0.02 * i}, cmd_seq=i, rtt_ms=40, owd_up_ms=20,
                 safety_hold=False) for i, x in enumerate(held)]
    p = write_episode(str(tmp_path), 0, rows, satlog=sat_rows)
    ep, sat = load_episode(p), load_sat(p)
    with_sat = episode_metrics(ep, True, 4.0, 200, 200, sat=sat)
    without = episode_metrics(ep, True, 4.0, 200, 200)          # the old, held path
    assert without["stall_frac"] > 0.35                          # the artefact floor
    assert with_sat["stall_frac"] < 0.15, with_sat["stall_frac"]
    assert with_sat["ldlj"] > without["ldlj"]                    # hold artefact dominated it
    assert with_sat["stalls"] == 0 and with_sat["max_dt_s"] < 0.01


def test_stalls_flag_a_contaminated_episode(tmp_path):
    """T06: a satellite cycle longer than STALL_DT is CPU contention, not the link."""
    t = list(np.arange(0, 1.0, 0.002)) + [1.9, 1.902]            # one 0.9 s gap
    log = [(int(x * 1e9), 0, i, False, [0.0] * 7) for i, x in enumerate(t)]
    rows = [dict(**{"observation.state": [0.0] * 7, "action": [0.0] * 7,
                    "timestamp": 0.02 * i}, cmd_seq=i, rtt_ms=1, owd_up_ms=0,
                 safety_hold=False) for i in range(50)]
    p = write_episode(str(tmp_path), 0, rows, satlog=log)
    em = episode_metrics(load_episode(p), True, 2.0, 50, 50, sat=load_sat(p))
    assert em["stalls"] == 1 and abs(em["max_dt_s"] - 0.898) < 0.01
    assert aggregate([em, em])["stalls"] == 2


def test_info_json_carries_the_lerobot_keys(tmp_path):
    """T11: a v2.x loader parses these before it ever opens a data file."""
    rows = [dict(**{"observation.state": [0.0] * 7, "action": [0.0] * 7,
                    "timestamp": 0.02 * i}, cmd_seq=i, rtt_ms=1, owd_up_ms=0,
                 safety_hold=False, assist=(i > 40)) for i in range(50)]
    write_episode(str(tmp_path), 0, rows, task="capture")
    write_episode(str(tmp_path), 1, rows, task="peg", index0=50)
    info = json.loads((tmp_path / "meta" / "info.json").read_text())
    for k in ("total_tasks", "total_videos", "total_chunks", "chunks_size", "splits",
              "data_path", "video_path", "codebase_version", "fps", "features"):
        assert k in info, k
    assert info["codebase_version"] == "v2.1" and info["total_tasks"] == 2
    assert info["splits"] == {"train": "0:2"} and info["total_episodes"] == 2
    f = info["features"]
    assert f["observation.state"]["names"][:2] == ["Rotation", "Pitch"]
    assert f["action"]["shape"] == [7] and "task_index" in f
    tasks = [json.loads(l) for l in
             (tmp_path / "meta" / "tasks.jsonl").read_text().splitlines()]
    assert [t["task"] for t in tasks] == ["capture", "peg"]
    assert [t["task_index"] for t in tasks] == [0, 1]
    ep = load_episode(str(tmp_path / "data" / "episode_000001.npz"))
    assert ep["task_index"].tolist() == [1] * 50          # the column the loader joins on
    assert ep["assist"].sum() == 9                        # H11 mask, ground or satellite


def test_smoothness_ranks_a_jittery_trajectory_below_a_smooth_one():
    t = np.linspace(0, 2, 400)
    dt = float(t[1] - t[0])
    smooth = np.exp(-((t - 1.0) / 0.3) ** 2)
    rough = smooth * (1 + 0.6 * np.sin(2 * np.pi * 9 * t))
    assert sal(rough, dt) < sal(smooth, dt) < 0
    assert ldlj(rough, dt) < ldlj(smooth, dt) < 0
    assert np.isnan(sal(np.zeros(400), dt)) and np.isnan(ldlj([1.0] * 4, dt))


def test_sat_sidecar_round_trips(tmp_path):
    log = [(i * 1_000_000, i * 1_000_000 - 5, i // 4, i > 80, [0.001 * i] * 7)
           for i in range(100)]
    rows = [dict(**{"observation.state": [0.0] * 7, "action": [0.0] * 7,
                    "timestamp": 0.02 * i}, cmd_seq=i, rtt_ms=40, owd_up_ms=20,
                 safety_hold=False) for i in range(100)]
    p = write_episode(str(tmp_path), 0, rows, satlog=log)
    sat = load_sat(p)
    assert sat["setpoint"].shape == (100, 7) and sat["hold"].sum() == 19
    assert sat["t_ns"][-1] == 99_000_000 and sat["cmd_seq"][-1] == 24
    # 0.001 rad per 1 ms = 1 rad/s: under a 2 rad/s clamp, over a 0.5 rad/s one
    assert episode_metrics(load_episode(p), True, 1.0, 100, 100, sat=sat)["unsafe"] == 0
    assert episode_metrics(load_episode(p), True, 1.0, 100, 100, sat=sat,
                           vmax=0.5)["events"]["vel_over"] == 99
    assert load_sat(str(tmp_path / "data" / "episode_000009.npz")) is None


def test_recorder_retry_replaces_metadata_suffix_and_stale_sidecar(tmp_path):
    row = dict(**{"observation.state": [0.0] * 7, "action": [0.0] * 7,
                  "timestamp": 0.0}, cmd_seq=0, rtt_ms=1.0, owd_up_ms=0.5,
               safety_hold=False)
    log = [(1, 0, 0, False, [0.0] * 7)]
    out = str(tmp_path)
    read_meta = lambda: [json.loads(line) for line in
                         (tmp_path / "meta/episodes.jsonl").read_text().splitlines()]
    write_episode(out, 0, [row] * 2, satlog=log, task="capture")
    write_episode(out, 1, [row] * 3, index0=2, task="peg")
    write_episode(out, 2, [row], index0=5)
    # A retry from episode 1 retains episode 0 and supersedes the old 1..2 metadata.
    write_episode(out, 1, [row] * 4, index0=2, outcome={"success": False})
    entries = read_meta()
    assert [e["episode_index"] for e in entries] == [0, 1]
    assert [e["length"] for e in entries] == [2, 4]
    assert entries[-1]["outcome"] == {"success": False}
    info = json.loads((tmp_path / "meta/info.json").read_text())
    assert info["total_episodes"] == 2 and info["total_frames"] == 6
    with pytest.raises(ValueError, match="recorded prefix"):
        write_episode(out, 3, [row], index0=6)
    assert read_meta() == entries, "an invalid index must not modify existing metadata"
    # Reusing the directory from episode 0 creates fresh metadata, without deleting
    # unrelated old data files or letting an obsolete sidecar describe the new episode.
    path = write_episode(out, 0, [row], task="capture")
    assert len(read_meta()) == 1 and read_meta()[0]["length"] == 1
    assert load_sat(path) is None
    assert (tmp_path / "data/episode_000002.npz").exists()
    info = json.loads((tmp_path / "meta/info.json").read_text())
    assert info["total_episodes"] == info["total_frames"] == info["total_tasks"] == 1
    assert info["splits"] == {"train": "0:1"}
    tasks = [json.loads(line) for line in
             (tmp_path / "meta/tasks.jsonl").read_text().splitlines()]
    assert tasks == [{"task_index": 0, "task": "capture"}]
    write_episode(out, 1, [row] * 2, index0=1)
    assert [e["length"] for e in read_meta()] == [1, 2]
