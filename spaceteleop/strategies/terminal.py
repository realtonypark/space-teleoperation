"""H11: terminal grasp / insertion primitive. **THIS IS THE ONBOARD-COMPUTE BRANCH.**

SYNTHESIS section 5 excludes every subgoal primitive and all vision from the baseline, so
nothing in this file is allowed to fly under decision (c). It is the measured value of
buying the exclusion back: `Terminal` runs the primitive on the satellite from the true
state (ground-truth pose, therefore an UPPER BOUND on what an onboard estimator could do),
`TerminalGround` runs the identical primitive on the ground from telemetry the link has
already aged, and P - Pg is what the onboard compute is worth.

The operator still produces every approach and every carry. Delegated is only the segment
latency destroys: the last <= 8 cm of a capture, or the last few mm of an insertion, both
bounded to 2 s and both entered only on the operator's own jaw-close / descent command.

Flow, satellite side: `sat_step` runs the baseline playout first, then, if the trigger
holds, replaces the target with one damped-least-squares step from the TRUE `d.qpos`
toward the object at <= 0.07 m/s. Either way the emitted setpoint goes through the
inherited baseline tail (hold, retract, ramp limit, joint clamp), which is why the section
6 envelopes still hold over the primitive's output and why `move_in_hold`, `ramp_clip`,
`pos_clamp` and `vel_over` keep counting the stream the arm actually saw.

The hand-back is the whole risk (H11 risk 3). While the primitive drives, the operator's
internal `qc` stays where it was, so its first post-primitive setpoint is several cm from
where the arm now is. Two things fix it and both are needed: this file crossfades from the
primitive's last output to the operator's stream over BLEND_S, which lands exactly on the
operator's value instead of ramp-clipping toward it for dozens of cycles; and
`SyntheticOperator._capture` re-anchors `qc` to the seen `tel["q"]` on entering `carry`,
which is what a human watching video does. Read the hand-back before the success column:
without the blend the arm snaps back, knocks the box away, and the gain is cancelled by a
chase. H11 states the check as "`ramp_clip` ~ 0 and `vel_over` = 0"; measured, `ramp_clip`
is never ~0 in this testbed (the BASELINE logs thousands per `capture` episode, because a
1 kHz control loop renders a 50 Hz jittered command stream), so the operative form is
`ramp_clip(P) <= ramp_clip(B)` on the same seeds AND `vel_over` = 0. Both hold; see the
phase-4 sanity tables.
"""
import time

import numpy as np
import mujoco

from .. import sim
from ..proto import F_GRASPED, F_SAFETY_HOLD, F_SUCCESS
from .baseline import Baseline

# ponytail: the primitive reads the simulator's exact object pose, so every number here is
# the UPPER BOUND of H11, never the flight value. The lower bound needs the noise cell the
# hypothesis asks for (5 mm position noise + 33 ms lag on `obj`), which is ~3 lines in
# `_run` plus a flag; add it when the upper bound turns out to be worth having.
REACH = 0.08        # m, capture trigger radius [design choice, H11]
MAX_S = 2.0         # s, hard bound on one primitive engagement [design choice, H11]
V = 0.07            # m/s, Cartesian speed of the primitive (H11 "<= 7 cm/s")
BLEND_S = 0.5       # s, hand-back crossfade back onto the operator's stream


