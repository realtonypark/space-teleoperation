"""Self-check: the emulator delays, loses and blacks out real UDP datagrams."""
import socket
import threading
import statistics
import time

from spaceteleop.link.emulator import Link
from spaceteleop.link.profiles import PROFILES, _d


def _pair():
    """(sender, receiver) UDP sockets on loopback."""
    a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    b.bind(("127.0.0.1", 0))
    b.settimeout(2.0)
    return a, b


def _run(prof, n=300, gap=0.002, pay=b"x" * 45, settle=0.5):
    """Send n paced datagrams through the emulator while draining the far side."""
    tx, rx = _pair()
    link = Link(dict(up=prof, down=_d(0, 0)), rx.getsockname(), ("127.0.0.1", 1), seed=7).start()
    sent, delays, order, stop = {}, [], [], []
    rel = {}

    def drain():                      # must run concurrently or the socket buffer adds delay
        while not stop:
            try:
                pkt, _ = rx.recvfrom(65535)
            except socket.timeout:
                continue
            i = int.from_bytes(pkt[:4], "little")
            order.append(i)
            delays.append((time.monotonic() - sent[i]) * 1000)

    rx.settimeout(0.05)
    th = threading.Thread(target=drain, daemon=True)
    th.start()
    t0 = time.monotonic()
    for i in range(n):
        sent[i] = time.monotonic()
        rel[i] = sent[i] - link.up.t0
        tx.sendto(i.to_bytes(4, "little") + pay, ("127.0.0.1", link.up_port))
        time.sleep(gap)
    elapsed = time.monotonic() - t0
    time.sleep(settle + prof["mean_ms"] / 1000.0)
    stop.append(1)
    th.join(1.0)
    link.stop()
    return delays, order, rel, link.up.phase


def test_delay_matches_profile():
    n = 300
    delays, *_ = _run(_d(40, 10), n=n)
    assert len(delays) == n
    assert abs(statistics.mean(delays) - 40) < 8, statistics.mean(delays)
    assert min(delays) > 25, min(delays)          # floor is mean - jitter, plus scheduling


def test_zero_profile_is_fast():
    delays, *_ = _run(PROFILES["zero"]["up"], n=100)
    assert len(delays) == 100 and statistics.mean(delays) < 5, statistics.mean(delays)


def test_loss_fraction_matches():
    n = 400
    delays, *_ = _run(_d(5, 0, loss=0.2), n=n, gap=0.001)
    assert 0.12 < 1 - len(delays) / n < 0.28, len(delays) / n


def test_outage_drops_everything_in_window():
    # 1.0 s period, 0.4 s blackout -> ~40% of a uniformly paced stream is gone
    n = 400
    _, order, rel, ph = _run(_d(5, 0, outage_period_s=1.0, outage_dur_s=0.4), n=n, gap=0.005)
    assert 0.3 < 1 - len(order) / n < 0.6, len(order)
    for i in order:                                  # nothing sent inside a window survived
        assert not (0.005 < (rel[i] + ph) % 1.0 < 0.395), (i, rel[i], ph)


def test_no_reorder_is_fifo():
    _, order, *_ = _run(_d(20, 20, reorder=False), n=200)
    assert order == sorted(order)


def test_bandwidth_cap_queues():
    # 4500 B/s with 49-byte datagrams ~= 92 pkt/s; offering 500 pkt/s must build a queue
    delays, order, _, _ = _run(_d(0, 0, bw_bps=4500), n=150, gap=0.002, settle=2.5)
    assert len(delays) == 150
    assert delays[-1] > 1000.0, delays[-1]            # ~1.6 s behind by the last packet
    assert order == sorted(order)                     # the queue drains in order
    assert delays[0] < 100.0, delays[0]               # ...and only builds up over time


# --- SYNTHESIS section 7 mechanisms -----------------------------------------------

import random
from spaceteleop.link.emulator import _Dir, outage_schedule
from spaceteleop.link.profiles import PROFILES, get, rtt_ms as nominal_rtt


def _dir(p):
    d = _Dir(p, ("127.0.0.1", 1), random.Random(3))
    d.sock.close()
    d.out.close()
    return d


