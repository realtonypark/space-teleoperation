# Ground teleoperation of robot arms inside a LEO satellite for physical-AI data collection

Final report, draft. Experiments are still running; every experimental number is a `{{RESULTS:...}}` placeholder. Every other number carries its source as `report §section`, where the report is a file in `docs/research/`, or a path into the repo for testbed constants. Values marked `[design choice]` are ours; `[unverified]` marks a figure no report could source.

---

## 1. Executive summary

**The question.** Can people on Earth teleoperate simple robot arms inside a rideshare-class LEO satellite well enough to collect physical-AI demonstration data that Earth-side simulation and labs cannot produce? The engineering objective is minimum end-to-end latency; the acceptance metric is demonstration quality and throughput relative to a zero-latency baseline (PROGRAM.md).

**The verdict.** Conditional yes (SYNTHESIS §1). Feasible with hardware buyable in 2026 if the mission flies a Starlink mini-laser relay terminal, first third-party flights Q1 2027, or accepts pass-limited sessions at a 21 % duty cycle through a four-site polar ground network. Either way the task set is restricted to slow, coarse manipulation. No program has flown a manipulator inside a free-flyer under ground teleoperation, and none has logged robot-learning demonstrations in orbit (space_teleop_prior_art §2, §3). The sub-100 ms space link exists only on direct passes (space_teleop_prior_art §1); continuous sub-150 ms coverage is one product away (leo_link_options §2 b1).

**The recommended architecture, in five bullets.**

- **Link.** Primary: two Starlink mini-laser terminals, contracted 2026 for a 2027 flight, 48 ms RTT median with 15 s spikes to about 125 ms. Fallback: direct ground-station passes through a four-site polar network. Safety channel: IDRS L-band or Iridium Certus. GEO relay is disqualified by its propagation floor (SYNTHESIS §2).
- **Protocol.** A 50 Hz UDP stream of timestamped, sequence-keyed joint setpoints, 40 B payload, sent twice. Video is two 720p30 streams per operator inside a 10.4 Mbps downlink for four operators (multi_operator_bandwidth §2, §3).
- **Satellite.** Decision (c): setpoint playout with a 30 ms buffer, hold at 300 ms, retract at 10 s, ramp-limited resume, static envelopes, and hardware cutoffs, all on a rad-tolerant supervisor. No vision, no models, no autonomy that changes the trajectory (SYNTHESIS §5).
- **Ground.** Leader-follower or VR without force feedback, a session broker that grants one write authority per arm, fanned-out observers, and a 50 Hz follower rate regardless of link rate (multi_operator_bandwidth §4; teleop_fundamentals §1.4).
- **Mission.** A pressurised ESPA-class bus (Apex Aries, 100 kg) with a 100–300 L aluminium cylinder at 1 atm holding four Dynamixel-class 6-DoF arms, global-shutter cameras, a Jetson Orin NX for video, and a separate deterministic supervisor. Order-of-magnitude cost $6–12 M including launch (SYNTHESIS §4; hardware_landscape §7).

**The three numbers that matter.**

| Number | Value |
|---|---|
| Baseline success on `leo_relay` as a fraction of zero-latency success, task `capture` | `{{RESULTS:acceptance_table}}` |
| Baseline knee: first RTT at which success falls below 80 % of zero-latency, per task | `{{RESULTS:knees}}` |
| Unsafe-motion events across all episodes on all four named profiles | `{{RESULTS:acceptance_table}}` |

---

## 2. Problem and scope

The charter (PROGRAM.md) fixes the goal: determine whether, and how, humans on Earth can teleoperate simple robot arms inside a LEO satellite to collect physical-AI demonstration data that Earth-side simulation cannot produce. We cannot launch. The proof is a validated architecture plus a runnable testbed that reproduces orbit-link behaviour over real sockets and shows the numbers.

**Fixed by the user.** Deliverable: architecture spec, testbed, experiments, this report, mission sketch as appendix. No human in the loop; agents review agents. Leader-follower or VR interface, no force feedback, synthetic operators in the testbed. Onboard baseline at minimum (b): joint setpoints, a short interpolated command buffer, hold or retract on timeout; no models or vision, with one hypothesis branch quantifying onboard compute. Scale 4–8 arms and 4 concurrent operators. MuJoCo at zero gravity, TLE-driven pass geometry, a UDP link emulator on localhost, video as delay plus bandwidth budget, LeRobot data format. Default acceptance: 80 % of zero-latency success and demos per hour with zero unsafe motion on dropout. About 20 quality-gated hypotheses, verifier-ranked, top 3–5 implemented against a naive baseline.

**Decided by research.** Link path, orbit, bus class, pressurisation, onboard capability level, task set, hardware stack and input device, under two constraints: rideshare-launchable, buyable today. Sections 3 to 6 report the choices.

**Rules every agent followed.** Cite or mark unverified; abstain over padding; end with a concrete implication; numbers over adjectives; stay in your lane (PROGRAM.md).

---

## 3. Feasibility today

### 3.1 What has flown

Three flown cases put an arm on a free-flying satellite under ground control: ETS-VII (1997–99, 5–7 s through a GEO relay, every task class completed with a predictive display and an autonomy layer), Orbital Express (2007, scripted autonomy with go/no-go gates) and Xiyuan-0 (2026, hand-controller teleop over direct passes, no numbers). Every interior-arm case lived on a crewed station (space_teleop_prior_art §1, §2). Flown latency collapses to two regimes, direct passes at 20–30 ms with 4–20 min windows and GEO relay at 0.8–1.1 s with loss-of-signal gaps; nothing between has been measured in orbit (space_teleop_prior_art §2).

| Program | Direction | Round trip | Scheme | Lesson |
|---|---|---|---|---|
| ETS-VII 1997–99 | ground to orbit | 5–7 s | low-level commands, predictive display, interactive autonomy | link infrastructure caused the outages, not the robot |
| ROKVISS 2005–10 | ground to orbit | 20–30 ms, 0.1 % loss, ±2 ms jitter | bilateral force feedback, 245 kbit/s up, 4 Mbit/s down | the only sub-100 ms space link ever flown, bought with a dedicated antenna and ≤7.5 min passes |
| Kontur-2 2015–17 | orbit to ground | 20–30 ms, ±2 ms jitter | 4-channel passivity | "30 ms is already a huge challenge for robotic control" |
| Haptics-2, Interact, SUPVIS-Justin, Analog-1 2015–19 | orbit to ground | 0.8–1.1 s | bilateral or supervisory over TDRS | the 1–3 s tail and dropouts hurt, not the mean |
| Canadarm2 / Dextre 2005– | ground to orbit | 0.3–0.5 s (secondary) | pre-validated sequences, LOS-safe motion | 170 days/yr, >100,000 commands, no continuous human loop |
| Astrobee 2019– | ground to orbit | not published | plans, hold on LOS, keep-out zones | the accepted ISS pattern for ground-driven robots |
| GITAI S1 2021 | ground to orbit | not published | autonomous then teleop, inside Bishop airlock | a commercial arm inside a pressurised volume; no numbers |
| Xiyuan-0 2026 | ground to orbit | "sub-second" | hand-controller teleop over direct passes | first commercial small-sat arm teleoperated by a human; no data |

All rows: space_teleop_prior_art §1.

### 3.2 Link ranking

The link decision is the most consequential in the program. Five candidate paths were ranked (SYNTHESIS §2).

