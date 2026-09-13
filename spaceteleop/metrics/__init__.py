"""Episode metrics. Input is what record.load_episode returns plus a per-episode summary.

demos_per_hour follows the spec: 3600 / mean wall time of the SUCCESSFUL episodes. It
therefore ignores the wall time burned by failures; read it together with success_rate.
Path smoothness is the sum of squared joint jerk of the commanded action (third difference
over the command period), which is what the operator asked the arm to do.
"""
import numpy as np


def percentile(a, p):
    return float(np.percentile(a, p)) if len(a) else float("nan")


def episode_metrics(ep, success, duration_s, cmds_sent, cmds_rx):
    """ep: arrays from record.load_episode. -> flat dict of one episode's numbers."""
    rtt = np.asarray(ep["rtt_ms"])
    rtt = rtt[rtt > 0]
    hold = np.asarray(ep["safety_hold"])
    act = np.asarray(ep["action"], float)[:, :6]
    d = np.diff(np.asarray(ep["timestamp"], float))
    period = float(np.median(d)) if len(d) else 0.02
    jerk = np.diff(act, 3, axis=0) / period ** 3 if len(act) > 3 else np.zeros((1, 6))
    return dict(success=bool(success), duration_s=float(duration_s),
                rtt_p50=percentile(rtt, 50), rtt_p95=percentile(rtt, 95),
                rtt_max=float(rtt.max()) if len(rtt) else float("nan"),
                cmd_loss=1.0 - cmds_rx / max(1, cmds_sent),
                hold_frames=int(hold.sum()), hold_s=float(hold.sum()) * period,
                jerk=float(np.sum(jerk ** 2)), frames=len(act))


def aggregate(eps):
    """eps: list of episode_metrics dicts. -> summary incl. demos/hour."""
    ok = [e for e in eps if e["success"]]
    mean = lambda k, src: float(np.mean([e[k] for e in src])) if src else float("nan")
    return dict(episodes=len(eps), success_rate=len(ok) / max(1, len(eps)),
                mean_duration_s=mean("duration_s", ok),
                demos_per_hour=3600.0 / mean("duration_s", ok) if ok else 0.0,
                rtt_p50=mean("rtt_p50", eps), rtt_p95=mean("rtt_p95", eps),
                rtt_max=max([e["rtt_max"] for e in eps], default=float("nan")),
                cmd_loss=mean("cmd_loss", eps), hold_s=mean("hold_s", eps),
                jerk=mean("jerk", eps))


def table(name, agg):
    return "\n".join([
        f"profile          {name}",
        f"episodes         {agg['episodes']}",
        f"success_rate     {agg['success_rate']:.2f}",
        f"mean_duration_s  {agg['mean_duration_s']:.2f}",
        f"demos_per_hour   {agg['demos_per_hour']:.1f}",
        f"rtt_p50_ms       {agg['rtt_p50']:.1f}",
        f"rtt_p95_ms       {agg['rtt_p95']:.1f}",
        f"rtt_max_ms       {agg['rtt_max']:.1f}",
        f"cmd_loss         {agg['cmd_loss']:.3f}",
        f"safety_hold_s    {agg['hold_s']:.2f}",
        f"jerk_sum_sq      {agg['jerk']:.3g}",
    ])