def test_jitter_sd_matches_for_every_dist():
    for dist in ("exp", "gauss", "lognormal", "gamma"):
        d = _dir(_d(100, 14, dist=dist))
        v = [d.delay() * 1000 for _ in range(20000)]
        assert abs(statistics.mean(v) - 100) < 1.0, (dist, statistics.mean(v))
        assert abs(statistics.stdev(v) - 14) < 1.0, (dist, statistics.stdev(v))


def test_ar1_correlates_consecutive_jitter():
    d = _dir(_d(100, 14, dist="gauss", rho=0.8))
    v = [d.delay() for _ in range(20000)]
    r = statistics.correlation(v[:-1], v[1:])
    assert 0.7 < r < 0.9, r
    assert abs(statistics.stdev(v) * 1000 - 14) < 1.0   # AR(1) preserves the SD


def test_spike_decays_from_period_start():
    p = _d(30, 0, period_s=15.0, spike_ms=74.0, spike_dur_s=0.140,
           end_bump_ms=20.0, end_bump_s=0.075)
    d = _dir(p)
    at = lambda t: d.structure(t)[0] - d.shift_ms
    assert 73 < at(0.0) <= 74, at(0.0)
    assert 30 < at(0.070) < 40, at(0.070)                 # half way down the ramp
    assert abs(at(1.0)) < 1e-9, at(1.0)                   # flat in the middle
    assert abs(at(14.99) - 20.0) < 1e-9, at(14.99)        # end bump
    assert 73 < at(15.0) <= 74, at(15.0)                  # next period spikes again
    assert all(abs(_dir(p).structure(k * 15.0)[0] - 74.0) <= 5.0 for k in range(5))


def test_burst_forces_the_bad_state():
    d = _dir(_d(1, 0, period_s=15.0, burst_frac=1.0))
    assert d.structure(0.5)[1] and not d.structure(2.0)[1]   # only the first second
    assert not _dir(_d(1, 0, period_s=15.0, burst_frac=0.0)).structure(0.5)[1]


def test_poisson_outage_rate_and_mixture():
    mix = ((0.87, 0.3, 2.0), (0.10, 2.0, 5.0), (0.03, 5.0, 31.0))
    s = outage_schedule(1.7, mix, 3600 * 500, random.Random(11))
    assert abs(len(s) / 500.0 - 1.7) < 0.15, len(s) / 500.0
    dur = [b - a for a, b in s]
    assert abs(statistics.mean(dur) - 2.11) < 0.3, statistics.mean(dur)   # mixture mean
    assert sum(x > 5.0 for x in dur) / len(dur) < 0.06                    # the 3 % tail
    assert s == sorted(s) and all(a < b for a, b in s)
    assert outage_schedule(0.0, mix, 1e6, random.Random(1)) == []


def test_pass_window_blocks_everything_outside_it():
    # 0.05 s of contact then 5 s of nothing; the phase starts inside the pass
    _, order, rel, _ = _run(_d(2, 0, pass_on_s=0.05, pass_off_s=5.0), n=200, gap=0.005)
    assert 0 < len(order) < 25, len(order)
    for i in order:
        assert rel[i] < 0.06, (i, rel[i])


def test_profiles_are_the_synthesis_table():
    for d in PROFILES["zero"].values():                      # zero is literally zero
        assert not any(d[k] for k in d if k not in ("dist", "reorder", "p_bg")), d
    assert nominal_rtt("leo_relay") == 48 and nominal_rtt("geo_relay") == 600
    assert nominal_rtt("direct_gs") == 30 and nominal_rtt("zero") == 0
    up = PROFILES["leo_relay"]["up"]
    assert up["jitter_ms"] == 14 and up["dist"] == "lognormal" and up["rho"] == 0.25
    assert up["spike_ms"] == 74 and up["burst_frac"] == 0.31 and up["period_s"] == 15
    mean_loss = up["loss_b"] * up["p_gb"] / (up["p_gb"] + up["p_bg"])
    assert abs(mean_loss - 0.005) < 0.0005, mean_loss        # 0.5 % background
    for r in (0.0, 100.0, 250.0, 1000.0):                    # sweep hits its target RTT
        s = get(f"sweep:{r}")
        assert abs(s["up"]["mean_ms"] + s["down"]["mean_ms"] - r) < 1e-9
        assert s["up"]["spike_ms"] == 74 and s["up"]["dist"] == "lognormal"
