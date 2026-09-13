"""Link profiles = SYNTHESIS section 7, verbatim. Plain dicts, one entry per direction.

Per direction (every field past `jitter_ms` is optional and defaults to off):
  mean_ms     base one-way delay
  jitter_ms   SD of the mean-0 jitter added to it
  dist        jitter shape: "exp" | "gauss" | "lognormal" | "gamma"
  rho         AR(1) correlation between consecutive jitter samples
  p_gb/p_bg   Gilbert-Elliott transition probs per packet; loss_g/loss_b loss per state
  period_s    length of the repeating structure (0 = none), with, inside each period:
    spike_ms      peak delay added at period start, decaying linearly over spike_dur_s
    end_bump_ms   delay added over the last end_bump_s of the period
    shift_ms      per-period offset drawn U(-shift_ms, +shift_ms)
    burst_frac    fraction of periods forced into the GE bad state for their first second
  outage_rate_per_h  Poisson blackout rate, durations from outage_mix [(prob, lo_s, hi_s)]
  outage_period_s / outage_dur_s  periodic blackout (GEO handover)
  drop_at_s / drop_len_s  ONE forced blackout, `drop_len_s` long, starting `drop_at_s`
                  after Link.start(); deterministic, so every episode sees it
  pass_on_s / pass_off_s  periodic contact window; outside a pass every packet is dropped
  reorder     if False the direction is forced FIFO (delay is monotonised)
  bw_bps      serialisation cap in BYTES/s (0 = unlimited)

Bandwidth caps below are the section 7 bit rates divided by 8.
"""

# 87 % U(0.3, 2) s, 10 % U(2, 5) s, 3 % U(5, 31) s -- network_emulation section 1.1
RELAY_MIX = ((0.87, 0.3, 2.0), (0.10, 2.0, 5.0), (0.03, 5.0, 31.0))


def _d(mean_ms, jitter_ms=0.0, dist="exp", rho=0.0, loss=0.0, p_gb=0.0, p_bg=1.0,
       loss_b=0.0, period_s=0.0, spike_ms=0.0, spike_dur_s=0.0, end_bump_ms=0.0,
       end_bump_s=0.0, shift_ms=0.0, burst_frac=0.0, outage_rate_per_h=0.0, outage_mix=(),
       outage_period_s=0.0, outage_dur_s=0.0, drop_at_s=0.0, drop_len_s=0.0,
       pass_on_s=0.0, pass_off_s=0.0, reorder=True, bw_bps=0):
    return dict(mean_ms=mean_ms, jitter_ms=jitter_ms, dist=dist, rho=rho, loss_g=loss,
                loss_b=loss_b, p_gb=p_gb, p_bg=p_bg, period_s=period_s, spike_ms=spike_ms,
                spike_dur_s=spike_dur_s, end_bump_ms=end_bump_ms, end_bump_s=end_bump_s,
                shift_ms=shift_ms, burst_frac=burst_frac,
                outage_rate_per_h=outage_rate_per_h, outage_mix=tuple(outage_mix),
                outage_period_s=outage_period_s, outage_dur_s=outage_dur_s,
                drop_at_s=drop_at_s, drop_len_s=drop_len_s,
                pass_on_s=pass_on_s, pass_off_s=pass_off_s, reorder=reorder, bw_bps=bw_bps)


def _leo(up_ms, down_ms, **kw):
    """leo_relay structure at an arbitrary base delay; `sweep` reuses it."""
    ge = dict(p_gb=0.0034, p_bg=0.2, loss=0.0, loss_b=0.3)
    struct = dict(period_s=15.0, spike_dur_s=0.140, end_bump_ms=20.0, end_bump_s=0.075,
                  shift_ms=5.0, burst_frac=0.31, outage_rate_per_h=1.7,
                  outage_mix=RELAY_MIX, **kw)
    return dict(up=_d(up_ms, 14.0, "lognormal", rho=0.25, spike_ms=74.0,
                      bw_bps=625_000, **ge, **struct),
                down=_d(down_ms, 11.0, "lognormal", rho=0.25, spike_ms=37.0,
                        bw_bps=6_250_000, **ge, **struct))


