"""Self-check: wire format round-trips and rejects junk; recorder + metrics round-trip."""
import numpy as np

from spaceteleop.metrics import aggregate, episode_metrics
from spaceteleop.proto import (F_SAFETY_HOLD, pack_cmd, pack_tel, unpack_cmd, unpack_tel)
from spaceteleop.record import load_episode, write_episode


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
    em = episode_metrics(ep, True, 2.0, cmds_sent=100, cmds_rx=95)
    assert em["success"] and abs(em["cmd_loss"] - 0.05) < 1e-9
    assert 40 <= em["rtt_p50"] <= 44 and em["hold_frames"] == 9
    assert abs(em["hold_s"] - 0.18) < 1e-6
    agg = aggregate([em, dict(em, success=False)])
    assert agg["success_rate"] == 0.5 and abs(agg["demos_per_hour"] - 1800) < 1
