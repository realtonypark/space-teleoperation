# Hardware landscape: rideshare small satellite carrying 4–8 teleoperated arms (buyable 2026)

> First-wave research note, retained for traceability. The [second-wave evidence review](second_wave_evidence.md) corrects consequential source claims; the [current synthesis](SYNTHESIS.md) governs decisions.

Scope: what can be bought in 2026 for a rideshare-launched satellite with 4–8 simple robot arms inside an enclosed volume, continuous video down, low-rate command up. Numbers carry a source or `[unverified]`; arithmetic I did myself is marked `[derived]`. Research date: 2026-09-12.

## 1. Bus class

| Class | Product | Payload mass | Payload volume | Orbit-average payload power | Rough cost | TRL | Source |
|---|---|---|---|---|---|---|---|
| 12U | NanoAvionics M12P | 17–18 kg | 8–9U | 26–33 W (sun-tracking) | n/p; 7-month lead | 9 | [1] |
| 12U | EnduroSat 12U | 14–16 kg | 9U (197×197×225 mm) | 20–45 W | n/p | 9 | [2] |
| 16U | EnduroSat 16U | 24 kg | 10.3U (218×218×254 mm) | 25–60 W | n/p; "in orbit in 6 months" | 9 | [3] |
| 16U | NanoAvionics M16P | 21.5–22 kg | 13U | 18–25 W | n/p | 9 | [4] |
| ESPA | Apex LEO Aries | 100 kg on SpaceX rideshare (150 max) | 865×1170×550 mm | 175 W EOL (500 W option) | $3.5–9.5M (secondary) | 9 (first flight 2024) | [5][6] |
| ESPA | EnduroSat FRAME S | 70 kg | n/p | 95–342 W | n/p | [unverified] | [7] |
| ESPA | York S-CLASS | 85 kg+ | 24"×24" stowed | ~100 W (secondary) | ~$9.4M SDA [unverified] | 9 | [8] |
| ESPA | Blue Canyon X-SAT Venus | 90 kg | 20.5×16.4×27.0 in | 192/384 W array | n/p | 9 | [9] |
| ESPA | Terran Orbital Nebula | 130 kg | 82×58×39 cm | 1 kW array | n/p | 9 | [10] |

Launch: SpaceX rideshare 2026 is $350k for 50 kg then $7,000/kg [11]; a 150 kg ESPA sat is ~$1.05M `[derived]`. Deployer limits (Exolaunch EXOpod Nova): 12U ≤26 kg, 16U ≤36 kg [12]. ESPA port limits: standard 15" 257 kg, Grande 700 kg [13].

**Call:** ESPA-class. Payload demand `[derived]`: 4–8 COTS arms 30–80 W peak `[unverified]`, compute 15–25 W, 4 cameras ~4 W, X-band 12 W, optical relay terminal 40–70 W, heaters, gives 100–190 W continuous. That is 2–5× a 16U's 25–60 W orbit-average [3] and 55–100% of Aries' 175 W [5]. A 16U works only for a 2-arm, DTE-only demo.

## 2. Pressurized enclosure

Precedents at 1 atm: GeneSat-1 (3U, sealed cylinder, 35 °C) [14]; O/OREOS and PharmaSat "hermetically sealed at one atmosphere" [15]; BioSentinel 6U with a 4U sealed 1-atm BioSensor [16]. Bion-M No.2 landed 19 Sep 2025 after 30 days with 75 mice (6,300 kg, not rideshare-class) [17]. Varda W-series capsule is 120 kg, ~0.9 m, "tens of kg" payload, >100 W; pressurization `[unverified]` [18]. Dragon 2 trunk is unpressurized (37 m³) [19]. Bishop airlock 3.99 m³ hosted GITAI S1 [20].

Feasibility on our bus: SpaceX PUG v11 treats a sealed 1-atm container as pressurized equipment: yield 1.5×MEOP, ultimate 2.0×MEOP, no proof test, all-metallic preferred [21]. Mass `[derived, Al 6061-T6 σy = 276 MPa [22], FS 2]`: hoop stress at Δp = 101 kPa is 10 MPa for r = 10 cm and 30 MPa for r = 30 cm at 1 mm wall, so minimum gauge dominates, not pressure. Cylinder L/D = 2: 30 L → 1.5 kg, 100 L → 3.4 kg, 300 L → 7.0 kg, plus 30–50% for flanges, feedthroughs, O-ring grooves. Flat boxes cost ~3× more; use a cylinder with domed ends. Leak spec precedent: ISS seal <0.0011 kg/day [23]; verification tiers 1e-9 to 1e-4 sccs [24].