class _Prim(Baseline):
    """The primitive itself. `Terminal` runs it in `sat_step`, `TerminalGround` in
    `ground_step`; everything below is state-source agnostic on purpose, so the ablation
    measures the state it sees and nothing else."""

    sat = None      # (m, d, st), set by sat/controller.py after sim.reset
    m = None        # model, passed by run.py for the ground ablation

    def __init__(self, **kw):
        super().__init__(**kw)
        self.assist = False
        self.ev.update(assist_frac=0.0, handback_peak=0.0)
        self._d = self._site = self._is_peg = None
        self._t_on = self._t_off = self._prev = None
        self._qp = self._q = None                   # the primitive's last output / command
        self._hb, self._T = False, BLEND_S          # hand-back cycle flag / its window
        self._armed = True                          # the trigger is edge-, not level-, read
        self._n = self._na = 0

    def _scratch(self, m):
        if self._d is None:
            self._d = mujoco.MjData(m)
            self._site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "grasp")
            self._is_peg = bool(sim.ids(m)["fix"])  # the fixture exists only in `peg`
        return self._d

    def _fk(self, m, q):
        d = self._scratch(m)
        d.qpos[:sim.NJ] = q
        mujoco.mj_forward(m, d)
        return d.site_xpos[self._site].copy()

    def _run(self, m, q, obj, grasped, won, cmd, dt, alive, seed):
        """One primitive cycle. -> 7 setpoints, or None when the operator owns the arm.

        The error and the Jacobian are taken at the TRUE joint state (that is the whole
        point of running onboard), but the step is integrated onto the setpoint stream
        rather than added to the measurement: a position-servo arm sits a little behind
        its command, so `q_true + delta` every cycle re-commands the lag and the arm only
        creeps. `seed` is the setpoint this side is currently emitting."""
        site = self._fk(m, q)
        if self._is_peg:
            off = obj - site                        # the unknown grasp offset, as seen
            lat = float(np.linalg.norm(obj[:2] - sim.HOLE[:2]))
            near, done = lat < 3 * sim.CLEAR, won
            tip = self._fk(m, cmd[:sim.NJ])[2] + off[2] - sim.PEG_H
            trig = near and tip < sim.FIX_TOP + sim.PEG_H     # commanded descent begun
            goal = sim.HOLE - off
            goal[2] = sim.INSERT_Z - off[2] if lat < sim.CLEAR else site[2]
        else:
            dist = float(np.linalg.norm(obj - site))
            near, done = dist < REACH, grasped
            trig = near and not grasped and cmd[sim.JAW] < 0.5 * sim.JAW_OPEN
            goal = obj.copy()
        if self._t_on is None:
            # edge-triggered: the 2 s bound is per commit, so after an exit the trigger has
            # to fall before the primitive may engage again. Without this the timeout exit
            # re-engages on the next cycle and the bound means nothing.
            self._armed = self._armed or not trig
            if not (trig and alive and self._armed):
                return None
            self._t_on, self._q = 0.0, np.array(seed[:sim.NJ], float)
        self._t_on += dt
        if done or not near or not alive or self._t_on > MAX_S:
            self._t_on, self._armed = None, False
            return None
        dx = goal - site
        n = float(np.linalg.norm(dx))
        if n > 1e-6:
            self._q += sim.dls(m, self._scratch(m), self._site, q, dx / n * min(n, V * dt))
        self._q = np.clip(self._q, m.jnt_range[:sim.NJ, 0], m.jnt_range[:sim.NJ, 1])
        out = list(self._q) + [cmd[6]]
        out[sim.JAW] = cmd[sim.JAW]                 # the jaw stays the operator's
        return out

    def _step(self, m, q, obj, grasped, won, cmd, dt, alive, tgt, seed):
        """Primitive, then hand-back. `tgt` is what the operator would command; the
        crossfade ends ON it, so the baseline resumes with no step to ramp away."""
        self._n += 1
        self._hb = False
        out = self._run(m, q, obj, grasped, won, cmd, dt, alive, seed) if alive else None
        if out is not None:
            self._na, self.assist, self._t_off = self._na + 1, True, None
            return out
        if self.assist:
            # just exited. Crossfade, never jump, and stretch the crossfade so its own
            # rate stays at a quarter of the clamp however far the operator's stream has
            # drifted: a fixed window plus a wide gap IS the ramp_clip storm H11 warns
            # about (measured: a fixed 0.5 s window put `ramp_clip` 47 % above baseline).
            gap = max(abs(y - x) for x, y in zip(self._qp, tgt))
            self.assist, self._t_off = False, 0.0
            self._T = max(BLEND_S, 4.0 * gap / self.vmax)
        if self._t_off is None or not alive:
            self._t_off = None
            return None
        self._t_off += dt
        a = self._t_off / self._T
        if a >= 1.0:
            self._t_off = None
            return None
        self._hb = True
        return [p + a * (t - p) for p, t in zip(self._qp, tgt)]

    def _rate(self, sp, dt):
        """Book the two H11 numbers on the setpoint that was actually EMITTED, after the
        baseline ramp.

        `handback_peak` is the peak applied joint speed inside the hand-back window. Read
        it next to the episode's own baseline, not against `vmax` on its own: measured, the
        baseline runs AT the 2.0 rad/s clamp on 5-15 % of `capture` control cycles anyway
        (the 1 kHz control loop renders a 50 Hz jittered command stream), so a 2.0 here
        means "one cycle at the clamp", not "the arm jumped". `ramp_clip` P vs B and
        `vel_over` = 0 are the decidable pair."""
        self.ev["assist_frac"] = round(self._na / max(1, self._n), 3)
        if self.assist:
            self._qp = list(sp)     # blend from what was EMITTED, not from what was asked
        if self._hb and self._prev is not None and dt > 0:
            v = max(abs(y - x) for x, y in zip(self._prev, sp)) / dt
            self.ev["handback_peak"] = round(max(self.ev["handback_peak"], v), 3)
        self._prev = list(sp)


class Terminal(_Prim):
    """ONBOARD-COMPUTE BRANCH: the primitive runs on the satellite, from the true state."""

    def sat_step(self, buf, now):
        if self.sat is None or not buf:
            self.assist, self._t_off = False, None   # empty buffer: hold, per H11 exit
            return super().sat_step(buf, now)
        dt = 0.0 if self.t_prev is None else min(now - self.t_prev, 0.05)
        m, d, st = self.sat
        a = st["ids"]["qadr"]
        out = self._step(m, np.array(d.qpos[:sim.NJ]), np.array(d.qpos[a:a + 3]),
                         st["grasped"], st["success"], buf[-1][2], dt,
                         now - buf[-1][0] <= self.timeout_s,
                         self._playout(buf, now - self.interp_s), self.last)
        # either way the baseline tail owns the emitted setpoint: same ramp, same clamp,
        # same counters. A one-entry buffer IS "play this target now".
        sp = super().sat_step(buf if out is None else [(now, 0, out)], now)
        self._rate(sp, dt)
        return sp


class TerminalGround(_Prim):
    """Ablation (Pg): the identical primitive, on the ground, from delayed telemetry.

    It re-anchors to a state that is one round trip old every cycle, which is exactly the
    thing onboard compute buys off. P - Pg is the measured value of that compute."""

    _t_gnd = None

    def ground_step(self, tel, target):
        now = time.monotonic()
        dt = 0.0 if self._t_gnd is None else min(now - self._t_gnd, 0.05)
        self._t_gnd = now
        f = tel["flags"]
        out = self._step(self.m, np.array(tel["q"][:sim.NJ]), np.array(tel["obj"][:3]),
                         bool(f & F_GRASPED), bool(f & F_SUCCESS), target, dt,
                         not f & F_SAFETY_HOLD, target, target)
        sp = target if out is None else out
        self._rate(sp, dt)
        return sp