| Rank | Path | RTT p50 / p95 | Coverage | Up / down | Why it wins or loses |
|---|---|---|---|---|---|
| 1 | Starlink mini-laser relay ×2 | 48 / 125 ms (network_emulation §4 P2) | >99 % with two terminals, Muon claim `[unverified]`, minus 1.7 outages/h (network_emulation §1.1) | 25 Gbps ISL; ground allocation unpublished | only continuous, sub-150 ms candidate; loses only on schedule, Q1 2027 first flights (leo_link_options §3) |
| 2 | Direct GS, 4 polar sites, X-band down, S-band up | 30 / 45 ms in contact (space_teleop_prior_art §1; network_emulation §1.4) | 21.3 %; 33 passes/day, 9.2 min mean, 35 min median gap (network_emulation §1.4) | 256 kbps / 100–150 Mbps (multi_operator_bandwidth §3; hardware_landscape §6) | only regime with flown, measured numbers; hard outages between passes |
| 3 | Kepler optical relay + SDA terminal | unpublished; 50–300 ms one-way `[unverified]` (hardware_landscape §6) | intermittent until 2028 (leo_link_options §2 b2) | 2.5 Gbps | live since 24 Aug 2026 but no latency figure; optical ground stations weather-limited |
| 4 | IDRS L-band / Iridium Certus | 0.5–1.5 s (hardware_landscape §6) | 80–100 % | 250 / 200 kbps | safety and heartbeat only |
| 5 | GEO relay (TDRS, EDRS, InRange) | 600 / 850 ms (network_emulation §1.3) | >99 % | 20 / 90 Mbps | propagation floor ≥474 ms is disqualifying; TDRS closed to new users Nov 2024 (leo_link_options §2 c) |

Two reports disagreed on the buyable-today primary: hardware_landscape §6 named Kepler on a 95 % continuity datasheet claim, leo_link_options §2 b2 estimated it as not continuous with 10–33 satellites. The synthesis took leo_link_options because the 95 % is a full-constellation claim `[unverified]` and no Kepler latency number exists (SYNTHESIS §2).

### 3.3 The "one product away" argument

The physics floor for a direct or Starlink-relayed link is 4–30 ms RTT (leo_link_options §1). Consumer Starlink measures a median 40 ms bent-pipe RTT across 19.2 million tests, a 15 s reconfiguration cycle, about 1 % loss and 1.7 outages per hour (network_emulation §1.1). SpaceX has flight-tested a 25 Gbps mini-laser terminal for third-party satellites, Muon Space and Starcloud have contracted for it, and first hardware reaches orbit in Q1 2027 (leo_link_options §2 b1). One 4,000 km hop on the consumer median gives the 48 ms design RTT, 90 ms with margin (SYNTHESIS §2).

Human tolerance leaves margin there: coarse pick-and-place time grows ×1.45 at 250 ms and ×2.04 at 500 ms, first significant loss appears at 200–300 ms, precision insertion is "ideal" below 200 ms (teleop_fundamentals §1.2, §4), and the relay machine loop without the human is about 163 ms (SYNTHESIS §8). Two unknowns bound the verdict: no measured latency for a third-party satellite over Starlink inter-satellite links (network_emulation §1.2), and no radiation data for Dynamixel or Feetech servos (hardware_landscape §3).

---

## 4. Recommended end-to-end architecture

### 4.1 Block diagram

```
 GROUND                                     LINK                               SATELLITE (ESPA bus, 1 atm cylinder)
 ┌──────────────────────────┐                                                 ┌──────────────────────────────────────┐
 │ operator 1..4            │                                                 │ rad-tolerant SUPERVISOR MCU          │
 │  leader arm / VR         │   50 Hz UDP setpoints, 40 B, sent twice         │  seq-keyed buffer, 30 ms playout     │
 │  no force feedback       │ ───────────────────────────────────────────►    │  hold 300 ms, retract 10 s           │
 │  synthetic operator in   │        ┌────────────────────────────┐           │  ramp-limited resume, envelopes      │
 │  the testbed, tau_h 0.17 │        │ PRIMARY: 2x Starlink       │           │  watchdog, latching current limiters │
 └───────────┬──────────────┘        │  mini-laser, 48 ms RTT     │           └───────────────┬──────────────────────┘
             │                       │ FALLBACK: direct GS passes │                           │ servo bus 3-8 ms
 ┌───────────┴──────────────┐        │  4 polar sites, 30 ms RTT  │           ┌───────────────┴──────────────────────┐
 │ SESSION BROKER           │        │ SAFETY: IDRS / Iridium     │           │ 4x Dynamixel-X 6-DoF arm + gripper   │
 │  one write authority per │        │  0.5-1.5 s, 250 kbps       │           │  inside a cage = keep-out box        │
 │  arm, observers fanned   │        └────────────────────────────┘           │  task cells: granular, liquid, cable │
 │  out, pass-sized slots   │   ◄───────────────────────────────────────────  └───────────────┬──────────────────────┘
 └───────────┬──────────────┘   telemetry 30 Hz + 2 video streams/operator                    │ 720p30 global shutter
             │                  720p30, 1.5-2.5 Mbps each, FEC, intra-refresh   ┌─────────────┴──────────────────────┐
 ┌───────────┴──────────────┐                                                   │ Jetson Orin NX (may reboot)        │
 │ RECORDER                 │                                                   │  cameras, NVENC, mux, datasets     │
 │  LeRobot v2 layout       │                                                   │  never in the setpoint path        │
 │  sat-side applied log    │                                                   └────────────────────────────────────┘
 │  per-row link timestamps │
 └──────────────────────────┘
```

### 4.2 Link path

Primary: Starlink mini-laser relay, two terminals so one re-acquires while the other carries traffic (leo_link_options §2 b1). Fallback: direct passes through the Svalbard, Troll, Inuvik and Punta Arenas union, 33.4 passes per day, 9.2 min mean, 35 min median gap (network_emulation §1.4), for commissioning, bulk downlink and pass-bounded teleop. Safety channel: IDRS L-band at 250 kbps and 0.5–1.5 s, or Iridium Certus (hardware_landscape §6), heartbeat and safe-mode only.

### 4.3 Protocol

**Command uplink.** Seven float32 setpoints, an 8 B timestamp and a 4 B sequence make a 40 B payload, 68 B over raw UDP/IPv4, 27 kbps at 50 Hz (multi_operator_bandwidth §2). A WebRTC data channel would double it to 133 B, which matters against the 256 kbps S-band uplink of the pass regime (multi_operator_bandwidth §3). Sending every setpoint twice at 100 Hz is still ≤0.2 Mbps per operator, and RFC 8854 favours retransmission only when RTT is inside the budget, which a bursty pass-bounded link does not guarantee (multi_operator_bandwidth §2). Duplicate-send, not NACK.

**Playout.** The receiver keys on sequence number, never arrival time: a command not newer than the newest received is dropped, because uplink jitter reorders a double-digit share of consecutive packets and playing a stale one is a backwards jump of the arm (`spaceteleop/sat/controller.py`). The interpolator renders the buffer as it stood 30 ms ago in the satellite's own clock.

**Telemetry.** 30 Hz frames carry joints, velocities, object pose, flags, and an echo of the last applied command's sequence, send timestamp and application time. RTT is measured only at the ground from its own echoed timestamp with dwell subtracted, so no two-host clock comparison is needed (`spaceteleop/ground/loop.py`). The testbed datagrams are 45 B up and 123 B down plus an optional frame-bytes field for the video budget (`spaceteleop/proto/__init__.py`).

### 4.4 Satellite controller, decision (c)

Decision (c): the (b) baseline plus small deterministic safety logic, all on the rad-tolerant supervisor, none on the Jetson. The allowed list, verbatim from SYNTHESIS §5:

