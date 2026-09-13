"""UDP proxy on 127.0.0.1 that really delays packets.

Each direction is a receive thread that samples a release time and pushes the datagram on
a heap, plus a drain thread that sleeps until the earliest release time and then sends.
Nothing is simulated in-process: the ground and sat sockets see wall-clock-late datagrams.

Delay = mean_ms + jitter, where jitter is mean-0 with SD `jitter_ms` in one of four shapes
(`dist`), optionally AR(1)-correlated with coefficient `rho`; on top of that sits the
optional 15 s structure (spike at period start, end bump, per-period shift) of the relay
profile. Loss is Gilbert-Elliott, with `burst_frac` of periods forced into the bad state
for their first second. Blackouts come from three independent sources: a Poisson schedule
with a duration mixture, a periodic pair (GEO handover), and pass windows.

Bandwidth is a serialisation model (next_free += nbytes/bw_bps), not a token bucket.
# ponytail: serialisation cap, replace with a token bucket if burst behaviour matters.
"""
import heapq
import math
import random
import socket
import threading
import time

HORIZON_S = 3600.0          # how far ahead the Poisson outage schedule is drawn
_S = 0.6                    # log-normal shape; fixed, only the SD is a profile knob
_LN_M = math.exp(_S * _S / 2)
_LN_SD = _LN_M * math.sqrt(math.exp(_S * _S) - 1.0)

# unit samplers: mean 0, SD 1. The profile scales them by jitter_ms.
_UNIT = {
    "exp": lambda r: r.expovariate(1.0) - 1.0,
    "gauss": lambda r: r.gauss(0.0, 1.0),
    "lognormal": lambda r: (math.exp(r.gauss(0.0, _S)) - _LN_M) / _LN_SD,
    "gamma": lambda r: (r.gammavariate(2.0, 1.0) - 2.0) / math.sqrt(2.0),
}


def outage_schedule(rate_per_h, mix, horizon_s, rng):
    """Poisson blackouts at `rate_per_h`, durations from `mix` = [(prob, lo_s, hi_s)].

    -> [(start_s, end_s)] sorted, covering [0, horizon_s). Pure function of `rng`, so it
    is unit-testable without a socket.
    """
    if not rate_per_h or not mix:
        return []
    out, t = [], 0.0
    while True:
        t += rng.expovariate(rate_per_h / 3600.0)
        if t > horizon_s:
            return out
        u, c = rng.random(), 0.0
        for prob, lo, hi in mix:
            c += prob
            if u <= c:
                break
        out.append((t, t + rng.uniform(lo, hi)))


class Link:
    def __init__(self, profile, sat_addr, ground_addr, seed=0):
        self.up = _Dir(profile["up"], sat_addr, random.Random(seed))
        self.down = _Dir(profile["down"], ground_addr, random.Random(seed + 1))
        self.up_port = self.up.sock.getsockname()[1]
        self.down_port = self.down.sock.getsockname()[1]
        self._threads = []

    def start(self):
        self.t_start = t0 = time.monotonic()
        for d in (self.up, self.down):
            d.t0 = t0
            for fn in (d.recv_loop, d.drain_loop):
                th = threading.Thread(target=fn, daemon=True)
                th.start()
                self._threads.append(th)
        return self

    def stop(self):
        for d in (self.up, self.down):
            d.stop = True
        for d in (self.up, self.down):
            d.sock.close()
            d.out.close()

    def stats(self):
        """Packet and byte counters. Bytes are offered bytes: a dropped datagram still
        occupied the wire on the sending side, which is what a bandwidth budget pays for."""
        s = time.monotonic() - self.t_start
        return dict(up_sent=self.up.sent, up_dropped=self.up.dropped,
                    down_sent=self.down.sent, down_dropped=self.down.dropped,
                    up_bytes=self.up.bytes, down_bytes=self.down.bytes, wire_s=s,
                    up_bps=self.up.bytes / max(s, 1e-9), down_bps=self.down.bytes / max(s, 1e-9))


