"""H10: the operator looks at a ground twin instead of at delayed telemetry.

Two halves, each removing a different piece of the perceived lag:

  arm      the near future of the arm is already fixed by the setpoints in flight, so the
           phantom is a setpoint the ground itself sent. It is the one sent at `now - tau_h`,
           NOT the newest one. The ground loop deliberately hands the operator a frame that
           is `tau_h` old (the human reaction model); substituting the newest setpoint would
           delete that delay from the arm channel and win just as much on `zero` as on a
           500 ms link, which is H13's artefact, not a latency hider.
  object   a free body in microgravity without contact moves at constant velocity, so the
           last two telemetry frames give a finite-difference velocity that is extrapolated
           over the lag the operator's command still has to travel: rtt/2 + dwell + interp_s.

Fallbacks, both to the raw frame: a safety hold (the satellite is frozen, so a phantom that
keeps moving is a lie), and an echoed `last_cmd_seq` that has not advanced for two telemetry
periods (nothing is getting through, so the setpoint log is not the arm's future either).

`innov` is the twin's own error signal: |predicted - next seen| per frame. Keep-out clipping
of the sent setpoint is deliberately not implemented (V3: the satellite clamps anyway).
"""
import time
from collections import deque

from ..proto import F_SAFETY_HOLD
from .baseline import Baseline


class Twin(Baseline):
    tau_h = 0.17
    tel_hz = 30.0

    def __init__(self, **kw):
        super().__init__(**kw)
        self.sent = deque(maxlen=128)     # (t_wall, setpoint) put on the wire
        self.frames = deque(maxlen=2)     # (t_send_ns, obj_xyz) of two DISTINCT frames
        self.echo = (-1, None)            # echoed last_cmd_seq, when it last changed
        self.pred, self.innov = None, []

    def ground_step(self, tel, sp):
        self.sent.append((time.monotonic(), list(sp)))
        return sp

    def observe(self, tel, now):
        if tel["last_cmd_seq"] != self.echo[0]:
            self.echo = (tel["last_cmd_seq"], now)
        t_echo = self.echo[1]
        if not self.frames or tel["t_send"] != self.frames[-1][0]:
            obj = list(tel["obj"][:3])
            if self.pred is not None:
                self.innov.append(sum((a - b) ** 2 for a, b in zip(self.pred, obj)) ** 0.5)
            self.frames.append((tel["t_send"], obj))
        if tel["flags"] & F_SAFETY_HOLD or now - t_echo > 2.0 / self.tel_hz:
            return tel
        phantom = next((sp for t, sp in reversed(self.sent) if t <= now - self.tau_h), None)
        if phantom is None or len(self.frames) < 2 or not tel["last_cmd_t_send"]:
            return tel
        dwell = max(0, tel["t_send"] - tel["t_cmd_applied"]) / 1e9
        # this frame reached the ground ~tau_h ago (ground/loop hands the operator a stale
        # frame), so take tau_h back out or it reads as round-trip time and doubles up below
        rtt = max(0.0, (time.monotonic_ns() - tel["last_cmd_t_send"]) / 1e9 - dwell - self.tau_h)
        lead = rtt / 2 + dwell + self.interp_s
        (t0, p0), (t1, p1) = self.frames
        dt = (t1 - t0) / 1e9
        v = [(b - a) / dt for a, b in zip(p0, p1)] if dt > 1e-6 else [0.0, 0.0, 0.0]
        self.pred = [x + w * lead for x, w in zip(p1, v)]
        return dict(tel, q=phantom, obj=self.pred + list(tel["obj"][3:]))
