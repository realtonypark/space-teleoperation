# Network emulation and measurement for the LEO teleop testbed

Scope: (1) what public measurements say about Starlink-class LEO links, LEO-relay paths, GEO relay (TDRSS) and direct ground-station (GS) passes; (2) how to build a faithful UDP link emulator in Python on macOS; (3) TLE-based contact windows for a 550 km SSO satellite; (4) four concrete link profiles ready to implement. Numbers without a citation are marked `[unverified]` or `[own computation]` (scripts and command output are reproduced below).

## 1. Measured link behaviour

### 1.1 Starlink user-terminal links

| Quantity | Value | Setup | Source |
|---|---|---|---|
| Uplink OWD (idle) | 52 ± 14 ms mean ± SD | irtt, 3 ms probe interval, dish in EU, server ≤1 ms from PoP | Mohan et al. WWW'24 [1] |
| Downlink OWD (idle) | 35 ± 11 ms | same | [1] |
| "Bent-pipe" RTT (UT→sat→GS→PoP) | ≈40 ms median, 36–48 ms across countries; GS↔PoP ≈5 ms (7–8 ms US/CA) | 19.2 M M-Lab tests, 34 countries | [1] |
| Minimum access RTT | ≈20 ms (propagation + MAC polling) | UT to gateway | Pan et al. [2] |
| Median RTT per region | US 75th pct <50 ms; EU tail >100 ms; Africa/S. America 75th pct >100 ms, tail 200 ms | M-Lab | [1] |
| RTT under load (bufferbloat) | 2–4× inflation, 400–500 ms during downloads | M-Lab | [1] |
| Queue | 1400–1600 packets, drop-front; 30–60 ms queueing delay variation | UDP bursts, Karlstad + Malaga | [3] |
| Reconfiguration period | 15 s, globally synchronised; RTT and throughput shift between periods, stable within a period; brief sub-second disruptions at boundaries | dishes in 2 countries | [1] |
| Boundary spike (UL) | first 140 ms of each period: peak +74 ms above period mean; last 75 ms: smaller secondary rise | 500 Hz bidirectional OWD probes, Aalborg (57°N), three ~8 h datasets | Casparsen et al. [4] |
| UL vs DL boundary sensitivity | uplink OWD more affected by 15 s cycles; >500 M probes over 10 days | Karlstad | Garcia et al. [5] (abstract only; full text paywalled) |
| Loss at boundaries | 30.73 % of reallocation periods have a 1 s window with loss >2 %, vs 4.32 % of normal periods; in those windows loss ×16, latency ×4.49, bandwidth −24 % | 1-week UDP livecast trace | BAROC [6] |
| Background loss | best countries 0.23–0.24 %; most 1–4 %; Philippines 18.27 % | RIPE Atlas ICMP, 2022–2024 | Bajpai et al. [7] |
| Loss under load | 4–8 % at 75th percentile of M-Lab downloads | TCP | [1] |
| Outages | 3,755 events in 3 months (≈1.7 h⁻¹); ≈80 % chance of ≥1 outage per 60 min; 87.33 % <2 s, 2.73 % >5 s, max 31 s; +150 % during evening peak | Starlink dish telemetry | Robust Live Streaming [8] |
| Weather | rain: UL throughput −52 %, DL −38 %, "no noticeable impact on RTT" | Oulu, FHP terminal | [9] |
| Operator figure | median peak-hour latency 25.7 ms (US, mid-2025); goal 20 ms | Starlink | [10] |

Distribution shape: Casparsen et al. found that a single Gaussian fits the intra-period core only for short horizons, while 2–3 component Gaussian mixtures track the 99th percentile well [4]. No paper tests log-normal against gamma on Starlink specifically. **No finding** on Starlink packet reordering rates.

### 1.2 LEO-to-LEO ISL relay paths

Only user-terminal data exist. Users who depend on ISL routing (e.g., Nigeria) see RTT 2–5× the median about one third of the time, and ≥70 % of customers see sustained latency spikes daily [11]. Pan et al. note ISL paths show "considerable stage effect" (different hop counts to the same PoP) [2]. Hardware for a third-party satellite: SpaceX mini laser terminal, 25 Gbps at up to 4,000 km, flight-tested Aug 2025; first partner satellite planned Q1 2027 [12]. **No finding** on measured latency for a third-party satellite relayed over Starlink ISLs. Propagation only: 4,000 km ISL = 13.3 ms; each intra-mesh hop of 1,000–2,000 km adds 3.3–6.7 ms `[own computation]`.

