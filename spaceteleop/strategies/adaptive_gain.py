"""H14: scale the OPERATOR's speed by the loop delay it is actually closing through.

The operator servos toward the seen object at v = min(speed, max(slow, K*n)), which through
a loop delay L is the delayed integrator x' = -K x(t-L): oscillatory above K*L = 1/e and
unstable above pi/2. Pinning K*L at the `zero` profile's value by scaling speed replaces
overshoot-and-chase with a slower continuous approach.

What is scaled is `operator.speed`, NOT the setpoint on the wire. `SyntheticOperator.servo`
integrates its own `qc` and linearises the Jacobian there, so scaling what is sent leaves
`qc` running (1-s) of the travel ahead of the arm and the DLS step is computed at a pose the
arm never visits: that measures windup, not gain scheduling (V4).

`tau_h` is a known constant of the ground station, added to the estimate rather than read
off the wire. The frame in hand is already `tau_h` old (ground/loop hands the operator a
stale frame), so `now - last_cmd_t_send` carries `tau_h` once; it is subtracted back out so
the measurement is round-trip time and `tau_h` is counted exactly once in L.

The EMA is per telemetry echo, not per second: one sample arrives per telemetry frame, so
alpha = 1 - exp(-(1/tel_hz)/ema_s) is the 0.2 s time constant with no clock reading at all.
"""
import math
import time

from .baseline import Baseline


class Gain(Baseline):
    RTT0 = 0.002    # s, the measured `zero`-profile link RTT (audit T04, E1: 1.25 ms)
    tau_h = 0.17
    tel_hz = 30.0
    ema_s = 0.2
    operator = None

    def __init__(self, **kw):
        super().__init__(**kw)
        self.rtt = self.speed0 = None
        self.echo = -1
        self.s = 1.0

    @property
    def L0(self):
        """The MEASURED zero-latency loop delay this pins K*L to (audit F5).

        Same four terms L_hat is built from, at the zero profile's own RTT: playout +
        half a telemetry period of satellite dwell + the human + the loopback link. At the
        defaults that is 30 + 16.7 + 170 + 2 = 219 ms. The old hard-coded 0.29 was 58 ms
        above the loop it was meant to represent, so `s` stayed pinned at 1.000 on
        `leo_relay` (G was literally B there) and moved with `tau_h` on block E, which made
        the tau_h comparison a comparison of two different controllers."""
        return self.interp_s + 0.5 / self.tel_hz + self.tau_h + self.RTT0

    def ground_step(self, tel, target):
        if self.operator is None:                     # satellite-side copy: nothing to scale
            return target
        if self.speed0 is None:
            # F6: the operator persists across chained episodes, so a fresh Gain must not
            # take the PREVIOUS episode's already-scaled speed as its reference.
            self.speed0 = getattr(self.operator, "speed0", None) or self.operator.speed
            self.operator.speed0 = self.speed0
        dwell = max(0, tel["t_send"] - tel["t_cmd_applied"]) / 1e9
        if tel["last_cmd_seq"] != self.echo and tel["last_cmd_t_send"] > 0:
            self.echo = tel["last_cmd_seq"]
            r = max(0.0, (time.monotonic_ns() - tel["last_cmd_t_send"]) / 1e9
                    - dwell - self.tau_h)
            a = 1.0 - math.exp(-1.0 / (self.tel_hz * self.ema_s))
            self.rtt = r if self.rtt is None else self.rtt + a * (r - self.rtt)
        if self.rtt is not None:
            lhat = self.rtt + dwell + self.interp_s + self.tau_h
            self.s = min(1.0, self.L0 / lhat) if lhat > 0 else 1.0
            self.operator.speed = self.speed0 * self.s
        return target
