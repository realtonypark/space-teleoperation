"""Self-check: the capture task is solvable at zero latency, and reset is seed-stable."""
import numpy as np

from spaceteleop import sim
from spaceteleop.ground.operators import SyntheticOperator


def _solve(seed, tau_h=0.0, max_s=25.0):
    """Operator and sim coupled directly, no link: the zero-latency ceiling."""
    m, d = sim.build()
    st = sim.reset(m, d, seed)
    op = SyntheticOperator(m, seed=seed, tau_h=tau_h)
    tel = dict(q=list(d.qpos[:sim.NJ]) + [0.0], obj=list(sim.obj_pose(d, st)), flags=0)
    t = 0.0
    while t < max_s:
        sp = op.step(tel, 0.02)
        for _ in range(10):                       # 50 Hz operator, 500 Hz sim
            sim.step(m, d, sp, st, t)
            t += m.opt.timestep
        tel = dict(q=list(d.qpos[:sim.NJ]) + [0.0], obj=list(sim.obj_pose(d, st)),
                   flags=(0x02 if st["grasped"] else 0))
        if st["success"]:
            return True, t
    return False, t


def test_capture_solvable_at_zero_latency():
    res = [_solve(s) for s in range(4)]
    assert all(ok for ok, _ in res), res
    assert all(t < 20.0 for _, t in res), res


def test_reset_is_seeded_and_clear_of_the_arm():
    m, d = sim.build()
    a = sim.obj_pose(d, sim.reset(m, d, 3)).copy()
    b = sim.obj_pose(d, sim.reset(m, d, 3))
    assert np.allclose(a, b)
    assert not np.allclose(a, sim.obj_pose(d, sim.reset(m, d, 4)))
    assert d.ncon == 0                            # never spawns inside the arm