1. Joint-setpoint playout: receive timestamped setpoints, sort by sequence, interpolate linearly at the control rate with a fixed playout delay of 30 ms `[design choice]`, bounded by teleop_fundamentals §2 (buffering more than ~50–70 ms of jitter costs more than it saves) and network_emulation §1.1 (uplink jitter SD 14 ms).
2. Hold on timeout: if no command newer than 300 ms, freeze the commanded setpoint at the last interpolated value. The window sits between the 15 s uplink spike (+74 ms over 140 ms, must not trigger) and the outage tail (87 % under 2 s, must trigger); leo_link_options §Implication puts the threshold at 300–500 ms.
3. Retract to a stowed pose after 10 s of silence `[design choice]`: only the 3 % of outages lasting 5–31 s reach it (network_emulation §1.1).
4. Ramp-limited resume: on link return the interpolator ramps from the frozen value at no more than the rated joint velocity, never a jump.
5. Static envelopes: joint position, velocity and acceleration clamps, and a keep-out box that is the cage interior. This is the Astrobee keep-out-zone and Canadarm2 LOS-safe pattern that every flown ground-driven robot uses (space_teleop_prior_art §1, §Implication).
6. Hardware cutoffs: per-motor thermal cutoff and a latching current limiter at 80 % of peak, exactly the Astrobee arm design (hardware_landscape §3).

Excluded from the baseline: vision, learned models, admittance or force control, any subgoal primitive, any autonomy that changes the trajectory. The onboard-compliance result, nut threading 49 → 65–81 % (teleop_fundamentals §2), is the strongest hider in the evidence and is therefore a hypothesis branch. (c) beats (b) because the relay path has 1.7 heavy-tailed outages per hour and every flown system that survived loss of signal did so with onboard envelopes, not hold alone (SYNTHESIS §5). The logic is stateless bar one timer and sits on the supervisor because a Jetson single-event functional interrupt is a multi-second reboot (hardware_landscape §5).

### 4.5 Ground client

Leader-follower or VR without force feedback: force coupling is what became unstable in every relay-path program, and passivity control is irrelevant without it (space_teleop_prior_art §Implication; teleop_fundamentals §2). The follower runs at 50 Hz regardless of link rate; 5 Hz teleop cost 62 % more time (teleop_fundamentals §1.4; data_pipeline §2.1).

Sessions follow the Astrobee and ISS POIC pattern (multi_operator_bandwidth §4): one commanding authority per arm, enforced on the ground; everyone else a read-only subscriber of one fanned-out stream; onboard safe behaviour on loss of signal; robot time booked in pass-sized slots. A session broker implements this.

In the testbed the human is a synthetic operator: it sees only link-delayed telemetry, reacts to what it saw 0.17 s ago, and commands a position at bounded Cartesian speed until it sees it has arrived (`spaceteleop/ground/operators.py`). Policy and gains are identical at every latency, so the operator is the constant and the link the variable. The 0.17 s is the human online visuomotor correction latency of 143–170 ms (teleop_fundamentals §3).

### 4.6 Video pipeline budget

Pipeline: global-shutter MIPI or GMSL camera, hardware encoder with intra-refresh and no B-frames, 0–10 ms playout hint, 60–144 Hz display; the 100 ms USB-webcam path is disqualifying (multi_operator_bandwidth §1.2). Two live streams per operator, scene plus wrist, 720p30 at about 1 Mbps each; other dataset cameras are logged onboard (multi_operator_bandwidth §1.3).

| Operators | Streams | Downlink video | Downlink with FEC and headers | Uplink at 100 Hz, sent twice |
|---|---|---|---|---|
| 4 | 2 mono 720p30 at 1 Mbps (lean) | 8 Mbps | 10.4 Mbps | 0.85 Mbps |
| 4 | 3 mono 720p30 at 2.5 Mbps (standard) | 30 Mbps | 39 Mbps | 0.85 Mbps |
| 8 | 2 mono lean | 16 Mbps | 20.8 Mbps | 1.7 Mbps |
| 8 | 3 mono standard | 60 Mbps | 78 Mbps | 1.7 Mbps |

Source: multi_operator_bandwidth §3. The lean case fits X-band direct-to-Earth at 100–150 Mbps and any relay; S-band alone supports one lean operator (hardware_landscape §6). Bandwidth is not the constraint.

### 4.7 Latency budget

| Stage | ms | Source |
|---|---|---|
| Sensor exposure + readout, 720p30 global shutter | 25 | hardware_landscape §4 (16–33) |
| Encode, Jetson NVENC 720p H.264 | 8 | hardware_landscape §4 (5–8); multi_operator_bandwidth §1.2 |
| Downlink propagation + mesh + PoP | 18 | network_emulation §4 P2 |
| Jitter buffer | 10 | teleop_fundamentals §3; multi_operator_bandwidth §1.2 |
| Decode | 10 | teleop_fundamentals §3 |
| Display, 60–144 Hz | 12 | teleop_fundamentals §3 (8–17) |
| Human visuomotor correction | 170 | teleop_fundamentals §3 (143–170) |
| Input polling + command path + IK | 12 | teleop_fundamentals §3 |
| Uplink propagation + mesh + PoP | 30 | network_emulation §4 P2 |
| Satellite playout buffer | 30 | SYNTHESIS §5 item 1 `[design choice]` |
| Servo bus + actuation | 8 | teleop_fundamentals §3 (3–8) |
| **Sum** | **333** | SYNTHESIS §8 |
| Sum excluding the human (machine loop) | 163 | SYNTHESIS §8 |

The human is 51 % of the loop, the link 14 %, the playout buffer 9 %. The link is not the dominant term; in the Anvari telesurgery series only 14 ms of 135 was network (teleop_fundamentals §3). On `direct_gs` the sum is about 315 ms, on `geo_relay` about 885 ms (SYNTHESIS §8).

### 4.8 Data pipeline

The testbed writes a LeRobot-v2-shaped dataset: one `.npz` per episode in place of parquet, `meta/info.json` and `meta/episodes.jsonl`, the standard state, action, timestamp and index columns, plus extras `cmd_seq`, `rtt_ms`, `owd_up_ms` and `safety_hold` (`spaceteleop/record/__init__.py`). LeRobot's `timestamp` is synthetic and its loader rejects jittery wall-clock stamps, so link timing lives in extra columns (data_pipeline §1.2).

Three choices come from the data-quality evidence.

- **A satellite-side applied log.** A sidecar holds one row per control cycle: cycle time, application time, sequence, hold flag, applied setpoint, assist and tether flags. The main table carries about 85 ms of observation-action skew on `leo_relay`; the sidecar re-pairs the true applied action, and smoothness is computed on it rather than on 30 Hz telemetry aliased to 50 Hz rows (selection.md §3).
- **Per-row link timestamps.** Policies trained on zero-latency data need latency matching at deployment, so every row carries measured RTT and a `link_state` of ok, hold, retract or outage (data_pipeline §2.3, §3.1).
- **Curation metrics, reported not gated.** robomimic "Worse" operators reached 92 % on Can but produced 39 % versus 66 % policies on Square; keeping the top half by spectral arc length lifted policy success from 39 % to 55 % (data_pipeline §2.1). The recorder reports SAL, log dimensionless jerk and stall fraction per episode against the zero-latency baseline (SYNTHESIS §6).

---

## 5. Mission shape and hardware stack

**Bus class: ESPA.** Continuous payload draw is 100–190 W, 2–5× a 16U CubeSat's 25–60 W orbit-average and 55–100 % of the Apex Aries' 175 W end-of-life power (hardware_landscape §1). The Aries carries 100 kg on a SpaceX rideshare, first flew in 2024, and costs $3.5–9.5 M (secondary) plus about $1.05 M launch (hardware_landscape §1, §7).

