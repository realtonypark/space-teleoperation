"""Self-check for H11 (`Terminal`, onboard-compute branch) and H20 (`capture_chain`).

The primitive is driven directly against a hand-placed scene instead of through sockets:
the trigger, the four exits and the hold behaviour are all decidable from one buffer and
one `MjData`, and a socket run would only add wall clock. The chain test does need the
operator in the loop -- that IS the property under test (the reset is teleoperated, not a
teleport) -- so it runs the operator against the sim through a pure transport delay, like
tests/test_sim_operator.py.
"""
import time

import numpy as np
import mujoco

from spaceteleop import sim
from spaceteleop.ground.operators import SyntheticOperator
from spaceteleop.strategies.terminal import MAX_S, REACH, Terminal

JAW_SLOT = sim.JAW


def _rig(dist=0.05, task="capture"):
    """A satellite-side Terminal looking at a box `dist` m from its grasp site."""
    m, d = sim.build(task)
    st = sim.reset(m, d, 0, task)
    mujoco.mj_forward(m, d)
    a, v = st["ids"]["qadr"], st["ids"]["vadr"]
    d.qpos[a:a + 3] = d.site_xpos[st["ids"]["site"]] + np.array([dist, 0.0, 0.0])
    d.qvel[v:v + 6] = 0
    mujoco.mj_forward(m, d)
    s = Terminal()
    s.last = s.reset_pose = list(d.ctrl[:sim.NJ]) + [0.0]
    s.qlim = (list(m.jnt_range[:sim.NJ, 0]) + [-1e9], list(m.jnt_range[:sim.NJ, 1]) + [1e9])
    s.sat = (m, d, st)
    return m, d, st, s


def _cmd(d, jaw):
    c = list(d.qpos[:sim.NJ]) + [0.0]
    c[JAW_SLOT] = jaw
    return c


def _drive(s, d, jaw, n=20, now=None, dt=0.002, buf=True):
    """n control cycles with the newest setpoint commanding `jaw`. -> (last sp, now)."""
    now = time.monotonic() if now is None else now
    sp = None
    for _ in range(n):
        now += dt
        sp = s.sat_step([(now, 1, _cmd(d, jaw))] if buf else [], now)
    return sp, now


def test_trigger_needs_both_the_jaw_command_and_the_range():
    _, d, _, s = _rig(dist=0.05)
    _drive(s, d, sim.JAW_OPEN)
    assert not s.assist                       # in range, but the operator has not committed

    _, d, _, s = _rig(dist=0.05)
    _drive(s, d, sim.JAW_CLOSED)
    assert s.assist and s.ev["assist_frac"] > 0

    _, d, _, s = _rig(dist=REACH + 0.04)
    _drive(s, d, sim.JAW_CLOSED)
    assert not s.assist                       # committed, but the box is not its business


def test_exits_on_grasp_timeout_range_and_empty_buffer():
    _, d, st, s = _rig(dist=0.05)             # (a) grasped: the primitive is done
    _, now = _drive(s, d, sim.JAW_CLOSED)
    assert s.assist
    st["grasped"] = True
    _drive(s, d, sim.JAW_CLOSED, n=2, now=now)
    assert not s.assist

    _, d, st, s = _rig(dist=0.05)             # (b) 2 s bound, always
    _, now = _drive(s, d, sim.JAW_CLOSED, n=5)
    assert s.assist
    _, now = _drive(s, d, sim.JAW_CLOSED, n=int(MAX_S / 0.01) + 5, now=now, dt=0.01)
    assert not s.assist

    m, d, st, s = _rig(dist=0.05)             # (c) out of range: box knocked away
    _, now = _drive(s, d, sim.JAW_CLOSED)
    assert s.assist
    a = st["ids"]["qadr"]
    d.qpos[a:a + 3] = d.site_xpos[st["ids"]["site"]] + np.array([REACH + 0.05, 0.0, 0.0])
    mujoco.mj_forward(m, d)
    _drive(s, d, sim.JAW_CLOSED, n=2, now=now)
    assert not s.assist

    _, d, _, s = _rig(dist=0.05)              # (d) empty buffer = hold, not a free arm
    _, now = _drive(s, d, sim.JAW_CLOSED)
    assert s.assist
    _drive(s, d, sim.JAW_CLOSED, n=2, now=now, buf=False)
    assert not s.assist