### 1.3 GEO relay (TDRSS class)

| Quantity | Value | Source |
|---|---|---|
| ISS Ku-band via TDRSS RTT | 600 ms, 500 Mbps max downlink | NASA HDTN ISS testing [13] |
| Latency range | "approximately 0.6 seconds to 1 second"; coverage predictable but not continuous | NASA DTN for ISS [14] |
| Coverage | >99 % of every orbit since Guam terminal closed the zone of exclusion (1998) | NASA [15] |
| Ku handover loss of signal | ≈30 s to 1 min per TDRS handover `[secondary source]` | [16] |
| Allowable ISS DTN bandwidth | 90 Mbps downlink (typically ~30), ~20 Mbps uplink | [14] |
| Commercial L-band alternative (IDRS) | >200 kbps, up to 99 % of orbit, "latency of under two seconds" (vendor claim) | Addvalue/Viasat [17] |

Geometry check: LEO→GEO 36,000–44,000 km plus GEO→ground ~38,000 km gives 0.25–0.27 s one-way, so the 600 ms RTT is ~90 % propagation `[own computation]`.

### 1.4 Direct ground-station passes (550 km SSO)

Computed with `sgp4` (WGS72, `sgp4init`, i = 97.6°, e = 0.001, 7 days, 5 s steps, TEME→ECEF by GMST rotation) `[own computation, script in §3]`:

| Station | Mask | Passes/day | Mean pass (min) | Max pass | Coverage | Mean gap (min) | Max gap (min) |
|---|---|---|---|---|---|---|---|
| Svalbard 78.2°N | 5° | 13.0 | 7.9 | 9.6 | 7.2 % | 103 | 380 |
| Svalbard | 10° | 10.7 | 6.7 | 7.8 | 5.0 % | 128 | 572 |
| Troll 72°S | 5° | 10.9 | 8.3 | 9.8 | 6.2 % | 120 | 573 |
| Inuvik 68.4°N | 5° | 10.3 | 7.7 | 9.6 | 5.5 % | 126 | 576 |
| Punta Arenas 53°S | 5° | 5.7 | 7.3 | 9.7 | 2.9 % | 249 | 677 |
| Seoul 37.5°N | 5° | 4.0 | 7.4 | 9.5 | 2.0 % | 340 | 686 |
| Singapore 1.3°N | 5° | 3.1 | 7.3 | 9.5 | 1.6 % | 439 | 705 |
| Svalbard+Troll+Inuvik+Punta Arenas | 5° | 33.4 | 9.2 | — | 21.3 % | 34 (median 35) | 85 |

Slant range at 5° elevation is 2,206 km (7.36 ms one-way), 1,816 km at 10° (6.06 ms), 550 km at zenith (1.83 ms); orbital period 95.6 min. An independent NASA study of a 550 km CubeSat and one mid-latitude station reports 10.7 min mean contact and 7.2 contacts/day `[search-snippet only, not verified against full text]` [18]. Conclusion: even a four-station polar network gives ≈21 % duty cycle with 35 min median gaps. Direct-GS is a burst-download path, not a teleop path.

## 2. Building the emulator on macOS

**Kernel path (pf + dummynet) is unsuitable.** `dnctl` supports fixed `delay`, Bernoulli `plr`, `bw` and `queue` only; delay is "rounded to the next multiple of the clock tick (typically 10 ms)" [19]. On this machine `sysctl kern.clockrate` reports `hz = 100` (macOS 26.2), so the tick is 10 ms `[own measurement]`. It needs `sudo pfctl -E` and anchors [20]; no jitter distribution, no burst model, no periodic outage. Use it only as an optional cross-check.

**User-space proxy (recommended).** One `asyncio` `DatagramProtocol` per direction; on receive, sample a delay, push `(release_ns, seq, payload)` on a `heapq`, drain with a single timer. Measured on this M4 Pro `[own measurement]`:

