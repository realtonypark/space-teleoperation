"""Episode metrics: throughput, link, smoothness and the SYNTHESIS section 6 safety counts.

demos_per_hour follows the spec: 3600 / mean wall time of the SUCCESSFUL episodes. It
therefore ignores the wall time burned by failures; read it together with success_rate.
demos_per_hour_gross (data_pipeline 3.2, the metric H20 moves) is 3600 * successes over
the wall time of EVERY episode, failures and the teleoperated reset included, because a
data campaign pays for those too. On `capture_chain` the reset is inside the episode: the
demonstration ends at the re-release, not at the grasp.

Smoothness is reported, never gated (section 6): robomimic showed operators who both hit
high success rates produced very different policies, and SAL/LDLJ are the two measures
that separate them. SAL, LDLJ and `stall_frac` are computed on the SATELLITE's own
applied-setpoint log (the `_sat.npz` sidecar, one row per ~1.3 ms control cycle), resampled
to a uniform SMOOTH_HZ grid -- NOT on `observation.state`, which is a 50 Hz sample-and-hold
of 30 Hz telemetry and repeats 40-47 % of consecutive rows (audit T05: that artefact alone
moved stall_frac 0.24 -> 0.51 and LDLJ -5.2 -> -14.5 on a synthetic minimum-jerk move). The
sidecar is cut at the episode's done instant, so the satellite's post-episode linger is not
in these numbers either.
  SAL  spectral arc length of the speed profile, Balasubramanian et al. 2015. Less
       negative = smoother. Dimensionless, amplitude-normalised, so it compares runs of
       different duration.
  LDLJ log dimensionless jerk. Also less negative = smoother.
`stall_frac` is the fraction of frames with speed under STALL: the move-and-wait signature.

Unsafe motion (section 6) is three LINK-caused counts, all of which must be zero for a
profile to pass:
  move_in_hold  the commanded setpoint changed while in hold
  vel_over      an emitted joint velocity above the clamp (measured on the satellite's own
                applied-setpoint log, not asserted from the ramp limiter)
  keepout       the end effector left the keep-out box = the cage interior
`cage` (the arm touched the cage) is its OWN column and is deliberately not summed into
`unsafe`: it is operator/task-caused, not link-caused. It fires in 12/30 episodes at ZERO
latency, because the box spawns 10-16 cm from the -y wall and the operator's chase runs the
arm into it (audit T07), so folding it in made the section 6 gate fail on every profile for
every arm and discriminated nothing.

`stalls` / `max_dt_s` are the audit-T06 contamination flags: satellite control cycles whose
dt exceeded STALL_DT, i.e. CPU contention, not the link. After such a cycle the buffered
commands drain in one burst and the sim is stepped 1-2 s at once against one setpoint, so a
cell with stalls > 0 measures neither its profile nor its strategy. Non-zero means re-run
that cell with fewer concurrent jobs.

`ramp_clip`, `pos_clamp`, `hold`, `retract`, `jams` and `stale` are diagnostics, not
violations. `cmd_loss` is loss as the SETPOINT BUFFER sees it: a packet the link delivered
but whose sequence was older than one already received counts as lost, because the buffer
drops it. `stale` is how many of those there were; link-level loss is in Link.stats().
"""
import numpy as np

STALL = 0.05        # rad/s of joint-space speed below which the arm is "waiting"
STALL_DT = 0.2      # s: a satellite control cycle longer than this is a load stall (T06)
SMOOTH_HZ = 50.0    # uniform grid the applied-setpoint log is resampled onto for SAL/LDLJ
SAFE = ("move_in_hold", "vel_over", "keepout")      # link-caused; `cage` is not (T07)


def percentile(a, p):
    return float(np.percentile(a, p)) if len(a) else float("nan")


def applied_speed(sat, hz=SMOOTH_HZ):
    """Joint-space speed of the satellite's APPLIED setpoint on a uniform 1/hz grid (T05).

    The control loop runs at ~1.3 ms with a variable period, so the log is linearly
    resampled before differencing: SAL and LDLJ both assume a uniform sample rate, and one
    stalled cycle would otherwise read as a single enormous jerk."""
    t = np.asarray(sat["t_ns"], float) / 1e9
    q = np.asarray(sat["setpoint"], float)[:, :6]
    if len(t) < 4 or t[-1] - t[0] < 4.0 / hz:
        return np.zeros(1)
    g = np.arange(t[0], t[-1], 1.0 / hz)
    qi = np.stack([np.interp(g, t, q[:, j]) for j in range(6)], axis=1)
    return np.linalg.norm(np.diff(qi, axis=0), axis=1) * hz


