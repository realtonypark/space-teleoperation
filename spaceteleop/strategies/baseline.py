"""Baseline: ground sends the operator target unchanged; sat plays the buffer back with a
one-interval lag and linear interpolation, and freezes on a gap.

Playback is in the satellite's own arrival-time domain (never in the ground's clock): at
`now` the controller renders the buffer as it stood `interp_s` ago, interpolating between
the two setpoints that bracket that instant. A late or lost packet therefore degrades into
a freeze at the newest setpoint instead of a jump.
"""
from .base import Strategy


class Baseline(Strategy):
    def sat_step(self, buf, now):
        if not buf:
            return self.last
        t = now - self.interp_s
        if t <= buf[0][0]:
            self.last = buf[0][2]
        elif t >= buf[-1][0]:
            self.last = buf[-1][2]                       # gap -> freeze at newest
        else:
            i = max(j for j in range(len(buf)) if buf[j][0] <= t)
            t0, t1 = buf[i][0], buf[i + 1][0]
            a = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            p, q = buf[i][2], buf[i + 1][2]
            self.last = [x + a * (y - x) for x, y in zip(p, q)]
        return self.last