| Primitive | p50 | p99 |
|---|---|---|
| UDP loopback echo RTT (200 B) | 22 µs | 70 µs |
| `asyncio.sleep(1 ms)` overshoot | 0.15 ms | 0.19 ms |
| `time.sleep(1 ms)` overshoot | 0.26 ms | 0.29 ms |

Sub-0.3 ms timer error against 20–50 ms link delays is adequate. Release timestamps must use `time.monotonic_ns()` (`mach_absolute_time`, non-adjustable, 41.7 ns resolution) [21].

**Delay model** (per direction, per packet i in period p):

```
d_i = base_dir + shift_p + J_i + spike(t_i mod 15 s)
```

- `base_dir`: asymmetric constants (UL > DL) [1].
- `shift_p ~ U(−5, +5) ms`, redrawn every 15 s: RTT "typically remains relatively consistent within an interval, but fluctuates between intervals" [1]. Magnitude `[unverified]`.
- `J_i`: right-skewed jitter. Neither log-normal nor gamma is validated on Starlink; the only fit reported is a 2–3 component Gaussian mixture [4]. Decision: use shifted log-normal parametrised by mean and SD (matches the 52 ± 14 / 35 ± 11 ms moments [1] while keeping a tail) and keep a `dist` switch (`lognormal|gamma|gmm`) so the hypothesis track can A/B it. Add AR(1) correlation ρ = 0.25 on `J_i` (netem uses the same correlation idea [22]).
- `spike(τ)`: for τ < 140 ms, add a decaying pulse peaking at +74 ms; for τ > 14.925 s, a +20 ms `[unverified]` bump [4]. Spike applies fully to UL, half to DL [5, abstract].
- Reordering: emerges from independent per-packet delay; add a `fifo=True` option that clamps `release ≥ previous release` when reordering is not wanted. Receiver logic keys on sequence numbers regardless.

**Loss model: Gilbert-Elliott** with states G/B, transition p (G→B) and r (B→G), loss prob 1−k in G, 1−h in B. Stationary π_B = p/(p+r); mean loss = (1−k)π_G + (1−h)π_B; mean burst length = 1/r; given target loss p_E and k = 1: p = p_E·r/(h − p_E) [23]. Layer a deterministic 15-s trigger on top: with probability 0.31 a period is "anomalous" and the chain is forced into B for the first 1 s [6].

**Outage model**: Poisson arrivals at 1.7 h⁻¹ (×2.5 during a configurable "peak" window); duration mixture: 87 % U(0.3, 2) s, 10 % U(2, 5) s, 3 % U(5, 31) s [8]. All packets dropped during an outage.

**Clocks and one-way delay.** Everything runs on one host, so the sender writes `time.monotonic_ns()` into the header and the receiver computes exact OWD; no synchronisation problem exists in the testbed. For a future two-host run: the RTT/2 assumption is wrong by ≈8 ms on Starlink because UL and DL differ (52 vs 35 ms) [1]; estimate OWD with the RFC 7679 metric [24] plus Moon–Skelly–Towsley linear-programming skew removal, which is O(N) and keeps skew-corrected delays positive [25].

## 3. TLE-based visibility (implementation sketch)

```python
from sgp4.api import Satrec, WGS72, jday          # sgp4>=2.27 already in pyproject
import math, numpy as np
RE, MU, C = 6378.137, 398600.4418, 299792.458
a = RE + 550.0; n = math.sqrt(MU / a**3) * 60       # rad/min
sat = Satrec(); sat.sgp4init(WGS72, 'i', 99999, 25000.0, 1e-4, 0, 0, 0.001, 0, math.radians(97.6), 0, n, 0, 0)
def gmst(jd, fr):                                  # IAU-82 GMST, deg -> rad
    T = (jd + fr - 2451545.0) / 36525.0
    return math.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0 + fr) + 3.87933e-4 * T * T) % 360)
# r_teme from sat.sgp4_array(jd, fr); rotate by -gmst about z to get ECEF; elevation = asin(dot(d, up)/|d|)
# pass = contiguous samples with elevation >= mask; one-way delay = |d| / C
```

Full script (stations, 7-day run, table above) is 60 lines and runs in ~1 s. Replace the synthetic element set with a real TLE via `Satrec.twoline2rv` when a rideshare orbit is chosen. The GMST-only rotation ignores polar motion and nutation (<1 km error), which is irrelevant for pass statistics `[own computation]`.

