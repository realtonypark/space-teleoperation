"""Self-check: a real socket episode on each of two profiles, recorded and measured.

Runs in wall clock (see spaceteleop/run.py), so --max-s is kept small on purpose.
"""
import time
from types import SimpleNamespace

from spaceteleop import sim
from spaceteleop.link.profiles import rtt_ms
from spaceteleop.metrics import episode_metrics
from spaceteleop.record import load_episode, write_episode
from spaceteleop.run import episode

ARGS = dict(max_s=10.0, cmd_hz=50.0, tel_hz=30.0, tau_h=0.25, frame_bytes=0)


def _one(tmp_path, profile, seed=0):
    m, d = sim.build()
    t0 = time.monotonic()
    rows, s = episode(m, d, profile, seed, SimpleNamespace(**ARGS))
    wall = time.monotonic() - t0
    path = write_episode(str(tmp_path / profile), 0, rows)
    ep = load_episode(path)                       # the recorder round-trips
    assert len(ep["action"]) == len(rows) > 50
    assert ep["observation.state"].shape[1] == 7 and ep["next.done"][-1]
    return episode_metrics(ep, s["success"], wall, s["cmds_sent"], s["cmds_rx"]), wall


def test_zero_profile(tmp_path):
    em, wall = _one(tmp_path, "zero")
    assert wall < 30.0, wall
    assert em["success"], em
    # nominal 0 ms; what is left is ground/sat polling (~1/2cmd_hz + a little)
    assert em["rtt_p50"] < 25.0, em["rtt_p50"]
    assert em["cmd_loss"] < 0.05, em["cmd_loss"]


def test_leo_relay_profile(tmp_path):
    em, wall = _one(tmp_path, "leo_relay")
    assert wall < 30.0, wall
    nominal = rtt_ms("leo_relay")
    assert abs(em["rtt_p50"] - nominal) <= 0.2 * nominal, (em["rtt_p50"], nominal)
    assert em["frames"] > 50 and em["jerk"] > 0