def test_stale_link_is_a_hold_even_mid_primitive():
    """The SYNTHESIS 6 property the primitive is not allowed to break: while the link is
    timed out the commanded setpoint does not move, primitive or no primitive."""
    _, d, _, s = _rig(dist=0.05)
    sp, now = _drive(s, d, sim.JAW_CLOSED)
    assert s.assist
    stale, seen = now, []                      # buffer stops being refreshed here
    for _ in range(200):
        now += 0.005
        seen.append(s.sat_step([(stale, 1, _cmd(d, sim.JAW_CLOSED))], now))
    assert not s.assist and s.held
    assert s.ev["move_in_hold"] == 0
    assert all(x == seen[-1] for x in seen[-100:])          # hold means hold (onset ~0.3 s)
    assert seen[-1] != sp                                   # and it did move before that


def _chain(seed, reset_mode, lag_s=0.0, max_s=30.0, tau_h=0.17, hz=50):
    """Operator vs sim through a pure transport delay. -> (st, phases, box track)."""
    m, d = sim.build("capture_chain")
    st = sim.reset(m, d, seed, "capture_chain", reset_mode)
    op = SyntheticOperator(m, seed=seed, task="capture_chain", tau_h=tau_h,
                           reset_mode=reset_mode)
    n = max(1, round((lag_s + tau_h) * hz))
    sub = round(1.0 / hz / m.opt.timestep)
    a = st["ids"]["qadr"]
    look = lambda: dict(q=list(d.qpos[:sim.NJ]) + [0.0], obj=list(sim.obj_pose(d, st)),
                        flags=(0x02 if st["grasped"] else 0))
    t, hist, phases, track = 0.0, [look()], [], []
    while t < max_s and not st["done"]:
        sp = op.step(hist[max(0, len(hist) - n)], 1.0 / hz)
        phases.append((t, op.phase))
        for _ in range(sub):
            sim.step(m, d, sp, st, t)
            t += m.opt.timestep
        track.append(np.array(d.qpos[a:a + 3]))
        hist.append(look())
    return st, phases, np.array(track), t


def test_canonical_reset_is_teleoperated_and_costs_real_time():
    st, phases, track, t_end = _chain(0, "teleop")
    assert st["success"] and st["done"], (st["success"], st["done"])
    r = t_end - st["t_success"]
    assert r > 0.5, r                          # a reset that costs nothing is the trap
    # it went through the operator, not through sim.reset: a return phase, then a release
    seen = [p for _, p in phases]
    assert "return" in seen and "release" in seen
    assert seen.index("return") < seen.index("release")
    assert np.linalg.norm(track[-1] - sim.SPAWN) < 0.06, track[-1]   # back at the spawn
    assert np.abs(np.diff(track, axis=0)).max() < 0.01               # never teleported
    assert np.allclose(st["target"], sim.TARGET_POS)                 # canonical: still A


def test_chained_release_seeds_the_next_demo():
    st, _, track, _ = _chain(0, "free")
    assert st["success"] and st["done"] and not st["grasped"]
    assert np.allclose(st["target"], sim.TARGET_B)        # A -> B, no canonical state
    assert np.abs(np.diff(track, axis=0)).max() < 0.01    # the box was never moved for us


def test_tether_is_slack_inside_the_working_volume():
    m, d = sim.build("capture_chain")
    st = sim.reset(m, d, 1, "capture_chain")
    for k in range(500):
        sim.step(m, d, list(d.ctrl[:sim.NJ]) + [0.0], st, k * m.opt.timestep)
    assert m.ntendon == 1 and d.ten_length[0] < sim.SLACK
    # H20: a 20 cm dead band has to cover every target and the spawn zone, or the "free
    # 6-DoF body" subset is empty
    for p in (sim.TARGET_POS, sim.TARGET_B, sim.SPAWN):
        assert np.linalg.norm(p - sim.TETHER) < sim.SLACK, p


