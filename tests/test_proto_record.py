"""Self-check: wire format round-trips and rejects junk; recorder + metrics round-trip."""
import numpy as np

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
    assert em["unsafe"] == 3 and em["events"]["vel_over"] == 0   # `hold` is a diagnostic
    agg = aggregate([em, dict(em, success=False)])
    assert agg["success_rate"] == 0.5 and abs(agg["demos_per_hour"] - 1800) < 1
    assert agg["unsafe"] == 6 and agg["events"]["cage"] == 4
    assert "cage=4" in table("t", agg) and "hold=14" in table("t", agg)


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
