"""MuJoCo scenes for the two testbed tasks of SYNTHESIS section 3, zero g.

`capture` (task 2): a free-floating box drifting at 2-5 cm/s and tumbling at up to 1 rad/s.
Grasp it inside a jaw-scale envelope and hold it in the target region. The operator only
ever sees where the box WAS, so the steady-state chase error is (box speed x loop delay);
at GRASP_TOL = 25 mm that error decides the episode, which is the whole point. Capture needs
the jaw to be physically shut on the box, not merely commanded shut (see JAW_GRASP).

`capture_chain` (H20): `capture` plus a dead-band tether on the box and two targets. The
demonstration ends with a re-release that seeds the next one (targets alternate A->B->A),
so there is no canonical reset to pay for; with `--reset teleop` the operator instead
carries the box back to the spawn zone and releases it there, and that wall time is
charged to the run. The tether's SPRING is slack (dead band) everywhere inside the working
volume; its damping is not, see `_tendon`.

`peg` (task 5): a 60 mm peg hanging from the jaw by its top with an unknown lateral grasp
offset, inserted into a hole in a fixture bolted to the cage floor, CLEAR = 6 mm per side.
Touching the fixture while the tip is below the fixture top jams the peg: it is left behind
in the world and the operator has to withdraw and come back for it.

Both scenes carry the cage of section 5 item 5: six static walls whose interior IS the
keep-out box, so end-effector escape and cage contact are both observable events.

# ponytail: grasping is kinematic (the object rides the grasp site inside a capture
# envelope) and the peg is held rigidly upright, so only XY alignment and depth decide the
# insertion. Real pad friction on a 16 mm box with a 3.5 N gripper is a tuning project of
# its own and is not what this program measures; contact physics still applies BEFORE
# capture and before insertion, which is where the latency failure mode lives.
# Upgrade path: equality weld at the pads, then a true friction grasp.
"""
import numpy as np
import mujoco
from robot_descriptions import so_arm100_mj_description as _d

NJ = 6                      # SO-100 joints: Rotation Pitch Elbow Wrist_Pitch Wrist_Roll Jaw
JAW = 5
JAW_OPEN, JAW_CLOSED = 1.2, 0.0
VMAX = 2.0                  # rad/s rated joint velocity [design choice], SYNTHESIS 5 item 4

# cage interior = keep-out box. Encloses the arm; the arm can reach x = +-0.42, so the
# side walls are a real limit and not decoration.
CAGE_LO = np.array([-0.32, -0.44, -0.04])
CAGE_HI = np.array([0.32, 0.22, 0.44])

# --- capture ---
GRASP_TOL = 0.025           # m, box centre to grasp site (jaw-scale capture envelope).
# Was 0.020; raised once capture started requiring the PHYSICAL jaw (below), which costs the
# 0.6 s the jaw needs to ramp shut. Measured zero-latency baseline over 30 seeds: 21/30 on
# the old command-only predicate, 16/30 with the physical jaw at 20 mm, 18/30 at >= 24 mm
# (it saturates there: the rest of the failures are the T16 reachability seeds, not the
# envelope). Nothing about the operator was touched; `close_at` (18 mm) is unchanged.
# Capture needs the PHYSICAL jaw closed, not the close COMMAND (audit T01): the jaw takes
# ~0.6 s to travel JAW_OPEN -> JAW_CLOSED under the 2 rad/s ramp, and a box that drifts out
# of the pads in that window was never grasped. JAW_GRASP is model-derived: it is the jaw
# angle at which the pad gap equals the box's diagonal (2*BOX*sqrt(2) = 22.6 mm), i.e. the
# box can no longer pass back out between the pads. tests/test_sim_operator.py re-derives it
# from the MJCF; the commanded JAW_CLOSED settles at a 17.8 mm gap, well inside it.
# The angle is necessary but NOT sufficient: a box pinched between the pads STOPS the jaw
# wherever its own projected width does, which for a tumbling 16 mm cube runs up to its
# space diagonal (27.7 mm) and so can stall the jaw ABOVE JAW_GRASP (measured: 0.077 rad
# with both pads bearing on the box). That is a real grasp the angle alone can never see,
# and in `capture_chain` it deadlocked the whole run, so a pinch counts too -- see
# `_capture`. Neither branch is satisfiable by the close COMMAND, which is T01's point.
JAW_GRASP = 0.062           # rad
TARGET_POS = np.array([0.16, -0.16, 0.22])
TARGET_R = 0.05
HOLD_S = 0.2                # must stay in the target region this long
BOX = 0.008                 # half-size
DRIFT = (0.020, 0.045)      # m/s, SYNTHESIS section 3 task 2 (2-5 cm/s)
TUMBLE = (0.3, 1.0)         # rad/s, task 2 (<= 1 rad/s)

