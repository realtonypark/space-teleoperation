"""Satellite side: UDP in -> setpoint buffer -> interpolated joint command -> MuJoCo.

Realtime: the sim is stepped up to wall-clock elapsed each iteration, so injected link
delay (also wall clock) and control lag live in the same time base. No logical clock.

The buffer is keyed on SEQUENCE, not on arrival time: a command whose seq is not newer
than the newest one already received is dropped on arrival. Uplink jitter reorders a
double-digit percentage of consecutive packets, and without this the interpolator would
happily play an older setpoint after a newer one -- a real backwards jump of the arm.

`t_cmd_applied` is stamped on the control cycle that first used the newest command, so the
ground can subtract the satellite's telemetry dwell time from its RTT measurement (both
stamps come from this host's clock, so the difference is valid across hosts).

Safety is all in the Strategy (SYNTHESIS section 5 (c)): playout, hold, retract, ramp
limit, joint clamp. This module supplies the model-derived constants, counts the sim-side
events (keep-out box, cage contact) and logs the applied setpoint every control cycle, so
a recorded episode carries what the ARM did and when, not only what the ground asked for.
Before the FIRST command ever arrives the hold flag stays clear: the arm is still parked
at its reset pose and was never under control.
"""
import time

import numpy as np

from .. import sim
from ..proto import (F_ASSIST, F_DONE, F_GRASPED, F_SAFETY_HOLD, F_SUCCESS, pack_tel,
                     unpack_cmd)

BUFLEN = 64
# H20: a chained episode does not end at success but at the teleoperated re-release that
# seeds the next one, so the max_s guillotine has to allow for the reset segment.
# This extends the TOTAL episode cap after capture, not a timer from capture.
RESET_MAX = 8.0
# One telemetry frame is one datagram, and macOS caps a UDP datagram at 9216 bytes
# (net.inet.udp.maxdgram, root-only). 8 kB/frame at 30 Hz models a ~2 Mb/s video budget,
# which is the range this program cares about.
# ponytail: hard cap instead of fragmenting telemetry. Fragment if a bigger budget matters.
MAX_FRAME = 8192