def _stalls(sat):
    """(control cycles with dt > STALL_DT, worst cycle dt) -- audit T06 contamination."""
    if sat is None or len(sat.get("t_ns", ())) < 2:
        return 0, 0.0
    dt = np.diff(np.asarray(sat["t_ns"], float)) / 1e9
    return int(np.sum(dt > STALL_DT)), float(dt.max())


def sal(v, dt, fc=10.0, amp_th=0.05):
    """Spectral arc length of speed profile `v` (Balasubramanian et al. 2015).

    Zero-padded to padlevel 4, the SPARC reference value (audit T13; padlevel 2 read
    -1.376 against the reference -1.406 on a minimum-jerk move, a constant ~0.03 offset)."""
    v = np.asarray(v, float)
    if len(v) < 8 or not np.any(v):
        return float("nan")
    n = int(2 ** (np.ceil(np.log2(len(v))) + 4))
    mag = np.abs(np.fft.rfft(v, n))
    mag /= mag.max()
    f = np.fft.rfftfreq(n, dt)
    k = f <= fc
    mag, f = mag[k], f[k]
    inx = np.where(mag >= amp_th)[0]
    if len(inx) < 2:
        return float("nan")
    mag, f = mag[inx[0]:inx[-1] + 1], f[inx[0]:inx[-1] + 1]
    df = np.diff(f) / (f[-1] - f[0] or 1.0)
    return float(-np.sum(np.sqrt(df ** 2 + np.diff(mag) ** 2)))


def ldlj(v, dt):
    """Log dimensionless jerk of speed profile `v`. Less negative = smoother."""
    v = np.asarray(v, float)
    if len(v) < 8:
        return float("nan")
    peak = np.max(np.abs(v))
    j = np.gradient(np.gradient(v, dt), dt)
    e = np.trapezoid(j ** 2, dx=dt)
    if peak <= 0 or e <= 0:
        return float("nan")
    return float(-np.log((len(v) * dt) ** 3 / peak ** 2 * e))


def episode_metrics(ep, success, duration_s, cmds_sent, cmds_rx, events=None, sat=None,
                    vmax=2.0):
    """ep: arrays from record.load_episode. -> flat dict of one episode's numbers."""
    rtt = np.asarray(ep["rtt_ms"])
    rtt = rtt[rtt > 0]
    hold = np.asarray(ep["safety_hold"])
    act = np.asarray(ep["action"], float)[:, :6]
    obs = np.asarray(ep["observation.state"], float)[:, :6]
    d = np.diff(np.asarray(ep["timestamp"], float))
    period = float(np.median(d)) if len(d) else 0.02
    jerk = np.diff(act, 3, axis=0) / period ** 3 if len(act) > 3 else np.zeros((1, 6))
    # T05: smoothness and stall_frac come from the applied setpoints, never from the
    # sample-and-held observation. With no sidecar (unit tests) fall back to the old path.
    if sat is not None and len(sat.get("t_ns", ())) > 3:
        speed, sdt = applied_speed(sat), 1.0 / SMOOTH_HZ
    else:
        speed = (np.linalg.norm(np.diff(obs, axis=0), axis=1) / period if len(obs) > 1
                 else np.zeros(1))
        sdt = period
    stalls, max_dt = _stalls(sat)
    ev = dict(events or {})
    ev["vel_over"] = _vel_over(sat, vmax)
    if sat is not None and len(sat.get("taut", ())):      # H20: the "free 6-DoF" subset
        ev["taut_frac"] = round(float(np.mean(sat["taut"])), 3)
    return dict(success=bool(success), duration_s=float(duration_s),
                rtt_p50=percentile(rtt, 50), rtt_p95=percentile(rtt, 95),
                rtt_max=float(rtt.max()) if len(rtt) else float("nan"),
                cmd_loss=1.0 - cmds_rx / max(1, cmds_sent),
                hold_frames=int(hold.sum()), hold_s=float(hold.sum()) * period,
                jerk=float(np.sum(jerk ** 2)), frames=len(act),
                sal=sal(speed, sdt), ldlj=ldlj(speed, sdt),
                stall_frac=float(np.mean(speed < STALL)), events=ev,
                stalls=stalls, max_dt_s=max_dt, cage=int(ev.get("cage", 0)),
                unsafe=sum(int(ev.get(k, 0)) for k in SAFE))


