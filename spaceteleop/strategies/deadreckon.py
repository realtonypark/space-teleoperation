"""H12: the satellite extrapolates the command stream instead of lagging it by `interp_s`.

Baseline renders the buffer as it stood `interp_s` ago, so the arm trails the operator's
hand by uplink delay + playout. This fits a least-squares line over the last K setpoints and
evaluates it `L` ahead of where Baseline would have played it, which is negative playout
delay. The lead over the baseline is exactly `L`: at L = 0 the two arms are identical.

Time base is SEQUENCE, `t_i = seq_i / cmd_hz`, never arrival time. A burst of K packets
draining out of the emulator after a jitter spike arrives with near-identical arrival stamps
and distinct sequence numbers: fitted in arrival time the slope explodes, fitted in sequence
time it is exactly right. Arrival time enters only as the scalar `age` of the newest packet.

Horizon: past `H` the line is stale, and continuing it would walk the arm into the hold at
full speed, so the extrapolator stands down and the baseline playout (a freeze at the newest
setpoint) takes over. The whole result then goes through the inherited hold / retract / ramp
/ clamp tail, so `move_in_hold` and `vel_over` stay baseline-guaranteed.

Seam: `Baseline.sat_step` asks `_playout` for the target and applies every envelope to the
answer, so overriding `_playout` is the entire strategy. It is called at `now - interp_s`.
"""
import numpy as np

from .baseline import Baseline

JAW = 5     # spaceteleop.sim.JAW, inlined to keep the strategies free of MuJoCo


class DeadReckon(Baseline):
    L = 0.060       # lead: one uplink-plus-playout interval
    K = 8           # points in the fit; smooths the operator's per-tick noise
    H = 0.100       # horizon: older than this and the line is not trusted. H < timeout_s
    cmd_hz = 50.0   # plumbed from run.py --cmd-hz; the sequence-time unit

    def _playout(self, buf, t):
        now = t + self.interp_s              # Baseline calls us at now - interp_s
        age = now - buf[-1][0]
        if len(buf) < 2 or age > self.H:
            return super()._playout(buf, t)  # freeze at the newest, baseline gap behaviour
        w = buf[-self.K:]
        ts = np.array([s for _, s, _ in w], float) / self.cmd_hz
        sp = np.array([p for _, _, p in w], float)
        tm, pm = ts.mean(), sp.mean(0)
        slope = np.clip((ts - tm) @ (sp - pm) / ((ts - tm) ** 2).sum(), -self.vmax, self.vmax)
        # - interp_s so the lead over the baseline playout is EXACTLY L (audit F1): Baseline
        # renders at `now - interp_s`, and without this the evaluation instant was
        # `now + L`, i.e. a lead of L + 30 ms. L = 0 now really is the baseline.
        out = pm + slope * (ts[-1] + age - self.interp_s + self.L - tm)
        out[JAW] = w[-1][2][JAW]             # the jaw is a step command, never extrapolated
        return out.tolist()


DeadReckon30 = type("DeadReckon30", (DeadReckon,), {"L": 0.030})