**Pressurisation: yes.** A 100–300 L aluminium cylinder at 1 atm with domed ends weighs 3.5–10 kg with fittings (hardware_landscape §2). Brushed motors need atmosphere for the commutator film, hobby servos have no convection path in vacuum, and vacuum-rated arms such as the 50 kg GITAI IN2 exceed the payload budget (hardware_landscape §2). Tasks 1 and 3 independently prefer a pressurised bus (unique_data_study §4). SpaceX treats a sealed 1-atm container as pressurised equipment at 1.5× yield and 2.0× ultimate (hardware_landscape §2).

**Arms: four in the baseline, eight as the scale branch.** Four is what four operators use, what the bandwidth budget is sized for, and what unique_data_study §5 allocates cells to (SYNTHESIS §4). The precedent is Astrobee: stock Dynamixel X servos, a hardware flip-flop cutting the driver at 80 % of peak current, a bimetal thermostat per motor, on the ISS since July 2019 (hardware_landscape §3).

| Subsystem | Choice | Source |
|---|---|---|
| Bus + launch | Apex Aries 100 kg + SpaceX rideshare, ≈$1.05 M launch | hardware_landscape §1, §7 |
| Enclosure | 100–300 L 1-atm Al cylinder, domed ends, 3.5–10 kg | hardware_landscape §2 |
| Arms | 4× Dynamixel-X 6-DoF + parallel gripper, XM430 on loaded joints | hardware_landscape §3 |
| Cameras | 4–8× IMX296 or AR0234 global shutter, 720p30, 1.5–2.5 Mbps each | hardware_landscape §4 |
| Compute | Jetson Orin NX (cameras, NVENC, mux) + rad-tolerant supervisor MCU (setpoint buffer, hold/retract, watchdog, current limiters) | hardware_landscape §5 |
| Relay | 2× Starlink mini-laser terminals; mass and power unpublished, budget conservatively | leo_link_options §2 b1 |
| Direct to Earth | Syrlinks EWC27 X-band down + S-band receive | hardware_landscape §6 |
| Safety channel | IDRS L-band 250 kbps or Iridium Certus 9770 | hardware_landscape §6; leo_link_options §2 d |
| Thermal | 0.1–0.25 m² radiator, heat strap from cylinder wall | hardware_landscape §6 |

Order-of-magnitude total: $6–12 M including launch, and the bus dominates (hardware_landscape §7).

**Top risks** (hardware_landscape, "Top three risks").

1. No buyable path is both continuous and low-latency in 2026. Kepler is "sub-second" with no published number; X-band direct-to-Earth covers under 10 % of the orbit per station; the Starlink mini laser is the only candidate for both and its mass, power, price and ITAR status are unpublished.
2. COTS radiation behaviour is unquantified where it matters. No TID or SEE data for Dynamixel or Feetech servos, no published on-orbit Jetson reboot rate, and Jetson TX2 boards died at 9.7–25 krad. The arms must be held by an independent supervisor through Jetson reboots.
3. Power and thermal ceiling. 100–190 W continuous rules out 12U and 16U; Aries at 175 W leaves little margin; no CubeSat X-band radio datasheet states a continuous-transmit qualification.

**What a 16U pass-only variant gives up.** Requiring a continuous link is the most cost-driving decision: relay terminals at 40–70 W plus continuous downlink power push the payload past any CubeSat class (SYNTHESIS §4). A 16U with 10.3U of payload volume supports one cylinder of about 8 L, one or two small arms, direct-to-Earth passes only (hardware_landscape §1, §2). It gives up continuous coverage, so teleop runs at 21 % duty in 9 min windows with 35 min median gaps (network_emulation §1.4); four concurrent operators; and the granular and liquid cells. It keeps the flown, measured 20–30 ms regime and is the right shape for a flight whose job is to validate the link emulator against a real pass.

---

## 6. Task set and why the data is unobtainable on Earth

No Earth analog gives 6-DoF free motion for longer than about 24 s; the only long-duration analog, the planar air bearing, has three degrees of freedom. Parabolic flight measures 0.041 ± 0.005 g in its "zero g" phase; drop towers reach 1e-4 to 1e-5 g for 5–9 s with no operator loop (unique_data_study §1).

The residual gap after the best simulator and the best Earth analog ranks as follows (unique_data_study §2).

1. **Granular media below 1e-4 g.** Behaviour "cannot be extrapolated" from 1e-2 g parabolic data; rebound and ejecta appear at 10 cm/s in microgravity but not at lunar gravity; the ISS mass-flow law deviates at low g. MuJoCo has no granular material.
2. **Fluids.** Before SPHERES-Slosh "little experimental data for long-duration zero-gravity slosh existed"; the ISS study reached only qualitative CFD comparison.
3. **Deformables.** Astrobee cargo-bag work is simulation-only and calls deformable dynamics "an open challenge". No sustained microgravity dataset of a gripper handling cable or fabric exists.
4. **Free-floating capture.** Rigid dynamics at zero g is flight-verified, but MuJoCo has no restitution coefficient and "cannot simulate elastic collision". Real grasp impulses on a free 6-DoF target over minutes exist only in orbit.

Arm-base coupling, tool use, vacuum contact and lighting rank 5 to 8: exactly simulable, reproducible in thermal-vacuum chambers, or absent inside a pressurised LED-lit volume (unique_data_study §2).

| # | Task | Phenomenon exposed | Latency sensitivity |
|---|---|---|---|
| 1 | Scoop, transport, pour sieved granular simulant (<250 µm) between open trays in a transparent cell | regolith behaviour below 1e-4 g (unique_data_study §2 A) | low: coarse class, degrades at 250 ms, unusable ≥750 ms |
| 2 | Capture and re-release of a slowly spinning cm-scale rigid object (≤1 rad/s, ≤2–5 cm/s `[unverified]`) | real grasp impulses on a truly free 6-DoF body (unique_data_study §2 D) | medium: approach tolerant to 225 ms; the grasp event is precision-class, ~150–200 ms |
| 3 | Partially filled liquid container handling and capillary pour | long-duration slosh, capillary flow, contact-line dynamics (unique_data_study §2 B) | low: capillary flows take seconds |
| 4 | Cable routing and fabric pouch open/close (30 cm cable, two connectors, Velcro pouch) | deformable dynamics in microgravity (unique_data_study §2 C) | medium: connector mating is insertion-class, ~150–200 ms |
| 5 | Peg-in-hole on a fixture rigidly mounted to the bus, wheel torques logged | arm-base momentum coupling and base identification (unique_data_study §2 E) | high: precision insertion, ideal <200 ms, drops 500–700 ms |

Source: SYNTHESIS §3; latency classes from teleop_fundamentals §4. All tasks run inside a cage so nothing drifts out of reach, with objects at order cm/s (unique_data_study §3, §4). Tasks 1–4 are the unique-value payload; at least two arms should carry a granular cell and one a liquid cell (unique_data_study §5). Tasks 2 and 5 are the MuJoCo proxies for the success-versus-latency curve; capture results are a lower bound because grasp-impulse transients are not simulated (SYNTHESIS §3). The slowness of the unique-value tasks is the largest latency hider available (SYNTHESIS §10).

---

## 7. The testbed

### 7.1 What it is

Pure Python 3.12; mujoco, numpy and sgp4 are the only runtime dependencies (`pyproject.toml`). Three roles run as threads in one interpreter over real UDP sockets on 127.0.0.1 (`spaceteleop/run.py`).

