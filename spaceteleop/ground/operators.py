"""Ground operators. Synthetic = a plausible human proxy, not an oracle.

SyntheticOperator models the three things that make a human latency-sensitive:
  1. it only ever sees telemetry that the link already delayed,
  2. it reacts to what it saw `tau_h` seconds ago (human reaction time; the ground loop
     applies it by handing this operator an older telemetry frame),
  3. it commands a *position* at a bounded Cartesian speed and keeps commanding until it
     SEES that it has arrived -- so it trails a moving object by roughly (object speed x
     loop delay) and commits to an insertion on a stale view of the alignment.

The policy, gains and speeds are IDENTICAL at every latency. Nothing here is tuned per
profile: the operator is the constant and the link is the variable, which is the only way
the success-vs-latency curve means anything.

Joint targets come from one damped-least-squares step per tick on the ground-side copy of
the model (mj_jacSite at the operator's internal joint state, not the delayed measurement,
which is what a leader-follower rig gives you: the hand moves smoothly regardless of lag).
"""
import numpy as np
import mujoco

from .. import sim

LAMBDA = 0.05      # DLS damping: bounds the joint step near wrist singularities
F_GRASPED = 0x02


class SyntheticOperator:
    # minimum approach speed per task: the operator eases off to this and no slower, so
    # its residual position error is (slow x loop delay). Chasing a 2-5 cm/s object needs
    # 5 cm/s; lining a peg up is done slowly, as a human does it. Constant across profiles.
    SLOW = {"capture": 0.05, "peg": 0.02, "capture_chain": 0.05}

    def __init__(self, m, seed=0, task="capture", tau_h=0.17, speed=0.07, slow=None,
                 noise=0.0015, close_at=0.018, reset_mode="free"):
        """close_at must stay below sim.GRASP_TOL: the operator commands the jaw shut when
        it SEES the object that close, and the capture envelope has to still contain it
        once the true state has moved on by one round trip.

        `reset_mode` (H20, `capture_chain` only) picks what this operator does once it sees
        the box parked in the target: `free` lets go where it is, which seeds the next
        demonstration; `teleop` carries it back to the spawn zone first and lets go there,
        which is the canonical reset and is charged to wall time. Same instance, same
        `speed`, `tau_h` and `noise` either way -- the reset is not allowed to be a
        different, faster operator."""
        self.m, self.d = m, mujoco.MjData(m)
        self.rng = np.random.default_rng(seed)
        self.tau_h, self.speed, self.noise, self.close_at = tau_h, speed, noise, close_at
        self.slow, self.task = self.SLOW[task] if slow is None else slow, task
        self.site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "grasp")
        self.qc = None
        self.phase = "align" if task == "peg" else "approach"
        self.jaw = sim.JAW_CLOSED if task == "peg" else sim.JAW_OPEN
        self.off = None
        self.chain, self.reset_mode = task == "capture_chain", reset_mode
        self.target, self.dwell = sim.TARGET_POS.copy(), 0.0

    def restart(self, released):
        """Next chained demonstration, same operator: only the phase restarts. The target
        alternates with the scene's, and only if the scene really saw the release."""
        if released and self.reset_mode == "free":
            self.target = (sim.TARGET_B if np.allclose(self.target, sim.TARGET_POS)
                           else sim.TARGET_POS.copy())
        self.phase, self.jaw, self.dwell = "approach", sim.JAW_OPEN, 0.0

    def _fk(self, q):
        self.d.qpos[:sim.NJ] = q
        mujoco.mj_forward(self.m, self.d)
        return self.d.site_xpos[self.site].copy()

    def _dls(self, q, dx):
        """One damped-least-squares step: joint delta that moves the grasp site by dx."""
        return sim.dls(self.m, self.d, self.site, q, dx, LAMBDA)

    def servo(self, tel, dt, goal):
        """Move the internal joint state so the grasp site heads for `goal` at `speed`."""
        if self.qc is None:
            self.qc = np.array(tel["q"][:sim.NJ])
        err = goal - self._fk(np.array(tel["q"][:sim.NJ]))    # seen error, not true error
        n = np.linalg.norm(err)
        if n > 1e-6:
            v = min(self.speed, max(self.slow, 2.0 * n))       # ease off over the last few cm
            self.qc = np.clip(self.qc + self._dls(self.qc, err / n * min(n, v * dt)),
                              self.m.jnt_range[:sim.NJ, 0], self.m.jnt_range[:sim.NJ, 1])
        out = self.qc + self.rng.normal(0, self.noise, sim.NJ)
        out[sim.JAW] = self.jaw
        return list(out) + [0.0]

    def step(self, tel, dt):
        """tel: the telemetry the operator is looking at (already delayed). -> 7 setpoints."""
        return (self._peg if self.task == "peg" else self._capture)(tel, dt)

    def _capture(self, tel, dt):
        ee_obs = self._fk(np.array(tel["q"][:sim.NJ]))
        obj = np.array(tel["obj"][:3])
        seen = np.linalg.norm(obj - ee_obs)
        if self.phase == "approach":
            goal = obj
            if seen < self.close_at:
                self.jaw, self.phase = sim.JAW_CLOSED, "closing"
        elif self.phase == "closing":
            goal = obj
            if tel["flags"] & F_GRASPED:
                # re-anchor to the arm as SEEN: a human watching video does not keep
                # commanding from a leader pose the arm never went to. Without this the
                # H11 primitive's hand-back is a several-cm step (H11 risk 3).
                self.phase, self.qc = "carry", np.array(tel["q"][:sim.NJ])
            elif seen > 3 * self.close_at:              # knocked it away, open up and chase
                self.jaw, self.phase = sim.JAW_OPEN, "approach"
        elif self.phase == "carry":
            goal = self.target
            if self.chain:                              # H20: let go once it looks parked
                near = np.linalg.norm(obj - self.target) < sim.TARGET_R
                self.dwell = self.dwell + dt if near else 0.0
                if self.dwell > sim.HOLD_S:
                    self.phase = "return" if self.reset_mode == "teleop" else "release"
                    self.dwell = 0.0
        elif self.phase == "return":                    # canonical reset, teleoperated
            goal = sim.SPAWN
            self.dwell = self.dwell + dt if np.linalg.norm(obj - sim.SPAWN) < 0.04 else 0.0
            if self.dwell > 0.1:
                self.phase, self.dwell = "release", 0.0
        else:                                           # release: hold still and open up
            goal, self.jaw = ee_obs, sim.JAW_OPEN
        return self.servo(tel, dt, goal)

    def _peg(self, tel, dt):
        """Align above the hole, then commit to a descent. The alignment the operator
        commits on is the one it SAW; a jam shows up as the peg no longer tracking the
        gripper, and the recovery is to withdraw and come back for it."""
        site = self._fk(np.array(tel["q"][:sim.NJ]))
        peg = np.array(tel["obj"][:3])
        if self.off is None:
            self.off = peg - site                       # learn the grasp offset by looking
        held = np.linalg.norm(peg - site - self.off) < sim.GRIP_R
        if held:
            self.off = peg - site
        lat = float(np.linalg.norm((peg - sim.HOLE)[:2]))
        goal = sim.HOLE - self.off
        if self.phase == "align":
            goal[2] = sim.APPROACH_Z - self.off[2]
            if held and lat < sim.CLEAR and peg[2] > sim.FIX_TOP + 0.5 * sim.PEG_H:
                self.phase = "insert"
        else:
            goal[2] = sim.INSERT_Z - self.off[2]
            if not held or lat > 2 * sim.CLEAR:         # jammed or drifted off: back out
                self.phase = "align"
        if not held:                                    # peg left behind: go back for it
            goal = peg + sim.GRIP
        return self.servo(tel, dt, goal)


