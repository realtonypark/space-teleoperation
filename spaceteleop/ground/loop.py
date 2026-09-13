"""Ground side: operator -> command packets at cmd_hz, telemetry -> RTT and the record.

RTT is measured only here: each telemetry echoes `last_cmd_t_send`, the ground's own
monotonic timestamp from the command the satellite last applied, so RTT = now - that,
with no cross-host clock comparison. A sample is taken only when the echoed sequence
number changes, otherwise repeated echoes would count stale commands again.

`rtt_ms` is the LINK round trip: the satellite's own dwell between applying a command and
sampling the next telemetry frame (t_send - t_cmd_applied, a difference of two stamps from
the satellite's clock, so no clock comparison) is subtracted. The lag an operator actually
feels is rtt_ms + that dwell, which averages 1/(2*tel_hz) ~= 17 ms at the default 30 Hz.

One-way uplink delay is reported as RTT/2. That is an assumption, not a measurement: it is
exactly true only for a symmetric link, and space links usually are not (uplink and
downlink are separate profiles here and can differ). Anything that needs true one-way
delay needs synchronised clocks (GPS/PTP), which this testbed does not model.
"""
import time

import numpy as np

from ..proto import F_DONE, F_SAFETY_HOLD, F_SUCCESS, pack_cmd, unpack_tel


def run_episode(sock, up_addr, operator, strategy, cmd_hz=50.0, tau_h=0.17, max_s=20.0):
    """Drive one episode. Returns (rows, stats). Ends when telemetry says done."""
    dt = 1.0 / cmd_hz
    t0 = next_send = time.monotonic()
    hist, rows = [], []
    seq, sent, last_echo, rtt_ms, tel_rx = 0, 0, -1, 0.0, 0
    tel = None
    while True:
        now = time.monotonic()
        while True:
            try:
                pkt, _ = sock.recvfrom(65535)
            except (BlockingIOError, OSError):
                break
            t = unpack_tel(pkt)
            if t is None:
                continue
            tel_rx += 1
            hist.append((now, t))
            if t["last_cmd_seq"] != last_echo and t["last_cmd_t_send"] > 0:
                last_echo = t["last_cmd_seq"]
                dwell = max(0, t["t_send"] - t["t_cmd_applied"])   # sat-side sampling wait
                rtt_ms = max(0.0, (time.monotonic_ns() - t["last_cmd_t_send"] - dwell) / 1e6)
            if t["flags"] & (F_DONE | F_SUCCESS):
                tel = t
        if tel is not None and tel["flags"] & (F_DONE | F_SUCCESS):
            break
        if now - t0 > max_s + 3.0:
            break
        seen = next((t for ts, t in reversed(hist) if ts <= now - tau_h), None)
        if seen is None:                                  # nothing has arrived yet
            time.sleep(0.002)
            continue
        seen = strategy.observe(seen, now)     # identity unless the strategy shows a twin
        sp = strategy.ground_step(seen, operator.step(seen, dt))
        ts = time.monotonic_ns()
        sock.sendto(pack_cmd(seq, ts, sp), up_addr)
        seq, sent = seq + 1, sent + 1
        rows.append(dict(**{"observation.state": list(hist[-1][1]["q"]), "action": list(sp),
                            "timestamp": now - t0, "next.done": False},
                         cmd_seq=seq, rtt_ms=rtt_ms, owd_up_ms=rtt_ms / 2,
                         safety_hold=bool(hist[-1][1]["flags"] & F_SAFETY_HOLD)))
        next_send += dt
        slack = next_send - time.monotonic()
        if slack > 0:
            time.sleep(slack)
        else:
            next_send = time.monotonic()   # fell behind: resync, never burst to catch up
    last = hist[-1][1] if hist else None
    return rows, dict(cmds_sent=sent, tel_rx=tel_rx, wall_s=time.monotonic() - t0,
                      success=bool(last and last["flags"] & F_SUCCESS),
                      last_tel_seq=last["seq"] if last else 0)
