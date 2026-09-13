# LEO satellite-to-ground link options for continuous low-latency teleop (buyable in 2026)

Scope: a small payload in a ~550 km orbit, 4 operators, each needing a live video downlink and a command uplink, target RTT < 150 ms, continuous coverage. Numbers marked `[computed]` come from a 30-day circular-orbit simulation run for this document (stdlib Python: Keplerian motion + J2 nodal precession at sun-synchronous inclination, Earth rotation, 5 s steps; not committed). `[secondary]` = trade press or vendor comparison site, not a primary source. `[unverified]` = no source found.

## 1. Physics floor and where the rest of the latency comes from

| Path segment | One-way delay | Basis |
|---|---|---|
| 550 km sat → ground, zenith | 1.8 ms | 550 km slant range `[computed]` |
| 550 km sat → ground, 10° elevation | 6.1 ms | 1,815 km slant range `[computed]` |
| 550 km sat → ground, 5° elevation | 7.4 ms | 2,205 km slant range `[computed]` |
| One laser ISL hop, 1,000 / 2,000 / 4,000 km | 3.3 / 6.7 / 13.3 ms | free-space `[computed]` |
| Starlink gateway → PoP (terrestrial) | ≈5 ms (7–8 ms US/Canada) | Mohan et al. WWW'24 traceroutes |
| LEO → GEO relay → ground | 237–278 ms | 35,236–41,585 km + 35,786–41,673 km `[computed]` |

