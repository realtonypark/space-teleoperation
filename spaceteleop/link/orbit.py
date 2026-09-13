"""TLE -> ground-station contact windows (sgp4 only, no skyfield).

Geometry: propagate to TEME, treat TEME as ECI (the difference is ~arcseconds of polar
motion and does not move an elevation mask by anything we care about), rotate the station
ECEF position into ECI with GMST, take elevation from the local up vector.
# ponytail: spherical Earth + GMST-only rotation. Good to <0.1 deg of elevation, which is
# far inside any real min-elevation mask. Upgrade path: skyfield, if pointing matters.
"""
import math
from sgp4.api import Satrec, jday

RE = 6378.137  # km, WGS-84 equatorial


def gmst(jd, fr):
    """Greenwich mean sidereal time, radians (IAU 1982)."""
    t = (jd - 2451545.0 + fr) / 36525.0
    s = 67310.54841 + (876600 * 3600 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t ** 3
    return math.radians((s % 86400.0) / 240.0)


def station_eci(lat_deg, lon_deg, alt_km, jd, fr):
    la, lo = math.radians(lat_deg), math.radians(lon_deg) + gmst(jd, fr)
    r = RE + alt_km
    return [r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)]


def elevation_deg(sat_eci, st_eci):
    d = [a - b for a, b in zip(sat_eci, st_eci)]
    rn = math.sqrt(sum(x * x for x in st_eci))
    up = [x / rn for x in st_eci]
    dn = math.sqrt(sum(x * x for x in d)) or 1e-9
    return math.degrees(math.asin(max(-1.0, min(1.0, sum(a * b for a, b in zip(d, up)) / dn))))


def contact_windows(tle1, tle2, stations, start_utc, minutes, step_s=10.0, min_elev=10.0):
    """stations: [(name, lat, lon, alt_km)]. start_utc: (y, mo, d, h, mi, s).

    Returns [(name, t_start_s, t_end_s, peak_elev_deg)] with times in seconds from start.
    """
    sat = Satrec.twoline2rv(tle1, tle2)
    jd0, fr0 = jday(*start_utc)
    out, open_w = [], {}
    for k in range(int(minutes * 60 / step_s) + 1):
        t = k * step_s
        fr = fr0 + t / 86400.0
        e, r, _ = sat.sgp4(jd0, fr)
        if e:
            continue
        for name, lat, lon, alt in stations:
            el = elevation_deg(r, station_eci(lat, lon, alt, jd0, fr))
            if el >= min_elev:
                w = open_w.setdefault(name, [t, t, el])
                w[1], w[2] = t, max(w[2], el)
            elif name in open_w:
                w = open_w.pop(name)
                out.append((name, w[0], w[1], w[2]))
    for name, w in open_w.items():
        out.append((name, w[0], w[1], w[2]))
    return sorted(out, key=lambda w: w[1])
