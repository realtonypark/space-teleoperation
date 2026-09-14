"""Ground side: operator -> command packets at cmd_hz, telemetry -> RTT and the record.

RTT is measured only here: each telemetry echoes `last_cmd_t_send`, the ground's own
monotonic timestamp from the command the satellite last applied, so RTT = arrival - that,
with no cross-host clock comparison. A sample is taken only when the echoed sequence
number changes, otherwise repeated echoes would count stale commands again.

`rtt_ms` is the LINK round trip: the satellite's own dwell between applying a command and
sampling the next telemetry frame (t_send - t_cmd_applied, a difference of two stamps from
the satellite's clock, so no clock comparison) is subtracted. The lag an operator actually
feels is rtt_ms + that dwell, which averages 1/(2*tel_hz) ~= 17 ms at the default 30 Hz.

Telemetry is stamped ON ARRIVAL, not at the next 50 Hz tick: the loop spends its idle
slack inside `select()` and drains the socket the moment a datagram lands (audit T04).
Sleeping the slack instead put the ground's own poll dwell - U(0, 20 ms), mean 10 ms -
inside every RTT sample, which is what made the `zero` cell read 10 ms instead of ~1 ms.

One-way uplink delay is reported as RTT/2. That is an assumption, not a measurement: it is
exactly true only for a symmetric link, and space links usually are not (uplink and
downlink are separate profiles here and can differ). Anything that needs true one-way
delay needs synchronised clocks (GPS/PTP), which this testbed does not model.
"""
import select
import time

from ..proto import F_ASSIST, F_DONE, F_SAFETY_HOLD, F_SUCCESS, pack_cmd, unpack_tel


def run_episode(sock, up_addr, operator, strategy, cmd_hz=50.0, tau_h=0.17, max_s=20.0):
    """Drive one episode. Returns (rows, stats). Ends when telemetry says done."""
    dt = 1.0 / cmd_hz
    t0 = next_send = time.monotonic()
    hist, rows = [], []
    seq, sent, last_echo, rtt_ms, tel_rx = 0, 0, -1, 0.0, 0
    tel = None

    def poll(until):
        """Drain telemetry, stamping each frame when it ARRIVES, until `until`."""
        nonlocal tel_rx, last_echo, rtt_ms, tel
        while True:
            slack = until - time.monotonic()
            if slack > 0 and not select.select([sock], [], [], slack)[0]:
                return                                     # idled out, nothing arrived
            try:
                pkt, _ = sock.recvfrom(65535)
            except (BlockingIOError, OSError):
                if slack <= 0:
                    return                                 # socket empty, nothing to wait for
                continue
            now_ns = time.monotonic_ns()
            t = unpack_tel(pkt)
            if t is None:
                continue
            tel_rx += 1
            hist.append((now_ns / 1e9, t))
            if t["last_cmd_seq"] != last_echo and t["last_cmd_t_send"] > 0:
                last_echo = t["last_cmd_seq"]
                dwell = max(0, t["t_send"] - t["t_cmd_applied"])   # sat-side sampling wait
                rtt_ms = max(0.0, (now_ns - t["last_cmd_t_send"] - dwell) / 1e6)
            if t["flags"] & (F_DONE | F_SUCCESS):
                tel = t
                return

    while True:
        now = time.monotonic()
        poll(now)                                          # whatever is already queued
        if tel is not None and tel["flags"] & (F_DONE | F_SUCCESS):
            break
        if now - t0 > max_s + 3.0:
            break
        source = next(((ts, t) for ts, t in reversed(hist) if ts <= now - tau_h), None)
        if source is None:                                # nothing has arrived yet
            poll(now + 0.002)
            continue
        received_at, raw_seen = source
        seen = strategy.observe(raw_seen, now) # identity unless the strategy shows a twin
        sp = strategy.ground_step(seen, operator.step(seen, dt))
        # H11 Pg: a ground-side primitive tells the satellite that THIS frame is
        # robot-executed, so the recorded assist mask means the same thing for P and Pg
        assist = bool(getattr(strategy, "assist", False))
        ts = time.monotonic_ns()
        sock.sendto(pack_cmd(seq, ts, sp, F_ASSIST if assist else 0), up_addr)
        rows.append(dict(**{"observation.state": list(seen["q"]), "action": list(sp),
                            "observation.object": list(seen["obj"]),
                            "observation.tel_seq": raw_seen["seq"],
                            "observation.t_send_ns": raw_seen["t_send"],
                            "observation.t_rx_ns": int(received_at * 1e9),
                            "observation.predicted": seen is not raw_seen,
                            "command.t_send_ns": ts,
                            "timestamp": now - t0, "next.done": False},
                         cmd_seq=seq, rtt_ms=rtt_ms, owd_up_ms=rtt_ms / 2,
                         safety_hold=bool(hist[-1][1]["flags"] & F_SAFETY_HOLD),
                         assist=assist))
        seq, sent = seq + 1, sent + 1
        next_send += dt
        if next_send < time.monotonic():
            next_send = time.monotonic()   # fell behind: resync, never burst to catch up
        poll(next_send)                    # idle inside select, not inside sleep
    last = hist[-1][1] if hist else None
    return rows, dict(cmds_sent=sent, tel_rx=tel_rx, wall_s=time.monotonic() - t0,
                      success=bool(last and last["flags"] & F_SUCCESS),
                      last_tel_seq=last["seq"] if last else 0)