- **Ground** (`spaceteleop/ground/`): hands the operator a frame `tau_h` old, sends 7-slot setpoints at 50 Hz, measures RTT from the echo with dwell subtracted.
- **Link** (`spaceteleop/link/emulator.py`): a UDP proxy with two independent directions, each a receive thread that samples a release time onto a heap and a drain thread that sends at release. Nothing is simulated in-process. Timer error is under 0.3 ms against 20–50 ms delays (network_emulation §2).
- **Satellite** (`spaceteleop/sat/controller.py`): sequence-keyed buffer, strategy call every cycle at about 1 kHz, MuJoCo stepped up to wall clock, 30 Hz telemetry, keep-out and cage counters, applied-setpoint log.
- **Sim** (`spaceteleop/sim/`): MuJoCo at zero gravity with the SO-100 from `robot_descriptions`. `capture`: a 16 mm box drifting at 2–4.5 cm/s and tumbling at 0.3–1 rad/s, a 20 mm capture envelope, a 50 mm target region held 0.2 s (SYNTHESIS §3 task 2). `peg`: a 60 mm peg, 6 mm radial clearance, unknown grasp offset up to 6 mm, and a jam rule that leaves the peg behind on fixture contact (SYNTHESIS §3 task 5). `capture_chain` adds a dead-band tether and two alternating targets. Both scenes carry a six-wall cage, 0.64 × 0.66 × 0.48 m, whose interior is the keep-out box (`spaceteleop/sim/__init__.py`).
- **Strategy hook** (`spaceteleop/strategies/base.py`): `observe`, `ground_step` and `sat_step`. A hypothesis subclasses `Baseline` and is selected by `--strategy`; nothing else changes.

### 7.2 What it models, and what it does not

| Aspect | Modelled as | Not modelled |
|---|---|---|
| Video | delay in the latency budget plus a `--frame-bytes` field padded onto telemetry so the bandwidth cap bites, up to 8 kB per frame at 30 Hz for a ~2 Mb/s budget (`spaceteleop/sat/controller.py`) | codec, frame content, perceptual quality |
| Grasp | kinematic: the object rides the grasp site once inside the 20 mm envelope; the peg is held rigidly upright so only XY alignment and depth decide the insertion (`spaceteleop/sim/__init__.py` docstring) | pad friction, restitution, grasp-impulse transients; contact physics does apply before capture and before insertion, which is where the latency failure mode lives |
| Clock | realtime: the sim is stepped up to wall-clock elapsed and the emulator delays in wall clock, so injected latency, control lag and sim time share one time base (`spaceteleop/run.py` docstring) | faster-than-realtime runs; an episode costs its own wall-clock duration |
| Operator | `SyntheticOperator` with `tau_h` = 0.17 s, 0.07 m/s Cartesian speed easing to 5 cm/s for capture and 2 cm/s for peg, 1.5 mrad per-tick noise, jaw commanded at 18 mm seen distance (`spaceteleop/ground/operators.py`) | fatigue, learning, strategy switching such as move-and-wait emerging on its own |
| Concurrency | `--arms N` runs N independent triplets in one process for the 4-operator scaling case; experiment cells run one arm per process because threads share the GIL and inflate dwell (selection.md §3) | multi-host clocks, one-way delay measurement, network stacks other than loopback |
| Link | four profiles plus a sweep, below | packet reordering rates on Starlink (no finding, network_emulation §1.1), ISL stage effects |

### 7.3 Profiles

All delays are one-way per direction. Loss is Gilbert-Elliott; jitter is a mean-zero distribution of the stated SD (SYNTHESIS §7).

| Parameter | `zero` | `direct_gs` | `leo_relay` | `geo_relay` |
|---|---|---|---|---|
| Base delay up / down | 0 / 0 (loopback 22 µs measured, network_emulation §2) | 15 / 15 ms (network_emulation §4 P1; consistent with Kontur-2 20–30 ms RTT, space_teleop_prior_art §1) | 30 / 18 ms (network_emulation §4 P2) | 300 / 300 ms (network_emulation §4 P3) |
| Jitter | none | Gaussian, SD 2 ms (space_teleop_prior_art §1) | shifted log-normal, SD 14 ms up / 11 ms down, AR(1) ρ 0.25 `[unverified]` (network_emulation §1.1) | Gaussian, SD 2 ms `[unverified]` |
| 15 s structure | none | none | period 15 s; per-period shift U(−5, +5) ms `[unverified]`; uplink spike +74 ms decaying over 140 ms, downlink half; end bump +20 ms `[unverified]` over the last 75 ms (network_emulation §1.1) | none |
| Loss | 0 | GE(0.001, 0.2, 0, 0.3) → 0.15 % `[unverified]`; Kontur-2 measured 0.1 % | GE(0.0034, 0.2, 0, 0.3) → 0.5 % background plus 31 % of periods forced bad for their first 1 s; long-run ≈1.1 % (network_emulation §1.1) | GE(0.0091, 0.2, 0, 0.3) → 1.3 % (Analog-1 measured 1.27 %, space_teleop_prior_art §1) |
| Outages | none | none inside a pass | Poisson 1.7 h⁻¹; 87 % U(0.3, 2) s, 10 % U(2, 5) s, 3 % U(5, 31) s (network_emulation §1.1) | handover LOS 45 s every 45 min `[unverified]` (network_emulation §1.3) |
| Bandwidth cap up / down | none | 256 kbps / 100 Mbps (multi_operator_bandwidth §3; hardware_landscape §6) | 5 Mbps / 50 Mbps `[design choice]` | 20 / 90 Mbps (network_emulation §1.3) |
| Contact windows | always on | 9 min on, 35 min off, starting at a pass (network_emulation §1.4) | always on minus outages | always on minus handovers |
| Reordering | none | FIFO | allowed | FIFO |

`sweep:<rtt>` reuses the `leo_relay` structure with the base delay scaled to the requested RTT at the same 30:18 split; `sweep:0` separates structure from base delay (`spaceteleop/link/profiles.py`). Four corrections to the source values are recorded in SYNTHESIS §7, including the P2 loss parameter re-derived to yield the stated 0.5 % and the Casparsen spike read as +74 ms peak over 140 ms duration.

### 7.4 Safety criterion

Zero unsafe-motion events across all episodes on all four named profiles (SYNTHESIS §6). Unsafe motion is any of four counts, measured, not asserted (`spaceteleop/metrics/__init__.py`):

- `move_in_hold`: the commanded setpoint changed while in hold;
- `vel_over`: an emitted joint velocity above the clamp, on the satellite's applied-setpoint log;
- `keepout`: the end effector left the cage interior;
- `cage`: the arm touched the cage.

`hold`, `retract`, `ramp_clip`, `pos_clamp`, `jams` and `stale` are diagnostics.

### 7.5 Acceptance criterion

Solved means: on `leo_relay`, success ≥ 80 % of zero-latency success AND demos per hour ≥ 80 % of zero-latency demos per hour, with the safety criterion met on every profile (SYNTHESIS §6). The bar is a real discriminator: coarse pick-and-place throughput is 69 % of zero-latency at 250 ms and 49 % at 500 ms (teleop_fundamentals §1.2). The 163 ms relay machine loop sits under the 200 ms "ideal" bound for precision, so 80 % is expected to hold for coarse tasks and fail for insertion-class tasks with the baseline (SYNTHESIS §6). On `direct_gs` throughput is reported per pass, because every prior program was window-limited once delay was under about 1 s (space_teleop_prior_art §Implication). Smoothness is reported and never gated.

Two throughput metrics exist. `demos_per_hour` is 3600 over the mean wall time of successful episodes. `demos_per_hour_gross` charges every episode, failures and the teleoperated reset included (data_pipeline §3.2). Only the second moves under H20.

---

## 8. Hypothesis program

### 8.1 Pool and abstentions

Twenty slots across five axes: link path (L), transport (T), latency-hiding control (C), operator interface and workflow (O), task and data design (D) (SYNTHESIS §10). Seven returned a measured abstention, a "NO HYPOTHESIS" verdict with the argument written out: H03, H04, H05, H06, H13, H17 and H18 (selection.md §1). Each found the mechanism already owed to the baseline, the effect bounded below the 10 % bar on the acceptance profile, or a measured null. H13, for example, measured the baseline in the repo, found the whole `leo_relay` penalty under 5 % of throughput, and identified the one way a phantom display "wins" here as an artefact against the operator model, not the link (docs/hypotheses/H13.md). That rule became a rejection clause for two selected hypotheses.

