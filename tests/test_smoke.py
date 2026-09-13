"""Phase 0 smoke: MuJoCo headless + SO-100 arm loads with gravity 0, sgp4 propagates."""
import numpy as np


def test_mujoco_zero_g_arm():
    import mujoco
    from robot_descriptions.loaders.mujoco import load_robot_description

    model = load_robot_description("so_arm100_mj_description")
    model.opt.gravity[:] = 0
    data = mujoco.MjData(model)
    for _ in range(100):
        mujoco.mj_step(model, data)
    assert model.nu >= 6, model.nu
    assert np.all(np.isfinite(data.qpos))
    r = mujoco.Renderer(model, 240, 320)
    r.update_scene(data)
    assert r.render().shape == (240, 320, 3)


def test_sgp4_iss():
    from sgp4.api import Satrec, jday
    l1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000"
    l2 = "2 25544  51.6400 208.9163 0006703  69.9862  25.2906 15.49560000000000"
    s = Satrec.twoline2rv(l1, l2)
    e, r, v = s.sgp4(*jday(2024, 1, 1, 12, 0, 0))
    assert e == 0 and 6600 < np.linalg.norm(r) < 7000
