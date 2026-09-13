"""Self-check: both tasks are solvable at zero latency, degrade with it, and seeds are stable.

Runs the operator against the sim through a pure transport delay instead of sockets, so a
whole latency sweep costs a few seconds of wall clock instead of minutes.
"""
import numpy as np

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
    """The discriminator the whole testbed exists for: same operator, worse link."""
    for task in ("capture", "peg"):
        lo = sum(solve(task, s)[0] for s in range(8))
        hi = sum(solve(task, s, lag_s=0.5)[0] for s in range(8))
        assert hi <= lo - 2, (task, lo, hi)      # >= 25 points of success lost at 1 s RTT


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