### 8.2 Verifier scoring

Five verifiers, one per axis, scored every hypothesis on five 1–5 columns, evidence, testability, expected gain, cost (5 is cheap) and independence, out of 25 (docs/hypotheses/scores_V1.md). They spot-checked sources, reproduced arithmetic, and twice reproduced geometry with the repo's own `orbit.py`. The selection adjusted scores only for a stated reason and read every candidate against the working tree, which already contained most of what verifiers called "owed to the baseline": sequence keying, the (c) envelopes, the applied log, the unsafe-motion counts, the 20 mm envelope, the `peg` task and the §7 profiles (selection.md, opening table).

The fact that shaped the selection: on `leo_relay` the baseline sits near the ceiling on `capture`, so no hider can clear a +10 % bar on the acceptance profile with that task. The discriminating cells are the sweep from about 250 ms up, `geo_relay`, and `peg`. Every hider is therefore read as a shift of the success-versus-RTT knee (selection.md, opening).

### 8.3 The five selected strategies

Five hypotheses on three axes, C, O and D. No link-path or transport hypothesis survived its verifier on a primary metric; both axes reduced to baseline engineering plus one appendix sweep (selection.md §2). Each fits the `Strategy` seams in about 100 lines and is falsified by the same matrix.

**H10 `Twin` (arm T), merges H09.** The operator looks at a ground twin instead of delayed telemetry. The arm half shows the setpoint the ground itself sent at `now − tau_h`, since the arm's near future is fixed by the setpoints in flight; the object half extrapolates a finite-difference velocity over the lag the command still has to travel. It falls back to the raw frame during a hold or when the echo stalls (`spaceteleop/strategies/twin.py`). It attacks the whole machine loop on the operator's view, link 48 plus playout 30 plus dwell 17 ms, and the object chase error that fails capture at the 20 mm envelope (selection.md §2). Reject if: at `geo_relay` or any sweep point ≥ 500 ms demos per hour < 1.10× baseline; success below baseline anywhere; any unsafe-motion event or hold increase; jerk or SAL worse by > 20 %; or a gain on the `zero` cell beyond the seed spread, which would be a gain against the operator model (selection.md §3). `peg` reads as the arm-twin result, `capture` as the object result.

**H12 `DeadReckon` (arm D), merges H08.** The satellite fits a least-squares line over the last K = 8 setpoints in sequence time, never arrival time, and evaluates it L = 60 ms ahead of the newest packet, which is negative playout delay. Past a 100 ms horizon the baseline freeze takes over, and the result runs through the inherited hold, retract, ramp and clamp tail (`spaceteleop/strategies/deadreckon.py`). It attacks uplink plus playout, 60 of the 163 ms machine loop, from the satellite side, with no perception, so it is "supervisor-side extrapolation" and not the onboard-compute branch (selection.md §2). Reject if: at the best L on `leo_relay` demos per hour is not ≥ 10 % above baseline with the CI excluding zero, or success falls > 3 points, or any unsafe-motion event, or jerk > 2× baseline, or measured lag reduction < 0.5·L. The `leo_relay` clause is expected to reject from the ceiling; the hider is confirmed only if the knee moves right by ≥ 0.5·L with the CI excluding zero (selection.md §3).

**H14 `Gain` (arm G).** Scale the operator's Cartesian speed by the loop delay it is closing through. The operator's servo through delay L is the delayed integrator x' = −K·x(t − L), oscillatory above K·L = 1/e; pinning K·L at the `zero` value replaces overshoot-and-chase with a slower continuous approach. It scales the operator's speed, not the wire setpoint, which would measure windup instead (`spaceteleop/strategies/adaptive_gain.py`). It attacks the chase instability from about 250 ms at the 20 mm envelope (selection.md §2). Reject if: at 400 and 500 ms and on `peg`, success ≤ baseline + 10 points or demos per hour < 1.1× baseline; on `leo_relay` demos per hour < 0.9× baseline; the `zero`-cell control as for H10; and knock-away counts must fall where success rises (selection.md §3).

**H11 `Terminal` (arm P) with `TerminalGround` ablation (arm Pg). This is the onboard-compute branch.** The operator produces every approach and carry; delegated is only the segment latency destroys, the last ≤ 8 cm of a capture after the operator's own jaw-close command, or the last millimetres of an insertion after the commanded descent begins, bounded to 2 s. One damped-least-squares step per cycle from the true joint state at ≤ 7 cm/s, then a crossfade back onto the operator's stream so the hand-back never jumps. `Terminal` runs on the satellite from ground-truth pose, an upper bound on any estimator; `TerminalGround` runs the identical code on the ground from delayed telemetry; P − Pg is the measured value of onboard compute (`spaceteleop/strategies/terminal.py`). It attacks SYNTHESIS §6's predicted failure, the insertion or grasp event, and is the one thing SYNTHESIS §Implication says to run first (selection.md §2). Reject if, on `peg` `leo_relay` and `capture` ≥ 500 ms: success gain < 10 points with the CI covering zero, or demos-per-hour gain < 10 %; any unsafe-motion event; robot-executed frames > 25 % of successful episodes; the ground ablation within 5 points of onboard; or SAL and LDLJ worse than baseline (selection.md §3). The flight cost, a Jetson pose estimator and a Jetson-to-supervisor path, is reported next to the result.

**H20 `capture_chain` (arm C versus Cr), merges H15 and H16.** The demonstration ends with a re-release that seeds the next one, targets alternating A to B, so there is no canonical reset. A dead-band tether keeps the box in the working volume at zero force inside it. Arm Cr runs the same task with a canonical teleoperated reset: the same operator instance carries the box back to the spawn zone through the real link, and that time is charged (`spaceteleop/sim/__init__.py`; `spaceteleop/ground/operators.py`). It attacks reset wall time, which `demos_per_hour` charges at zero, and supplies the honest reset model the gross metric needs for every arm (selection.md §2). Reject if: chained gross demos per hour at `leo_relay` < 1.10× canonical, or success < 0.90×, or any unsafe-motion event, or SAL and LDLJ worse than the seed spread, because the release must not turn demonstrations into chases (selection.md §3). The tether-taut row fraction makes the "free 6-DoF" subset countable.

### 8.4 Experiment matrix

Common settings: 50 Hz commands, 30 Hz telemetry, 20 s episodes (30 s for `peg` and every ≥ 500 ms cell), `tau_h` 0.17 s, same seeds across arms within a cell, one `run.py` process per cell (selection.md §3). Eleven profiles: the four named plus `sweep:{0, 100, 250, 400, 500, 750, 1000}`.

| Block | Task | Arms | Profiles | tau_h | Cells |
|---|---|---|---|---|---|
| A | capture | B, T, D, G, P, Pg | all 11 | 0.17 | 66 |
| B | peg | B, T, D, G, P, Pg | all 11 | 0.17 | 66 |
| C | capture_chain free / teleop reset | C, Cr | zero, direct_gs, leo_relay, sweep:250, sweep:500, sweep:1000 | 0.17 | 12 |
| E | capture, peg | B, T, D, G, P | leo_relay, sweep:400, geo_relay | 0.25 | 30 |

Tier 1 is 174 cells × 30 seeds = 5,220 episodes, about 17 h serial or 4 h on five processes. Tier 2 confirms at 100 paired seeds on the sweep cell nearest the baseline knee plus each file's gating cell, about 2,700 episodes. A 10-point unpaired difference needs about 250 episodes per arm; same-seed pairing turns it into a McNemar test, and 100 paired seeds gives ≥ 80 % power for 10 points at ≤ 15 % discordance (selection.md §3). The achieved CI is always stated.

