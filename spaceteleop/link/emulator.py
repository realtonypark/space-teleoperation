"""UDP proxy on 127.0.0.1 that really delays packets.

Each direction is a receive thread that samples a release time and pushes the datagram on
a heap, plus a drain thread that sleeps until the earliest release time and then sends.
Nothing is simulated in-process: the ground and sat sockets see wall-clock-late datagrams.

Delay = (mean_ms - jitter_ms) + Exp(mean=jitter_ms), clamped at 0. Mean is exactly
mean_ms, the tail is one-sided and heavy, which is what a real link looks like.
Bandwidth is a serialisation model (next_free += nbytes/bw_bps), not a token bucket.
# ponytail: serialisation cap, replace with a token bucket if burst behaviour matters.
"""
import heapq
import random
import socket
import threading
import time


class Link:
    def __init__(self, profile, sat_addr, ground_addr, seed=0):
        self.up = _Dir(profile["up"], sat_addr, random.Random(seed))
        self.down = _Dir(profile["down"], ground_addr, random.Random(seed + 1))
        self.up_port = self.up.sock.getsockname()[1]
        self.down_port = self.down.sock.getsockname()[1]
        self._threads = []

    def start(self):
        t0 = time.monotonic()
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
        return dict(up_sent=self.up.sent, up_dropped=self.up.dropped,
                    down_sent=self.down.sent, down_dropped=self.down.dropped)


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
        self.sent = self.dropped = 0
        self.t0 = time.monotonic()
        self.next_free = 0.0
        # random phase: otherwise every episode would start inside the same blackout
        self.phase = rng.random() * (p["outage_period_s"] or 1.0)
        self.last_release = 0.0

    def _drop(self, now):
        p = self.p
        if p["outage_dur_s"] and (now - self.t0 + self.phase) % p["outage_period_s"] < p["outage_dur_s"]:
            return True
        self.bad = (self.rng.random() > p["p_bg"]) if self.bad else (self.rng.random() < p["p_gb"])
        return self.rng.random() < (p["loss_b"] if self.bad else p["loss_g"])

    def delay(self):
        p = self.p
        if not p["jitter_ms"]:
            return p["mean_ms"] / 1000.0
        d = p["mean_ms"] - p["jitter_ms"] + self.rng.expovariate(1.0 / p["jitter_ms"])
        return max(0.0, d) / 1000.0

    def recv_loop(self):
        while not self.stop:
            try:
                pkt, _ = self.sock.recvfrom(65535)
            except (socket.timeout, OSError):
                continue
            now = time.monotonic()
            if self._drop(now):
                self.dropped += 1
                continue
            rel = now + self.delay()
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
