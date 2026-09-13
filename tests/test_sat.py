"""Self-check: no fresh commands past timeout_s -> setpoint freezes and safety_hold set."""
import socket
import threading
import time

import numpy as np

from spaceteleop import sim
from spaceteleop.proto import F_SAFETY_HOLD, pack_cmd, unpack_tel
from spaceteleop.sat.controller import run_episode
from spaceteleop.strategies.baseline import Baseline


def test_hold_on_timeout():
    m, d = sim.build()
    sat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sat.bind(("127.0.0.1", 0))
    sat.setblocking(False)
    gnd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gnd.bind(("127.0.0.1", 0))
    gnd.settimeout(1.0)
    stop = []
    th = threading.Thread(target=run_episode, daemon=True, args=(
        m, d, sat, gnd.getsockname(), 0, Baseline()),
        kwargs=dict(max_s=3.0, stop=lambda: bool(stop)))
    th.start()

    target = [0.6, -1.2, 1.2, 1.0, -1.0, 0.0, 0.0]
    for i in range(30):                       # 0.6 s of commands at 50 Hz
        gnd.sendto(pack_cmd(i, time.monotonic_ns(), target), sat.getsockname())
        time.sleep(0.02)
    t_silence = time.monotonic_ns()
    time.sleep(1.2)                           # silence > timeout_s = 0.5
    stop.append(1)
    th.join(2.0)

    held, q = [], None
    gnd.setblocking(False)
    while True:                               # drain the whole episode, then look past the timeout
        try:
            t = unpack_tel(gnd.recv(65535))
        except (BlockingIOError, OSError):
            break
        if t["t_send"] > t_silence + 0.6e9:   # timeout_s elapsed with no command
            held.append(bool(t["flags"] & F_SAFETY_HOLD))
            q = np.array(t["q"][:6])

    assert held and all(held), held                       # every sample inside the silence
    frozen = np.array(d.ctrl[:6])
    assert np.allclose(frozen, target[:6], atol=0.05), frozen   # setpoint is the last one
    assert q is not None and np.allclose(q, frozen, atol=0.15), (q, frozen)