### 8.5 What was rejected and why

| ID | Status | One-line reason (selection.md §5) |
|---|---|---|
| H01 dense direct-pass network, 3 teams | DEFERRED | the ×2.5 is a duty-cycle fold with 12 operators; only the geometry is testbed-falsifiable, run as a 20-line `orbit.py` appendix |
| H02 dual-terminal hedged send | DEFERRED | −14 ms of jitter on a 333 ms loop; spikes are synchronous across terminals; iid emulator jitter flatters it |
| H03 relay control + direct-GS video | NO-HYPOTHESIS | gains 9 ms during 21 % of the time and opens a blind-commanding window; its ground-side telemetry-silence freeze is adopted |
| H04 two independent links, first-arrival | NO-HYPOTHESIS | outage exposure caps any gain at 1.4–5.7 % of episodes; its outage-rate sweep is adopted as an appendix |
| H05 uplink FEC / command repetition | NO-HYPOTHESIS | `leo_relay` loss never produces a gap over 160 ms against a 300 ms hold; seq-keying already in the baseline |
| H06 windowed setpoints per packet | NO-HYPOTHESIS | a lost 50 Hz command costs ≤ 1.4 mm of path; a transport-baseline note |
| H07 priority state stream decoupled from video | REJECTED | nominal gain 16 ms of 333; the saturated arm measures the emulator queue, not the operator |
| H08 send-timestamp scheduled playout | MERGED INTO H12 | its effect table is the seq-keying the baseline has; adaptive depth adds a 60 ms step at every 15 s spike |
| H09 ground-side phantom arm | MERGED INTO H10 | same mechanism; its phantom removes `tau_h` and its own criterion rejects its success |
| H13 latency-aware UI | NO-HYPOTHESIS | correct null on `leo_relay`; its `zero`-cell artefact rule is now a rejection clause for H10 and H14 |
| H15 pass-synchronous scheduler, onboard reset macro | MERGED INTO H20 | reset time is author-chosen so > 10 % is guaranteed; an onboard macro that carries the object is the excluded branch |
| H16 arm pool N > M with scripted resets | MERGED INTO H20 | same mechanism as H15 plus a session-mode controller it does not budget; 7.5 h realtime per sweep |
| H17 task segmentation at ≈ 333 ms | NO-HYPOTHESIS | measured null below 0.75 s; its jaw-scale envelope is already in the tree |
| H18 post-hoc relabeling | NO-HYPOTHESIS | moves no collection-time metric; the sat-side log it asked for is already in the tree |
| H19 seed-and-replay in pass gaps | REJECTED | replays are robot-executed and a replay moving the arm is an unsafe-motion event by the §6 definition |

---

## 9. Results

All numbers in this section come from `docs/experiments/results.md`, `results.json` and `paired.md` produced by `experiments/aggregate.py`. Nothing below is filled in until the matrix has finished.

### 9.1 Success versus RTT, per task and arm

`{{RESULTS:capture_curve}}`

| Arm | zero | sweep:100 | sweep:250 | sweep:400 | sweep:500 | sweep:750 | sweep:1000 | leo_relay | direct_gs | geo_relay |
|---|---|---|---|---|---|---|---|---|---|---|
| B baseline | | | | | | | | | | |
| T twin | | | | | | | | | | |
| D deadreckon | | | | | | | | | | |
| G gain | | | | | | | | | | |
| P terminal (onboard branch, upper bound) | | | | | | | | | | |
| Pg terminal ground (ablation) | | | | | | | | | | |

One table each for `capture` and `peg`; cells are success rate with a 95 % Wilson CI and n, then demos per hour, then RTT p50 / p95 measured from the echo.

### 9.2 Acceptance readout, SYNTHESIS §6

`{{RESULTS:acceptance_table}}`

| Arm | Task | leo_relay success / own zero | leo_relay demos/h / own zero | Unsafe events on zero, direct_gs, leo_relay, geo_relay | Verdict |
|---|---|---|---|---|---|
| B | capture | | | | |
| B | peg | | | | |
| T, D, G, P, Pg | capture, peg | | | | |

Per-pass throughput on `direct_gs` is listed separately.

### 9.3 Knees

`{{RESULTS:knees}}`

| Arm | Task | First RTT with success < 80 % of zero | Knee shift versus baseline, with CI |
|---|---|---|---|

### 9.4 Paired tests

`{{RESULTS:paired_tests}}`

| Task | Profile | Arm vs B | Paired success difference | Discordant seeds | McNemar exact p | Demos/h ratio, paired bootstrap 95 % CI |
|---|---|---|---|---|---|---|

Per hypothesis, the mechanism checks: twin innovation per frame (T), measured command-to-applied lag by cross-correlation against the applied log (D), knock-away counts (G, T), assist frame fraction and hand-back velocity peak with `ramp_clip(P) ≤ ramp_clip(B)` and `vel_over = 0` (P), and the P − Pg difference.

### 9.5 H20 gross throughput

`{{RESULTS:h20_gross}}`

| Profile | Arm | Success | demos/h spec | demos/h gross | Measured reset R, s | Tether-taut row fraction | SAL, LDLJ versus baseline |
|---|---|---|---|---|---|---|---|

### 9.6 Multi-arm scaling

`{{RESULTS:multi_arm}}`

| Arms in one process | Profile | Per-arm success | Per-arm demos/h | Wire up, B/s | Wire down, B/s | RTT p50 inflation versus one arm |
|---|---|---|---|---|---|---|

### 9.7 Smoothness distributions

SAL, LDLJ and stall fraction per arm and profile against the zero-latency baseline, reported and never gated. Included in `{{RESULTS:capture_curve}}`.

---

## 10. Verification

An independent audit reads the raw `summary.json` files, recomputes the aggregate tables from the per-seed vectors in `results.json`, checks every acceptance and rejection clause in selection.md §3 against the numbers, and confirms that the four unsafe-motion counts are zero on the four named profiles for every arm.

`{{RESULTS:audit_summary}}`

The audit also states which cells were skipped or crashed and retried by the resumable matrix runner, and whether any strategy's mechanism check failed even where its headline metric passed.

---

## 11. Near-future upgrades and what they change

- **Starlink third-party laser terminal, Q1 2027.** Muon Space's Halo flies in Q1 2027 and Starcloud's within a year of May 2026 (leo_link_options §2 b1). A measured latency and a published mass, power, price and allocation would settle SYNTHESIS §9 question 1. An RTT inside the 30–90 ms estimate changes nothing; above 150 ms the mission reverts to the pass regime and the 16U variant becomes competitive.
- **Kepler's 2028 constellation.** Continuous coverage of a non-Kepler-plane satellite needs it (leo_link_options §2 b2). A published latency would make Kepler a real second path with SDA-standard terminals already shipping; optical ground stations stay weather-limited at about 69 % single-site, 93.6 % with three (hardware_landscape §6).
- **Telesat Lightspeed and Amazon Leo.** Lightspeed slipped to 2028; Amazon has a NASA relay demonstration planned but no product (leo_link_options §2 b3, b4). Either adds a third relay vendor.
- **Onboard compute branch.** If P − Pg is positive and large on `peg`, the flight cost is a Jetson pose estimator and a Jetson-to-supervisor path, both excluded by (c). The 5 mm noise plus 33 ms lag cell bounds a real estimator. No rad-tolerant board with hardware video encode exists off the shelf; Aitech's S-A2300 would be the first (hardware_landscape §5).
- **Jitter distribution.** Only a 2–3 component Gaussian mixture is validated on Starlink (network_emulation §1.1). The emulator has a `dist` switch with exp, gauss, lognormal and gamma (`spaceteleop/link/profiles.py`); a GMM sampler and a sweep re-run is the cheapest sensitivity check not yet done.
- **Radiation-screened cameras.** Teledyne e2v's Ruby 1.3M USV is tested to 10 and 20 krad (hardware_landscape §4) and replaces the IMX296 if COTS hot-pixel growth matters.
- **Two-host operation.** One host makes one-way delay exact. Two hosts need RFC 7679 one-way delay with Moon–Skelly–Towsley skew removal, because RTT/2 is wrong by about 8 ms on Starlink (network_emulation §2).
- **Direct-pass density.** A 45-site network gives about 64 % duty by the verifier's reproduction (docs/hypotheses/scores_V1.md), but about 1× per operator-hour because it needs three regional teams. A schedule hedge, not a throughput gain.