# --- capture_chain (H20) ---
TARGET_B = np.array([-0.16, -0.30, 0.10])   # the other end of the A<->B alternation
SPAWN = np.array([0.0, -0.31, 0.14])        # canonical spawn zone centre = teleop reset goal
TETHER = np.array([0.0, -0.24, 0.16])       # anchor: A, B and SPAWN are all < SLACK from it
SLACK = 0.20                                # m of dead band: zero force inside the volume
PUSH = (0.020, 0.040)                       # m/s release push, SYNTHESIS 3 task 2 (2-5 cm/s)

# --- peg ---
PEG_H = 0.030               # half-length: a 60 mm peg
CLEAR = 0.006               # m of radial clearance per side
HOLE = np.array([0.15, -0.27, 0.0])     # hole axis (x, y); z is the cage floor
FIX_TOP = 0.07              # fixture top face, m
DEPTH = 0.025               # tip this far below FIX_TOP = inserted
APPROACH_Z = 0.145          # peg centre height for the align phase
INSERT_Z = FIX_TOP - DEPTH + PEG_H - 0.004   # peg centre height that clears DEPTH
GRIP_R = 0.012              # regrasp radius after a jam
OFFSET = 0.006              # m, unknown lateral grasp offset drawn U(-OFFSET, OFFSET)
GRIP = np.array([0.0, 0.0, PEG_H])   # peg centre -> the point the jaw holds (its top)


def _cage():
    t = 0.005
    c, h = (CAGE_LO + CAGE_HI) / 2, (CAGE_HI - CAGE_LO) / 2
    out = []
    for ax in range(3):
        s = h.copy()
        s[ax] = t
        for sgn in (-1, 1):
            p = c.copy()
            p[ax] = (CAGE_HI if sgn > 0 else CAGE_LO)[ax] + sgn * t
            out.append(f'<geom name="cagewall{ax}{sgn}" type="box" pos="{p[0]} {p[1]} {p[2]}" '
                       f'size="{s[0]} {s[1]} {s[2]}" rgba="0.4 0.5 0.6 0.10"/>')
    return "\n".join(out)


def _fixture():
    """Four blocks around a square hole of half-width BOX + CLEAR, standing on the floor."""
    w, t, hz = BOX + CLEAR, 0.012, (FIX_TOP - CAGE_LO[2]) / 2
    z = CAGE_LO[2] + hz
    out = []
    for ax in (0, 1):
        for sgn in (-1, 1):
            p, s = HOLE.copy(), [w + 2 * t, w + 2 * t, hz]
            p[2] = z
            p[ax] += sgn * (w + t)
            s[ax] = t
            out.append(f'<geom name="holewall{ax}{sgn}" type="box" pos="{p[0]} {p[1]} {p[2]}" '
                       f'size="{s[0]} {s[1]} {s[2]}" rgba="0.5 0.5 0.55 1"/>')
    return "\n".join(out)


def _tether():
    return (f'<site name="anchor" pos="{TETHER[0]} {TETHER[1]} {TETHER[2]}" size="0.004" '
            f'rgba="0.2 0.2 0.2 0.6"/>\n'
            f'<site name="targetB" pos="{TARGET_B[0]} {TARGET_B[1]} {TARGET_B[2]}" '
            f'size="{TARGET_R}" rgba="0.9 0.6 0.2 0.15"/>')


def _tendon():
    """Dead-band spatial tendon, H20's numbers verbatim (stiffness 0.005, damping 0.01).

    `springlength="0 SLACK"` is a dead band on the SPRING only: zero elastic force until the
    thread is straight. MuJoCo tendon damping has no dead band, so the thread also applies
    -0.01 * (radial speed) while slack. Measured: a box released at 4.1 cm/s is down to
    2.5 cm/s after 6 s (tau = m/c = 5 s), i.e. the "free 6-DoF body" subset (phenomenon D,
    unique_data_study 2 D) is NOT force-free even when `taut_frac` reads 0.
    # ponytail: kept at the specified 0.01 and reported, not silently retuned. `damping="0"`
    # makes the slack thread exactly force-free at the cost of a bouncier return.
    Second measured caveat: at stiffness 0.005 N/m a 3 cm/s box carries 2.3e-5 J, which the
    spring only absorbs after ~9.5 cm of stretch, so this thread bounds an escape softly
    rather than "returning it at its exit speed"."""
    return (f'\n<tendon><spatial name="tether" limited="false" stiffness="0.005" '
            f'damping="0.01" springlength="0 {SLACK}" width="0.0008" rgba="0.3 0.3 0.3 0.5">'
            f'<site site="anchor"/><site site="objsite"/></spatial></tendon>')