Why pressurize: graphite brushes in brushed DC motors need O₂/humidity to form the commutator film and brush wear rises "several times" in vacuum [25][26]; hobby servos have no convection path and unrated grease. Inside a 1-atm cylinder, unmodified COTS arms and cameras work, with gas convection to the wall. Vacuum-rated arms (GITAI IN2, 50 kg, 60/200 W [27]) exceed the whole payload budget of a 16U.

**Call:** a 100–300 L 1-atm aluminium cylinder, 3.5–10 kg with fittings, fits Aries' 865×1170×550 mm volume [5]. On a 16U the 10.3U (11.9 L) payload volume [3] allows one ~8 L cylinder: 1–2 small arms, not 4–8.

## 3. Arms

| Arm | Actuators | DoF | Mass | Cost | Space evidence | TRL | Source |
|---|---|---|---|---|---|---|---|
| GITAI S2 | BLDC (n/p) | 2×8, 1.5 m | n/p | not public | outside ISS Jan 2024 | 7 | [28] |
| GITAI Inchworm IN2 | BLDC + harmonic | 7, 2 m | 50 kg | not public | TVAC TRL 6 Oct 2024 | 6 | [27][29] |
| Motiv xLink | n/p | 4–7 | [unverified] | "1/10th" | none flown (OSAM-2 cancelled) | [unverified] | [30] |
| Tethers KRAKEN | n/p | 7, 1 m | 5.0 kg | n/p | none flown | [unverified] | [31] |
| USNA RSat-P | steppers | 2×7, 60 cm | 3U | n/p | flew Dec 2018 | 7 | [32] |
| Astrobee perching arm | 2× Dynamixel XM430/XH430-W210 | 2 + gripper | 315 g (proto) | n/p | ISS since Jul 2019 | 9 | [33][34] |
| SO-101 | 6× Feetech STS3215 ($24 ea) | 6 | [unverified] | $199–278 kit | none | 4 | [35][36] |
| Koch v1.1 | 2× XL430 + 4× XL330 | 6 | [unverified] | ~$250 | none | 4 | [37] |
| ALOHA ViperX-300 | XM430/XM540 | 6 | 4.75 kg | $7,150 | Dynamixel X family flown on Astrobee | 4 | [38][39] |

Astrobee is the decisive precedent: stock Dynamixel X servos in an aluminium case, a hardware flip-flop cutting the driver at 80% peak current, and a bimetal thermostat per motor, because "a radiation event may cause the motor to stall" [33][34]. No TID or SEE test on any Dynamixel or Feetech servo was found `[unverified, absence]`. Environment: ~2.7 krad(Si)/yr at 550 km/51.6° behind 2.5 mm Al (model) [40]; measured 0.17–0.63 krad/yr at 480–490 km SSO behind 2.9–5.7 mm Al [41]. COTS electronics start to drift near 5 krad [42]; for a 1–2 year mission the servo MCUs sit under the threshold. Mitigation: servo bus behind a latching current limiter (µs response, ms power cycle clears SEL) [43], watchdog power cycling, and the Astrobee thermal cutoff.

**Call:** Dynamixel-X-based 6-DoF arms (Koch/ALOHA-class, XM430 for the loaded joints) inside the 1-atm cylinder. STS3215 is cheaper but has no flight lineage.

## 4. Cameras and encode latency

| Item | Product | Resolution / fps | Radiation evidence | Cost | TRL | Source |
|---|---|---|---|---|---|---|
| Sensor | Sony IMX296 (global shutter) | 1456×1088 / 60 | none; flown on a 3U hyperspectral CubeSat | ~$50 module [unverified] | 5 | [44] |
| Sensor | onsemi AR0234 (global shutter) | 1920×1200 / 120, −40…+85 °C | none | [unverified] | 4 | [45] |
| Sensor | Teledyne e2v Ruby 1.3M USV (GS) | 1280×1024 / 60 | 10 and 20 krad(Si), SEL/SEFI tested; EMs end-2025 | [unverified] | 6–7 | [46] |
| Camera | 3D PLUS 3DCM734 | 2048² / 7–16 | 10 krad; 400 mA SEL limiter | [unverified] | 9 | [47] |
| Camera | Raspberry Pi Camera v2 | 8 MP | GASPACS 2022 survived X-class flares; Astro Pi ISS 2015–2022 | ~$25 | 7 | [48][49] |