## 4. Proposed link profiles

All values are one-way per direction unless noted. `L/N(m, s)` = log-normal with mean m, SD s; GE = Gilbert-Elliott (p, r, 1−k, 1−h).

| Parameter | P0 zero-latency | P1 direct-GS | P2 LEO-relay (Starlink-ISL class) | P3 GEO-relay (TDRSS class) |
|---|---|---|---|---|
| Base delay UL / DL | 0 / 0 (loopback 22 µs measured) | propagation from slant range each tick, 1.8–7.4 ms `[own]` + backhaul 10 ms `[unverified]` | 30 / 18 ms (≈50 ms RTT; bent-pipe 40 ms RTT [1] + one 4,000 km ISL hop 13 ms `[own]`) | 300 / 300 ms (600 ms RTT [13]) + ±13 ms orbital drift `[own]` |
| Jitter | none | Gaussian σ = 0.5 ms `[unverified]` | L/N(0, 14) UL, L/N(0, 11) DL [1], AR(1) ρ = 0.25 `[unverified]` | Gaussian σ = 2 ms `[unverified]` |
| 15-s structure | none | none | shift_p U(±5 ms); UL spike +74 ms over 140 ms, end bump 75 ms [4] | none |
| Loss | 0 | GE(0.001, 0.2, 0, 0.3) → 0.15 % `[unverified]`; ×10 when elevation <10° `[unverified]` | GE(0.00144, 0.2, 0, 0.3) → 0.5 % background [7,23]; 31 % of periods forced into B for 1 s [6] | GE(0.0005, 0.2, 0, 0.3) → 0.07 % `[unverified]` |
| Outages | none | link only during passes: 7–9 min contacts, 35 min median gap (4 polar stations) `[own]` | Poisson 1.7 h⁻¹; 87 % <2 s, 3 % 5–31 s [8] | handover LOS 30–60 s [16], every ~45 min `[unverified]` |
| Bandwidth cap | none | 100 Mbps `[unverified]` | 25 Gbps ISL [12]; cap at 50 Mbps to force video budgeting `[design choice]` | 20 Mbps up / 90 Mbps down [14] |
| Reordering | none | fifo | allowed (independent delays) | fifo |

Acceptance-relevant RTT medians: P0 ≈0, P1 ≈25–35 ms while in contact, P2 ≈50 ms with 15-s spikes to ≈125 ms, P3 ≈600 ms. P2 without the spike/loss layers is a useful "P2-clean" control for the hypothesis track.

## Implication for our design

The testbed's default operating profile must be P2 (LEO relay): direct GS gives ≈21 % duty cycle even with four polar stations, and GEO relay costs 600 ms RTT, which is outside any plausible ≥80 %-of-baseline teleop band. P2's median 50 ms RTT is benign, but its structure is not: every 15 s the uplink sees a +74 ms spike for 140 ms, ~31 % of periods carry a ≥2 % loss burst, and ~1.7 outages per hour last 0.3–31 s. That means the onboard command buffer and hold/retract logic must be tuned to a 15-s deterministic clock plus a heavy-tailed outage distribution, not to Gaussian jitter. Build the emulator as a user-space `asyncio` proxy on `time.monotonic_ns()` (dummynet is 10 ms-quantised on this Mac and has no burst or period model), expose `dist`, GE and spike parameters as one dataclass per profile so the log-normal-vs-gamma-vs-GMM question and the spike magnitude can be swept as hypotheses, and log true OWD from the shared clock so every experiment reports the full success-vs-latency curve.

## Sources

