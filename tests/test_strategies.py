"""Self-check: the one property of each strategy that its own hypothesis file calls a trap.

Twin        the phantom is the setpoint sent tau_h ago, never the newest one (H13 artefact)
DeadReckon  the line is fitted in SEQUENCE time, so a burst of packets sharing one arrival
            stamp still gives the right slope; it freezes past H and never moves in hold
Gain        the operator's speed falls as measured RTT rises, stays positive, and the
            setpoint on the wire is untouched
"""
import time
from types import SimpleNamespace

import pytest

from spaceteleop.strategies.adaptive_gain import Gain
from spaceteleop.strategies.deadreckon import JAW, DeadReckon
from spaceteleop.strategies.twin import Twin

HOME = [0.0] * 7


def tel(seq=1, rtt_ms=0.0, flags=0):
    """A telemetry frame whose echo says the sat applied our command `rtt_ms` ago."""
    now = time.monotonic_ns()
    return dict(seq=seq, t_send=now, t_cmd_applied=now, last_cmd_seq=seq,
                last_cmd_t_send=now - int(rtt_ms * 1e6), q=list(HOME),
                qd=list(HOME), obj=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], flags=flags)


def test_twin_phantom_is_the_setpoint_sent_tau_h_ago():
    tw = Twin(tau_h=0.10, tel_hz=30.0)
    sent = []
    for i in range(20):                                  # 0.4 s of commands at 50 Hz
        sp = [0.01 * i] * 7
        tw.observe(tel(seq=i), time.monotonic())         # keeps the echo and frames alive
        tw.ground_step(tel(seq=i), sp)
        sent.append((time.monotonic(), sp))
        time.sleep(0.02)
    now = time.monotonic()
    seen = tw.observe(tel(seq=99), now)
    want = [sp for t, sp in sent if t <= now - 0.10][-1]
    assert seen["q"] == want                             # what the human saw tau_h ago
    assert seen["q"] != sent[-1][1]                      # NOT the newest setpoint
    assert 0.08 < now - next(t for t, sp in sent if sp == want) < 0.14


def test_twin_falls_back_to_raw_telemetry_on_a_stalled_echo():
    tw = Twin(tau_h=0.02, tel_hz=30.0)
    for _ in range(5):
        tw.observe(tel(seq=7), time.monotonic())         # same echo the whole time
        tw.ground_step(tel(seq=7), [0.5] * 7)
        time.sleep(0.02)
    t = tel(seq=7)                                       # echo stuck > 2/tel_hz = 67 ms
    assert tw.observe(t, time.monotonic())["q"] == t["q"]


def test_deadreckon_fits_in_sequence_time_not_arrival_time():
    """Eight packets draining out of the emulator together: one arrival stamp, eight seqs.
    Joint 0 rises 0.02 rad per sequence step = 1.0 rad/s in sequence time."""
    dr = DeadReckon(cmd_hz=50.0)
    now = time.monotonic()
    burst = [(now, s, [0.02 * s] * 5 + [0.3, 0.0]) for s in range(8)]
    out = dr._playout(burst, now - dr.interp_s)
    # t* = seq_n/cmd_hz + age(0) + L = 0.14 + 0.060 -> 0.20 rad on the 1.0 rad/s line
    assert out[0] == pytest.approx(0.20, abs=1e-9)
    assert out[JAW] == 0.3                               # the jaw is never extrapolated
    assert DeadReckon(cmd_hz=50.0, L=0.030)._playout(burst, now - dr.interp_s)[0] == \
        pytest.approx(0.17, abs=1e-9)

    stale = [(now - 0.5, s, sp) for _, s, sp in burst]   # age 0.5 s > H = 0.1
    assert dr._playout(stale, now - dr.interp_s) == stale[-1][2]

    dr.last, dr.reset_pose = list(HOME), list(HOME)      # hold: gap 0.5 s > timeout_s
    for k in range(3):
        out = dr.sat_step(stale, now + 0.02 * k)
    assert dr.held and out == HOME and dr.ev["move_in_hold"] == 0


def test_gain_scales_operator_speed_down_as_rtt_rises_and_never_below_zero():
    op = SimpleNamespace(speed=0.07)
    g = Gain(operator=op, tau_h=0.17, tel_hz=30.0)
    seq, speeds = 0, []
    for rtt in (0.0, 0.1, 0.25, 0.5, 1.0, 5.0):
        for _ in range(120):                             # let the 0.2 s EMA settle
            seq += 1
            target = [0.4] * 7
            # the ground loop hands the strategy a frame that is already tau_h old, so the
            # echo reads rtt + tau_h; Gain takes tau_h back out and counts it once in L_hat
            t = tel(seq=seq, rtt_ms=(rtt + g.tau_h) * 1000)
            assert g.ground_step(t, target) == target    # the wire is never touched
        speeds.append(op.speed)
    assert speeds[0] == 0.07                             # L_hat 0.20 < L0 -> s = 1, no scaling
    assert all(b < a for a, b in zip(speeds, speeds[1:]))
    assert all(s > 0 for s in speeds)
    assert speeds[-1] == pytest.approx(0.07 * 0.29 / (5.0 + 0.03 + 0.17), rel=0.05)