def _stall_the_jaw_on_the_box(m, d, ids, quat_seed=21):
    """Close the jaw from OPEN onto a box parked at the grasp site, raw physics only.

    The box blocks the pads, so the jaw stops wherever the box's projected width puts it,
    which for this orientation is ABOVE JAW_GRASP. Returns the stall angle."""
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[sim.JAW] = d.ctrl[sim.JAW] = sim.JAW_OPEN
    mujoco.mj_forward(m, d)
    a, v = ids["qadr"], ids["vadr"]
    q = np.random.default_rng(quat_seed).normal(size=4)
    d.qpos[a:a + 3] = d.site_xpos[ids["site"]]
    d.qpos[a + 3:a + 7] = q / np.linalg.norm(q)
    d.qvel[v:v + 6] = 0
    mujoco.mj_forward(m, d)
    hold, jaw = np.array(d.qpos[:sim.NJ]), sim.JAW_OPEN
    for _ in range(1200):                          # ramp shut at vmax, like the strategy
        jaw = max(sim.JAW_CLOSED, jaw - sim.VMAX * m.opt.timestep)
        d.ctrl[:sim.NJ] = hold
        d.ctrl[sim.JAW] = jaw
        mujoco.mj_step(m, d)
    return float(d.qpos[sim.JAW])


def _chain_run(seed, reset_mode, episodes, max_s=20.0, tau_h=0.17, hz=50):
    """`episodes` chained demonstrations, same operator and same scene, as run.run_arm
    chains them. -> [(success, reset_s, duration_s, phase)] per episode."""
    m, d = sim.build("capture_chain")
    st = sim.reset(m, d, seed, "capture_chain", reset_mode)
    op = SyntheticOperator(m, seed=seed, task="capture_chain", tau_h=tau_h,
                           reset_mode=reset_mode)
    n, sub = max(1, round(tau_h * hz)), round(1.0 / hz / m.opt.timestep)
    look = lambda: dict(q=list(d.qpos[:sim.NJ]) + [0.0], obj=list(sim.obj_pose(d, st)),
                        flags=(0x02 if st["grasped"] else 0))
    out = []
    for k in range(episodes):
        if k:                                      # sat.controller's chained carry-over
            st.update(success=False, done=False, t_success=None, in_region_since=None)
        t0, hist = d.time, [look()]
        while d.time - t0 < max_s and not st["done"]:
            sp = op.step(hist[max(0, len(hist) - n)], 1.0 / hz)
            for _ in range(sub):
                sim.step(m, d, sp, st, d.time)
            hist.append(look())
        out.append((st["success"] and st["done"],
                    (d.time - st["t_success"]) if st["t_success"] else 0.0,
                    d.time - t0, op.phase))
        op.restart(st["done"])
    return out


def test_chained_teleop_run_survives_a_jaw_that_stalls_on_the_box():
    """The H20 regression: a box PINCHED between the pads stops the jaw wherever its own
    width does, which can be above JAW_GRASP. The angle-only capture predicate then never
    fired on a grasp that had physically happened, the operator sat in `closing` for the
    rest of the episode, and because `capture_chain` never resets the scene every later
    demonstration inherited the same jammed jaw (30-seed teleop run at `zero`: 3/30, the
    losers all at `closing` with the jaw stalled at 0.068-0.083 rad)."""
    m, d = sim.build("capture_chain")
    ids = sim.ids(m)
    stall = _stall_the_jaw_on_the_box(m, d, ids)
    assert stall > sim.JAW_GRASP, stall            # the angle alone can never see this one
    st = dict(sim.reset(m, d, 0, "capture_chain"), grasped=False)
    _stall_the_jaw_on_the_box(m, d, st["ids"])     # reset() moved the box; re-stall it
    gp = d.site_xpos[st["ids"]["site"]]
    assert np.linalg.norm(d.qpos[st["ids"]["qadr"]:st["ids"]["qadr"] + 3] - gp) < sim.GRASP_TOL
    sim._capture(m, d, st, gp, 0.0)
    assert st["grasped"], f"jaw stalled ON the box at {stall:.3f} rad and was not a capture"

    eps = _chain_run(0, "teleop", 4)
    assert sum(ok for ok, *_ in eps) >= 3, eps
    for k, (ok, reset_s, _, _) in enumerate(eps):
        if k:                                      # H20: the chained reset is teleoperated
            assert reset_s > 0.0, (k, eps)