---

## 12. Open questions and what remains unproven without flight

Ranked by design impact (SYNTHESIS §9).

1. **Measured latency and terms for a third-party satellite over Starlink mini-laser.** No measurement exists; mass, power, price, ITAR status and ground-side allocation are unpublished. This decides whether the primary path is real.
2. **Kepler latency and coverage of a non-Kepler-plane satellite.** Only "sub-second" from trade press; the datasheet's 95 % continuity and leo_link_options' "intermittent" estimate are unresolved.
3. **Radiation behaviour of COTS servos and the on-orbit Jetson reboot rate.** No TID or SEE data for Dynamixel or Feetech; no operator publishes Jetson reboot statistics.
4. **Does latency-collected demonstration data train worse policies?** No study collects demonstrations at controlled latency and reports policy success (data_pipeline §2.3). The link runs only through operator-quality proxies such as robomimic's proficiency result.
5. **Jitter distribution shape on Starlink.** The uplink one-way sum of 52 + 35 ms from idle probes also exceeds the 40 ms RTT median from M-Lab, and which dataset describes a laser-relayed satellite is unknown.
6. **Ground backhaul latency from any provider, and continuous-transmit thermal qualification of CubeSat X-band radios.**
7. **Packet reordering and ISL stage effects on relayed paths.**
8. **Capture task limits.** Safe release spin rate and target speed are rules of thumb `[unverified]` (unique_data_study §4).
9. **LeRobot loader tolerance** for a missing `stats/*` block and for sidecar files (data_pipeline §1.5, §3.2).

**Honest limits of the testbed.** Things the testbed cannot show, distinct from the research questions above.

- **Grasp physics.** The grasp is kinematic and MuJoCo has no restitution, so the grasp-impulse transients that make task 2 unique are absent. Capture success-versus-latency is a lower bound on real failure (SYNTHESIS §3; unique_data_study §5).
- **The operator is a model.** Fixed reaction delay, no move-and-wait, no learning, no fatigue. Whether its knee lands where human curves put it, ×1.45 at 250 ms and ×2.04 at 500 ms, is what §9 reports; a mismatch indicts the model, not the humans.
- **Video is bytes.** Compression, frame drops and stereo have no perceptual model, and VISTA shows success falling from 97 % to 35 % as bandwidth, delay and loss co-vary (multi_operator_bandwidth §1.3).
- **One host, one clock, one interpreter.** One-way delay is exact only because both ends share a clock. Threads share the GIL, so `--arms 4` measures the interpreter as much as the link; the matrix runs one arm per process for that reason.
- **No force.** No wrist force/torque and no contact detection beyond the sim's predicates, so nothing on delayed contact detection as a safety risk (teleop_fundamentals §4).
- **Unique-value tasks are absent.** Granular, liquid and deformable tasks have no MuJoCo proxy. The testbed proves the loop and the envelopes on two rigid-body proxies only.
- **`ramp_clip` is not a safety count.** A 1 kHz loop rendering a 50 Hz jittered stream clips thousands of times per episode even for the baseline; the decidable pair is `ramp_clip(P) ≤ ramp_clip(B)` on the same seeds and `vel_over = 0` (`spaceteleop/strategies/terminal.py`).

---

## 13. Appendix: repo map and how to reproduce

### Repo map

```
docs/
  PROGRAM.md                 charter and settled decisions
  TESTBED_SPEC.md            the decision-independent testbed spec
  research/                  eight research reports + SYNTHESIS.md (decision record)
  hypotheses/                H01-H20, scores_V1-V5, selection.md
  experiments/               results.md, results.json, paired.md, raw/<cell>/
  REPORT.md                  this document
spaceteleop/
  run.py                     runner: ground <-> link <-> sat over UDP, --profile --task --strategy
  proto/                     struct-packed command and telemetry datagrams
  link/emulator.py           UDP proxy: delay, jitter, GE loss, 15 s structure, outages, passes, caps
  link/profiles.py           zero, direct_gs, leo_relay, geo_relay, sweep:<rtt>
  link/orbit.py              sgp4 contact windows for a station list
  ground/loop.py             operator loop, RTT measurement, LeRobot rows
  ground/operators.py        SyntheticOperator (tau_h, DLS servo), KeyboardOperator
  sat/controller.py          seq-keyed buffer, strategy call, MuJoCo stepping, telemetry, applied log
  sim/__init__.py            SO-100 at g=0: capture, capture_chain, peg; cage; predicates
  strategies/                base, baseline, twin, deadreckon, adaptive_gain, terminal, registry
  record/                    LeRobot-v2-shaped npz writer + sat sidecar
  metrics/                   success, demos/h (spec and gross), RTT, safety counts, SAL, LDLJ
experiments/
  matrix.py                  selection.md section 3 as data + resumable subprocess runner
  aggregate.py               raw/*/summary.json -> results.md, results.json, paired.md
tests/                       53 tests: link, sat, sim/operator, proto/record, strategies, e2e, matrix
```

### Reproduce

Requirements: Python 3.12 via `uv`, macOS or Linux. The clock is realtime, so an episode takes its own wall-clock duration.

```
uv sync
uv run pytest -q                      # 53 tests, about one minute on an M4 Pro (verified 2026-09-12)

# one cell by hand
uv run python -m spaceteleop.run --profile leo_relay --task capture --episodes 8 --seed 0 \
    --out docs/experiments/raw/demo
uv run python -m spaceteleop.run --profile sweep:500 --task peg --strategy terminal --episodes 8
uv run python -m spaceteleop.run --profile leo_relay --arms 4 --episodes 2      # scaling case
uv run python -m spaceteleop.run --task capture_chain --reset teleop --profile leo_relay --episodes 20

# the matrix (selection.md section 3), resumable; one run.py process per cell
uv run python experiments/matrix.py --dry-run --tier 1 --strategies baseline,twin
uv run python experiments/matrix.py --tier 1 --blocks A,B \
    --strategies baseline,twin,deadreckon,gain,terminal,terminal_ground --ablations terminal_ground \
    --seeds 30 --jobs 5 --out docs/experiments/raw
uv run python experiments/matrix.py --tier 1 --blocks C --strategies baseline --seeds 30 --jobs 5
uv run python experiments/matrix.py --tier 1 --blocks E \
    --strategies baseline,twin,deadreckon,gain,terminal --seeds 30 --jobs 5
uv run python experiments/matrix.py --tier 2 \
    --arm-map T=twin,D=deadreckon,G=gain,P=terminal --seeds 100 --jobs 5

# aggregate
uv run python experiments/aggregate.py --raw docs/experiments/raw --out docs/experiments
```

`matrix.py` skips any cell whose `summary.json` exists without an error and retries crashed cells; every cell uses the same seed base, so arms are paired seed by seed. `aggregate.py` writes the per-task tables, the knee per arm, the SYNTHESIS §6 acceptance readout, and `paired.md` with McNemar exact p and paired-bootstrap demos-per-hour ratios.