The 3DCM734 and Malin ECAM class are ≤16 fps, too slow for teleop; they are radiation references only. Encode latency, measured: Jetson NVENC 720p H.264 ≈5 ms, 1080p ≈8 ms mean, 12 ms peak [50]; Zynq UltraScale+ VCU 1080p60 HEVC 3–4 ms single, 4–6 ms with 4 streams [51]; Raspberry Pi ≈40 ms per 1080p frame [52]. Whole-camera-to-display without a space link on Jetson: 61–121 ms [53]. Bitrate: 720p at 1.2–3 Mbps per stream [54][55] → 4 streams 5–12 Mbps `[derived]`. Pre-link video budget: 16–33 ms exposure/readout + 5–12 ms encode + ~10 ms decode + display ≈ 50–90 ms `[derived]`.

**Call:** 4–8 IMX296 or AR0234 global-shutter modules on MIPI/GMSL into an NVENC-capable Jetson, 720p30, 1.5–2.5 Mbps each. No finding on in-orbit hot-pixel growth for COTS global-shutter CMOS.

## 5. Edge compute

| Product | SoC | Power | HW encode | Radiation evidence | Heritage | Cost | TRL | Source |
|---|---|---|---|---|---|---|---|---|
| Jetson Orin NX 16 GB | Orin NX | 10–40 W | 7×1080p60 H.265 | proton SEFIs (no σ published); AGX Orin TID 19 krad | Aethero Aug 2024, Planet Pelican-2+ | $999 module | 7 | [56][57][58][59] |
| Jetson Orin Nano | Orin Nano | 7–25 W | **none** (CPU only) | neutron reboot study | none confirmed | $399 | 5 | [56][60] |
| Aitech S-A2300 | Orin | [unverified] | NVENC | reports "on request" | none; "LEO-ready Q1 2026" | [unverified] | 6 | [61] |
| Spiral Blue SE-1 | Xavier NX | 7 W | NVENC | none public | orbit since 2023 | [unverified] | 8 | [62][63] |
| Xiphos Q8S | XCZU7EG | 4–25 W | no VCU | >25–30 krad, TMR supervisor, scrubbing | Q7S since 2016 incl. ISS | ~$50–100k [unverified] | 9 | [64][63] |
| Unibap iX10-101 | Ryzen V1000 + PolarFire | <40 W | AMD VCN [unverified] | 30 krad / 50 MeV SEL | first launch 2025 | [unverified] | 8 | [65][63] |
| KP Labs Leopard | ZU6/9/15EG | 7.5–40 W | no VCU | R5 lockstep, ECC, TMR boot | Intuition-1 Nov 2023 | [unverified] | 8–9 | [66] |

Ground data on Jetson: TX2 200 MeV protons produced SEFIs in every run, all needing a power cycle [67]; TX2i failed to reboot after 9.7 krad, flash implicated [68]; Jetson Nano ran past 20 krad [69]; AGX Orin limited to 19 krad(Si) [70]. Aitech S-A1760 (TX2i) observed <1 Type-2 SEFI per 158 days [63]. Zynq UltraScale+ SEL threshold is low, 0.1–5.7 MeV·cm²/mg, destructive without a current limit [71][72]. No operator publishes on-orbit Jetson reboot rates `[unverified]`. Evidence for the mitigation stack: latching current limiter per rail (TPS2553 2 µs [73]; ZES723LCL 75 krad [74]), external heartbeat watchdog power-cycling the SoC (GASPACS Pi Zero [48]), dual boot media (Unibap SafetyBoot [75]).

**Call:** Jetson Orin NX does cameras, NVENC, and stream muxing. The deterministic setpoint-interpolation and hold/retract loop runs on a separate rad-tolerant MCU or the Q8S-class supervisor that also owns the watchdog and LCLs, so a Jetson SEFI (seconds of reboot) never reaches the servo bus. Rad-tolerant Zynq boards buyable today use EG parts with no video codec, so "rad-tolerant + hardware encode" on one board does not exist off the shelf.