Measured end-to-end references:
- Starlink consumer terminals, bent-pipe (terminal → sat → gateway → PoP): 36–48 ms RTT, median ≈40 ms across countries; US peak-hour median 25.7 ms (Starlink, June 2025), with <1% of US measurements >55 ms.
- Starlink reconfigures user↔satellite paths every 15 s; handover adds 30–50 ms spikes (worst case 30→80 ms), inter-RTT jitter ≈6.7 ms, long-run loss ≈1% (Huston, APNIC/CircleID, Aug 2023–Mar 2024). A 2026 study reports spikes of ≈140 ms at cycle start and ≈75 ms at cycle end, 99th-percentile prediction error <50 ms.
- ISLs to a distant gateway can raise latency up to 5× vs a bent pipe to a nearby gateway (LEO-NET'24 gateway-placement study).
- ISS Ku-band via TDRS: NASA emulates it at 500 Mbps down, 600 ms RTT; ground control of Canadarm2 copes with 0.3–0.5 s, "which prevents direct teleoperation".

Implication: the propagation floor for a direct or Starlink-relayed link is 4–30 ms RTT. Everything above that is modem framing, ISL hop count, gateway/PoP, and the terrestrial path to the operator (a further 5–50 ms one-way depending on where operators sit `[unverified]`). Any GEO hop puts the floor at ≥474 ms RTT and is disqualifying.

## 2. Option comparison

| Option | One-way / RTT | Coverage per day | Uplink / downlink | Jitter, outages | Cost class | Third-party access (2026) |
|---|---|---|---|---|---|---|
| (a) Ground station passes | 2–7 ms prop + backhaul; RTT ≈15–60 ms during pass `[estimate]` | 1–7 % per station; passes 6–8 min | S-band up (kbps–Mbps); X/Ka down (hundreds Mbps–Gbps) | Hard outages between passes; 90–100 min gaps at mid-latitude | $3–22 / antenna-min (AWS) `[secondary]`; others quote-only | Open, self-serve |
| (b1) Starlink mini-laser relay | est. 15–45 ms one-way, 30–90 ms RTT `[estimate]`; "milliseconds" (Muon/SpaceX) | Near-continuous (mesh; 7,800+ sats) | 25 Gbps ISL both ways at ≤4,000 km; ground-side allocation unpublished | 15 s reconfig spikes 30–140 ms; ≈1% loss (consumer data) | Unpublished; bespoke contracts | Contractable now; first third-party hardware on orbit ≈mid-2027 (Starcloud, Muon Q1 2027) |
| (b2) Kepler optical relay | "low-latency"; "sub-second" `[secondary]`; no ms figure published | Not continuous with 10 sats + 10 OGS `[estimate]` | Up to 100 Gbps optical (future); SDA-compatible ISL | Optical ground stations are weather-limited `[unverified]` | Unpublished | Commercial service since 24 Aug 2026 |
| (b3) Amazon Leo (Kuiper) | Not offered | — | 100 Gbps ISL demo | — | — | NASA CSP demo of a third-party LEO sat planned; no commercial relay product |
| (b4) Telesat Lightspeed | Not offered | — | — | — | — | Service 2028; optical relay demo with Planet in 2027 only |
| (c) GEO relay (TDRS/NSN, EDRS, Viasat InRange) | ≥237 ms one-way, ≥474 ms RTT `[computed]`; ISS Ku 600 ms RTT | TDRS ≈95% of LEO orbit; EDRS ~hemispheric | TDRS Ka 50 Mbps fwd / 600–1,200 Mbps rtn; EDRS 1.8 Gbps rtn; InRange L-band low rate `[unverified]` | Stable when locked | Institutional | TDRS closed to new missions since 8 Nov 2024; EDRS Copernicus-only in practice; InRange = launch telemetry |
| (d) Iridium Certus from LEO | Message delivery: 90% of telemetry within 30 min, 70% of commands within 15 min (MiniCarb, 500 km) | Intermittent | 22 kbps up / 88 kbps down (Certus 9770) | Doppler ≈37.5 kHz; link only inside <2,000 km | Cheap: 185 g, 3.5 W modem | Open (COTS) |
| (e) Hosted payload, ISS Bartolomeo | ISS Ku via TDRS: 600 ms RTT | Ku route 70–90 % of orbit | 0.1 Mbit/s real-time per slot; ≈1 GB/day via Columbus Ku; up to 10 Gbit/s optical burst | Real-time "when available" | €0.3–3.5 M / year | Open commercial service |

### (a) Ground station passes at 550 km `[computed]`

| Station | Min elevation | Passes/day | Mean pass | Max pass | Coverage |
|---|---|---|---|---|---|
| Svalbard (78°N) | 5° / 10° | 13.3 / 10.9 | 8.1 / 6.8 min | 9.8 / 7.9 min | 7.4 % / 5.2 % |
| Mid-latitude (45°) | 5° / 10° | 4.6 / 3.8 | 7.7 / 6.1 min | 9.8 / 7.9 min | 2.5 % / 1.6 % |
| Equator | 5° / 10° | 3.1 / 2.5 | 7.6 / 6.3 min | 9.8 / 7.8 min | 1.7 % / 1.1 % |

Networks: KSAT 135 antennas at 26 sites (S up, X/Ka down, 145,000 contacts/month, 99.75% historical availability); Leaf Space S/X/Ka, per-minute pay-as-you-go; ATLAS 50+ antennas at 34+ sites; Viasat RTE S/X/Ka on six continents, 15–6,400 Mbps receivers, available via Azure Orbital; AWS Ground Station S up, X down, billed per minute rounded up, narrowband <40 MHz vs wideband. Even a polar site covers ≈7% of the day; a global multi-site network cannot approach continuity from 550 km because each pass is bounded at ≈10 min and the ground track revisits any site only a few times per day. Ground stations are the right tool for bulk data and commissioning, not for continuous teleop.

### (b1) Starlink mini laser (the only near-continuous, sub-150 ms candidate)

Facts: SpaceX announced a "mini laser" for third-party satellites (25 Gbps at up to 4,000 km, faster at shorter range), tested on orbit on a satellite launched with Starlink G10-20 (Aug 2025). Muon Space (announced 21 Oct 2025) is the first outside customer; first Starlink-connected Halo launches Q1 2027. Starcloud (26 May 2026) ordered 50+ terminals for 25+ satellites, two per spacecraft, first hardware on orbit within a year. SpaceX's stated benefit is "persistently connected through our in-space laser mesh"; Muon quotes "milliseconds from orbit to ground". No pricing, terminal mass/power, ground-side throughput allocation, or measured latency has been published `[unverified]`. Starlink satellites carry three optical terminals at up to 200 Gbps per link; the network has 100+ US gateways.

Latency estimate for our satellite: 0–13 ms (our ISL) + 1–3 mesh hops (3–13 ms each) + gateway downlink (2–7 ms) + gateway→PoP (≈5 ms) + PoP→operator. One-way 15–45 ms, RTT 30–90 ms `[estimate]`. This sits below 150 ms with margin, but the consumer-side data say to plan for 15 s periodic spikes of 30–140 ms and ≈1% loss. Two terminals per spacecraft (Starcloud's configuration) is the obvious way to keep one link up while the other re-acquires.

### (b2) Kepler

10 × 300 kg satellites launched 11 Jan 2026 into SSO (altitude not published `[unverified]`); on-orbit compute commissioned 16 Mar 2026; commercial service declared 24 Aug 2026 with 33 satellites launched to date and "more than 10 optical ground stations". Customer satellites need an SDA-compatible optical terminal, or fly as a hosted payload on a Kepler bus. Kepler's published wording is "low-latency" and "real-time"; the "sub-second" figure appears only in trade press. With ~10–30 satellites in SSO planes, coverage of a third-party satellite in a different plane is intermittent; continuous coverage would need the 2028 constellation. Optical ground stations add weather outages that RF gateways do not.

### (c) GEO relay: no finding beyond disqualification

TDRS is not onboarding new missions since 8 Nov 2024 and serves existing users until the mid-2030s; NASA plans to buy commercial relay from ~2031. EDRS relays Sentinel data at 600 Mbit/s (1.8 Gbit/s capable) with delivery "less than 20 minutes" from capture to analyst; no third-party ms-class service. Viasat InRange/HaloNet is an L-band launch-telemetry relay (flight-tested on New Glenn NG-2, 13 Nov 2025); it is GEO, so ≥474 ms RTT. All three fail the target on propagation alone.

### (d) Iridium: TT&C heartbeat only

MiniCarb (500 km) delivered 90% of telemetry within 30 min and 70% of commands within 15 min using SBD; the paper's own conclusion is "semi-real-time". Certus 9770: 22/88 kbps, 185 g, 3.5 W, 12 VDC. Useful as an out-of-band safe-mode channel, not a control loop.

### (e) Hosted payload

Bartolomeo (ISS): 0.1 Mbit/s real-time per slot, Columbus Ku route 70–90% availability, ISS Ku RTT 600 ms; €300k–3.5M per year. Fails latency. A hosted slot on a Muon Halo, Starcloud or Kepler bus inherits that bus's relay link and is effectively option (b) without owning the spacecraft; terms unpublished `[unverified]`.

## 3. Ranked recommendation

1. **Starlink mini-laser relay, two terminals, contract in 2026 for a 2027 flight.** Only option with continuous coverage and an estimated 30–90 ms RTT. Video for 4 operators (≈4 × 2–4 Mbps) and command uplink (≈100 kbps) are negligible against a 25 Gbps link; the real limit is the unpublished ground-side allocation. Design the controller for 15 s periodic spikes to ~150 ms and ≈1% loss.
2. **Kepler optical relay as second path.** Available now, SDA-standard terminal, but intermittent coverage and no published latency. Worth a quote and a coverage simulation once the altitude is known.
3. **Ground station network (KSAT/Leaf/AWS) for commissioning, bulk downlink and fallback teleop.** 6–8 min windows, 4–13 passes/day per site, 15–60 ms RTT during a pass. Use it to run the "short-session" experiments and to validate the link emulator against a real pass.
4. **Iridium Certus** as safe-mode/heartbeat only.
5. GEO relay and ISS hosting: rejected on latency floor.

## Implication for our design

The testbed's link emulator should model two regimes, not one: a relay regime with 30–90 ms RTT, ≈7 ms jitter, ≈1% loss and a 15 s periodic spike of 30–140 ms lasting ~0.1–0.2 s; and a ground-pass regime with 15–60 ms RTT, near-zero loss, and hard outages of 80–100 min between 6–8 min windows. The onboard safety logic (hold/retract on timeout) must survive both the periodic 100-ms-class spike without triggering and the multi-second dropout with triggering, so the timeout threshold sits around 300–500 ms. The bus must reserve mass, power and pointing for two optical terminals (figures unpublished, so budget conservatively) and a low-rate S-band or Iridium heartbeat. Hypotheses about onboard compute should be scored against the relay regime, because that is the only regime in which continuous teleop exists at all.

## Sources

- https://gcn.com/4-000-kilometer-laser-link-between/21373/
- https://www.datacenterdynamics.com/en/news/spacex-developing-laser-to-connect-starlink-satellites-with-third-party-satellites/
- https://satnews.com/2025/10/29/muon-space-integrating-spacexs-starlink-mini-space-lasers-into-halo-satellite-platform/
- https://www.muonspace.com/starlink-lasers-halo/
- https://finance.yahoo.com/sectors/technology/articles/starcloud-integrate-spacex-starlink-mini-170000947.html
- https://www.businesswire.com/news/home/20260526670395/en/Starcloud-to-Integrate-SpaceXs-Starlink-Mini-Lasers-Into-Its-Orbital-Data-Center-Constellation
- https://starlink.com/updates/network-update
- https://www.theregister.com/2025/07/16/starlink_network_update/
- https://www.nitindermohan.com/documents/2024/pubs/starlinkWWW2024.pdf
- https://circleid.com/posts/20240517-transport-protocol-perspective-on-optimizing-starlink-performance
- https://arxiv.org/abs/2601.08439
- https://dl.acm.org/doi/10.1145/3697253.3697269
- https://kepler.space/kepler-successfully-launches-first-tranche-of-optical-relay-satellites/
- https://kepler.space/kepler-delivers-optical-infrastructure-for-real-time-space-operations/
- https://spaceq.ca/kepler-communications-to-launch-10-optical-data-relay-satellites-in-january-2026/
- https://spaceq.ca/keplers-real-time-next-generation-optical-data-relay-network-starts-commercial-service/
- https://satnews.com/2026/03/17/kepler-commissions-first-nvidia-powered-cloud-infrastructure-across-optical-constellation/
- https://spacenews.com/amazon-gears-up-for-nasa-satellite-data-relay-demonstration/
- https://www.nasa.gov/technology/space-comms/nasas-push-toward-commercial-space-communications-gains-momentum/
- https://www.satellitetoday.com/finance/2026/03/17/telesats-lightspeed-service-launch-slips-to-2028/
- https://www.satellitetoday.com/government-military/2024/10/16/nasas-tdrs-system-to-stop-onboarding-new-missions-in-november/
- https://www.nasa.gov/technology/space-comms/what-is-the-near-space-network/
- https://www.eoportal.org/satellite-missions/tdrs
- https://ntrs.nasa.gov/api/citations/20240007078/downloads/HDTN_ISS_Testing_2024.pdf
- https://arxiv.org/pdf/2002.10594
- https://resilience.esa.int/archives/news/space-data-relay-system-shows-its-speed
- https://www.esa.int/Applications/Connectivity_and_Secure_Communications/EDRS/Europe_s_SpaceDataHighway_relays_first_Sentinel-1_images_via_laser
- https://www.viasat.com/news/latest-news/government/2023/launch-vehicle-telemetry-expected-to-become-commercially-available-faster-as-inrange-moves-to-market/
- https://www.viasat.com/news/latest-news/government/2025/viasat-newglenn2-nasa-launch-telemtry-relay/
- https://jossonline.com/wp-content/uploads/2021/03/Final-Simms-Lessons-Learned-Using-Iridium-to-Communicate-with-a-CubeSat-in-Low-Earth-Orbit-2.pdf
- https://orizonmobile.com/wp-content/uploads/2023/09/Iridium-Certus-9770-Datasheet.pdf
- https://www.eoportal.org/satellite-missions/iss-bartolomeo
- https://www.ksat.no/ground-network-services/ksatlite/
- https://leaf.space/faq/
- https://atlasspace.com/
- https://investors.viasat.com/news-releases/news-release-details/viasat-real-time-earth-ground-service-available-via-microsoft-azure-orbital
- https://docs.aws.amazon.com/ground-station/latest/ug/contacts.billing.html
- https://aws.amazon.com/ground-station/pricing/
- https://www.observationdata.com/providers/ground-station-services/
