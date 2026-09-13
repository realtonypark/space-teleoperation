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