## 6. Radios and terminals

| Link | Up / down | One-way latency | Continuity | DC power | Mass | TRL | Source |
|---|---|---|---|---|---|---|---|
| X-band DTE (Syrlinks EWC27 / EnduroSat X-band) + S-band Rx | 256 kbps / 100–150 Mbps | in-pass ~10–100 ms [unverified] | 3–9 % of orbit per station; 20–40 % with a network [unverified] | 10–15 W Tx + 1–11 W Rx | 0.3–0.6 kg | 9 | [76][77][78] |
| Ka-band DTE (Tethers SWIFT-KTX) | — / 25–500 Mbps | as above | as above | 25 W | <0.5 kg | 7–8 | [79] |
| Kepler optical relay + SDA OCT | 2.5 Gbps both | "sub-second"; 50–300 ms [unverified] | 95 % anywhere >400 km | 40 W (3 kg OCT) / 70 W (15 kg) | 3 / 15 kg | 8–9 (service live 24 Aug 2026) | [80][81] |
| Starlink Mini Laser ("Plug and Plaser") | 25 Gbps both, ≤4,000 km | est. 10–50 ms (1.8–3.6 ms per leg + hops + PoP) [derived] | >99 % with multiple terminals (Muon claim) | [unverified] | [unverified] | 6–7 for third parties; first flights Q1 2027 | [82][83][84] |
| Optical DTE (Tesat CubeLCT) | 1 Mbps / 100 Mbps | ~10 ms in-pass | 3–9 % × ~70 % weather ≈ 2–6 % | 8 W | 360 g | 9 (PIXL-1 2021) | [85] |
| Addvalue IDRS (Viasat L-band GEO) | 250 kbps / 200 kbps | 0.5–1.5 s end-to-end | 80–100 % ≤1,000 km | 7 W Rx, 25–40 W Tx peak, ~9–10 W avg | 1 kg + antenna | 9 (22 sats flying) | [86][87] |
| TDRSS | — | RTT 832 ms avg measured (METERON) | ~100 % | — | — | closed to new users Oct 2024 | [88][89] |

Other terminals: Tesat SCOT80 10 Gbps, 12–15 kg, 60–80 W [90]; Mynaric CONDOR Mk3 100 Mbps–100 Gbps, SDA-compliant, 100+ delivered, mass/power `[unverified]` [91]; AAC CubeCat 1 Gbps DTE, 1.3 kg, ~15 W [92]. Ground networks: KSATlite 135 antennas, 145,000 passes/month, >99.75 % success [93]; AWS Ground Station $3–22/min [94]. Single-station pass at 550 km is 8–12 min, 4–6 passes/day mid-latitude [95]. Optical ground station weather availability ~69 % single site, 93.6 % with 3 nodes [96]. No provider publishes ground-to-cloud backhaul latency `[unverified]`; the best measured RF direct link analogue is Kontur-2's 20–30 ms RTT [88].

Power/thermal of continuous downlink: 2 W RF X-band costs 10–15 W DC [76][77]; no CubeSat X-band datasheet states a continuous-transmit thermal limit `[unverified, absence]`, and CubeLCT is designed around 10 min per pass [85]. A 30–60 W continuous link is 720–1,440 Wh/day; eclipse energy is trivial (18–35 Wh) but generation is the constraint: 50–200 % of a 16U's orbit-average power versus 10–60 % on an ESPA bus `[derived]` [3][7]. Radiator: net ~250–300 W/m² in LEO [97], so 20–60 W of payload heat needs 0.07–0.25 m² `[derived]`; ACT sized a 20×30 cm deployable loop-heat-pipe radiator for 50 W on a 12U [98].

**Call:** Kepler optical relay (95 % continuity, buyable, 40 W) as the primary continuous path, X-band DTE as the low-latency path during passes, and IDRS L-band as an always-on 250 kbps command and safety channel. Starlink Mini Laser is the 2027 upgrade that would make the relay path both continuous and ~10–50 ms.

## 7. Candidate stack

