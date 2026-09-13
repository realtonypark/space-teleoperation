"""MuJoCo scene for task v0 "capture": SO-100 arm, zero g, one free-floating box.

The Menagerie `so_arm100.xml` text is patched (string surgery, per spec) to add:
zero gravity, a `grasp` site between the jaw pads, a free-floating box `obj`, and a
visual target site. Grasping is kinematic: when the jaw is commanded closed and the box
centre is inside `GRASP_TOL` of the grasp site, the box is carried by the site until the
jaw opens again.

# ponytail: kinematic attach inside a 50 mm capture envelope instead of a friction grasp,
# i.e. a soft-capture/snare proxy rather than the SO-100's 20 mm jaw. Real pad friction on
# a 16 mm box with a 3.5 N gripper is a tuning project of its own and is not what this
# program measures; contact physics still applies *before* capture, so a late, overshooting
# operator still knocks the target away, which is the latency failure mode we care about.
# Upgrade path: equality weld at the pads, then a true friction grasp.
"""
import numpy as np
import mujoco
from robot_descriptions import so_arm100_mj_description as _d

NJ = 6                      # SO-100 joints: Rotation Pitch Elbow Wrist_Pitch Wrist_Roll Jaw
JAW = 5
JAW_OPEN, JAW_CLOSED = 1.2, 0.0
GRASP_TOL = 0.050           # m, box centre to grasp site (soft capture envelope)
TARGET_POS = np.array([0.16, -0.16, 0.22])
TARGET_R = 0.05
HOLD_S = 0.2                # must stay in the target region this long
BOX = 0.008                 # half-size


def _xml():
    src = open(_d.MJCF_PATH).read()
    site = ('<site name="grasp" pos="0 -0.085 0" size="0.004" rgba="0 1 0 0.4"/>\n'
            '<body name="Moving_Jaw"')
    world = f'''
    <body name="obj" pos="0 -0.30 0.15">
      <freejoint name="obj_free"/>
      <geom name="obj" type="box" size="{BOX} {BOX} {BOX}" mass="0.05" rgba="0.9 0.4 0.1 1"
            solimp="0.9 0.95 0.005" solref="0.02 1"/>
    </body>
    <site name="target" pos="{TARGET_POS[0]} {TARGET_POS[1]} {TARGET_POS[2]}"
          size="{TARGET_R}" rgba="0.2 0.6 1 0.15"/>
    </worldbody>'''
    return (src.replace('meshdir="assets/"', f'meshdir="{_d.PACKAGE_PATH}/assets/"')
               .replace('<option ', '<option gravity="0 0 0" ')
               .replace('<body name="Moving_Jaw"', site, 1)
               .replace('</worldbody>', world, 1))


def build():
    m = mujoco.MjModel.from_xml_string(_xml())
    return m, mujoco.MjData(m)


def ids(m):
    g = lambda t, n: mujoco.mj_name2id(m, t, n)
    return dict(site=g(mujoco.mjtObj.mjOBJ_SITE, "grasp"),
                obj=g(mujoco.mjtObj.mjOBJ_BODY, "obj"),
                qadr=m.jnt_qposadr[g(mujoco.mjtObj.mjOBJ_JOINT, "obj_free")],
                vadr=m.jnt_dofadr[g(mujoco.mjtObj.mjOBJ_JOINT, "obj_free")])


def reset(m, d, seed):
    """Fixed-seed reset -> state dict. Box starts inside reach with a small drift/tumble."""
    rng = np.random.default_rng(seed)
    mujoco.mj_resetDataKeyframe(m, d, 0)          # "home"
    i = ids(m)
    d.qpos[i["qadr"] + 3:i["qadr"] + 7] = [1, 0, 0, 0]
    for _ in range(100):                          # spawn clear of the arm, in front of the jaw
        d.qpos[i["qadr"]:i["qadr"] + 3] = [rng.uniform(-.10, .10), rng.uniform(-.34, -.28),
                                           rng.uniform(.06, .20)]
        mujoco.mj_forward(m, d)
        if d.ncon == 0:
            break
    else:
        raise RuntimeError("no free spawn")
    d.qvel[i["vadr"]:i["vadr"] + 3] = rng.normal(0, .008, 3)      # ~1 cm/s drift
    d.qvel[i["vadr"] + 3:i["vadr"] + 6] = rng.normal(0, .15, 3)   # slow tumble
    mujoco.mj_forward(m, d)
    return dict(ids=i, grasped=False, off=np.zeros(3), in_region_since=None, success=False)


def obj_pose(d, st):
    a = st["ids"]["qadr"]
    return np.array(d.qpos[a:a + 7])


def step(m, d, ctrl, st, t):
    """One sim step with the current joint setpoint. Handles capture and the success test."""
    d.ctrl[:NJ] = np.clip(ctrl[:NJ], m.jnt_range[:NJ, 0], m.jnt_range[:NJ, 1])
    mujoco.mj_step(m, d)
    i, a, v = st["ids"], st["ids"]["qadr"], st["ids"]["vadr"]
    gp = d.site_xpos[i["site"]]
    closing = d.ctrl[JAW] < 0.5 * JAW_OPEN
    if st["grasped"]:
        if not closing:
            st["grasped"] = False
        else:                                      # carry: box rides the grasp site
            st["off"] = st["off"] * 0.98
            d.qpos[a:a + 3] = gp + st["off"]
            d.qvel[v:v + 6] = 0
            mujoco.mj_forward(m, d)
    elif closing and np.linalg.norm(d.qpos[a:a + 3] - gp) < GRASP_TOL:
        st["grasped"], st["off"] = True, d.qpos[a:a + 3] - gp   # reel the offset in, no teleport
    inside = st["grasped"] and np.linalg.norm(d.qpos[a:a + 3] - TARGET_POS) < TARGET_R
    if not inside:
        st["in_region_since"] = None
    elif st["in_region_since"] is None:
        st["in_region_since"] = t
    elif t - st["in_region_since"] >= HOLD_S:
        st["success"] = True
    return st["success"]