1. Mohan et al., "A Multifaceted Look at Starlink Performance," WWW 2024. https://www.nitindermohan.com/documents/2024/pubs/starlinkWWW2024.pdf (also https://arxiv.org/pdf/2310.09242)
2. Pan, Zhao, Cai, "Measuring a Low-Earth-Orbit Satellite Network." https://arxiv.org/pdf/2307.06863
3. "Characterizing the Configuration of Starlink Queuing." https://arxiv.org/html/2605.27717
4. Casparsen et al., "Statistical Characterization and Prediction of E2E Latency over LEO Satellite Networks." https://arxiv.org/pdf/2601.08439
5. Garcia, Sundberg, Brunstrom, "A Detailed Characterization of Starlink One-way Delay," LEO-NET 2025. https://dl.acm.org/doi/10.1145/3748749.3749090 (abstract via https://www.researchgate.net/publication/393884400_A_Detailed_Characterization_of_Starlink_One-way_Delay)
6. "BAROC: Concealing Packet Losses in LSNs with Bimodal Behavior Awareness for Livecast Ingestion." https://arxiv.org/pdf/2504.16322
7. Bajpai et al., "Breaking Through the Clouds: Performance Insights into Starlink's Latency and Packet Loss." https://vaibhavbajpai.com/documents/papers/proceedings/starlink-networking-2025.pdf
8. "Robust Live Streaming over LEO Satellite Constellations: Measurement, Analysis, and Handover-Aware Adaptation," ACM MM 2024. https://arxiv.org/pdf/2508.13402
9. "Impact of Weather on Satellite Communication: Evaluating Starlink Resilience." https://arxiv.org/abs/2505.04772
10. The Register on Starlink's July 2025 network update. https://www.theregister.com/2025/07/16/starlink_network_update/ ; https://starlink.com/updates/network-update
11. Izhikevich et al., "Democratizing LEO Satellite Network Measurement," summarised at https://blog.apnic.net/2024/07/24/democratizing-leo-satellite-network-measurement/ (paper https://arxiv.org/pdf/2306.07469)
12. SpaceX mini laser terminal, 25 Gbps / 4,000 km. https://gcn.com/4-000-kilometer-laser-link-between/21373/ ; Muon Space adoption https://www.aol.com/articles/first-partner-stars-muon-space-224100987.html
13. NASA GRC, "Advances in High-rate Delay Tolerant Networking On-board the ISS," 2024. https://ntrs.nasa.gov/api/citations/20240007078/downloads/HDTN_ISS_Testing_2024.pdf
14. NASA, "Delay/Disruption Tolerant Networking for the International Space Station." https://ntrs.nasa.gov/api/citations/20160014037/downloads/20160014037.pdf
15. NASA, "TDRS: An Era of Continuous Space Communications." https://www.nasa.gov/missions/tdrs/tdrs-an-era-of-continuous-space-communications/
16. ISS Ku-band handover description (secondary). https://orbitalxploration.com/how-iss-communication-systems-use-ground-station-networks-to-stay-connected
17. Addvalue/Viasat IDRS. https://www.webwire.com/ViewPressRel.asp?aId=359450 ; https://www.addvaluetech.com/inter-satellite-data-relay-system-idrs/
18. NASA, "S-band Network Analysis and Strategies for LEO Multi-CubeSat Science Missions." https://ntrs.nasa.gov/api/citations/20210022422/downloads/S-band%20Network%20Analysis%20and%20Strategies%20for%20LEO%20Multi-CubeSat%20Science%20Missions_15Oct21c_final.pdf
19. dnctl(8) man page (macOS). https://www.manpagez.com/man/8/dnctl/ and local `man dnctl`
20. pf/dummynet on macOS walkthrough. https://blog.leiy.me/post/bw-throttling-on-mac/
21. Python `time` module docs. https://docs.python.org/3/library/time.html
22. tc-netem(8), delay distributions and correlation. https://man7.org/linux/man-pages/man8/tc-netem.8.html
23. Haßlinger & Hohlfeld, "The Gilbert-Elliott Model for Packet Loss in Real Time Services on the Internet," MMB 2008. https://people.computing.clemson.edu/~jmarty/projects/lowLatencyNetworking/papers/APPFEC/GEModelForLossinTheRTInternet.pdf
24. RFC 7679, "A One-Way Delay Metric for IP Performance Metrics." https://www.rfc-editor.org/rfc/rfc7679
25. Moon, Skelly, Towsley, "Estimation and Removal of Clock Skew from Network Delay Measurements," INFOCOM 1999. https://web.cs.umass.edu/publication/docs/1998/UM-CS-1998-043.pdf
26. Own computations: sgp4 pass script and loopback/timer measurements on M4 Pro, macOS 26.2, `sysctl kern.clockrate` → `hz = 100` (2026-09-12).
