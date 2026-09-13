"""Strategy hook: the one abstraction the runner knows about.

A hypothesis subclasses Strategy and is passed to run.py; neither the ground loop, the
sat controller nor the link changes. Two seams:

  ground_step(tel, target) -> setpoint    what the ground actually puts on the wire,
                                          given the newest (delayed) telemetry and the
                                          operator's intent.
  sat_step(buf, now)       -> setpoint    what the satellite commands right now, given
                                          its buffer of arrived setpoints.

`buf` is a list of (t_arrival_monotonic_s, seq, setpoints[7]), oldest first.
"""


class Strategy:
    interp_s = 0.02     # playout lag: one command interval at 50 Hz
    timeout_s = 0.5     # no fresh command for this long -> the controller raises safety_hold

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.last = None

    def ground_step(self, tel, target):
        return target

    def sat_step(self, buf, now):
        raise NotImplementedError
