"""Self-check: a real socket episode on each of two profiles, recorded and measured.

Runs in wall clock (see spaceteleop/run.py), so --max-s is kept small on purpose.
"""
import json
import time
from types import SimpleNamespace

from spaceteleop import sim
from spaceteleop.link.profiles import rtt_ms
from spaceteleop.metrics import episode_metrics
from spaceteleop.record import load_episode, load_sat, write_episode
from spaceteleop.run import episode, run_arm

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
    assert ep["cmd_seq"].tolist() == list(range(len(rows)))
    assert ep["observation.object"].shape == (len(rows), 7)
    assert ((ep["command.t_send_ns"] - ep["observation.t_rx_ns"]) / 1e9 >= ARGS["tau_h"]).all()
    assert (ep["observation.t_rx_ns"] >= ep["observation.t_send_ns"]).all()
    assert sat is not None and len(sat["setpoint"]) > 500 and sat["setpoint"].shape[1] == 7
    assert (sat["cmd_seq"][1:] >= sat["cmd_seq"][:-1]).all()  # seq-keyed playout, never back
    assert sat["state"].shape == sat["velocity"].shape == (len(sat["t_ns"]), 6)
    assert sat["object"].shape == (len(sat["t_ns"]), 7)
    assert (sat["sim_time"][1:] >= sat["sim_time"][:-1]).all()
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


def test_first_episode_blackout_is_recorded_as_a_failure(tmp_path, monkeypatch, capsys):
    from spaceteleop.link.profiles import PROFILES, _d

    monkeypatch.setitem(PROFILES, "test_blackout", dict(up=_d(0, loss=1), down=_d(0, loss=1)))
    args = SimpleNamespace(**dict(ARGS, max_s=0.05, cmd_hz=25, profile="test_blackout",
                                 seed=0, episodes=1, arms=1, reset="free", out=str(tmp_path)))
    m, _ = sim.build()
    sink = {}
    run_arm(m, args, 0, sink)
    em = sink[0][0][0]
    assert not em["success"] and em["no_link"] and em["frames"] == 0
    assert "rtt_p50=nanms" in capsys.readouterr().out
    path = str(tmp_path / "data" / "episode_000000.npz")
    assert load_episode(path)["action"].shape == (0, 7)
    assert len(load_sat(path)["state"]) > 0
    meta = json.loads((tmp_path / "meta" / "episodes.jsonl").read_text())
    assert meta["outcome"]["no_link"] and not meta["outcome"]["success"]
    assert len(meta["outcome"]["final_object"]) == 7
    assert json.loads((tmp_path / "meta" / "info.json").read_text())["fps"] == 25