| Subsystem | Choice | Rough cost | TRL | Alternative |
|---|---|---|---|---|
| Bus + launch | Apex Aries (100 kg rideshare config) + SpaceX rideshare | $3.5–9.5M bus (secondary) + ~$1.05M launch [derived] | 9 | EnduroSat FRAME S; 16U for a 2-arm demo only |
| Enclosure | 100–300 L Al 6061 cylinder at 1 atm, domed ends | 3.5–10 kg; cost n/p | 9 (GeneSat/BioSentinel pattern) | vacuum + GITAI IN2 (50 kg, not fundable at this scale) |
| Arms | 4–8× Dynamixel-X 6-DoF arms (Koch/ALOHA class) + Astrobee-style thermal/current cutoffs | $0.3–7k each | 4 (arm) / 9 (servo family) | SO-101 (STS3215) |
| Cameras | 4–8× IMX296 / AR0234 global shutter, 720p30 | ~$50–200 each [unverified] | 5 | e2v Ruby USV (rad-screened) |
| Compute | Jetson Orin NX (video) + rad-tolerant supervisor/MCU (safety loop, watchdog, LCLs) | $1k module + carrier; supervisor $50–100k [unverified] | 7 / 9 | Spiral Blue SE-1; Aitech S-A2300 |
| Downlink | Kepler OCT (3 kg, 40 W) + Syrlinks EWC27 X-band | OCT [unverified]; radio $30–80k [unverified] | 8–9 | Starlink Mini Laser (2027) |
| Uplink / safety | IDRS i100 L-band + S-band Rx | subscription [unverified] | 9 | S-band only (DTE passes) |
| Thermal | 0.1–0.25 m² radiator, heat strap from cylinder wall | n/p | 9 | deployable LHP radiator |

Order-of-magnitude total: $6–12M including launch `[derived, unverified]`; the bus dominates.

## Top three risks

1. **No buyable path is both continuous and low-latency in 2026.** Kepler is 95 % continuous but "sub-second" with no published number; X-band DTE is 20–30 ms-class but <10 % of the orbit; Starlink Mini Laser is the only candidate for both and its first third-party flights are Q1 2027 with mass, power, price, and ITAR status unpublished [80][82][83].
2. **COTS radiation behaviour is unquantified where it matters.** No TID/SEE data exists for Dynamixel or Feetech servos, no on-orbit Jetson reboot rate is published, and Jetson TX2/TX2i boards died at 9.7–25 krad through flash and regulators [67][68]. The architecture must tolerate Jetson reboots of seconds with the arms held by an independent supervisor.
3. **Power and thermal ceiling.** 100–190 W continuous payload draw rules out 12U/16U; even Aries at 175 W EOL leaves little margin, and no CubeSat X-band radio datasheet states a continuous-transmit qualification [5][76].

## Implication for our design

Model the satellite as an ESPA-class bus with a 1-atm enclosure holding 4–8 Dynamixel-class 6-DoF arms, 4–8 720p30 global-shutter cameras at 1.5–2.5 Mbps each (6–20 Mbps aggregate), and a split compute architecture: a Jetson that can reboot at any moment and a deterministic supervisor that owns the setpoint buffer, interpolation, and hold/retract. The link emulator should carry three profiles that match what is buyable: X-band DTE (RTT 20–60 ms, 8–12 min windows, 4–6 per day per station), Kepler-class optical relay (95 % availability, one-way 50–300 ms until measured), and IDRS L-band (0.5–1.5 s, 250 kbps, always on) as the command/safety floor; a Starlink-laser profile (10–50 ms, >99 %) is the near-future upgrade branch. Fixed pre-link video cost of 50–90 ms and a command uplink capped at 250–500 kbps are hard constants for every hypothesis.

## Sources

