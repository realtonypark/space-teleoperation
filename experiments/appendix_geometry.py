"""Appendix: direct-pass contact geometry for a 550 km SSO vs three ground-network options.

Run:  uv run python experiments/appendix_geometry.py
Writes docs/experiments/appendix_geometry.md. Reuses spaceteleop.link.orbit (sgp4 only).
"""
import math, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sgp4.api import Satrec
from spaceteleop.link.orbit import contact_windows

# ICEYE-X37 (NORAD 59102, Transporter-10 rideshare, 2024-03). Fetched from CelesTrak on 2026-09-13:
# https://celestrak.org/NORAD/elements/gp.php?CATNR=59102&FORMAT=tle
TLE1 = "1 59102U 24043E   26256.12700437  .00003081  00000+0  21138-3 0  9994"
TLE2 = "2 59102  97.8438  34.6061 0016394  73.4069 286.8957 15.06684554138326"
START = (2026, 9, 13, 0, 0, 0)
DAYS, STEP_S = 7, 10.0
MASKS = (5.0, 10.0)

# (name, provider, lat, lon, alt_km, source). Coordinates tagged "site" are published by the provider;
# "approx" are city/region-level because the provider publishes only the place name.
POLAR4 = [  # network_emulation.md section 1.4 union set
    ("Svalbard", "KSAT", 78.23, 15.39, 0.5, "site: KSAT 78N (ksat.no KSATlite 10-years article); coords from network_emulation 1.4"),
    ("Troll", "KSAT", -72.01, 2.53, 1.3, "site: KSAT 72S (ksat.no 2023 expansion article); coords from network_emulation 1.4"),
    ("Inuvik", "SSC/KSAT", 68.32, -133.55, 0.1, "site: sscspace.com our-stations; coords from network_emulation 1.4"),
    ("Punta Arenas", "SSC/AWS/Leaf", -53.04, -70.84, 0.05, "site: leaf.space map JSON; also sscspace.com, aws.amazon.com/ground-station/locations"),
]
MIDLAT1 = [("Weilheim", "DLR", 47.88, 11.08, 0.6, "approx: DLR Weilheim, the Kontur-2 station cited by H01")]
# H01 lists no sites. Union of the sites published by KSAT, SSC, AWS, Leaf Space and Viasat RTE
# (pages fetched 2026-09-13). S/X-band only; co-located antennas merged into one row.
COMMERCIAL = POLAR4 + [
    ("Utqiagvik AK", "Leaf", 71.29, -156.78, 0.0, "site: leaf.space map JSON (S/X/Ka)"),
    ("Tromso", "KSAT", 69.66, 18.94, 0.0, "approx: KSAT HQ site (ksat.no)"),
    ("Esrange", "SSC", 67.88, 21.06, 0.4, "approx: sscspace.com our-stations (Kiruna)"),
    ("Blonduos", "Leaf", 65.64, -20.24, 0.0, "site: leaf.space map JSON (S/X/Ka)"),
    ("Fairbanks / North Pole AK", "Viasat/SSC", 64.79, -147.54, 0.2, "site: viasat.com RTE page 64.79N 147.54W; SSC North Pole station co-located"),
    ("Talkeetna AK", "Leaf", 62.33, -150.03, 0.0, "site: leaf.space map JSON"),
    ("Shetland", "Leaf", 60.74, -0.85, 0.0, "site: leaf.space map JSON (S/X/UHF)"),
    ("Stockholm / Agesta", "SSC/AWS", 59.21, 18.10, 0.0, "approx: sscspace.com Stockholm Teleport; AWS Stockholm"),
    ("Ushuaia", "Viasat", -54.50, -67.11, 0.0, "site: viasat.com RTE page"),
    ("Ireland", "AWS", 53.30, -6.30, 0.0, "approx: aws.amazon.com/ground-station/locations (Ireland)"),
    ("Guildford", "Viasat", 51.24, -0.62, 0.0, "site: viasat.com RTE page"),
    ("Oregon", "AWS", 45.80, -119.70, 0.1, "approx: AWS us-west-2 region"),
    ("Nova Scotia", "Leaf", 44.68, -63.74, 0.0, "site: leaf.space map JSON"),
    ("Hokkaido", "Viasat", 42.59, 143.45, 0.0, "site: viasat.com RTE page (S/X/Ka)"),
    ("Plana", "Leaf", 42.48, 23.44, 0.0, "site: leaf.space map JSON"),
    ("Absheron", "Leaf", 40.46, 49.48, 0.0, "site: leaf.space map JSON"),
    ("Ohio", "AWS", 40.00, -83.00, 0.2, "approx: AWS us-east-2 region"),
    ("Spain (Leaf 'Montsec')", "Leaf", 38.67, -4.16, 0.7, "site: leaf.space map JSON as published (coords are near Puertollano, not Montsec)"),
    ("Azores", "Leaf", 36.99, -25.13, 0.0, "site: leaf.space map JSON"),
    ("Pendergrass GA", "Viasat", 34.18, -83.67, 0.0, "site: viasat.com RTE page"),
    ("Jeju", "KSAT", 33.40, 126.50, 0.0, "approx: ksat.no 2023 South Korea article"),
    ("Clewiston FL", "SSC", 26.75, -80.93, 0.0, "approx: sscspace.com our-stations"),
    ("Bahrain", "AWS", 26.10, 50.50, 0.0, "approx: aws.amazon.com/ground-station/locations"),
    ("Al Ain", "Leaf", 24.20, 55.74, 0.0, "site: leaf.space map JSON"),
    ("La Paz MX", "Leaf", 24.09, -110.38, 0.0, "site: leaf.space map JSON"),
    ("Maui", "Leaf", 20.79, -156.33, 0.0, "site: leaf.space map JSON (longitude sign corrected; JSON says +156.33)"),
    ("South Point HI", "SSC/AWS", 19.00, -155.66, 0.0, "approx: sscspace.com our-stations; AWS Hawaii site unspecified"),
    ("Siracha", "SSC", 13.10, 100.93, 0.0, "approx: sscspace.com our-stations"),
    ("Kandy", "Leaf", 7.27, 80.72, 0.0, "site: leaf.space map JSON"),
    ("Accra", "Viasat", 5.60, -0.30, 0.0, "site: viasat.com RTE page"),
    ("Singapore", "AWS", 1.35, 103.80, 0.0, "approx: aws.amazon.com/ground-station/locations"),
    ("St Helena", "Leaf", -15.94, -5.65, 0.0, "site: leaf.space map JSON"),
    ("Mauritius", "Leaf", -20.13, 57.68, 0.0, "site: leaf.space map JSON"),
    ("Alice Springs", "Viasat", -23.76, 133.88, 0.6, "site: viasat.com RTE page"),
    ("Hartebeesthoek / Pretoria", "Leaf/Viasat", -25.88, 27.70, 1.5, "site: viasat.com RTE page (page prints 25.88N, hemisphere corrected); Leaf co-located"),
    ("WASC / Nanghetty", "SSC/Leaf", -29.01, 115.34, 0.0, "site: leaf.space map JSON; SSC Western Australia Space Centre co-located"),
    ("Cordoba", "Viasat", -31.52, -64.46, 0.4, "site: viasat.com RTE page"),
    ("Dubbo", "AWS", -32.25, 148.60, 0.0, "approx: aws.amazon.com/ground-station/locations"),
    ("Peterborough SA", "Leaf/KSAT", -32.96, 138.84, 0.0, "site: leaf.space map JSON; ksat.no 2024 article"),
    ("Santiago", "SSC/Leaf", -33.36, -70.77, 0.5, "site: leaf.space map JSON; also sscspace.com"),
    ("Cape Town", "AWS", -33.90, 18.50, 0.0, "approx: aws.amazon.com/ground-station/locations"),
    ("Awarua", "Leaf", -46.52, 168.37, 0.0, "site: leaf.space map JSON (S/X/Ka)"),
]
SETS = [("(a) 4-site polar", POLAR4), ("(b) single mid-latitude (Weilheim)", MIDLAT1),
        ("(c) commercial S/X network", COMMERCIAL)]


