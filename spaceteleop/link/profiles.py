"""Link profiles: plain dicts, one entry per direction. Placeholder numbers.

Research replaces the VALUES, not the structure. Per direction:
  mean_ms   mean one-way delay (the distribution's exact mean)
  jitter_ms width of the exponential right tail; minimum delay is mean_ms - jitter_ms
  p_gb/p_bg Gilbert-Elliott transition probs per packet; loss_g/loss_b loss prob per state
  outage_period_s / outage_dur_s  periodic total blackout (0 = none)
  reorder   if False the direction is forced FIFO (delay is monotonised)
  bw_bps    serialisation cap in bytes/s (0 = unlimited)
"""


def _d(mean_ms, jitter_ms, loss=0.0, p_gb=0.0, p_bg=1.0, loss_b=0.5,
       outage_period_s=0.0, outage_dur_s=0.0, reorder=True, bw_bps=0):
    return dict(mean_ms=mean_ms, jitter_ms=jitter_ms, loss_g=loss, loss_b=loss_b,
                p_gb=p_gb, p_bg=p_bg, outage_period_s=outage_period_s,
                outage_dur_s=outage_dur_s, reorder=reorder, bw_bps=bw_bps)


PROFILES = {
    # ideal reference: the zero-latency baseline every other profile is scored against
    "zero": dict(up=_d(0, 0), down=_d(0, 0)),
    # [unverified] direct ground station, one hop, short pass
    "direct_gs": dict(up=_d(25, 8, loss=0.001, p_gb=0.002, p_bg=0.2, bw_bps=250_000),
                      down=_d(25, 10, loss=0.002, p_gb=0.004, p_bg=0.2, bw_bps=2_000_000)),
    # [unverified] LEO relay constellation, a few hops
    "leo_relay": dict(up=_d(45, 15, loss=0.002, p_gb=0.005, p_bg=0.15,
                            outage_period_s=30.0, outage_dur_s=0.4, bw_bps=250_000),
                      down=_d(45, 20, loss=0.004, p_gb=0.008, p_bg=0.15,
                              outage_period_s=30.0, outage_dur_s=0.4, bw_bps=2_000_000)),
    # [unverified] GEO relay, ~2 x 36000 km plus ground segment
    "geo_relay": dict(up=_d(260, 20, loss=0.003, p_gb=0.005, p_bg=0.2, bw_bps=150_000),
                      down=_d(260, 25, loss=0.005, p_gb=0.008, p_bg=0.2, bw_bps=1_000_000)),
}


def rtt_ms(name):
    """Nominal mean round trip of a profile, for sanity-checking measurements."""
    p = PROFILES[name]
    return p["up"]["mean_ms"] + p["down"]["mean_ms"]
