"""Baseline = SYNTHESIS section 5 (c): playout, hold, retract, ramp limit, static clamps.

Ground sends the operator target unchanged. The satellite plays the buffer back with a
30 ms lag and linear interpolation, in its OWN arrival-time domain (never in the ground's
clock): at `now` it renders the buffer as it stood `interp_s` ago, interpolating between
the two setpoints that bracket that instant.

Three envelopes sit on top of the interpolator and are the only onboard "autonomy":
  hold     no command newer than `timeout_s` -> the target freezes at the last value, so a
           lost packet degrades into a freeze and never into a continued old trajectory,
  retract  `retract_s` of silence -> the target becomes the reset pose, ramp-limited,
  ramp     every emitted setpoint moves at most vmax*dt from the previous one, so link
           resume is a ramp from the frozen value and never a jump,
plus a static joint-position clamp. All of it is stateless bar one timer.
"""
from .base import Strategy


class Baseline(Strategy):
    def _playout(self, buf, t):
        if t <= buf[0][0]:
            return buf[0][2]
        if t >= buf[-1][0]:
            return buf[-1][2]
        i = max(j for j in range(len(buf)) if buf[j][0] <= t)
        t0, t1 = buf[i][0], buf[i + 1][0]
        a = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
        return [x + a * (y - x) for x, y in zip(buf[i][2], buf[i + 1][2])]

    def sat_step(self, buf, now):
        if not buf:
            return self.last
        gap = now - buf[-1][0]
        held, retracting = gap > self.timeout_s, gap > self.retract_s
        tgt = self.reset_pose if retracting else self.last if held else self._playout(
            buf, now - self.interp_s)
        self.ev["hold"] += held and not self.held
        self.ev["retract"] += retracting and not self.retracting
        self.held, self.retracting = held, retracting

        dt = 0.0 if self.t_prev is None else min(now - self.t_prev, 0.05)
        self.t_prev, lim = now, self.vmax * dt
        if any(abs(y - x) > lim for x, y in zip(self.last, tgt)):
            self.ev["ramp_clip"] += 1                      # a jump the ramp just prevented
        new = [x + max(-lim, min(lim, y - x)) for x, y in zip(self.last, tgt)]
        if self.qlim is not None:
            clamped = [min(max(v, lo), hi) for v, lo, hi in zip(new, *self.qlim)]
            # 1e-9 or the counter fires every cycle the arm sits pinned at a joint limit,
            # where the clamp is only undoing float error on an already-legal setpoint
            self.ev["pos_clamp"] += any(abs(a - b) > 1e-9 for a, b in zip(clamped, new))
            new = clamped
        if held and not retracting and new != self.last:
            self.ev["move_in_hold"] += 1                   # must stay 0: hold means hold
        self.last = new
        return new