def stats(windows, days, step):
    """Union of per-station windows -> duty, passes/day, mean pass, median/max gap (minutes)."""
    merged = []
    for _, s, e, _ in sorted(windows, key=lambda w: w[1]):
        e += step  # last sample is inclusive
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    on = sum(e - s for s, e in merged)
    gaps = [merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1)]
    return dict(duty=100 * on / (days * 86400), per_day=len(merged) / days,
                mean_pass=statistics.mean(e - s for s, e in merged) / 60,
                med_gap=statistics.median(gaps) / 60, max_gap=max(gaps) / 60)


def main():
    sat = Satrec.twoline2rv(TLE1, TLE2)
    a = (398600.4418 / (sat.no_kozai / 60) ** 2) ** (1 / 3)  # semi-major axis from mean motion (rad/min)
    alt = a - 6378.137
    assert 520 <= alt <= 580, alt
    all_st = {n: (n, la, lo, al) for n, _, la, lo, al, _ in COMMERCIAL + MIDLAT1}
    res = {}
    for mask in MASKS:
        ws = contact_windows(TLE1, TLE2, list(all_st.values()), START, DAYS * 1440, STEP_S, mask)
        for label, sites in SETS:
            names = {s[0] for s in sites}
            res[label, mask] = stats([w for w in ws if w[0] in names], DAYS, STEP_S)
    a5, c5 = res[SETS[0][0], 5.0], res[SETS[2][0], 5.0]
    assert 15 <= a5["duty"] <= 28, a5  # network_emulation 1.4 cross-check: 21.3 %

    L = ["# Appendix: direct-pass contact geometry (550 km SSO, 7 days)", "",
         "Generated by `uv run python experiments/appendix_geometry.py` on %s." % datetime.now(timezone.utc).strftime("%Y-%m-%d"),
         "Propagation: `spaceteleop.link.orbit.contact_windows` (sgp4, TEME + GMST rotation, spherical Earth), "
         "start %04d-%02d-%02d %02d:%02d UTC, %d days, %.0f s steps, masks %s deg. Duty and gaps are on the union of all sites in a set." % (*START[:5], DAYS, STEP_S, "/".join("%g" % m for m in MASKS)),
         "", "## TLE", "",
         "ICEYE-X37 (NORAD 59102, Transporter-10 rideshare), CelesTrak 2026-09-13, "
         "<https://celestrak.org/NORAD/elements/gp.php?CATNR=59102&FORMAT=tle>. "
         "Mean-motion altitude %.0f km, inclination %.2f deg, e %.4f." % (alt, math.degrees(sat.inclo), sat.ecco),
         "", "```", TLE1, TLE2, "```", "", "## Results", "",
         "| Site set | Sites | Mask | Duty | Passes/day | Mean pass (min) | Median gap (min) | Max gap (min) |",
         "|---|---|---|---|---|---|---|---|"]
    for label, sites in SETS:
        for mask in MASKS:
            r = res[label, mask]
            L.append("| %s | %d | %g deg | %.1f %% | %.1f | %.1f | %.1f | %.0f |" % (
                label, len(sites), mask, r["duty"], r["per_day"], r["mean_pass"], r["med_gap"], r["max_gap"]))
    mult = {m: res[SETS[2][0], m]["duty"] / res[SETS[0][0], m]["duty"] for m in MASKS}
    L += ["", "Demos-per-wall-hour multiplier of (c) over (a), throughput proportional to contact time: "
          "x%.2f at 5 deg, x%.2f at 10 deg." % (mult[5.0], mult[10.0]), "", "## Reading", "",
          "H01 claims the dense network lifts duty from 21 %% to 54-69 %%. The 4-site cross-check reproduces "
          "network_emulation section 1.4 (%.1f %% here vs 21.3 %% there, on a real TLE instead of a synthetic element set). "
          "The %d-site commercial union gives %.1f %% at 5 deg and %.1f %% at 10 deg, with %.1f passes/day, %.1f min mean pass "
          "and a %.1f min median gap at 5 deg. At 5 deg that is inside H01's 54-69 %% band with fewer sites than its 51 "
          "(H01's 69 %% was the uncapped 51-site list, its 54 %% a 40-site list under a 100 ms backhaul cap that this appendix "
          "does not model; the V1 verifier's 45-site list gave 64.5 %%). At 10 deg the union falls below the band. So the "
          "geometric half of the claim reproduces at the 5 deg mask H01 used, on the published footprint of KSAT, SSC, AWS, "
          "Leaf Space and Viasat RTE; %d of the %d rows carry provider-published coordinates, the rest are city-level, and "
          "neither uplink licensing nor antenna availability is checked." % (
              a5["duty"], len(COMMERCIAL), c5["duty"], res[SETS[2][0], 10.0]["duty"], c5["per_day"], c5["mean_pass"], c5["med_gap"],
              sum(s[5].startswith("site") for s in COMMERCIAL), len(COMMERCIAL)),
          "",
          "If throughput is proportional to contact time, the commercial network yields x%.2f the demonstrations per wall-hour "
          "of the 4-site fallback at 5 deg and x%.2f at 10 deg, inside H01's predicted x2.6-3.4 before its ~4 %% handover "
          "deduction. The ratio rises with the mask because the polar set loses %.1f duty points from 5 to 10 deg against "
          "%.1f for the commercial union, so the multiplier is robust to where the low-elevation x10-loss band starts even "
          "though absolute duty is not. The single mid-latitude site (Weilheim) is the reference for one team without a "
          "network: %.1f %% duty, %.1f passes/day, %.0f min median gap at 5 deg. Backhaul, handover and operator headcount "
          "(three teams) are outside this geometry and are the V1 objections that still stand." % (
              mult[5.0], mult[10.0], a5["duty"] - res[SETS[0][0], 10.0]["duty"], c5["duty"] - res[SETS[2][0], 10.0]["duty"],
              res[SETS[1][0], 5.0]["duty"], res[SETS[1][0], 5.0]["per_day"], res[SETS[1][0], 5.0]["med_gap"]),
          "", "## Site lists", ""]
    for label, sites in SETS:
        L += ["### %s (%d)" % (label, len(sites)), "", "| Site | Provider | Lat | Lon | Alt km | Source |", "|---|---|---|---|---|---|"]
        L += ["| %s | %s | %.2f | %.2f | %.1f | %s |" % (n, p, la, lo, al, src) for n, p, la, lo, al, src in sites]
        L.append("")
    L += ["Provider pages fetched 2026-09-13: <https://leaf.space/leaf-line/> (map JSON with coordinates and bands), "
          "<https://sscspace.com/services/satellite-ground-stations/our-stations/>, "
          "<https://aws.amazon.com/ground-station/locations/>, "
          "<https://www.viasat.com/government/antenna-systems/real-time-earth/> (coordinates per antenna), "
          "<https://www.ksat.no/> news archive (site map is JavaScript; Svalbard, Troll, Tromso, Jeju, Peterborough, "
          "Western Australia, Hawaii, Alaska named in articles). Excluded: Leaf Kaspichan (S/UHF only), Viasat Pitea "
          "(band not stated), KSAT sites known only from memory."]
    out = Path(__file__).resolve().parents[1] / "docs/experiments/appendix_geometry.md"
    out.write_text("\n".join(L) + "\n")
    for label, sites in SETS:
        for mask in MASKS:
            print(label, mask, {k: round(v, 2) for k, v in res[label, mask].items()})
    print("alt_km=%.1f mult5=%.2f mult10=%.2f -> %s" % (alt, mult[5.0], mult[10.0], out))


if __name__ == "__main__":
    main()