class KeyboardOperator:
    """Manual client: w/s/a/d/q/e nudge the Cartesian goal, blank line toggles the jaw.

    # ponytail: line-buffered stdin in a thread, no termios raw mode, so it needs Enter per
    # key. Unused by the experiments; make it raw-mode when a human actually drives it.
    """

    KEYS = {"w": (0, +1), "s": (0, -1), "a": (1, +1), "d": (1, -1), "q": (2, +1), "e": (2, -1)}

    def __init__(self, m, step_m=0.01, **kw):
        import sys, threading
        self.op = SyntheticOperator(m, **kw)
        self.op.noise = 0.0
        self.step_m, self.goal, self.buf = step_m, None, []
        threading.Thread(target=lambda: [self.buf.append(l.strip().lower()) for l in sys.stdin],
                         daemon=True).start()

    def step(self, tel, dt):
        if self.goal is None:
            self.goal = np.array(tel["obj"][:3])
        while self.buf:
            k = self.buf.pop(0)
            if k in self.KEYS:
                i, s = self.KEYS[k]
                self.goal[i] += s * self.step_m
            else:
                self.op.jaw = sim.JAW_OPEN if self.op.jaw == sim.JAW_CLOSED else sim.JAW_CLOSED
        return self.op.servo(tel, dt, self.goal)