class _Dir:
    def __init__(self, p, dst, rng):
        self.p, self.dst, self.rng = p, dst, rng
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.05)
        self.out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.heap, self.lock = [], threading.Lock()
        self.stop = False
        self.bad = False
        self.sent = self.dropped = self.bytes = 0
        self.t0 = time.monotonic()
        self.next_free = 0.0
        # random phase: otherwise every episode would start inside the same blackout
        self.phase = rng.random() * (p["outage_period_s"] or 1.0)
        # pass windows start AT a pass on purpose: direct_gs throughput is reported per
        # pass (SYNTHESIS section 6), and a 20 s episode must not land in a 35 min gap.
        self.outages = outage_schedule(p["outage_rate_per_h"], p["outage_mix"],
                                       HORIZON_S, rng)
        self.period_i, self.shift_ms, self.burst, self.j = None, 0.0, False, 0.0
        self.last_release = 0.0

    def structure(self, t):
        """-> (extra_delay_ms, force_bad_state) for elapsed time `t` in the 15 s layer."""
        p = self.p
        if not p["period_s"]:
            return 0.0, False
        i = int(t / p["period_s"])
        if i != self.period_i:                     # new period: redraw shift and burst
            self.period_i = i
            self.shift_ms = self.rng.uniform(-p["shift_ms"], p["shift_ms"])
            self.burst = self.rng.random() < p["burst_frac"]
        ph = t - i * p["period_s"]
        e = self.shift_ms
        if p["spike_dur_s"] and ph < p["spike_dur_s"]:
            e += p["spike_ms"] * (1.0 - ph / p["spike_dur_s"])
        if p["end_bump_s"] and ph > p["period_s"] - p["end_bump_s"]:
            e += p["end_bump_ms"]
        return e, self.burst and ph < 1.0

    def blacked_out(self, t):
        p = self.p
        if p["pass_on_s"] and (t % (p["pass_on_s"] + p["pass_off_s"])) >= p["pass_on_s"]:
            return True
        if p["outage_dur_s"] and (t + self.phase) % p["outage_period_s"] < p["outage_dur_s"]:
            return True
        # ponytail: linear scan over a handful of Poisson outages per hour. Bisect if the
        # schedule ever grows past thousands of entries.
        return any(a <= t < b for a, b in self.outages)

    def _lost(self, force_bad):
        p = self.p
        if force_bad:
            self.bad = True
        else:
            self.bad = (self.rng.random() > p["p_bg"]) if self.bad else (self.rng.random() < p["p_gb"])
        return self.rng.random() < (p["loss_b"] if self.bad else p["loss_g"])

    def delay(self):
        p = self.p
        if p["jitter_ms"]:
            j = _UNIT[p["dist"]](self.rng)
            if p["rho"]:
                j = self.j = p["rho"] * self.j + math.sqrt(1.0 - p["rho"] ** 2) * j
            return max(0.0, p["mean_ms"] + j * p["jitter_ms"]) / 1000.0
        return p["mean_ms"] / 1000.0

    def recv_loop(self):
        while not self.stop:
            try:
                pkt, _ = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            now = time.monotonic()
            t = now - self.t0
            self.bytes += len(pkt)
            extra, force_bad = self.structure(t)
            if self.blacked_out(t) or self._lost(force_bad):
                self.dropped += 1
                continue
            rel = now + self.delay() + extra / 1000.0
            if self.p["bw_bps"]:
                self.next_free = max(self.next_free, now) + len(pkt) / self.p["bw_bps"]
                rel = max(rel, self.next_free)
            if not self.p["reorder"]:
                rel = self.last_release = max(rel, self.last_release)
            with self.lock:
                heapq.heappush(self.heap, (rel, self.sent + self.dropped, pkt))

    def drain_loop(self):
        while not self.stop:
            with self.lock:
                rel = self.heap[0][0] if self.heap else None
            if rel is None:
                time.sleep(0.0005)
                continue
            dt = rel - time.monotonic()
            if dt > 0:
                time.sleep(min(dt, 0.005))
                continue
            with self.lock:
                if not self.heap or self.heap[0][0] > time.monotonic():
                    continue
                _, _, pkt = heapq.heappop(self.heap)
            try:
                self.out.sendto(pkt, self.dst)
                self.sent += 1
            except OSError:
                return
