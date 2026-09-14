"""Self-check: the SYNTHESIS section 5 (c) envelopes. Hold, retract, ramp, seq playout."""
import socket
import threading
import time
from types import SimpleNamespace

import numpy as np
import pytest

from spaceteleop import sim
from spaceteleop.proto import F_ASSIST, F_SAFETY_HOLD, pack_cmd, unpack_tel
from spaceteleop.sat.controller import run_episode
from spaceteleop.strategies.baseline import Baseline

TARGET = [0.6, -1.2, 1.2, 1.0, -1.0, 0.0, 0.0]


@pytest.mark.parametrize("win_at, expected", [(0.004, True), (0.012, False)])
def test_done_freezes_simulation_and_outcome_during_linger(monkeypatch, win_at, expected):
    """A success after the deadline cannot get credit or advance the next chain scene."""
    from spaceteleop.sat import controller

    clock = [10.0]
    monkeypatch.setattr(controller, "time", SimpleNamespace(
        monotonic=lambda: clock[0], monotonic_ns=lambda: int(clock[0] * 1e9),
        sleep=lambda dt: clock.__setitem__(0, clock[0] + dt)))
    m, d = sim.build()
    packets = []

    class Socket:
        def recvfrom(self, n):
            raise BlockingIOError

        def sendto(self, packet, addr):
            packets.append(unpack_tel(packet))

    def step(m, d, sp, st, t):
        d.time += 0.002
        st["success"] = d.time >= win_at
        return st["success"]

    monkeypatch.setattr(sim, "step", step)
    result = run_episode(m, d, Socket(), None, 0, Baseline(), max_s=0.010,
                         tel_hz=1000, linger_s=0.02)
    assert result["success"] is expected
    assert d.time <= (win_at if expected else 0.010) + 1e-9
    assert len(packets) > 10, "the terminal frame still needs retransmission"


def _pair():
    sat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sat.bind(("127.0.0.1", 0))
    sat.setblocking(False)
    gnd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gnd.bind(("127.0.0.1", 0))
    gnd.settimeout(1.0)
    return sat, gnd


def _run(strategy, feed, max_s=6.0):
    """Start a satellite, run `feed(sat_addr)`, stop it. -> (data, summary, telemetry)."""
    m, d = sim.build()
    sat, gnd = _pair()
    out, stop = {}, []
    th = threading.Thread(target=lambda: out.update(run_episode(
        m, d, sat, gnd.getsockname(), 0, strategy, max_s=max_s,
        stop=lambda: bool(stop))), daemon=True)
    th.start()
    feed(sat.getsockname())
    stop.append(1)
    th.join(3.0)
    tels = []
    gnd.setblocking(False)
    while True:
        try:
            tels.append(unpack_tel(gnd.recv(65535)))
        except (BlockingIOError, OSError):
            break
    return d, out, tels


def test_hold_on_timeout():
    t_silence = []

    def feed(addr):
        for i in range(40):                       # 0.8 s of commands at 50 Hz
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
                pack_cmd(i, time.monotonic_ns(), TARGET), addr)
            time.sleep(0.02)
        t_silence.append(time.monotonic_ns())
        time.sleep(1.0)                           # silence > timeout_s = 0.3

    d, out, tels = _run(Baseline(), feed)
    held = [bool(t["flags"] & F_SAFETY_HOLD) for t in tels
            if t["t_send"] > t_silence[0] + 0.4e9]
    assert held and all(held), held
    frozen = np.array(d.ctrl[:6])
    assert np.allclose(frozen, TARGET[:6], atol=0.05), frozen
    assert out["events"]["move_in_hold"] == 0      # hold means hold: never a new setpoint
    assert out["events"]["hold"] == 1 and out["events"]["retract"] == 0


def test_retract_after_long_silence_is_ramped():
    def feed(addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for i in range(25):
            s.sendto(pack_cmd(i, time.monotonic_ns(), TARGET), addr)
            time.sleep(0.02)
        time.sleep(2.2)                            # > retract_s below

    d, out, _ = _run(Baseline(timeout_s=0.2, retract_s=0.6), feed, max_s=6.0)
    assert out["events"]["retract"] == 1
    home = np.array([0.0, -1.57, 1.57, 1.57, -1.57, 0.0])
    assert np.allclose(d.ctrl[:6], home, atol=0.05), d.ctrl[:6]   # back at the reset pose
    log = out["satlog"]
    t = np.array([r[0] for r in log]) / 1e9
    sp = np.array([r[4] for r in log])[:, :6]
    v = np.abs(np.diff(sp, axis=0)).max(1) / np.diff(t)
    assert v.max() <= Baseline.vmax * 1.05, v.max()               # never a jump


def test_ground_side_assist_flag_reaches_the_sidecar():
    """F8: for Pg the primitive runs on the GROUND, so the satellite's own strategy never
    sets `assist` and the recorded mask was all-False for every Pg episode. The flag now
    rides up on the command and the controller ORs it in, so P and Pg record the same
    thing."""
    def feed(addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for i in range(30):
            s.sendto(pack_cmd(i, time.monotonic_ns(), TARGET, F_ASSIST if i > 14 else 0),
                     addr)
            time.sleep(0.02)

    _, out, tels = _run(Baseline(), feed, max_s=4.0)
    assist = [r[5] for r in out["satlog"]]
    assert any(assist) and not all(assist)
    assert not any(assist[:100]), "assist before the flag was ever sent"
    assert assist[-1], "the flag never reached the log"
    assert any(t["flags"] & F_ASSIST for t in tels)      # and it is echoed in telemetry


def test_playout_is_keyed_on_sequence_not_arrival():
    """Delivered out of order, the buffer must never play an older setpoint after a newer
    one. Joint 0 rises monotonically with seq, so any regression is a backwards jump."""
    def feed(addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pkts = [pack_cmd(i, time.monotonic_ns(), [0.02 * i] + TARGET[1:]) for i in range(40)]
        for i in range(0, 40, 2):                  # swap every neighbouring pair
            s.sendto(pkts[i + 1], addr)
            time.sleep(0.02)
            s.sendto(pkts[i], addr)
            time.sleep(0.02)
        time.sleep(0.2)

    _, out, _ = _run(Baseline(), feed, max_s=4.0)
    assert out["reordered"] == 20, out["reordered"]
    sp = np.array([r[4] for r in out["satlog"]])[:, 0]
    assert np.all(np.diff(sp) >= -1e-9), sp[np.argmin(np.diff(sp))]
    assert np.all(np.diff(np.array([r[2] for r in out["satlog"]])) >= 0)