def dls(m, d, site, q, dx, lam=0.05):
    """One damped-least-squares step: the joint delta that moves `site` by `dx` at `q`.
    `d` is scratch MjData and is left forwarded at `q`. Damping bounds the step at wrist
    singularities."""
    d.qpos[:NJ] = q
    mujoco.mj_forward(m, d)
    jac = np.zeros((3, m.nv))
    mujoco.mj_jacSite(m, d, jac, None, site)
    j = jac[:, :NJ]
    return j.T @ np.linalg.solve(j @ j.T + lam ** 2 * np.eye(3), dx)


def _xml(task):
    src = open(_d.MJCF_PATH).read()
    site = ('<site name="grasp" pos="0 -0.085 0" size="0.004" rgba="0 1 0 0.4"/>\n'
            '<body name="Moving_Jaw"')
    sz = f"{BOX} {BOX} {PEG_H}" if task == "peg" else f"{BOX} {BOX} {BOX}"
    world = f'''
    <body name="obj" pos="0 -0.30 0.15">
      <freejoint name="obj_free"/>
      <geom name="obj" type="box" size="{sz}" mass="0.05" rgba="0.9 0.4 0.1 1"
            solimp="0.9 0.95 0.005" solref="0.02 1"/>
      <site name="objsite" size="0.002" rgba="0 0 0 0"/>
    </body>
    {_cage()}
    {_fixture() if task == "peg" else ""}
    <site name="target" pos="{TARGET_POS[0]} {TARGET_POS[1]} {TARGET_POS[2]}"
          size="{TARGET_R}" rgba="0.2 0.6 1 0.15"/>
    {_tether() if task == "capture_chain" else ""}
    </worldbody>{_tendon() if task == "capture_chain" else ""}'''
    return (src.replace('meshdir="assets/"', f'meshdir="{_d.PACKAGE_PATH}/assets/"')
               .replace('<option ', '<option gravity="0 0 0" ')
               .replace('<body name="Moving_Jaw"', site, 1)
               .replace('</worldbody>', world, 1))


def build(task="capture"):
    m = mujoco.MjModel.from_xml_string(_xml(task))
    return m, mujoco.MjData(m)


def ids(m):
    g = lambda t, n: mujoco.mj_name2id(m, t, n)
    names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(m.ngeom)]
    return dict(site=g(mujoco.mjtObj.mjOBJ_SITE, "grasp"),
                obj=g(mujoco.mjtObj.mjOBJ_BODY, "obj"),
                objg=g(mujoco.mjtObj.mjOBJ_GEOM, "obj"),
                cage={i for i, n in enumerate(names) if n.startswith("cagewall")},
                fix={i for i, n in enumerate(names) if n.startswith("holewall")},
                padm={i for i, n in enumerate(names) if n.startswith("moving_jaw_pad")},
                padf={i for i, n in enumerate(names) if n.startswith("fixed_jaw_pad")},
                qadr=m.jnt_qposadr[g(mujoco.mjtObj.mjOBJ_JOINT, "obj_free")],
                vadr=m.jnt_dofadr[g(mujoco.mjtObj.mjOBJ_JOINT, "obj_free")])


