"""Strategy hook: the one abstraction the runner knows about.

A hypothesis subclasses Strategy and is passed to run.py; neither the ground loop, the
sat controller nor the link changes. Two seams:

  ground_step(tel, target) -> setpoint    what the ground actually puts on the wire,
                                          given the newest (delayed) telemetry and the
                                          operator's intent.
  sat_step(buf, now)       -> setpoint    what the satellite commands right now, given
                                          its buffer of arrived setpoints.

`buf` is a list of (t_arrival_monotonic_s, seq, setpoints[7]), oldest first and strictly
increasing in seq: the controller drops any command older than the newest one received, so
a jitter-reordered straggler can never be played after a newer setpoint.

Defaults are SYNTHESIS section 5 (c): 30 ms playout, hold at 300 ms, retract at 10 s,
2 rad/s rated joint velocity. The controller fills in `reset_pose` and `qlim` from the model.
"""


class Strategy:
    interp_s = 0.030    # section 5 item 1: fixed playout delay
    timeout_s = 0.300   # section 5 item 2: no command newer than this -> hold
    retract_s = 10.0    # section 5 item 3: silence this long -> retract to the reset pose
    vmax = 2.0          # section 5 item 4: rated joint velocity, rad/s [design choice]

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.last = self.reset_pose = self.qlim = None
        self.held = self.retracting = False
        self.t_prev = None
        self.ev = dict(hold=0, retract=0, move_in_hold=0, ramp_clip=0, pos_clamp=0)

    def ground_step(self, tel, target):
        return target

    def sat_step(self, buf, now):
        raise NotImplementedError