def run_episode(m, d, sock, down_addr, seed, strategy, task="capture", max_s=20.0,
                tel_hz=30.0, frame_bytes=0, linger_s=1.0, stop=None, st=None,
                reset_mode="free"):
    """Run one episode. Returns a summary dict. Blocks until success, max_s or stop().

    `st` carries a previous episode's sim state in (H20 chaining): passing it in means the
    scene is NOT reset, so the box, the arm and the alternating target continue where the
    last demonstration left them. Nothing else about the episode changes."""
    if frame_bytes > MAX_FRAME:
        raise ValueError(f"frame_bytes > {MAX_FRAME}: one telemetry frame is one datagram")
    if st is None:
        st = sim.reset(m, d, seed, task, reset_mode)
    else:                              # chained: new demonstration, same scene and box
        st.update(success=False, done=False, t_success=None, in_region_since=None,
                  keepout=0, cage_hits=0, jams=0, knockaway=0, t_out=None, t_hit=None, t_knock=None)
    strategy.sat = (m, d, st)          # H11: the primitive needs the satellite's own state
    home = list(d.ctrl[:sim.NJ]) + [0.0]
    strategy.last, strategy.reset_pose = list(home), list(home)
    strategy.qlim = (list(m.jnt_range[:sim.NJ, 0]) + [-1e9],
                     list(m.jnt_range[:sim.NJ, 1]) + [1e9])
    # sim_t0: a chained episode does not reset the scene, so MuJoCo time carries over and
    # "step up to wall clock" has to be measured from where this episode started.
    buf, t0, sim_t0 = [], time.monotonic(), d.time
    last_arr, last_seq, last_tsend, ncmd, reordered = None, 0, 0, 0, 0
    last_flags = 0
    tel_seq, next_tel, tel_dt = 0, 0.0, 1.0 / tel_hz
    frame = b"\0" * frame_bytes
    hold_time, holds, done_at, success_at = 0.0, 0, None, None
    prev, t_applied, seen, satlog, ev = t0, 0, 0, [], None
    done_i = None
    while True:
        while True:                                   # drain everything that arrived
            try:
                pkt, _ = sock.recvfrom(65535)
            except (BlockingIOError, OSError):
                break
            c = unpack_cmd(pkt)
            if c is None:
                continue
            if buf and c["seq"] <= buf[-1][1]:         # jitter-reordered straggler
                reordered += 1
                continue
            now = time.monotonic()
            buf.append((now, c["seq"], c["setpoints"]))
            del buf[:-BUFLEN]
            last_arr, ncmd = now, ncmd + 1
            last_seq, last_tsend, last_flags = c["seq"], c["t_send"], c["flags"]
        now = time.monotonic()
        sp = strategy.sat_step(buf, now)
        held = strategy.held
        if ncmd != seen:            # first control cycle that saw the newest command
            seen, t_applied = ncmd, time.monotonic_ns()
        if held:
            hold_time += now - prev
            holds += 1
        prev = now
        # the strategy ramp-limits against `now`; log the SAME instant or the
        # recorded velocity would be measured against a different clock reading
        # H11: the flag comes from whichever side ran the primitive. For Pg it rode up on
        # the command (ground/loop), for P the satellite strategy sets it. Same column either
        # way, so a training run can tell robot-executed frames from human ones for both.
        assist = bool(getattr(strategy, "assist", False) or last_flags & F_ASSIST)
        satlog.append((int(now * 1e9), t_applied, last_seq, held, sp, assist,
                       bool(m.ntendon and d.ten_length[0] > sim.SLACK),
                       d.time, list(d.qpos[:sim.NJ]), list(d.qvel[:sim.NJ]),
                       sim.obj_pose(d, st).tolist(), st["grasped"], st["success"]))
        budget = max_s + (RESET_MAX if task == "capture_chain" and success_at is not None else 0.0)
        # Linger retransmits the final state; it must never advance the task or award a
        # success after its deadline. Stop at the first terminal physics step as well.
        while done_at is None and d.time - sim_t0 < min(now - t0, budget):
            if sim.step(m, d, sp, st, d.time):
                done_at, done_i = now, len(satlog)
        if st["success"] and success_at is None:
            success_at = now                          # H20: R is measured from here
        if done_at is None and now - t0 >= max_s + (
                RESET_MAX if task == "capture_chain" and success_at is not None else 0.0):
            done_at, done_i = now, len(satlog)
        if now - t0 >= next_tel:
            next_tel += tel_dt
            tel_seq += 1
            # chained: F_SUCCESS is only raised at the end, or the ground loop would stop
            # driving before the operator has released. The operator sees the box parked
            # in the target region and lets go on its own, like a human watching video.
            won = st["success"] and (task != "capture_chain" or st["done"])
            flags = ((F_SAFETY_HOLD if held else 0) | (F_GRASPED if st["grasped"] else 0) |
                     (F_SUCCESS if won else 0) | (F_DONE if done_at else 0) |
                     (F_ASSIST if assist else 0))
            q = list(d.qpos[:sim.NJ]) + [0.0]
            qd = list(d.qvel[:sim.NJ]) + [0.0]
            sock.sendto(pack_tel(tel_seq, time.monotonic_ns(), last_seq, last_tsend,
                                 t_applied, q, qd, sim.obj_pose(d, st), flags, frame),
                        down_addr)
        if done_at is not None and ev is None:
            # freeze the counters at the end of the episode: the linger after `done_at` is
            # the ground having stopped sending, which would otherwise log a hold every run
            ev = dict(strategy.ev, keepout=st["keepout"], cage=st["cage_hits"],
                      jams=st["jams"], knockaway=st["knockaway"])
        if done_at is not None and now - done_at > linger_s:
            break
        if stop is not None and stop():
            break
        time.sleep(0.001)
    # the sidecar stops at done_at: everything past it is the linger, during which the
    # ground has stopped sending and every cycle logs a hold (audit F12). Keeping it would
    # put ~0.7 s of frozen setpoints into the smoothness and stall numbers (T05) and into
    # the assist denominator (F7).
    # Capture is a milestone; a reusable chain demonstration also needs release.
    won = st["success"] and (task != "capture_chain" or st["done"])
    return dict(success=won, duration=min(d.time - sim_t0, budget), cmds_rx=ncmd,
                last_seq=last_seq, hold_time=hold_time, hold_steps=holds,
                reordered=reordered, satlog=satlog[:done_i], st=st, success_wall=success_at,
                done_wall=done_at,
                released=st["done"],
                reset_s=(done_at - success_at) if success_at and done_at else 0.0,
                events=dict(ev or strategy.ev, stale=reordered),
                obj=sim.obj_pose(d, st)[:3].tolist())