def reset(m, d, seed, task="capture", reset_mode="free"):
    """Fixed-seed reset -> state dict carrying the task and its safety-event counters.

    `capture_chain` never calls this between chained demonstrations: the state dict (and
    with it the box, the arm and the alternating target) is carried over, which is the
    whole hypothesis. `reset_mode` only decides whether a release swaps the target
    (`free`, chained) or leaves it at A (`teleop`, canonical)."""
    rng = np.random.default_rng(seed)
    mujoco.mj_resetDataKeyframe(m, d, 0)          # "home"
    i = ids(m)
    a, v = i["qadr"], i["vadr"]
    d.qpos[a + 3:a + 7] = [1, 0, 0, 0]
    st = dict(ids=i, task=task, grasped=False, off=np.zeros(3), in_region_since=None,
              success=False, jammed=False, jams=0, keepout=0, cage_hits=0, knockaway=0,
              t_out=None, t_hit=None, t_knock=None, v0=0.0,
              target=TARGET_POS.copy(), rng=rng, reset=reset_mode, done=False, t_success=None)
    if task == "peg":
        st["pin"], st["left"] = None, False
        mujoco.mj_forward(m, d)
        st["grasped"] = True
        st["off"] = np.array([rng.uniform(-OFFSET, OFFSET),
                              rng.uniform(-OFFSET, OFFSET), 0.0]) - GRIP
        d.qpos[a:a + 3] = d.site_xpos[i["site"]] + st["off"]
        mujoco.mj_forward(m, d)
        return st
    for _ in range(200):                          # spawn clear of the arm, within reach
        d.qpos[a:a + 3] = [rng.uniform(-.10, .10), rng.uniform(-.34, -.28),
                           rng.uniform(.08, .20)]
        mujoco.mj_forward(m, d)
        if d.ncon == 0:
            break
    else:
        raise RuntimeError("no free spawn")
    u = rng.normal(size=3)
    d.qvel[v:v + 3] = u / np.linalg.norm(u) * rng.uniform(*DRIFT)
    w = rng.normal(size=3)
    d.qvel[v + 3:v + 6] = w / np.linalg.norm(w) * rng.uniform(*TUMBLE)
    st["v0"] = float(np.linalg.norm(d.qvel[v:v + 3]))          # the drift it was born with
    mujoco.mj_forward(m, d)
    return st


def obj_pose(d, st):
    a = st["ids"]["qadr"]
    return np.array(d.qpos[a:a + 7])


def _touching(d, gset, other=None, but=None):
    """Is any geom in `gset` in contact? `other` restricts, `but` excludes, the partner."""
    for k in range(d.ncon):
        g1, g2 = d.contact.geom1[k], d.contact.geom2[k]
        if not (g1 in gset or g2 in gset):
            continue
        partner = g2 if g1 in gset else g1
        if (other is None or partner == other) and partner != but:
            return True
    return False


EVENT_GAP = 0.25    # s of clean time before a renewed contact counts as a NEW event


def _edge(st, key, on, t):
    """Count one event per contiguous spell of `on`. Without the debounce a single sustained
    press on a cage wall chatters into hundreds of rising edges."""
    if on:
        last = st["t_" + key]
        if last is None or t - last > EVENT_GAP:
            st[{"out": "keepout", "hit": "cage_hits", "knock": "knockaway"}[key]] += 1
        st["t_" + key] = t
    return on


def step(m, d, ctrl, st, t):
    """One sim step with the current joint setpoint. Handles the task and safety events."""
    d.ctrl[:NJ] = np.clip(ctrl[:NJ], m.jnt_range[:NJ, 0], m.jnt_range[:NJ, 1])
    mujoco.mj_step(m, d)
    i, a, v = st["ids"], st["ids"]["qadr"], st["ids"]["vadr"]
    gp = d.site_xpos[i["site"]]
    _edge(st, "out", bool(np.any(gp < CAGE_LO) or np.any(gp > CAGE_HI)), t)
    # the free object bouncing off a wall is not an unsafe MOTION event; the arm is.
    # `cage_hits` is OPERATOR/TASK-caused, not link-caused: the box spawns 10-16 cm from the
    # -y wall and drifts, so the chase runs the arm into the wall at ZERO latency too (audit
    # T07: 12/30 zero-latency episodes). It is reported as its own column, never summed into
    # the link-caused counters (move_in_hold, vel_over, keepout).
    _edge(st, "hit", _touching(d, i["cage"], but=i["objg"]), t)
    (_peg if st["task"] == "peg" else _capture)(m, d, st, gp, t)
    # chained: the demonstration is over at the RE-release, not at the grasp, because the
    # release is what seeds the next one and it is teleoperated like everything else
    return st["done"] if st["task"] == "capture_chain" else st["success"]


