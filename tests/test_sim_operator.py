"""Self-check: both tasks are solvable at zero latency, degrade with it, and seeds are stable.

Runs the operator against the sim through a pure transport delay instead of sockets, so a
whole latency sweep costs a few seconds of wall clock instead of minutes.
"""
import numpy as np
import mujoco
import pytest

from spaceteleop import sim
from spaceteleop.ground.operators import SyntheticOperator

HZ = 50


def solve(task, seed, lag_s=0.0, max_s=20.0, tau_h=0.17):
    m, d = sim.build(task)
    st = sim.reset(m, d, seed, task)
    op = SyntheticOperator(m, seed=seed, task=task, tau_h=tau_h)
    n = max(1, round((lag_s + tau_h) * HZ))
    sub = round(1.0 / HZ / m.opt.timestep)
    look = lambda: dict(q=list(d.qpos[:sim.NJ]) + [0.0], obj=list(sim.obj_pose(d, st)),
                        flags=(0x02 if st["grasped"] else 0))
    t, hist = 0.0, [look()]
    while t < max_s:
        sp = op.step(hist[max(0, len(hist) - n)], 1.0 / HZ)
        for _ in range(sub):
            sim.step(m, d, sp, st, t)
            t += m.opt.timestep
        hist.append(look())
        if st["success"]:
            break
    return st["success"], t, st


def test_both_tasks_solvable_at_zero_latency():
    for task, floor in (("capture", 0.75), ("peg", 0.75)):
        ok = [solve(task, s)[0] for s in range(8)]
        assert sum(ok) / len(ok) >= floor, (task, ok)


def test_success_degrades_with_latency():
    """The discriminator the whole testbed exists for: same operator, worse link.

    1.0 s, not 0.5 s: over 30 seeds `capture` reads 18/20/15/18/4 at 0/0.1/0.25/0.5/1.0 s,
    i.e. flat to noise until half a second and only then falling off (the same shape as
    before capture required the physical jaw, audit T01: 21/22/16/18/3). Eight seeds at
    0.5 s cannot see that; 1.0 s is where the operator's chase genuinely loses the box."""
    for task in ("capture", "peg"):
        lo = sum(solve(task, s)[0] for s in range(8))
        hi = sum(solve(task, s, lag_s=1.0)[0] for s in range(8))
        assert hi <= lo - 2, (task, lo, hi)      # >= 25 points of success lost


def _pad_gap(m, d, q):
    """Distance between the two jaw pads at jaw angle `q`, straight out of the MJCF."""
    import mujoco
    gid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n)
    d.qpos[sim.JAW] = q
    mujoco.mj_forward(m, d)
    return float(np.linalg.norm(d.geom_xpos[gid("moving_jaw_pad_1")]
                                - d.geom_xpos[gid("fixed_jaw_pad_1")]))


def test_jaw_grasp_threshold_is_the_models_own_geometry():
    """T01: JAW_GRASP is where the pad gap equals the box diagonal, i.e. where the box can
    no longer pass back out between the pads. Re-derived here, not trusted as a constant."""
    m, d = sim.build()
    diag = 2 * sim.BOX * np.sqrt(2)
    assert _pad_gap(m, d, sim.JAW_GRASP) == pytest.approx(diag, abs=2e-4)
    assert _pad_gap(m, d, sim.JAW_GRASP + 0.05) > diag        # monotone: wider above
    assert _pad_gap(m, d, sim.JAW_CLOSED) < diag              # the commanded close is inside


def test_capture_needs_the_physical_jaw_not_the_close_command():
    """T01, the CRITICAL one: `grasped` used to be true on the first step of a close
    command, with the jaw wide open and the box merely within 20 mm. The jaw needs ~0.6 s
    to ramp shut, which is 12-27 mm of box drift, and that is the whole failure mode."""
    m, d = sim.build()
    st = sim.reset(m, d, 0)
    a, i = st["ids"]["qadr"], st["ids"]
    mujoco.mj_forward(m, d)
    d.qpos[sim.JAW] = sim.JAW_OPEN                            # jaw physically wide open
    d.qpos[a:a + 3] = d.site_xpos[i["site"]] + [0.0, 0.0, 0.010]   # box 10 mm from the site
    d.qvel[st["ids"]["vadr"]:st["ids"]["vadr"] + 6] = 0
    mujoco.mj_forward(m, d)
    ctrl = list(d.qpos[:sim.NJ]) + [0.0]
    ctrl[sim.JAW] = sim.JAW_CLOSED                            # commanded shut, not shut
    sim._capture(m, d, st, d.site_xpos[i["site"]], 0.0)
    assert not st["grasped"], "close COMMAND alone captured"

    d.qpos[sim.JAW] = sim.JAW_GRASP - 0.001                   # now the jaw really is shut
    d.ctrl[sim.JAW] = sim.JAW_CLOSED
    mujoco.mj_forward(m, d)
    sim._capture(m, d, st, d.site_xpos[i["site"]], 0.0)
    assert st["grasped"]

    st2 = sim.reset(m, d, 0)                                  # shut, but the box is gone
    d.qpos[sim.JAW] = sim.JAW_GRASP - 0.001
    d.ctrl[sim.JAW] = sim.JAW_CLOSED
    d.qpos[a:a + 3] = d.site_xpos[i["site"]] + [0.0, 0.0, sim.GRASP_TOL + 0.005]
    mujoco.mj_forward(m, d)
    sim._capture(m, d, st2, d.site_xpos[i["site"]], 0.0)
    assert not st2["grasped"]


def test_reset_is_seeded_and_clear_of_the_arm():
    m, d = sim.build()
    a = sim.obj_pose(d, sim.reset(m, d, 3)).copy()
    b = sim.obj_pose(d, sim.reset(m, d, 3))
    assert np.allclose(a, b)
    assert not np.allclose(a, sim.obj_pose(d, sim.reset(m, d, 4)))
    assert d.ncon == 0                            # never spawns inside the arm
    v = d.qvel[sim.ids(m)["vadr"]:sim.ids(m)["vadr"] + 3]
    assert sim.DRIFT[0] <= np.linalg.norm(v) <= sim.DRIFT[1]    # SYNTHESIS 3: 2-5 cm/s


def test_keepout_and_cage_events_are_recorded():
    """Both safety detectors fire, and the free object bouncing off a wall does not count
    (it is not an unsafe MOTION). The end effector can only leave the keep-out box if it
    is put there: in the built scene the cage wall physically stops it first, which is why
    `keepout` reads 0 in every run and `cage` does not."""
    m, d = sim.build()
    st = sim.reset(m, d, 0)
    reach = [0.0, -2.6, 0.6, 0.9, 0.0, sim.JAW_OPEN, 0.0]     # press into the front wall
    for k in range(3000):
        sim.step(m, d, reach, st, k * m.opt.timestep)
    assert st["cage_hits"] >= 1 and st["keepout"] == 0, st

    st = sim.reset(m, d, 0)
    d.qpos[:6] = [-0.25, 0.172, 1.507, 0.149, 2.442, 0.0]     # below the cage floor
    sim.step(m, d, list(d.qpos[:6]) + [0.0], st, 0.0)
    assert st["keepout"] == 1, st

    st2 = sim.reset(m, d, 0)
    for k in range(3000):                                     # arm parked, box drifts
        sim.step(m, d, list(d.ctrl[:6]) + [0.0], st2, k * m.opt.timestep)
    assert st2["cage_hits"] == 0 and st2["keepout"] == 0, st2