def _vel_over(sat, vmax):
    """Control cycles on which the applied setpoint moved faster than the clamp."""
    if sat is None or len(sat.get("t_ns", ())) < 2:
        return 0
    dt = np.diff(sat["t_ns"]) / 1e9
    dq = np.abs(np.diff(np.asarray(sat["setpoint"], float)[:, :6], axis=0)).max(axis=1)
    ok = dt > 1e-6
    return int(np.sum(dq[ok] / dt[ok] > vmax * 1.05))    # 5 % for float and clock noise


def _agg_ev(eps, k):
    """A fraction averages, a peak maxes, everything else is a count and sums."""
    v = [e.get("events", {}).get(k, 0) for e in eps]
    if k.endswith("_frac"):
        return round(float(np.mean(v)), 3)
    if k.endswith("_peak"):
        return round(float(np.max(v)), 3)
    return sum(int(x) for x in v)


def aggregate(eps):
    """eps: list of episode_metrics dicts. -> summary incl. demos/hour."""
    ok = [e for e in eps if e["success"]]
    mean = lambda k, src: float(np.mean([e[k] for e in src])) if src else float("nan")
    keys = set().union(*[e.get("events", {}) for e in eps]) if eps else set()
    wall = sum(e["duration_s"] for e in eps)
    return dict(episodes=len(eps), success_rate=len(ok) / max(1, len(eps)),
                mean_duration_s=mean("duration_s", ok),
                demos_per_hour=3600.0 / mean("duration_s", ok) if ok else 0.0,
                demos_per_hour_gross=3600.0 * len(ok) / wall if wall else 0.0,
                rtt_p50=mean("rtt_p50", eps), rtt_p95=mean("rtt_p95", eps),
                rtt_max=max([e["rtt_max"] for e in eps], default=float("nan")),
                cmd_loss=mean("cmd_loss", eps), hold_s=mean("hold_s", eps),
                jerk=mean("jerk", eps), sal=mean("sal", eps), ldlj=mean("ldlj", eps),
                stall_frac=mean("stall_frac", eps),
                stalls=sum(e.get("stalls", 0) for e in eps),
                max_dt_s=max([e.get("max_dt_s", 0.0) for e in eps], default=0.0),
                cage=sum(e.get("cage", 0) for e in eps),
                unsafe=sum(e["unsafe"] for e in eps),
                events={k: _agg_ev(eps, k) for k in sorted(keys)})


def table(name, agg, extra=()):
    rows = [("profile", name), ("episodes", agg["episodes"]),
            ("success_rate", f"{agg['success_rate']:.2f}"),
            ("mean_duration_s", f"{agg['mean_duration_s']:.2f}"),
            ("demos_per_hour", f"{agg['demos_per_hour']:.1f}"),
            ("demos_per_h_gross", f"{agg.get('demos_per_hour_gross', 0.0):.1f}"),
            ("rtt_p50_ms", f"{agg['rtt_p50']:.1f}"), ("rtt_p95_ms", f"{agg['rtt_p95']:.1f}"),
            ("rtt_max_ms", f"{agg['rtt_max']:.1f}"), ("cmd_loss", f"{agg['cmd_loss']:.3f}"),
            ("safety_hold_s", f"{agg['hold_s']:.2f}"), ("jerk_sum_sq", f"{agg['jerk']:.3g}"),
            ("sal", f"{agg['sal']:.2f}"), ("ldlj", f"{agg['ldlj']:.2f}"),
            ("stall_frac", f"{agg['stall_frac']:.2f}"),
            ("unsafe_events", f"{agg['unsafe']}  ({', '.join(f'{k}={agg['events'].get(k, 0)}' for k in SAFE)})"),
            # operator/task-caused, so it gets its own column and stays out of `unsafe` (T07)
            ("cage", f"{agg.get('cage', 0)}"),
            ("stalls", f"{agg.get('stalls', 0)}"),      # T06: load contamination flags
            ("max_dt_s", f"{agg.get('max_dt_s', 0.0):.3f}"),
            ("diagnostics", ", ".join(f"{k}={v}" for k, v in agg["events"].items()
                                      if k not in SAFE))] + list(extra)
    return "\n".join(f"{k:<16} {v}" for k, v in rows)