PROFILES = {
    # the zero-latency baseline every other profile is scored against: literally zero
    "zero": dict(up=_d(0, 0), down=_d(0, 0)),
    # direct ground station: 15 ms each way, Kontur-2 jitter/loss, 9 min pass in 44
    "direct_gs": dict(
        up=_d(15, 2.0, "gauss", p_gb=0.001, p_bg=0.2, loss_b=0.3, bw_bps=32_000,
              pass_on_s=540.0, pass_off_s=2100.0, reorder=False),
        down=_d(15, 2.0, "gauss", p_gb=0.001, p_bg=0.2, loss_b=0.3, bw_bps=12_500_000,
                pass_on_s=540.0, pass_off_s=2100.0, reorder=False)),
    # LEO relay, bent pipe + one ISL hop, 15 s structure, Poisson outages
    "leo_relay": _leo(30.0, 18.0),
    # Dropout block (audit T02): leo_relay plus ONE forced full outage, both directions,
    # 6.0 s after link start. The Poisson schedule gives P(outage inside a 20 s episode) =
    # 0.9 % per direction, so the matrix never exercised hold/retract and "zero unsafe
    # motion on dropout" was vacuous. 1.0 s trips hold (timeout 0.3 s) and returns; 12.0 s
    # crosses the 10 s retract, so the arm stows and then resumes ramp-limited.
    "leo_relay_drop1": _leo(30.0, 18.0, drop_at_s=6.0, drop_len_s=1.0),
    "leo_relay_drop12": _leo(30.0, 18.0, drop_at_s=6.0, drop_len_s=12.0),
    # GEO relay: 300 ms each way, TDRS handover LOS 45 s every 45 min
    "geo_relay": dict(
        up=_d(300, 2.0, "gauss", p_gb=0.0091, p_bg=0.2, loss_b=0.3, bw_bps=2_500_000,
              outage_period_s=2700.0, outage_dur_s=45.0, reorder=False),
        down=_d(300, 2.0, "gauss", p_gb=0.0091, p_bg=0.2, loss_b=0.3, bw_bps=11_250_000,
                outage_period_s=2700.0, outage_dur_s=45.0, reorder=False)),
}

_SPLIT = 30.0 / 48.0    # leo_relay's up share of its base round trip


def sweep(rtt):
    """leo_relay structure whose base up+down delay sums to `rtt` ms, same up/down split.

    `sweep:0` is therefore "the relay structure with NO base delay": the log-normal jitter
    (SD 14 ms up / 11 ms down), the 15 s spike layer and the loss model are all still there,
    and the per-packet delay floors at 0 (`delay()` clips the negative half). The clipping
    is not symmetric, so the realised one-way mean is NOT 0 (audit T08). Measured:
    `delay()` alone over 50 k draws gives 5.0 ms up / 4.0 ms down (SD 10.5 / 8.3 instead of
    the nominal 14 / 11); end to end over the sockets, with the 15 s structure and the
    scheduler on top, the audit measured 6.5 / 5.4 ms, i.e. a realised base RTT of ~12 ms.
    Read the sweep x-axis at 0 as "relay structure, no base delay, ~12 ms realised", not as
    0 ms; `rtt_ms("sweep:0")` still returns the nominal 0, which is what it is labelled.
    tests/test_link.py pins the two `delay()` means."""
    return _leo(rtt * _SPLIT, rtt * (1.0 - _SPLIT))


def get(name):
    """PROFILES[name], or `sweep:<rtt_ms>` for a point on the 0-1000 ms curve."""
    if name.startswith("sweep:"):
        return sweep(float(name.split(":", 1)[1]))
    return PROFILES[name]


def rtt_ms(name):
    """Nominal mean base round trip of a profile, for sanity-checking measurements."""
    p = get(name)
    return p["up"]["mean_ms"] + p["down"]["mean_ms"]