def _capture(m, d, st, gp, t):
    i, a, v = st["ids"], st["ids"]["qadr"], st["ids"]["vadr"]
    closing = d.ctrl[JAW] < 0.5 * JAW_OPEN
    # the jaw itself, not the command: it either travelled to JAW_GRASP or it stopped early
    # because the box is pinched between the two pads. Both need the ~0.6 s of real travel
    # (the pads are 64 mm apart the moment `closing` turns true, so no 16-28 mm box can be
    # touching both of them yet); only the angle alone was unsatisfiable on a grasp that
    # physically happened, which left the operator stuck in `closing` for the rest of the
    # run -- terminal in `capture_chain`, where nothing resets the scene.
    shut = closing and (d.qpos[JAW] < JAW_GRASP or
                        (_touching(d, i["padm"], other=i["objg"]) and
                         _touching(d, i["padf"], other=i["objg"])))
    if st["grasped"]:
        if not closing:
            st["grasped"] = False
            if st["task"] == "capture_chain":
                _release(m, d, st)
        else:                                      # carry: box rides the grasp site
            st["off"] = st["off"] * 0.98
            d.qpos[a:a + 3] = gp + st["off"]
            d.qvel[v:v + 6] = 0
            mujoco.mj_forward(m, d)
    elif shut and np.linalg.norm(d.qpos[a:a + 3] - gp) < GRASP_TOL:
        st["grasped"], st["off"] = True, d.qpos[a:a + 3] - gp   # reel the offset in
    # H14 mechanism check: the arm swept through the box and sent it off. "Faster than
    # 3 cm/s while ungrasped" alone would fire on an untouched box in half the episodes,
    # because the spawn drift itself is 2-4.5 cm/s; a free body in mu-g only changes speed
    # when something hits it, so require BOTH fast and disturbed.
    _edge(st, "knock", not st["grasped"] and
          np.linalg.norm(d.qvel[v:v + 3]) > max(0.03, st["v0"] + 0.005), t)
    inside = st["grasped"] and np.linalg.norm(d.qpos[a:a + 3] - st["target"]) < TARGET_R
    if not inside:
        st["in_region_since"] = None
    elif st["in_region_since"] is None:
        st["in_region_since"] = t
    elif t - st["in_region_since"] >= HOLD_S:
        st["success"] = True
        if st["t_success"] is None:
            st["t_success"] = t


def _release(m, d, st):
    """H20: the terminal act of one demonstration is the initial condition of the next.

    The box leaves with the velocity the arm had, plus a seeded 2-4 cm/s push and a small
    spin, and the target swaps. Nothing teleports: the box keeps the pose it is in."""
    i, v = st["ids"], st["ids"]["vadr"]
    vel = np.zeros(6)
    mujoco.mj_objectVelocity(m, d, mujoco.mjtObj.mjOBJ_SITE, i["site"], vel, 0)
    d.qvel[v:v + 3] = vel[3:]
    if not st["success"]:               # dropped it, not released it: no push, no credit
        return mujoco.mj_forward(m, d)
    u, w = st["rng"].normal(size=3), st["rng"].normal(size=3)
    d.qvel[v:v + 3] += u / np.linalg.norm(u) * st["rng"].uniform(*PUSH)
    d.qvel[v + 3:v + 6] = w / np.linalg.norm(w) * st["rng"].uniform(*TUMBLE)
    if st["reset"] == "free":           # chained: alternate A <-> B, no canonical state
        st["target"] = (TARGET_B if np.allclose(st["target"], TARGET_POS)
                        else TARGET_POS.copy())
    st["done"] = True
    mujoco.mj_forward(m, d)


def _peg(m, d, st, gp, t):
    """A peg whose lateral error exceeds CLEAR at the mouth binds: it stops where it is
    while the gripper keeps going, which is what the operator sees (the peg no longer
    tracks the jaw). Recovery is to withdraw and come back to it."""
    i, a, v = st["ids"], st["ids"]["qadr"], st["ids"]["vadr"]
    touch = _touching(d, i["fix"], i["objg"])
    tip = d.qpos[a + 2] - PEG_H
    if st["jammed"]:
        far = np.linalg.norm(st["pin"] + GRIP - gp) > GRIP_R
        st["left"] = st["left"] or far
        if st["left"] and not far:                              # withdrew AND came back
            st["jammed"], st["off"] = False, st["pin"] - gp
    elif touch and tip < FIX_TOP:                               # wedged in the mouth
        st["jammed"], st["jams"], st["left"] = True, st["jams"] + 1, False
        st["pin"] = d.qpos[a:a + 3].copy()
    d.qpos[a:a + 3] = st["pin"] if st["jammed"] else gp + st["off"]
    d.qpos[a + 3:a + 7] = [1, 0, 0, 0]
    d.qvel[v:v + 6] = 0
    mujoco.mj_forward(m, d)
    inside = np.linalg.norm((d.qpos[a:a + 2] - HOLE[:2])) < BOX + CLEAR
    tip = d.qpos[a + 2] - PEG_H
    touch = _touching(d, i["fix"], i["objg"])
    st["success"] = st["success"] or (inside and not touch and tip <= FIX_TOP - DEPTH)