1. https://nanoavionics.com/small-satellite-buses/12u-cubesat-nanosatellite-m12p/
2. https://catalog.orbitaltransports.com/12u-cubesat-platform-endurosat/
3. https://www.endurosat.com/products/16u-platform/
4. https://nanoavionics.com/small-satellite-buses/16u-cubesat-nanosatellite-m16p/
5. https://www.apexspace.com/platforms/leo-aries
6. https://research.contrary.com/company/apex
7. https://www.endurosat.com/products/the-frame-15-espa-class-satellite/
8. https://www.yorkspacesystems.com/platforms
9. https://satcatalog.s3.amazonaws.com/components/1237/SatCatalog_-_Blue_Canyon_Technologies_-_X-Sat_Venus_Class_-_Datasheet.pdf
10. https://terranorbital.com/spacecraft-platforms/nebula/
11. https://newspaceeconomy.ca/2026/02/27/spacex-rideshare-pricing-as-of-february-2026-what-it-costs-whats-included-and-how-buyers-budget-a-mission/
12. https://exolaunch.com/documents/EXOpod_Nova_User_Manual_June_2024.pdf
13. https://www.moog.com/products/spacecraft-payload-interfaces/espa.html
14. https://www.eoportal.org/satellite-missions/genesat
15. https://www.eoportal.org/satellite-missions/ooreos
16. https://cosmiac.unm.edu/about/ast.2019.2068.pdf
17. https://en.wikipedia.org/wiki/Bion-M_No.2
18. https://spacenews.com/vardas-second-mission-launches-with-u-s-air-force-payload/
19. https://en.wikipedia.org/wiki/SpaceX_Dragon_2
20. https://en.wikipedia.org/wiki/Nanoracks_Bishop_Airlock
21. https://storage.googleapis.com/rideshare-static/Rideshare_Payload_Users_Guide.pdf
22. https://asm.matweb.com/search/specificmaterial.asp?bassnum=ma6061t6
23. https://ntrs.nasa.gov/api/citations/20100019164/downloads/20100019164.pdf
24. https://ntrs.nasa.gov/api/citations/20100033653/downloads/20100033653.pdf
25. https://www.sciencedirect.com/science/article/pii/S2772683523000018
26. https://www.maxongroup.com/en-us/knowledge-and-support/blog/brushed-vs-brushless-dc-motors-17036
27. https://gitai.tech/wp-content/uploads/2023/04/Inchworm-IN2-datasheet.pdf
28. https://gitai.tech/2024/03/19/gitai-completes-fully-successful-technology-demonstration-outside-the-iss/
29. https://gitai.tech/2024/10/23/gitais-inchworm-type-robotic-arm-achieves-trl6-in-a-thermal-vacuum-chamber-test-simulating-the-lunar-south-pole-environment/
30. https://www.prnewswire.com/news-releases/motiv-space-systems-launches-xlink-the-highly-modular-cost-efficient-space-rated-robotic-arm-system-301063707.html
31. https://www.satcatalog.com/component/kraken/
32. https://en.wikipedia.org/wiki/Repair_Satellite_Prototype
33. https://ntrs.nasa.gov/api/citations/20170009546/downloads/20170009546.pdf
34. https://ntrs.nasa.gov/api/citations/20190002821/downloads/20190002821.pdf
35. https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html
36. https://www.seeedstudio.com/SO-101-Low-Cost-AI-Arm-Kit-Pro-p-6427.html
37. https://github.com/AlexanderKoch-Koch/low_cost_robot/blob/main/README.md
38. https://docs.trossenrobotics.com/interbotix_xsarms_docs/specifications/vx300s.html
39. https://store.trossenrobotics.com/products/viperx-aloha-follower-arms-single-2
40. https://hawklogicsystems.com/tools/radiation-dose
41. https://arxiv.org/pdf/2503.09520
42. https://ieeexplore.ieee.org/document/6062504/
43. https://beei.org/index.php/EEI/article/download/2488/1890
44. https://framos.com/products/sensors/area-sensors/imx296lqr-c-22545/
45. https://www.vadzoimaging.com/post/ar0234-global-shutter-mipi-camera-the-complete-guide-for-embedded-vision
46. https://www.teledynespaceimaging.com/en-us/Products_/Documents/Industrial%20Image%20Sensors%20Upscreened%20for%20Space/Ruby%201.3M%20USV%20flyer.pdf
47. https://www.3d-plus.com/app/uploads/2023/04/3DDS-0734.pdf
48. https://www.raspberrypi.com/news/raspberry-pi-zero-powers-cubesat-space-mission/
49. https://www.raspberrypi.com/for-industry/space/
50. https://developer.ridgerun.com/wiki/index.php/GStreamer_Encoding_Latency_in_NVIDIA_Jetson_Platforms
51. https://docs.amd.com/r/2020.2-English/pg252-vcu/Encoder-and-Decoder-Latencies-with-Xilinx-Low-Latency-Mode
52. https://forums.raspberrypi.com/viewtopic.php?t=209706
53. https://developer.ridgerun.com/wiki/index.php/Jetson_glass_to_glass_latency
54. https://library.zoom.com/admin-corner/network-management/quality-of-service-and-network-best-practices-explainer/calculating-bandwidth-usage-for-zoom-meetings-and-phone
55. https://support.google.com/youtube/answer/2853702?hl=en
56. https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/
57. https://doi.org/10.1109/iolts60994.2024.10616076
58. https://spacenews.com/cosmic-shielding-works-with-aethero-to-protect-nvidia-jetson-orin-nx-gpu/
59. https://www.planet.com/pulse/pelican-2025-in-review/
60. https://doi.org/10.1109/tns.2025.3539942
61. https://aitechsystems.com/s-a2300-ai-supercomputer-space-edge-processing/
62. https://spaceaustralia.com/news/spiral-blues-edge-one-computer-successfully-commissioned-orbit
63. https://www.nasa.gov/wp-content/uploads/2025/02/8-soa-small-spacecraft-avionics-2024.pdf
64. https://satcatalog.s3.amazonaws.com/components/460/SatCatalog_-_Xiphos_Systems_Corporation_-_Q8S_-_Datasheet.pdf
65. https://unibap.com/wp-content/uploads/2024/04/ix10-101-product-overview.pdf
66. https://lkdaerospace.com/wp-content/uploads/6821e342b8bbb3d66db0fd15_Leopard_DPU_Data_Sheet.pdf
67. https://ntrs.nasa.gov/api/citations/20190031856/downloads/20190031856.pdf
68. https://doi.org/10.1109/redw61050.2023.10265826
69. https://doi.org/10.1109/hpec43674.2020.9286222
70. https://doi.org/10.1109/redw61050.2023.10265818
71. https://www.osti.gov/servlets/purl/1513704
72. https://ieeexplore.ieee.org/document/8584296/
73. https://arxiv.org/pdf/2201.06973
74. https://zero-errorsystems.com/products/lcl-latching-current-limiter/
75. https://zenodo.org/records/5522872/files/12.02_OBDP2021_Flordal.pdf
76. https://satsearch.co/products/syrlinks-ewc27-x-band-transmitter
77. https://www.endurosat.com/products/x-band-transmitter/
78. https://www.nasa.gov/wp-content/uploads/2025/02/9-soa-communications-2024.pdf
79. https://satsearch.co/products/tui-swift-ktx
80. https://kepler.space/wp-content/uploads/2023/09/Optical-Datasheet-v6-2025-1.pdf
81. https://kepler.space/kepler-delivers-optical-infrastructure-for-real-time-space-operations/
82. https://www.prnewswire.com/news-releases/muon-space-to-integrate-spacexs-starlink-mini-space-lasers-into-its-halo-satellite-platform-302589505.html
83. https://satsearch.co/products/spacex-plug-and-plaser-lasercom-system
84. https://starlink.com/public-files/StarlinkLatency.pdf
85. https://www.tesat.de/images/downloads/DataSheet_CubeLCT.pdf
86. https://www.addvaluetech.com/wp-content/uploads/2021/07/White_Paper_IDRS_for_LEO_satellites_using_a_commercially_available_GEO_satellite_system.pdf
87. https://indico.esa.int/event/513/contributions/10248/attachments/6477/11429/[S3-02]%20Addvalue%20-%20Intersatellite%20data%20relay%20service.pdf
88. https://elib.dlr.de/130830/1/RA-L2019_final_Schmaus-Meteron_Supvis_Justin.pdf
89. https://www.executivebiz.com/articles/commercial-space-relay-communications-nasa-dow-pext-tdrs
90. https://www.tesat.de/products
91. https://satsearch.co/products/mynaric-condor-mk3
92. https://www.aac-clyde.space/wp-content/uploads/2021/10/CUBECAT.pdf
93. https://www.ksat.no/ground-network-services/ksatlite/
94. https://elasticscale.com/reduce-aws-ground-station-costs/
95. https://novasolver.jp/en/tools/polar-orbit-ground-station-pass.html
96. https://arxiv.org/html/2606.23711v2
97. https://blog.spacecomputer.io/orbital-data-center-cooling-vs-power/
98. https://www.1-act.com/wp-content/uploads/2025/09/ICES-3D-Printed-LHP-Final.pdf
