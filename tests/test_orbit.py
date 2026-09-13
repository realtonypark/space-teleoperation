"""Self-check: ISS passes over a known station have plausible count and duration."""
from spaceteleop.link.orbit import contact_windows

L1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000"
L2 = "2 25544  51.6400 208.9163 0006703  69.9862  25.2906 15.49560000000000"


def test_iss_windows():
    ws = contact_windows(L1, L2, [("madrid", 40.4, -3.7, 0.6)],
                         (2024, 1, 1, 12, 0, 0), minutes=360, min_elev=10.0)
    assert 2 <= len(ws) <= 6, ws  # ~3 ISS passes in 6 h at 40 deg N
    for _, t0, t1, el in ws:
        assert 60 <= t1 - t0 <= 900, (t0, t1)   # LEO pass: minutes, not hours
        assert el >= 10.0
    # a 51.6 deg orbit is never above the horizon from the south pole
    assert contact_windows(L1, L2, [("nowhere", -89.0, 0.0, 0.0)],
                           (2024, 1, 1, 12, 0, 0), minutes=360) == []
