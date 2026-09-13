"""Self-check: a real socket episode on each of two profiles, recorded and measured.

Runs in wall clock (see spaceteleop/run.py), so --max-s is kept small on purpose.
"""
import time
from types import SimpleNamespace

from spaceteleop import sim
from spaceteleop.link.profiles import rtt_ms
from spaceteleop.metrics import episode_metrics
from spaceteleop.record import load_episode, load_sat, write_episode
from spaceteleop.run import episode

ARGS = dict(max_s=10.0, cmd_hz=50.0, tel_hz=30.0, tau_h=0.17, frame_bytes=0, task="capture")


def _one(tmp_path, profile, seed=0):
    m, d = sim.build()
    t0 = time.monotonic()
    rows, s = episode(m, d, profile, seed, SimpleNamespace(**ARGS))
    wall = time.monotonic() - t0
    path = write_episode(str(tmp_path / profile.replace(":", "_")), 0, rows,
                         satlog=s["satlog"])
    ep, sat = load_episode(path), load_sat(path)              # both round-trip
    assert len(ep["action"]) == len(rows) > 50
    assert ep["observation.state"].shape[1] == 7 and ep["next.done"][-1]
    assert sat is not None and len(sat["setpoint"]) > 500 and sat["setpoint"].shape[1] == 7
    assert (sat["cmd_seq"][1:] >= sat["cmd_seq"][:-1]).all()  # seq-keyed playout, never back
    # T09: run.py charges the episode from its start to the done instant, not to the end
    # of the 1 s satellite linger plus the thread join plus the npz write
    em = episode_metrics(ep, s["success"], s["done_wall"] - t0, s["cmds_sent"], s["cmds_rx"],
                         events=s["events"], sat=sat)
    return em, wall, s


def test_zero_profile(tmp_path):
    em, wall, s = _one(tmp_path, "zero")
    assert wall < 30.0, wall
    assert em["success"], em
    # T04: telemetry is stamped on arrival, so what is left is the loopback link (~1 ms)
    # and the satellite's own cycle, NOT the ground's 20 ms poll quantisation (mean +10 ms)
    assert em["rtt_p50"] < 5.0, em["rtt_p50"]
    assert em["cmd_loss"] < 0.05, em["cmd_loss"]
    assert em["events"]["vel_over"] == 0 and em["events"]["move_in_hold"] == 0
    # T09: the episode ends at the done instant; the 1 s linger, join and write are not it
    assert em["duration_s"] <= wall - 0.9, (em["duration_s"], wall)
    assert em["stalls"] == 0, em["max_dt_s"]


def test_leo_relay_profile(tmp_path):
    em, wall, s = _one(tmp_path, "leo_relay")
    assert wall < 30.0, wall
    nominal = rtt_ms("leo_relay")
    assert abs(em["rtt_p50"] - nominal) <= 0.3 * nominal, (em["rtt_p50"], nominal)
    assert em["frames"] > 50 and em["jerk"] > 0
    assert em["sal"] < 0 and em["ldlj"] < 0 and 0.0 <= em["stall_frac"] <= 1.0
    assert s["link"]["up_bytes"] > 0 and s["link"]["down_bytes"] > 0


def test_sweep_profile_hits_its_rtt(tmp_path):
    em, _, _ = _one(tmp_path, "sweep:250")
    assert abs(em["rtt_p50"] - 250) <= 0.25 * 250, em["rtt_p50"]
