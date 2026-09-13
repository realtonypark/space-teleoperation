"""Satellite side: UDP in -> setpoint buffer -> interpolated joint command -> MuJoCo.

Realtime: the sim is stepped up to wall-clock elapsed each iteration, so injected link
delay (also wall clock) and control lag live in the same time base. No logical clock.

`t_cmd_applied` is stamped on the control cycle that first used the newest command, so the
ground can subtract the satellite's telemetry dwell time from its RTT measurement (both
stamps come from this host's clock, so the difference is valid across hosts).

Safety: with no command newer than `timeout_s` the commanded setpoint freezes at the last
interpolated value and F_SAFETY_HOLD is raised in telemetry. The arm holds position; it
never continues an old trajectory and never jumps when the link comes back (the playout
interpolator ramps from the frozen value). Before the FIRST command ever arrives the flag
stays clear: the arm is still parked at its reset pose and was never under control, so
counting that as a dropout would only measure link set-up time.
"""
import time

from .. import sim
from ..proto import (F_DONE, F_GRASPED, F_SAFETY_HOLD, F_SUCCESS, pack_tel, unpack_cmd)

BUFLEN = 64
# One telemetry frame is one datagram, and macOS caps a UDP datagram at 9216 bytes
# (net.inet.udp.maxdgram, root-only). 8 kB/frame at 30 Hz models a ~2 Mb/s video budget,
# which is the range this program cares about.
# ponytail: hard cap instead of fragmenting telemetry. Fragment if a bigger budget matters.
MAX_FRAME = 8192


def run_episode(m, d, sock, down_addr, seed, strategy, max_s=30.0, tel_hz=30.0,
                frame_bytes=0, linger_s=1.0, stop=None):
    """Run one episode. Returns a summary dict. Blocks until success, max_s or stop()."""
    if frame_bytes > MAX_FRAME:
        raise ValueError(f"frame_bytes > {MAX_FRAME}: one telemetry frame is one datagram")
    st = sim.reset(m, d, seed)
    strategy.last = list(d.ctrl[:sim.NJ]) + [0.0]
    buf, t0 = [], time.monotonic()
    last_arr, last_seq, last_tsend, ncmd = None, 0, 0, 0
    tel_seq, next_tel, tel_dt = 0, 0.0, 1.0 / tel_hz
    frame = b"\0" * frame_bytes
    hold_time, holds, done_at = 0.0, 0, None
    prev, t_applied, seen = t0, 0, 0
    while True:
        while True:                                   # drain everything that arrived
            try:
                pkt, _ = sock.recvfrom(65535)
            except (BlockingIOError, OSError):
                break
            c = unpack_cmd(pkt)
            if c is None:
                continue
            now = time.monotonic()
            buf.append((now, c["seq"], c["setpoints"]))
            buf[:] = sorted(buf[-BUFLEN:])            # late arrivals slot back into order
            last_arr, ncmd = now, ncmd + 1
            if c["seq"] >= last_seq:                  # a reordered straggler never becomes
                last_seq, last_tsend = c["seq"], c["t_send"]   # the echo the ground times
        now = time.monotonic()
        held = last_arr is not None and now - last_arr > strategy.timeout_s
        sp = strategy.sat_step([] if held else buf, now)
        if ncmd != seen:            # first control cycle that saw the newest command
            seen, t_applied = ncmd, time.monotonic_ns()
        if held:
            hold_time += now - prev
            holds += 1
        prev = now
        while d.time < now - t0:                      # step the sim up to wall clock
            if sim.step(m, d, sp, st, d.time) and done_at is None:
                done_at = now
        if now - t0 >= next_tel:
            next_tel += tel_dt
            tel_seq += 1
            flags = ((F_SAFETY_HOLD if held else 0) | (F_GRASPED if st["grasped"] else 0) |
                     (F_SUCCESS if st["success"] else 0) | (F_DONE if done_at else 0))
            q = list(d.qpos[:sim.NJ]) + [0.0]
            qd = list(d.qvel[:sim.NJ]) + [0.0]
            sock.sendto(pack_tel(tel_seq, time.monotonic_ns(), last_seq, last_tsend,
                                 t_applied, q, qd, sim.obj_pose(d, st), flags, frame),
                        down_addr)
        if done_at is None and now - t0 >= max_s:
            done_at = now
        if done_at is not None and now - done_at > linger_s:
            break
        if stop is not None and stop():
            break
        time.sleep(0.001)
    return dict(success=st["success"], duration=min(d.time, max_s), cmds_rx=ncmd,
                last_seq=last_seq, hold_time=hold_time, hold_steps=holds,
                obj=sim.obj_pose(d, st)[:3].tolist())
