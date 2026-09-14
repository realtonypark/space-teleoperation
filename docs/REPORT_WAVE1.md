# Ground teleoperation of robot arms inside a LEO satellite for physical-AI data collection

Final report, 2026-09-13. Research numbers cite `report §section` (a file in `docs/research/`) or a repo path. Experimental numbers come from `docs/experiments/`: `tier1/results.md` and `tier1/paired.md` (Tier 1, 198 cells × 30 seeds), `tier2/results.md` and `tier2/paired.md` (Tier 2, 34 cells × 100 paired seeds), `scaling.md`, `outage_sweep.md`, `appendix_geometry.md`. Tier 2 is quoted where it exists, Tier 1 otherwise. `[design choice]` marks our values; `[unverified]` marks a figure no report could source.

---

## 1. Executive summary

**The question.** Can people on Earth teleoperate simple robot arms inside a rideshare-class LEO satellite well enough to collect physical-AI demonstration data that Earth-side simulation and labs cannot produce? The engineering objective is minimum end-to-end latency; the acceptance metric is demonstration quality and throughput relative to a zero-latency baseline (PROGRAM.md).

**The verdict.** Conditional yes (SYNTHESIS §1), now backed by measured numbers; no program has flown a manipulator inside a free-flyer under ground teleoperation (space_teleop_prior_art §2). Feasible with hardware buyable in 2026 if the mission flies a Starlink mini-laser relay terminal, first third-party flights Q1 2027, or accepts pass-limited sessions at a 21 % duty cycle through a four-site polar ground network. The task set is slow, coarse manipulation plus one insertion-class task that needs a latency hider.

On the emulated relay link the naive onboard baseline passes the acceptance bar on both proxy tasks. It fails capture from about 250 ms round trip and insertion from about 100 ms. Two of five latency hiders move those knees materially, one is harmful on one task and strong on the other, and the forced-dropout block recorded zero link-caused unsafe motion.

**The numbers that matter.**

| Number | Value | Source |
|---|---|---|
| Baseline `leo_relay` success as a fraction of own zero-latency success, `capture` / `peg` | 0.94 / 0.99 (100 paired seeds) | tier2/results.md |
| Baseline `leo_relay` demos per hour as a fraction of own zero, `capture` / `peg` | 1.02 / 0.98 | tier2/results.md |
| Baseline knee, first RTT with success under 80 % of own zero, `capture` / `peg` | 250 ms / 97 ms | tier1/results.md |
| Zero-latency ceiling, baseline `capture` | 0.69 (69/100); 0.67 (20/30) in Tier 1 | tier2, tier1 results.md |
| Link-caused unsafe-motion events, forced-dropout block S, 24 cells, 720 episodes | 0 | tier1/results.md, block S |
| Holds / retracts, baseline `capture`, 1 s outage and 12 s outage | 24 / 0 and 24 / 24 | tier1/results.md, block S |
| Best knee shift, `capture`: ground twin | 250 → 787 ms | tier1/results.md |
| Best knee shift, `peg`: onboard terminal primitive | 97 → never (> 1000 ms); 100/100 vs 1/100 at 400 ms | tier1/results.md; tier2/paired.md |
| Measured value of onboard compute, P − Pg, `peg` `leo_relay` | +0.44 success (1.00 vs 0.56, n = 100) | tier2/paired.md |
| Chained release vs canonical teleoperated reset, gross demos per hour, `leo_relay` | 472.2 vs 389.6 (×1.21), 30 seeds | tier1/results.md |

**The recommended architecture, in five bullets.**

- **Link.** Primary: two Starlink mini-laser terminals, 48 ms RTT median with 15 s spikes to about 125 ms. Fallback: direct passes through a four-site polar network. Safety channel: IDRS L-band or Iridium. GEO relay is disqualified by its propagation floor (SYNTHESIS §2).
- **Protocol.** A 50 Hz UDP stream of timestamped, sequence-keyed joint setpoints, 40 B payload, sent twice. Two lean 720p30 streams per operator at about 1 Mbps each, 10.4 Mbps downlink with FEC for four operators (multi_operator_bandwidth §2, §3).
- **Satellite.** Decision (c): 30 ms playout, hold at 300 ms, retract at 10 s, ramp-limited resume, static envelopes, hardware cutoffs, all on a rad-tolerant supervisor; no vision, no models (SYNTHESIS §5). The experiments add satellite-side dead reckoning for insertion-class tasks and one priced onboard-compute upgrade, a terminal insertion primitive.
- **Ground.** Leader-follower or VR without force feedback, a session broker granting one write authority per arm, 50 Hz follower rate (multi_operator_bandwidth §4; teleop_fundamentals §1.4). The experiments add a ground digital twin as the operator's display: the largest capture-task hider found, at no satellite cost.
- **Mission.** A pressurised ESPA-class bus (Apex Aries, 100 kg), a 100–300 L aluminium cylinder at 1 atm holding four Dynamixel-class arms, global-shutter cameras, a Jetson Orin NX for video, a separate deterministic supervisor. About $6–12 M including launch `[unverified]` (SYNTHESIS §4; hardware_landscape §7).

**Honest limits.** One machine and one clock; video is delay plus bytes; the grasp is kinematic behind a physical-jaw gate; the operator is a synthetic model with a fixed 170 ms reaction; the Starlink third-party latency is unmeasured by anyone; servo radiation behaviour is unknown; nothing has flown (§12).

---

## 2. Problem and scope

The charter (PROGRAM.md) fixes the goal: determine whether, and how, humans on Earth can teleoperate simple robot arms inside a LEO satellite to collect physical-AI demonstration data that Earth-side simulation cannot produce. We cannot launch, so the proof is a validated architecture plus a runnable testbed over real sockets.

**Fixed by the user.** Deliverable: architecture spec, testbed, experiments, this report. No human in the loop. Leader-follower or VR, no force feedback, synthetic operators. Onboard baseline at minimum (b): joint setpoints, a short interpolated buffer, hold or retract on timeout; no models or vision, one branch quantifying onboard compute. 4–8 arms, 4 concurrent operators. MuJoCo at zero gravity, TLE pass geometry, a UDP link emulator on localhost, video as delay plus bandwidth, LeRobot format. Default acceptance: 80 % of zero-latency success and demos per hour, zero unsafe motion on dropout. About 20 hypotheses, verifier-ranked, top 3–5 implemented against a naive baseline.

**Decided by research.** Link path, orbit, bus class, pressurisation, onboard capability level, task set, hardware stack and input device, under two constraints: rideshare-launchable, buyable today. Every agent cited or marked unverified, abstained over padding, and stayed in its lane (PROGRAM.md).

---

## 3. Feasibility today

### 3.1 What has flown

Three flown cases put an arm on a free-flying satellite under ground control: ETS-VII (1997–99, 5–7 s through a GEO relay), Orbital Express (2007, scripted autonomy) and Xiyuan-0 (2026, direct passes, no numbers). Every interior-arm case lived on a crewed station. Flown latency collapses to two regimes, direct passes at 20–30 ms with 4–20 min windows and GEO relay at 0.8–1.1 s; nothing between has been measured in orbit (space_teleop_prior_art §1, §2).

| Program | Direction | Round trip | Scheme | Lesson |
|---|---|---|---|---|
| ETS-VII 1997–99 | ground to orbit | 5–7 s | low-level commands, predictive display, interactive autonomy | link infrastructure caused the outages, not the robot |
| ROKVISS 2005–10 | ground to orbit | 20–30 ms, 0.1 % loss, ±2 ms jitter (jitter from the Kontur-2 row, same S-band link) | bilateral force feedback, 245 kbit/s up, 4 Mbit/s down | the only sub-100 ms space link ever flown, bought with a dedicated antenna and ≤7.5 min passes |
| Kontur-2 2015–17 | orbit to ground | 20–30 ms, ±2 ms jitter | 4-channel passivity | "30 ms is already a huge challenge for robotic control" |
| Haptics-2, Interact, SUPVIS-Justin, Analog-1 2015–19 | orbit to ground | 0.8–1.1 s | bilateral or supervisory over TDRS | the 1–3 s tail and dropouts hurt, not the mean |
| Canadarm2 / Dextre 2005– | ground to orbit | 0.3–0.5 s (secondary) | pre-validated sequences, LOS-safe motion | 170 days/yr, >100,000 commands, no continuous human loop |
| Astrobee 2019– | ground to orbit | not published | plans, hold on LOS, keep-out zones | the accepted ISS pattern for ground-driven robots |
| GITAI S1 2021 | ground to orbit | not published | autonomous then teleop, inside Bishop airlock | a commercial arm inside a pressurised volume; no numbers |
| Xiyuan-0 2026 | ground to orbit | "sub-second" | hand-controller teleop over direct passes | first commercial small-sat arm teleoperated by a human; no data |

All rows: space_teleop_prior_art §1.

### 3.2 Link ranking

| Rank | Path | RTT p50 / p95 | Coverage | Up / down | Why it wins or loses |
|---|---|---|---|---|---|
| 1 | Starlink mini-laser relay ×2 | 48 / 125 ms (network_emulation §4 P2) | >99 % with two terminals, Muon claim `[unverified]`, minus 1.7 outages/h (network_emulation §1.1) | 25 Gbps ISL; ground allocation unpublished | only continuous, sub-150 ms candidate; loses only on schedule, Q1 2027 first flights (leo_link_options §3) |
| 2 | Direct GS, 4 polar sites, X-band down, S-band up | 30 / 45 ms in contact (space_teleop_prior_art §1; network_emulation §1.4) | 21.3 %; 33 passes/day, 9.2 min mean, 35 min median gap (network_emulation §1.4) | 256 kbps / 100–150 Mbps (multi_operator_bandwidth §3; hardware_landscape §6) | only regime with flown, measured numbers; hard outages between passes |
| 3 | Kepler optical relay + SDA terminal | unpublished; 50–300 ms one-way `[unverified]` (hardware_landscape §6) | intermittent until 2028 (leo_link_options §2 b2) | 2.5 Gbps | live since 24 Aug 2026 but no latency figure; optical ground stations weather-limited |
| 4 | IDRS L-band / Iridium Certus | 0.5–1.5 s (hardware_landscape §6) | 80–100 % | 250 / 200 kbps | safety and heartbeat only |
| 5 | GEO relay (TDRS, EDRS, InRange) | 600 / 850 ms (network_emulation §1.3) | >99 % | 20 / 90 Mbps | propagation floor ≥474 ms is disqualifying; TDRS closed to new users Nov 2024 (leo_link_options §2 c) |

Source: SYNTHESIS §2. hardware_landscape §6 named Kepler as the buyable-today primary on a 95 % continuity datasheet claim; leo_link_options §2 b2 estimated it as not continuous with 10–33 satellites. The synthesis took leo_link_options because the 95 % is a full-constellation claim `[unverified]` and no Kepler latency number exists.

### 3.3 The "one product away" argument

The physics floor for a direct or Starlink-relayed link is 4–30 ms RTT (leo_link_options §1). Consumer Starlink measures a median 40 ms bent-pipe RTT across 19.2 million tests, a 15 s reconfiguration cycle and 1.7 outages per hour (network_emulation §1.1), with about 1 % loss (leo_link_options §1). SpaceX has flight-tested a 25 Gbps mini-laser terminal for third-party satellites; first hardware flies in Q1 2027 (leo_link_options §2 b1). One 4,000 km hop on the consumer median gives the 48 ms design RTT, 90 ms with margin (SYNTHESIS §2). Human tolerance leaves margin: coarse pick-and-place time grows ×1.45 at 250 ms and ×2.04 at 500 ms, precision insertion is "ideal" below 200 ms (teleop_fundamentals §1.2, §4), and the relay machine loop without the human is about 163 ms (SYNTHESIS §8). Two unknowns bound the verdict: no measured latency for a third-party satellite over Starlink inter-satellite links, and no radiation data for Dynamixel or Feetech servos (network_emulation §1.2; hardware_landscape §3).

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
 └───────────┬──────────────┘   telemetry 30 Hz + 2 live video streams/operator              │ 720p30 global shutter
             │                  720p30, ~1 Mbps each live, FEC, intra-refresh   ┌─────────────┴──────────────────────┐
 ┌───────────┴──────────────┐   (logged dataset cameras 1.5-2.5 Mbps, onboard)  │ Jetson Orin NX (may reboot)        │
 │ RECORDER                 │                                                   │  cameras, NVENC, mux, datasets     │
 │  LeRobot v2.1 layout     │                                                   │  never in the setpoint path        │
 │  sat-side applied log    │                                                   └────────────────────────────────────┘
 │  per-row link timestamps │
 └──────────────────────────┘
```

Two items are architecture, not testbed: the testbed sends each setpoint once (H05's measured null justifies it), and the live-stream rate is the lean 1 Mbps case of multi_operator_bandwidth §3, while hardware_landscape §4 prices logged dataset cameras at 1.5–2.5 Mbps. Section 7.6 lists every deviation.

### 4.2 Link path

Primary: Starlink mini-laser relay, two terminals so one re-acquires while the other carries traffic (leo_link_options §2 b1). Fallback: direct passes through the Svalbard, Troll, Inuvik and Punta Arenas union, 33.4 passes per day, 9.2 min mean, 35 min median gap (network_emulation §1.4; reproduced on a real TLE in §13.3). Safety channel: IDRS L-band or Iridium Certus, heartbeat and safe-mode only (hardware_landscape §6).

### 4.3 Protocol

| Element | Design | Source |
|---|---|---|
| Command uplink | seven float32 setpoints, 8 B timestamp, 4 B sequence: 40 B payload, 68 B over raw UDP/IPv4, 27 kbps at 50 Hz; a WebRTC data channel would double it to 133 B; sent twice at 100 Hz is still ≤0.2 Mbps per operator, and RFC 8854 favours retransmission only when RTT is inside the budget, so duplicate-send, not NACK | multi_operator_bandwidth §2 |
| Playout | keyed on sequence number, never arrival time: a command not newer than the newest received is dropped, because 6–8 % of consecutive packets arrive out of order on the emulated relay and playing a stale one is a backwards jump of the arm; the interpolator renders the buffer as it stood 30 ms ago in the satellite's own clock | `spaceteleop/sat/controller.py`; audit T17 |
| Telemetry | 30 Hz frames: joints, velocities, object pose, flags, and an echo of the last applied command's sequence, send timestamp and application time; RTT measured only at the ground from its own echoed timestamp with the satellite's dwell subtracted, stamped on arrival since the Phase 5 fix (before it the `zero` cell read 10 ms for a 1.25 ms loopback link); 45 B up, 123 B down | `spaceteleop/ground/loop.py`; audit T04 |

### 4.4 Satellite controller, decision (c)

The (b) baseline plus small deterministic safety logic, all on the rad-tolerant supervisor (SYNTHESIS §5).

| # | Rule | Value and reason | In the testbed |
|---|---|---|---|
| 1 | Sequence-sorted setpoint playout, linear interpolation, fixed playout delay | 30 ms `[design choice]`; buffering more than 50–70 ms of jitter costs more than it saves (teleop_fundamentals §2) | yes |
| 2 | Hold on timeout | 300 ms, between the 15 s uplink spike (+74 ms over 140 ms, must not trigger) and the outage tail (87 % under 2 s, must trigger) | yes |
| 3 | Retract to a stowed pose | after 10 s of silence `[design choice]`; reached only by the 3 % of outages lasting 5–31 s | yes |
| 4 | Ramp-limited resume | never a jump; 2 rad/s rated joint velocity `[design choice]` | yes |
| 5 | Static envelopes | joint position, velocity and acceleration clamps; keep-out box = cage interior (Astrobee, Canadarm2 pattern) | position clamp, velocity ramp, keep-out box; acceleration clamp is architecture only |
| 6 | Hardware cutoffs | per-motor thermal cutoff; latching current limiter at 80 % of peak (hardware_landscape §3) | hardware, not modelled |

Excluded: vision, learned models, force control, any subgoal primitive. The onboard-compliance result, nut threading 49 → 65–81 % (teleop_fundamentals §2), is the strongest hider in the evidence and is therefore the H11 branch. (c) beats (b) because every flown system that survived loss of signal did so with onboard envelopes; the logic sits on the supervisor because a Jetson single-event functional interrupt is a multi-second reboot (hardware_landscape §5).

### 4.5 Ground client

Leader-follower or VR without force feedback. Force coupling is what the delay tail impaired on Analog-1 and what needs passivity control; Haptics-2 and Interact ran it over GEO relay at 0.8 s and ETS-VII at 6–7 s, so it is dropped as irrelevant without force feedback, not as unstable (space_teleop_prior_art §1; teleop_fundamentals §2). The follower runs at 50 Hz regardless of link rate; 5 Hz teleop cost 62 % more time (data_pipeline §2.1). A session broker implements the Astrobee and ISS POIC pattern: one commanding authority per arm, read-only observers, pass-sized booked slots (multi_operator_bandwidth §4).

In the testbed the human is a synthetic operator: it sees only link-delayed telemetry, reacts to what it saw 0.17 s ago, the human online visuomotor correction latency of 143–170 ms (teleop_fundamentals §3), and commands a position at bounded Cartesian speed (`spaceteleop/ground/operators.py`). Policy and gains are identical at every latency.

### 4.6 Video pipeline budget

Global-shutter MIPI or GMSL camera, hardware encoder with intra-refresh and no B-frames, 0–10 ms playout hint, 60–144 Hz display; the 100 ms USB-webcam path is disqualifying (multi_operator_bandwidth §1.2). Two live streams per operator at about 1 Mbps size the link; other dataset cameras are logged onboard at 1.5–2.5 Mbps (multi_operator_bandwidth §1.3; hardware_landscape §4).

| Operators | Streams | Downlink video | Downlink with FEC and headers | Uplink at 100 Hz, sent twice |
|---|---|---|---|---|
| 4 | 2 mono 720p30 at 1 Mbps (lean) | 8 Mbps | 10.4 Mbps | 0.85 Mbps |
| 4 | 3 mono 720p30 at 2.5 Mbps (standard) | 30 Mbps | 39 Mbps | 0.85 Mbps |
| 8 | 2 mono lean | 16 Mbps | 20.8 Mbps | 1.7 Mbps |
| 8 | 3 mono standard | 60 Mbps | 78 Mbps | 1.7 Mbps |

Source: multi_operator_bandwidth §3. The lean case fits X-band direct-to-Earth at 100–150 Mbps and any relay; S-band alone supports one lean operator (hardware_landscape §6). The four-arm run (§9.10) measured 250 kB/s down per arm, consistent with this table. Bandwidth is not the constraint.

### 4.7 Latency budget

| Stage | ms | Source |
|---|---|---|
| Sensor exposure + readout, 720p30 global shutter | 25 | hardware_landscape §4 (16–33) |
| Encode, Jetson NVENC 720p H.264 | 8 | hardware_landscape §4; multi_operator_bandwidth §1.2 |
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

The human is 51 % of the loop, the link 14 %, the playout buffer 9 %; in the Anvari telesurgery series only 14 ms of 135 was network (teleop_fundamentals §3). On `direct_gs` the sum is about 315 ms, on `geo_relay` about 885 ms (SYNTHESIS §8).

### 4.8 Data pipeline

The testbed writes a LeRobot-v2.1-shaped dataset: one `.npz` per episode in place of parquet, `meta/info.json` with the v2.1 keys a loader parses, `meta/episodes.jsonl`, `meta/tasks.jsonl`, the standard columns plus `task_index`, and extras `cmd_seq`, `rtt_ms`, `owd_up_ms`, `safety_hold` and `assist` (`spaceteleop/record/__init__.py`). The one deliberate deviation: `data_path` points at `.npz` with no parquet or stats block, because nothing here reads the data through `lerobot`. LeRobot's `timestamp` is synthetic, so link timing lives in extra columns (data_pipeline §1.2).

Three choices come from the data-quality evidence. A **satellite-side applied log**, one row per control cycle, because the main table carries about 85 ms of observation-action skew on `leo_relay` (`spaceteleop/record/__init__.py` docstring); smoothness is computed on it (audit T05). **Per-row link timestamps** for latency matching at deployment (data_pipeline §2.3): `rtt_ms`, `owd_up_ms` (RTT/2, off by about 6 ms on the relay profile, audit T18) and the boolean `safety_hold`; the `link_state` enumeration of data_pipeline §3.1 is a proposal, not a recorded column. **Curation metrics, reported not gated**: robomimic "Worse" operators reached 92 % on Can but produced 39 % versus 66 % policies on Square, and top-half selection by spectral arc length lifted policy success 39 → 55 % (data_pipeline §2.1), so SAL, LDLJ and stall fraction are reported per episode (SYNTHESIS §6).

---

## 5. Mission shape and hardware stack

**Bus class: ESPA.** Continuous payload draw is 100–190 W, 2–5× a 16U CubeSat's orbit-average and 55–100 % of the Apex Aries' 175 W end-of-life power (hardware_landscape §1). The Aries carries 100 kg on a SpaceX rideshare, first flew in 2024, and costs $3.5–9.5 M. hardware_landscape §7 derives a launch price of about $1.05 M for a 150 kg ESPA slot ($350 k plus 100 kg at $7,000/kg); the same rule gives about $0.7 M at the 100 kg configuration used here.

**Pressurisation: yes.** A 100–300 L aluminium cylinder at 1 atm weighs 3.5–10 kg with fittings. Brushed motors and hobby servos need atmosphere. A vacuum-rated arm such as the 50 kg GITAI IN2 would consume half the Aries' payload for one arm and exceeds the whole payload budget of a 16U, so it is not fundable at this scale (hardware_landscape §2, §7). Tasks 1 and 3 prefer a pressurised bus (unique_data_study §4).

**Arms: four in the baseline, eight as the scale branch.** Four is what four operators use, what the bandwidth budget is sized for, and what unique_data_study §5 allocates cells to. The precedent is Astrobee: stock Dynamixel X servos, a current cutoff at 80 % of peak, a thermostat per motor, on the ISS since 2019 (hardware_landscape §3).

| Subsystem | Choice | Source |
|---|---|---|
| Bus + launch | Apex Aries 100 kg + SpaceX rideshare, ≈$0.7–1.05 M launch by slot mass | hardware_landscape §1, §7 |
| Enclosure | 100–300 L 1-atm Al cylinder, domed ends, 3.5–10 kg | hardware_landscape §2 |
| Arms | 4× Dynamixel-X 6-DoF + parallel gripper, XM430 on loaded joints | hardware_landscape §3 |
| Cameras | 4–8× IMX296 or AR0234 global shutter, 720p30, logged at 1.5–2.5 Mbps each | hardware_landscape §4 |
| Compute | Jetson Orin NX (cameras, NVENC, mux) + rad-tolerant supervisor MCU (setpoint buffer, hold/retract, watchdog, current limiters) | hardware_landscape §5 |
| Relay | 2× Starlink mini-laser terminals; mass and power unpublished, budget conservatively | leo_link_options §2 b1 |
| Direct to Earth | Syrlinks EWC27 X-band down + S-band receive | hardware_landscape §6 |
| Safety channel | IDRS L-band 250 kbps or Iridium Certus 9770 | hardware_landscape §6; leo_link_options §2 d |
| Thermal | 0.1–0.25 m² radiator, heat strap from cylinder wall | hardware_landscape §6 |

Order-of-magnitude total: $6–12 M including launch `[unverified]`; the bus dominates (hardware_landscape §7).

**Top risks** (hardware_landscape): no buyable path is both continuous and low-latency in 2026, and the Starlink mini laser's mass, power, price and ITAR status are unpublished; COTS radiation behaviour is unquantified, with Jetson TX2 boards dead at 9.7–25 krad; 100–190 W continuous rules out 12U and 16U, and no CubeSat X-band datasheet states a continuous-transmit qualification.

**What a 16U pass-only variant gives up.** The continuous link is the most cost-driving decision: relay terminals at 40–70 W plus continuous downlink power push the payload past any CubeSat class (SYNTHESIS §4). A 16U supports about 8 L, one or two small arms, passes only at 21 % duty (hardware_landscape §1, §2). It keeps the flown 20–30 ms regime and suits a flight that validates the link emulator against a real pass.

---

## 6. Task set and why the data is unobtainable on Earth

No Earth analog gives 6-DoF free motion for longer than about 24 s; parabolic flight measures 0.041 ± 0.005 g in its "zero g" phase; drop towers reach 1e-4 to 1e-5 g for 5–9 s with no operator loop (unique_data_study §1). The residual gap after the best simulator and analog ranks: granular media below 1e-4 g, which "cannot be extrapolated" from 1e-2 g data; fluids, with only qualitative CFD comparison; deformables, simulation-only; and free-floating capture, where MuJoCo has no restitution coefficient. Arm-base coupling, tool use, vacuum contact and lighting rank 5 to 8 (unique_data_study §2).

| # | Task | Phenomenon exposed | Latency sensitivity |
|---|---|---|---|
| 1 | Scoop, transport, pour sieved granular simulant (<250 µm) between open trays in a transparent cell | regolith behaviour below 1e-4 g (unique_data_study §2 A) | low: coarse class, degrades at 250 ms, unusable ≥750 ms |
| 2 | Capture and re-release of a slowly spinning cm-scale rigid object (≤1 rad/s, ≤2–5 cm/s `[unverified]`) | real grasp impulses on a truly free 6-DoF body (unique_data_study §2 D) | medium: approach tolerant to 225 ms; the grasp event is precision-class, ~150–200 ms |
| 3 | Partially filled liquid container handling and capillary pour | long-duration slosh, capillary flow, contact-line dynamics (unique_data_study §2 B) | low: capillary flows take seconds |
| 4 | Cable routing and fabric pouch open/close (30 cm cable, two connectors, Velcro pouch) | deformable dynamics in microgravity (unique_data_study §2 C) | medium: connector mating is insertion-class, ~150–200 ms |
| 5 | Peg-in-hole on a fixture rigidly mounted to the bus, wheel torques logged | arm-base momentum coupling and base identification (unique_data_study §2 E) | high: precision insertion, ideal <200 ms, drops 500–700 ms |

Source: SYNTHESIS §3; latency classes from teleop_fundamentals §4. Tasks 1–4 are the unique-value payload; at least two arms carry a granular cell and one a liquid cell (unique_data_study §5). Tasks 2 and 5 are the MuJoCo proxies; capture results are a lower bound because grasp-impulse transients are not simulated (SYNTHESIS §3). The slowness of the unique-value tasks is the largest latency hider available (SYNTHESIS §10). The measured knees in §9 land where the table predicts.

---

## 7. The testbed

### 7.1 What it is

Python 3.12 with mujoco, numpy, sgp4 and robot-descriptions (the SO-100 MJCF) as runtime dependencies, pytest for tests (`pyproject.toml`). Three roles run as threads in one interpreter over real UDP sockets on 127.0.0.1 (`spaceteleop/run.py`).

| Role | Module | What it does |
|---|---|---|
| Ground | `spaceteleop/ground/` | hands the operator a frame `tau_h` old, sends 7-slot setpoints at 50 Hz, measures RTT from the echo, stamped on arrival |
| Link | `spaceteleop/link/emulator.py` | UDP proxy, two independent directions, each a receive thread that heaps a release time and a drain thread; measured mean one-way delay is nominal plus 0.3–1.0 ms (audit_testbed E1); each episode draws a random phase of the 15 s structure and the outage schedule (audit T03) |
| Satellite | `spaceteleop/sat/controller.py` | sequence-keyed buffer, strategy call at about 1 kHz, MuJoCo stepped up to wall clock, 30 Hz telemetry, keep-out and cage counters, applied-setpoint log per cycle |
| Sim | `spaceteleop/sim/` | MuJoCo at zero gravity with the SO-100. `capture`: a 16 mm box drifting at 2–4.5 cm/s and tumbling at 0.3–1 rad/s, a 25 mm capture envelope, a 50 mm target held 0.2 s; a capture requires the physical jaw closed past 0.062 rad, where the pad gap equals the box diagonal, or pinched with both pads on the box, never the close command alone. `peg`: a 60 mm peg, 6 mm radial clearance, unknown grasp offset up to 6 mm, a jam rule on fixture contact. `capture_chain` adds a dead-band tether and alternating targets. A six-wall cage, 0.64 × 0.66 × 0.48 m, is the keep-out box |
| Strategy hook | `spaceteleop/strategies/base.py` | `observe`, `ground_step`, `sat_step`; registry `baseline`, `twin`, `deadreckon`, `deadreckon30`, `gain`, `terminal`, `terminal_ground` |

### 7.2 What it models, and what it does not

| Aspect | Modelled as | Not modelled |
|---|---|---|
| Video | delay in the latency budget plus a `--frame-bytes` field padded onto telemetry so the bandwidth cap bites, up to 8 kB per frame at 30 Hz for a ~2 Mb/s budget (`spaceteleop/sat/controller.py`) | codec, frame content, perceptual quality |
| Grasp | kinematic: once the physical jaw is shut on a box inside the 25 mm envelope the object rides the grasp site; the peg is held rigidly upright so only XY alignment and depth decide the insertion (`spaceteleop/sim/__init__.py`) | pad friction, restitution, grasp-impulse transients; contact physics does apply before capture and before insertion, where the latency failure mode lives |
| Clock | realtime: the sim is stepped up to wall-clock elapsed and the emulator delays in wall clock (`spaceteleop/run.py` docstring) | faster-than-realtime runs; an episode costs its own wall-clock duration |
| Operator | `SyntheticOperator` with `tau_h` = 0.17 s, 0.07 m/s Cartesian speed easing to 5 cm/s for capture and 2 cm/s for peg, 1.5 mrad per-tick noise, jaw commanded at 18 mm seen distance (`spaceteleop/ground/operators.py`) | fatigue, learning, strategy switching such as move-and-wait |
| Concurrency | `--arms N` runs N independent triplets in one process for the scaling case; experiment cells run one arm per process because threads share the GIL and inflate dwell (selection.md §3) | multi-host clocks, one-way delay measurement, network stacks other than loopback |
| Link | eight named profiles plus a sweep, below | packet reordering rates on Starlink (no finding, network_emulation §1.1), ISL stage effects |

### 7.3 Profiles

One-way delays per direction; Gilbert-Elliott loss; mean-zero jitter of the stated SD (SYNTHESIS §7). The audit verified every value in `spaceteleop/link/profiles.py`: GE loss 0.153 / 0.493 / 1.302 % measured against 0.149 / 0.501 / 1.306 % nominal, burst fraction 30.2 % against 31 %, Poisson rate 1.70–1.72 h⁻¹, and the outage mixture, spike, jitter and pass windows (audit_testbed E1).

| Parameter | `zero` | `direct_gs` | `leo_relay` | `geo_relay` |
|---|---|---|---|---|
| Base delay up / down | 0 / 0 (loopback 22 µs measured, network_emulation §2) | 15 / 15 ms (network_emulation §4 P1; Kontur-2 20–30 ms RTT) | 30 / 18 ms (network_emulation §4 P2) | 300 / 300 ms (network_emulation §4 P3) |
| Jitter | none | Gaussian, SD 2 ms (space_teleop_prior_art §1) | shifted log-normal, SD 14 ms up / 11 ms down, AR(1) ρ 0.25 `[unverified]` (network_emulation §1.1) | Gaussian, SD 2 ms `[unverified]` |
| 15 s structure | none | none | period 15 s, random phase per episode; per-period shift U(−5, +5) ms `[unverified]`; uplink spike +74 ms decaying over 140 ms, downlink half; end bump +20 ms `[unverified]` over the last 75 ms | none |
| Loss | 0 | GE(0.001, 0.2, 0, 0.3) → 0.15 % `[unverified]`; Kontur-2 measured 0.1 % | GE(0.0034, 0.2, 0, 0.3) → 0.5 % plus 31 % of periods forced bad for their first 1 s; long-run ≈1.1 % | GE(0.0091, 0.2, 0, 0.3) → 1.3 % (Analog-1 measured 1.27 %) |
| Outages | none | none inside a pass | Poisson 1.7 h⁻¹; 87 % U(0.3, 2) s, 10 % U(2, 5) s, 3 % U(5, 31) s | handover LOS 45 s every 45 min `[unverified]` |
| Bandwidth cap up / down | none | 256 kbps / 100 Mbps | 5 Mbps / 50 Mbps `[design choice]` | 20 / 90 Mbps |
| Contact windows | always on | 540 s on, 2100 s off, starting at a pass | always on minus outages | always on minus handovers |
| Reordering | none | FIFO | allowed | FIFO |

**Forced-outage profiles (block S).** `leo_relay_drop1` and `leo_relay_drop12` are `leo_relay` plus one deterministic blackout in both directions 6.0 s after link start, lasting 1.0 s or 12.0 s. The 1 s outage trips the 300 ms hold; the 12 s outage crosses the 10 s retract, so the arm stows and resumes ramp-limited; `drop12` cells run at 30 s. They exist because the Poisson schedule puts an outage inside a 20 s episode 0.9 % of the time per direction, so blocks A, B and E never exercised hold or retract (audit T02). `leo_relay_out5` and `leo_relay_out12` raise the Poisson rate to 5 and 12 h⁻¹ (§9.11).

**Sweep.** `sweep:<rtt>` reuses the `leo_relay` structure with the base delay scaled to the requested RTT at the same 30:18 split. `sweep:0` clips the log-normal jitter at zero, so its realised base round trip is about 12 ms (6.5 / 5.4 ms one way; audit T08). Four corrections to the source values are recorded in SYNTHESIS §7.

### 7.4 Safety criterion

Zero link-caused unsafe-motion events across all episodes (SYNTHESIS §6, as implemented). Three counts gate, measured on the satellite's applied log (`spaceteleop/metrics/__init__.py`): `move_in_hold`, the setpoint changed while in hold; `vel_over`, an emitted joint velocity above the clamp; `keepout`, the end effector left the cage interior. `cage`, the arm touching the cage, is its own column and does not gate: it fires at zero latency on every arm (10 of 30 baseline episodes) because the box spawns 10–16 cm from the −y wall and the chase runs the arm into it (audit T07). `vel_over` cannot fire by construction (audit F9), so the independent safety evidence is `move_in_hold` and `keepout` on block S plus the sidecar velocity check. `hold`, `retract`, `ramp_clip`, `pos_clamp`, `jams` and `stale` are diagnostics; `stalls` and `max_dt_s` flag CPU contention (audit T06).

### 7.5 Acceptance criterion

Solved means: on `leo_relay`, success ≥ 80 % of zero-latency success AND demos per hour ≥ 80 % of zero-latency, with the safety criterion met on every profile (SYNTHESIS §6). The bar discriminates: coarse pick-and-place throughput is 69 % of zero-latency at 250 ms (teleop_fundamentals §1.2). On `direct_gs` throughput is also reported per 9.2 min pass. Smoothness is reported, never gated.

`demos_per_hour` is 3600 over the mean wall time of successful episodes; `demos_per_hour_gross` charges every episode, failures and teleoperated reset included (data_pipeline §3.2). Since the fix, wall time ends at the satellite's success or done stamp; the 1.0 s linger is excluded (audit T09, F2). The pre-fix run carried about 1 s per episode, which compressed every throughput ratio toward 1.

### 7.6 Where the testbed deviates from the architecture

| Architecture says | Testbed does | Note |
|---|---|---|
| setpoints sent twice | sent once | H05's measured null: `leo_relay` loss never gaps over 160 ms against a 300 ms hold |
| acceleration clamp | none | position clamp and velocity ramp only |
| `link_state` column | none | rows carry `rtt_ms`, `owd_up_ms`, `safety_hold` |
| measured one-way delay | `owd_up_ms` = RTT/2 | possible on one host, not logged |
| `geo_relay` ±13 ms orbital drift | none | network_emulation §4 P3 |
| `direct_gs` loss ×10 below 10° elevation | constant loss | SYNTHESIS §7 clause not implemented |
| jitter shape switch | log-normal σ fixed at 0.6 | only the SD is a profile knob |
| video codec | padding bytes only | |
| Gilbert-Elliott with rate dependence | per packet at 50 Hz | |
| H20 tether force-free while slack | damping −0.01·v applies inside the dead band | a box released at 4.1 cm/s is at 2.5 cm/s after 6 s (`spaceteleop/sim/__init__.py` `_tendon`) |

### 7.7 Phase 5: the audits and what they changed

Two adversarial audits ran against unmodified code while the first Tier 1 matrix was executing: `docs/experiments/audit_testbed.md` (T01–T20) and `docs/experiments/audit_strategies.md` (F1–F13). Their findings changed what the numbers mean, so the first run was archived and everything was re-run after two fix commits, "phase5: apply testbed audit fixes" (5dc0be5, 25 files) and "phase5: fix capture_chain regression" (bb133ea).

**What the audits found.**

| ID | Finding | Effect on the numbers |
|---|---|---|
| T01, critical | capture keyed on the jaw close command inside a 20 mm sphere; a box 18 mm away with the jaw fully open counted as grasped | success inflated at every latency, most for arms that time the close |
| T02, critical | the Poisson schedule never put a blackout inside an episode | `move_in_hold = 0` was vacuous; "zero unsafe motion on dropout" untested |
| T03 | 15 s structure phase-locked to link start | the spike never touched a live command in a successful episode |
| T04 | telemetry stamped at the next 50 Hz tick | U(0, 20 ms) added to every RTT sample; `zero` read 10 ms |
| T05 | smoothness on a 50 Hz sample-and-hold of 30 Hz telemetry | `stall_frac` 0.24 → 0.51, LDLJ −5.2 → −14.5 on a synthetic move |
| T06 | eight cells with CPU-contention stalls, incl. Gain's `zero` cell | those episodes measure neither profile nor strategy |
| T07 | `cage` fires at zero latency for every arm | a gate that summed it failed everywhere |
| T08, T10, T11, T17, T18, T20 | `sweep:0` realises at ≈12 ms; no per-pass figure; recorder not loadable by LeRobot v2.x; reordering 6–8 %; `owd_up_ms` = RTT/2; Wilson and McNemar match closed forms | labelling and metadata |
| F1 | DeadReckon led the baseline by 90 ms, not the labelled 60 | a 1.5× easier bar for H12 |
| F2 | the 1 s linger in every duration | every throughput ratio compressed toward 1 |
| F3 | the twin's small zero-cell gain is link-independent by construction | subtract it as a ratio of ratios; do not use it as a rejection |
| F5 | Gain's hard-coded L0 = 0.29 s sat 58 ms above the measured zero-latency loop | G was literally B on `leo_relay`; a different controller on block E |
| F9 | `vel_over` cannot fire: the ramp bounds every step | a zero there is not evidence |

**What was fixed** (commit 5dc0be5): physical-jaw capture with the envelope raised from 20 to 25 mm to pay for the 0.6 s of real jaw travel (zero-latency baseline over 30 seeds: 21/30 on the old predicate, 16/30 with the physical jaw at 20 mm, 18/30 at ≥24 mm); random per-episode phase; arrival-stamped telemetry; smoothness from the sidecar; `stalls` and `max_dt_s` with `--exclude-stalled`; linger-free durations; the forced-outage profiles and block S; LeRobot v2.1 metadata; DeadReckon's lead made exactly L; Gain's L0 = playout + half a telemetry period + tau_h + measured zero RTT = 30 + 16.7 + 170 + 2 = 0.219 s.

**The chain regression** (commit bb133ea): the physical-jaw predicate required the jaw angle below 0.062 rad, but a box pinched between the pads stops the jaw at its own projected width, up to the 27.7 mm space diagonal of a tumbling cube (0.068–0.083 rad). The predicate never fired on a real grasp, the operator sat in `closing` forever, and because `capture_chain` never resets the scene the wedged box was inherited by every later demonstration (chained zero run 3/30). The fix counts a pinch, both pads bearing on the box with the jaw commanded shut, as a capture; both branches still need the real jaw travel. Result: 3/30 → 30/30, and every Tier 1 cell was re-run.

**What the fixes changed in the numbers.** The `zero` cell RTT went from 10 ms p50 to 2 ms p50, 3 ms p95 (measured loopback link RTT 1.25 ms). The zero-latency capture ceiling went from 21/30 to 20/30. `stall_frac` on `zero` went from 0.47 to 0.02. Block S records 24 holds and 24 retracts per `drop12` cell. Contaminated cells went from 8 to 0. The pre-fix set is archived under `docs/experiments/tier1_prefix/`; none of its numbers are cited here.

---

## 8. Hypothesis program

### 8.1 Pool and abstentions

Twenty slots across five axes: link path, transport, latency-hiding control, operator interface, task and data design (SYNTHESIS §10). Seven returned a measured abstention: H03, H04, H05, H06, H13, H17 and H18 (selection.md §1). H13 found the whole `leo_relay` penalty under 5 % of throughput and showed that a phantom display "wins" only as an artefact against the operator model; that rule became a rejection clause for two selected hypotheses.

### 8.2 Verifier scoring

Five verifiers, one per axis, scored each hypothesis on evidence, testability, expected gain, cost and independence, 1–5 each, out of 25 (docs/hypotheses/scores_V1.md); the selection adjusted scores only for a stated reason (selection.md §1). The fact that shaped it: on `leo_relay` the baseline sits near its own ceiling on `capture`, so no hider can clear a +10 % bar there, and the ceiling is 0.63–0.77 on `zero`, not 1.0 (§9.1). Every hider is read as a shift of the success-versus-RTT knee.

### 8.3 The five selected strategies

Five hypotheses on axes C, O and D; no link-path or transport hypothesis survived its verifier on a primary metric (selection.md §2). Each fits the `Strategy` seams in about 100 lines. Each file's reject clauses, as amended in selection.md §3, are quoted clause by clause in the §9.7 tables.

**H10 `Twin` (arm T), merges H09.** The operator looks at a ground twin: the arm half shows the setpoint the ground itself sent at `now − tau_h`, the object half extrapolates a finite-difference velocity over the lag the command still has to travel; both fall back to the raw frame during a hold (`spaceteleop/strategies/twin.py`). Audit F3 amends its `zero`-cell clause: the twin has a small link-independent gain at zero by construction, so profile gains are read as a ratio of ratios.

**H12 `DeadReckon` (arm D), merges H08.** The satellite fits a least-squares line over the last 8 setpoints in sequence time and evaluates it exactly L = 60 ms ahead of the baseline playout (post audit F1); past a 100 ms horizon the baseline freeze takes over and the result runs through the inherited hold, retract, ramp and clamp tail (`spaceteleop/strategies/deadreckon.py`). Supervisor-side extrapolation, no perception. Its `leo_relay` throughput clause is expected to reject from the ceiling; the hider is confirmed only if the knee moves right by ≥ 0.5·L. A `deadreckon30` variant was not run.

**H14 `Gain` (arm G).** Scale the operator's Cartesian speed by the loop delay it closes through: the servo through delay L is the delayed integrator x' = −K·x(t − L), oscillatory above K·L = 1/e, so pinning K·L at the zero-latency value replaces overshoot-and-chase with a slower approach (`spaceteleop/strategies/adaptive_gain.py`); the pin point L0 is the measured zero-latency loop, 0.219 s (audit F5). It is evaluated at 400 and 500 ms and on `peg`, with a default-on clause on `leo_relay` and a knock-away mechanism check.

**H11 `Terminal` (arm P) with `TerminalGround` ablation (arm Pg). This is the onboard-compute branch.** Delegated is only the last ≤ 8 cm of a capture after the operator's own jaw-close command, or the last millimetres of an insertion, bounded to 2 s at ≤ 7 cm/s, with a crossfade back onto the operator's stream. `Terminal` runs on the satellite from ground-truth pose, an upper bound on any estimator; `TerminalGround` runs the identical code on the ground from delayed telemetry; P − Pg is the measured value of onboard compute (`spaceteleop/strategies/terminal.py`). The headline cell is `peg` `leo_relay`, with `capture` ≥ 500 ms secondary. The 5 mm noise plus 33 ms lag lower-bound cell was not run.

**H20 `capture_chain` (arm C versus Cr), merges H15 and H16.** The demonstration ends with a re-release that seeds the next one, targets alternating, so there is no canonical reset; a dead-band tether keeps the box in the working volume. Arm Cr runs the same task with a canonical teleoperated reset by the same operator through the real link, and that time is charged (`spaceteleop/sim/__init__.py`). The gate is gross demos per hour at `leo_relay` ≥ 1.10× canonical. The tether's damping caveat (§7.6) qualifies the "free 6-DoF body" claim.

### 8.4 Experiment matrix as run

Common settings: 50 Hz commands, 30 Hz telemetry, 20 s episodes (30 s for `peg`, ≥ 500 ms cells and `drop12`), `tau_h` 0.17 s, same seeds across arms, one process per cell (`experiments/matrix.py`). Eleven profiles for blocks A, B and E: the four named plus `sweep:{0, 100, 250, 400, 500, 750, 1000}`; block S adds two.

| Block | Task | Arms | Profiles | tau_h | Cells |
|---|---|---|---|---|---|
| A | capture | B, T, D, G, P, Pg | all 11 | 0.17 | 66 |
| B | peg | B, T, D, G, P, Pg | all 11 | 0.17 | 66 |
| C | capture_chain free / teleop reset | C, Cr | zero, direct_gs, leo_relay, sweep:250, sweep:500, sweep:1000 | 0.17 | 12 |
| E | capture, peg | B, T, D, G, P | leo_relay, sweep:400, geo_relay | 0.25 | 30 |
| S | capture, peg | B, T, D, G, P, Pg | leo_relay_drop1, leo_relay_drop12 | 0.17 | 24 |

Tier 1 is 198 cells × 30 seeds = 5,940 episodes (tier1/results.md). Block E exists because every hypothesis file quoted `tau_h` 0.25; it keeps their numbers comparable and checks sensitivity to the human model. With the pre-fix L0 the Gain arm on block E was a different controller from block A's; post-fix it is the same (audit F5).

Tier 2 confirms at 100 paired seeds on cells re-pointed from the post-audit-fix Tier 1 knees (commit bfab058; `matrix.py` TIER2: capture B 240 / T 471 ms, peg B 97 / D 256 / T 510 ms, G and P never). Each arm cell is paired with a baseline cell: 34 cells, 3,396 episodes (tier2/results.md). Same-seed pairing gives a McNemar test ≥ 80 % power for 10 points at ≤ 15 % discordance (selection.md §3). The final knees moved after the chain fix (capture T 471 → 787 ms) but the Tier 2 cells still bracket every knee.

| Arm | Tier 2 cells (each paired with B) |
|---|---|
| T twin | capture sweep:400, geo_relay, zero (control); peg sweep:400, sweep:500 |
| D deadreckon | capture sweep:250; peg leo_relay, sweep:100, sweep:250 |
| G gain | peg sweep:250, sweep:500, geo_relay, zero; capture sweep:400, zero |
| P terminal | peg leo_relay, sweep:400; capture sweep:500, leo_relay |
| Pg terminal ground | peg leo_relay, sweep:400 |
| C chain, D at L = 30 ms | in the template (capture_chain leo_relay, sweep:500; `deadreckon30`) but not run; H20 rests on Tier 1 alone |

### 8.5 What was rejected and why

| ID | Status | One-line reason (selection.md §5) |
|---|---|---|
| H01 dense direct-pass network, 3 teams | DEFERRED | the ×2.5 is a duty-cycle fold with 12 operators; only the geometry is testbed-falsifiable, run as an `orbit.py` appendix (§13.3) |
| H02 dual-terminal hedged send | DEFERRED | −14 ms of jitter on a 333 ms loop; spikes are synchronous across terminals; iid emulator jitter flatters it |
| H03 relay control + direct-GS video | NO-HYPOTHESIS | gains 9 ms during 21 % of the time and opens a blind-commanding window; its ground-side telemetry-silence freeze is adopted |
| H04 two independent links, first-arrival | NO-HYPOTHESIS | outage exposure caps any gain at 1.4–5.7 % of episodes; its outage-rate sweep is adopted as an appendix (§9.11) |
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

### 9.0 Which numbers this section reads

Two Tier 1 result sets exist. The pre-fix set (commit be74e18, archived under `docs/experiments/tier1_prefix/`, 174 cells) ran on the code the audit invalidated and is mentioned only as such. The canonical Tier 1 set (commit c984271, `docs/experiments/tier1/`, 198 cells) was run in full after both fix commits on 2026-09-13; Tier 2 (commit 8c54d8f, `docs/experiments/tier2/`, 34 cells) ran the same day. The top-level `docs/experiments/results.md`, `paired.md` and `curves.json` are copies of the Tier 1 files. Tables below are Tier 1 (n = 30) unless marked Tier 2 (n = 100).

**Contamination policy.** A stalled episode has a satellite control cycle over 0.2 s (CPU contention, audit T06). A cell with three or more is flagged contaminated (`CONTAM_EPS = 3` in `experiments/aggregate.py`) and can be dropped with `--exclude-stalled`. No canonical cell is contaminated; two single episodes stalled (peg deadreckon sweep:750, 1/30; Tier 2 peg terminal_ground sweep:400, 1/100) and none was excluded. The pre-fix run had eight contaminated cells.

### 9.1 The zero-latency ceiling and the zero-cell controls

The baseline does not reach 100 % on `capture` without latency: 20/30 on `zero`, 20/30 on `sweep:0`, 69/100 in Tier 2; every arm sits at 0.63–0.77 on `zero`. Audit T16 traces the failures to seven seeds whose drift path leaves the arm's reach within 10 s (a 7 cm/s operator against a 4.5 cm/s box), not to the envelope; 8 seeds fail under baseline, sweep:0 and twin alike, so the ceiling is a task property and the pairing works. Every "fraction of own zero" below is relative to it. On `peg` the ceiling is 29/30 and 98/100.

The zero-cell control (audit F3) asks that a hider not gain on the zero-latency cell. Tier 2: gain +0.00 [−0.07, +0.08] on capture and +0.00 on peg; twin +0.07 [−0.00, +0.15] with demos per hour 1.06 [0.97, 1.17], flagged "ok" because the CI touches zero. Tier 1 flags three peg arms for a 1–2 % demos-per-hour gain at zero, subtracted as a ratio of ratios where it matters (tier1/paired.md; tier2/paired.md).

### 9.2 Success versus RTT, task `capture`, Tier 1

Success rate of 30 seeds. Every cell's RTT p50 measured within 6 ms of nominal (`sweep:0` reads 6 / 27 ms p50 / p95, `zero` 2 / 3). Source: tier1/results.md.

| Arm | sweep:0 | zero | direct_gs | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay | sweep:750 | sweep:1000 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B baseline | 0.67 | 0.67 | 0.70 | 0.67 | 0.67 | 0.53 | 0.37 | 0.33 | 0.10 | 0.27 | 0.17 |
| T twin | 0.80 | 0.77 | 0.67 | 0.73 | 0.73 | 0.73 | 0.67 | 0.67 | 0.53 | 0.63 | 0.50 |
| D deadreckon | 0.67 | 0.70 | 0.67 | 0.70 | 0.73 | 0.53 | 0.40 | 0.40 | 0.23 | 0.23 | 0.20 |
| G gain | 0.70 | 0.77 | 0.70 | 0.67 | 0.60 | 0.27 | 0.03 | 0.10 | 0.03 | 0.00 | 0.00 |
| P terminal (onboard, upper bound) | 0.73 | 0.67 | 0.67 | 0.73 | 0.73 | 0.60 | 0.43 | 0.43 | 0.27 | 0.33 | 0.33 |
| Pg terminal ground (ablation) | 0.63 | 0.63 | 0.63 | 0.70 | 0.70 | 0.53 | 0.30 | 0.33 | 0.27 | 0.13 | 0.17 |

Demos per hour, spec metric (gross in brackets); `direct_gs` also per 9.2 min pass.

| Arm | zero | direct_gs | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay | sweep:1000 |
|---|---|---|---|---|---|---|---|---|
| B baseline | 471.8 [204.2] | 431.8 [212.9] = 66.2/pass | 458.9 [201.7] | 396.4 [135.4] | 340.8 [79.8] | 306.4 [50.2] | 228.3 [12.6] | 234.1 [21.8] |
| T twin | 443.3 [253.4] | 509.6 [211.0] = 78.1/pass | 477.4 [243.0] | 417.9 [226.6] | 419.1 [193.7] | 300.0 [133.3] | 289.2 [93.0] | 298.3 [85.6] |
| G gain | 405.1 [240.4] | 382.4 [200.2] = 58.6/pass | 384.2 [185.9] | 226.8 [50.8] | 276.9 [6.1] | 132.2 [12.1] | 122.4 [4.0] | 0.0 [0.0] |

Link-caused unsafe events: 0 in all 66 cells. Cage contacts rise with RTT for every arm except Gain (baseline 10 at `zero`, 39 at `geo_relay`; Gain 14 → 8), the slower approach at work.

### 9.3 Success versus RTT, task `peg`, Tier 1

| Arm | sweep:0 | zero | direct_gs | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay | sweep:750 | sweep:1000 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B baseline | 0.97 | 0.97 | 0.97 | 0.97 | 0.77 | 0.17 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| T twin | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.97 | 0.97 | 0.83 | 0.03 | 0.00 | 0.00 |
| D deadreckon | 1.00 | 1.00 | 1.00 | 1.00 | 0.97 | 0.83 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| G gain | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 | 0.93 | 0.93 | 0.93 | 0.93 | 0.97 | 0.93 |
| P terminal (onboard, upper bound) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Pg terminal ground (ablation) | 0.97 | 0.97 | 0.90 | 0.63 | 0.00 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Demos per hour, spec (gross in brackets).

| Arm | zero | direct_gs | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|---|
| B baseline | 841.3 [677.5] | 829.9 [670.1] = 127.2/pass | 824.0 [666.2] | 800.8 [264.2] | 612.2 [23.1] | 0.0 | 0.0 | 0.0 |
| T twin | 840.5 [840.5] | 837.2 [837.2] = 128.4/pass | 830.1 [830.1] | 815.7 [815.7] | 712.1 [591.2] | 572.1 [491.3] | 407.6 [242.7] | 272.7 [4.1] |
| D deadreckon | 858.5 [858.5] | 854.4 [854.4] = 131.0/pass | 852.4 [852.4] | 833.2 [672.2] | 630.7 [307.5] | 0.0 | 0.0 | 0.0 |
| G gain | 817.5 [662.0] | 744.7 [613.4] = 114.2/pass | 704.0 [585.5] | 602.8 [513.8] | 429.3 [341.9] | 340.0 [282.7] | 301.3 [255.5] | 263.7 [227.9] |
| P terminal | 847.1 [847.1] | 831.4 [831.4] = 127.5/pass | 820.7 [820.7] | 780.3 [780.3] | 702.7 [702.7] | 638.7 [638.7] | 608.8 [608.8] | 544.9 [544.9] |
| Pg terminal ground | 848.1 [681.9] | 832.9 [470.2] = 127.7/pass | 828.1 [165.8] | 0.0 | 642.9 [4.1] | 0.0 | 0.0 | 0.0 |

Link-caused unsafe events: 0 in all 66 cells. Terminal touches the cage in no peg episode at any RTT; the baseline touches it 23–29 times per cell at 250–400 ms while hunting for the hole; the ground ablation 24–29 times at 100–400 ms. Terminal's assist fraction is 0.17–0.26 of control cycles (0.24 on `leo_relay`); the ground ablation's hand-back peak on the wire reaches 7–21 rad/s at 100–750 ms, which the satellite ramp clips into a chase.

### 9.4 Knees

First sweep RTT at which an arm's success falls below 0.8× its own `zero` cell, linearly interpolated (tier1/results.md). No CI is computed on the knee; the paired tests in §9.7 carry the uncertainty.

| Task | B | T twin | D deadreckon | G gain | P terminal | Pg terminal ground |
|---|---|---|---|---|---|---|
| capture | 250 ms | 787 ms | 230 ms | 87 ms | 310 ms | 267 ms |
| peg | 97 ms | 510 ms | 256 ms | never (> 1000 ms) | never (> 1000 ms) | 20 ms |
| capture_chain (C) / canonical reset (Cr) | 312 ms / 556 ms | | | | | |

Tier 2 confirms the baseline knees: capture 250 ms, peg 112 ms, peg gain never (tier2/results.md).

### 9.5 Acceptance readout, SYNTHESIS §6

`leo_relay` as a fraction of each arm's own `zero` cell; the gate is both fractions ≥ 0.80 and zero link-caused unsafe events on `zero`, `direct_gs`, `leo_relay` and `geo_relay` (tier1/results.md; Tier 2 in the last column where run).

| Task | Arm | Success frac | Demos/h frac | Link-unsafe, four named profiles | Cage (not gated) | Gate | Tier 2 success / demos frac |
|---|---|---|---|---|---|---|---|
| capture | B | 1.00 | 0.97 | 0 | 70 | PASS | 0.94 / 1.02 |
| capture | T | 0.96 | 1.08 | 0 | 64 | PASS | |
| capture | D | 1.00 | 0.99 | 0 | 65 | PASS | |
| capture | G | 0.87 | 0.95 | 0 | 46 | PASS | |
| capture | P | 1.10 | 0.91 | 0 | 59 | PASS | |
| capture | Pg | 1.11 | 0.92 | 0 | 60 | PASS | |
| capture_chain | C | 1.00 | 0.96 | 0 (three profiles) | 0 | PASS | |
| capture_chain teleop | Cr | 1.00 | 0.98 | 0 (three profiles) | 0 | PASS | |
| peg | B | 1.00 | 0.98 | 0 | 6 | PASS | 0.99 / 0.98 |
| peg | T | 1.00 | 0.99 | 0 | 5 | PASS | |
| peg | D | 1.00 | 0.99 | 0 | 2 | PASS | |
| peg | G | 1.00 | 0.86 | 0 | 3 | PASS | |
| peg | P | 1.00 | 0.97 | 0 | 0 | PASS | |
| peg | Pg | 0.66 | 0.98 | 0 | 12 | FAIL | |

The baseline architecture passes the acceptance bar on both proxy tasks at 30 and at 100 seeds. Per 9.2 min `direct_gs` pass the baseline delivers 66 capture or 127 peg demonstrations.

### 9.6 Block S: forced dropout

The only block in which a hold ever started while an operator was driving (audit T02). Counts per 30-episode cell (tier1/results.md, block S).

| Task | Arm | 1 s outage: holds / retracts / link-unsafe / success | 12 s outage: holds / retracts / link-unsafe / success |
|---|---|---|---|
| capture | B | 24 / 0 / 0 / 0.70 | 24 / 24 / 0 / 0.20 |
| capture | T | 20 / 0 / 0 / 0.60 | 20 / 20 / 0 / 0.40 |
| capture | D | 23 / 0 / 0 / 0.70 | 23 / 23 / 0 / 0.30 |
| capture | G | 29 / 0 / 0 / 0.67 | 29 / 29 / 0 / 0.10 |
| capture | P | 24 / 0 / 0 / 0.63 | 24 / 24 / 0 / 0.27 |
| capture | Pg | 24 / 0 / 0 / 0.63 | 24 / 24 / 0 / 0.20 |
| peg | B | 1 / 0 / 0 / 0.97 | 1 / 1 / 0 / 0.97 |
| peg | T, D, P | 0 / 0 / 0 / 1.00 | 0 / 0 / 0 / 1.00 |
| peg | G | 1 / 0 / 0 / 0.97 | 1 / 1 / 0 / 0.97 |
| peg | Pg | 11 / 0 / 0 / 0.63 | 14 / 14 / 0 / 0.53 |

On `capture`, 20–29 of 30 episodes were still running at the 6 s blackout and every one tripped the hold; every 12 s blackout crossed the retract, the arm stowed, and it resumed under the ramp. Link-caused unsafe events: 0 in all 24 cells, 720 episodes. This is PROGRAM.md's "zero unsafe motion on dropout", measured rather than vacuous. The 1 s outage costs no success; the 12 s outage costs most of it because the box drifts while the arm is frozen or stowed. Most `peg` episodes finish in about 4.3 s, before the blackout. The evidence is `move_in_hold` and `keepout`, both zero, plus the 24-of-24 hold-then-retract sequences in the sidecar; `vel_over` is zero by construction (audit F9).

### 9.7 Paired tests and verdicts per hypothesis, Tier 2

McNemar exact p on discordant seeds (b = baseline only, c = arm only); demos-per-hour ratio with paired-bootstrap 95 % CI, 2,000 resamples (tier2/paired.md). Each hypothesis's own reject clauses, quoted from selection.md §3 as amended, are evaluated one by one; Tier 1 values are used where Tier 2 did not run the cell.

**H10 Twin.**

| Task | Profile | B | T | Diff | b / c | p | Demos/h ratio |
|---|---|---|---|---|---|---|---|
| capture | zero (control) | 0.69 | 0.76 | +0.07 | 4 / 11 | 0.12 | 1.06 [0.97, 1.17] |
| capture | sweep:400 | 0.44 | 0.72 | +0.28 | 3 / 31 | < 0.0001 | 1.12 [1.04, 1.20] |
| capture | geo_relay | 0.22 | 0.61 | +0.38 | 5 / 43 | < 0.0001 | 1.24 [1.09, 1.42] |
| peg | sweep:400 | 0.01 | 0.87 | +0.86 | 0 / 86 | < 0.0001 | 1.84 [1.79, 1.89] |
| peg | sweep:500 | 0.00 | 0.74 | +0.74 | 0 / 74 | < 0.0001 | undefined (baseline has no successes) |

| Reject clause | Measured | Result |
|---|---|---|
| (a) demos/h < 1.10× at `geo_relay` or any sweep ≥ 500 ms | `geo_relay` 1.24 [1.09, 1.42]; 400 ms 1.12; capture 500 ms 0.98 [0.80, 1.18] (Tier 1); gross throughput 2.7× at 500 ms (133.3 vs 50.2) | fails at 500 ms on spec throughput |
| (b) success below baseline anywhere | direct_gs −0.03, drop1 −0.10 (Tier 1, p ≥ 0.25) | inside the seed spread |
| (c) unsafe event or hold increase | 0; block S holds 20 vs 24 | pass |
| (d) jerk or SAL worse by > 20 % | SAL at `geo_relay` 35 % worse (Tier 1), 17 % (Tier 2, −4.83 vs −4.12); LDLJ better everywhere | marginal |
| (e) gain on `zero` beyond seed spread | +0.07 [−0.00, +0.15]; ratio of ratios 1.06 at 400 ms, 1.17 at `geo_relay` | pass |

**Verdict: CONFIRMED as a latency hider on success for both tasks, the largest knee shift in the program (capture 250 → 787 ms, peg 97 → 510 ms); PARTIAL on its spec-throughput clause, missed at 500 ms; SAL marginal at `geo_relay`.** On `peg` the gain is entirely the arm half of the twin; on `capture` it is mostly the object half.

**H12 DeadReckon.**

| Task | Profile | B | D | Diff | b / c | p | Demos/h ratio |
|---|---|---|---|---|---|---|---|
| capture | sweep:250 | 0.52 | 0.57 | +0.05 | 4 / 9 | 0.27 | 1.02 [0.95, 1.08] |
| peg | leo_relay | 0.97 | 0.99 | +0.02 | 0 / 2 | 0.50 | 1.03 [1.03, 1.04] |
| peg | sweep:100 | 0.84 | 0.98 | +0.14 | 0 / 14 | 0.0001 | 1.04 [1.03, 1.04] |
| peg | sweep:250 | 0.11 | 0.88 | +0.77 | 0 / 77 | < 0.0001 | 1.03 [1.02, 1.04] |

| Reject clause | Measured | Result |
|---|---|---|
| `leo_relay` demos/h not ≥ 10 % above B with CI excluding zero | capture 1.02 [0.99, 1.05] (Tier 1); peg 1.03 [1.03, 1.04] | fails, as predicted from the ceiling |
| success falls > 3 points | never | pass |
| unsafe event; jerk > 2× B | 0; LDLJ not worse | pass |
| lag reduction < 0.5·L | cross-correlation lag not in the results files | unreported |
| confirmed only if knee moves right ≥ 0.5·L (30 ms) | capture 250 → 230 ms; peg 97 → 256 ms (+159 ms), 250 ms cell p < 0.0001 | fails on capture, passes on peg |

**Verdict: REJECTED on `capture` (a 60 ms lead does not buy back a 25 mm chase against a moving box); CONFIRMED on `peg` (88/100 vs 11/100 at 250 ms).** This is the only hider that runs inside decision (c) hardware.

**H14 Gain.**

| Task | Profile | B | G | Diff | b / c | p | Demos/h ratio |
|---|---|---|---|---|---|---|---|
| capture | zero (control) | 0.69 | 0.69 | +0.00 | 7 / 7 | 1.00 | 1.00 [0.91, 1.09] |
| capture | sweep:400 | 0.44 | 0.03 | −0.41 | 41 / 0 | < 0.0001 | 0.65 [0.51, 0.81] |
| peg | zero (control) | 0.98 | 0.98 | +0.00 | 0 / 0 | 1.00 | 0.97 [0.97, 0.98] |
| peg | sweep:250 | 0.11 | 0.95 | +0.84 | 3 / 87 | < 0.0001 | 0.70 [0.70, 0.71] |
| peg | sweep:500 | 0.00 | 0.92 | +0.92 | 0 / 92 | < 0.0001 | undefined |
| peg | geo_relay | 0.00 | 0.94 | +0.94 | 0 / 93 | < 0.0001 | undefined |

| Reject clause | Measured | Result |
|---|---|---|
| (i) at 400 and 500 ms and on `peg`: success ≤ B + 10 points or demos/h < 1.1× | capture 400 ms −0.41; peg +0.84 to +0.94 but spec demos/h 0.70× at 250 ms | fails on capture; success passes, throughput fails on peg |
| (ii) `leo_relay` demos/h < 0.9× B (rejects default-on) | capture 0.84 [0.79, 0.87], peg 0.85 [0.85, 0.86] (Tier 1) | fails on both tasks |
| `zero`-cell control | +0.00 on both tasks | pass |
| knock-away must fall where success rises | capture knock-aways 35 → 7 at 400 ms while success also falls; peg has no free box | mechanism works against a moving target |

**Verdict: REJECTED on `capture`, where it is actively harmful (3/100 at 400 ms; a box drifting at 4.5 cm/s escapes an approach slowed to 46 % speed); PARTIAL on `peg`, where it is the second-strongest hider on success (knee never; 92–94/100 out to `geo_relay`) but fails both throughput clauses and cannot be default-on.** The first surprising result: the mechanism that stabilises a stationary insertion loses a moving target.

**H11 Terminal, the onboard-compute branch, with the ground ablation.**

| Task | Profile | B | P | Diff | b / c | p | Demos/h ratio | Pg | P − Pg |
|---|---|---|---|---|---|---|---|---|---|
| capture | leo_relay | 0.65 | 0.68 | +0.03 | 1 / 4 | 0.38 | 0.97 [0.94, 0.98] | Tier 1: 0.70 vs P 0.73 | ≈ 0 |
| capture | sweep:500 | 0.33 | 0.50 | +0.17 | 4 / 21 | 0.0009 | 1.01 [0.90, 1.13] | Tier 1: 0.33 vs P 0.43 | +0.10 (Tier 1) |
| peg | leo_relay | 0.97 | 1.00 | +0.03 | 0 / 3 | 0.25 | 0.99 [0.99, 1.00] | 0.56 (−0.41 vs B, p < 0.0001) | **+0.44** |
| peg | sweep:400 | 0.01 | 1.00 | +0.99 | 0 / 99 | < 0.0001 | 2.11 [2.10, 2.11] | 0.00 | **+1.00** |

| Reject clause | Measured | Result |
|---|---|---|
| (a) on `peg` `leo_relay`: success gain < 10 points with CI covering zero, or demos/h gain < 10 % | +0.03, p = 0.25; demos/h 0.99 | fails, from the ceiling as V3 predicted |
| (a) on `capture` ≥ 500 ms | +0.17, p = 0.0009; demos/h 1.01 [0.90, 1.13] | success passes, throughput fails |
| (b) unsafe event | 0 link-unsafe; 0 cage contacts on every peg cell | pass |
| (c) robot-executed frames > 25 % of successful episodes | 0.24 on `leo_relay`, 0.25–0.26 at 100–250 ms (Tier 1; every peg episode succeeds, so audit F7's denominator does not dilute it); capture 0.04–0.07 | on the line |
| (d) ground ablation within 5 points of onboard | Pg 44 points below P on `leo_relay`, 100 below at 400 ms | pass |
| (e) SAL, LDLJ worse than B | `leo_relay` −3.19 / −16.84 vs −3.43 / −17.26 | pass |

**Verdict: REJECTED by the letter of clause (a) on the headline `leo_relay` cell, where the baseline is already at 0.97; CONFIRMED on `peg` from 250 ms up, the strongest result in the program (100/100 at 400 ms against 1/100, 30/30 at every sweep point to 1000 ms); PARTIAL on `capture` (success at 500 ms confirmed, throughput not).** P − Pg, the measured value of onboard compute, is +0.44 on `peg` `leo_relay` and +1.00 at 400 ms; on `capture` about zero at `leo_relay` and +0.10 at 500 ms. The second surprising result: the identical primitive run on the ground from delayed telemetry is worse than no primitive on `peg` (56/100 vs 97/100 on `leo_relay`; 0/30 at 100 ms in Tier 1). Re-anchoring to a state one round trip old makes its hand-back a jump on the wire (peak 7–21 rad/s), which the satellite ramp turns into a chase and 24–29 cage contacts per cell. The upper-bound label stands: `Terminal` reads the simulator's exact pose, and the noise cell was not run. The flight cost is a Jetson pose estimator and a Jetson-to-supervisor path, both excluded by (c).

**H20 chained release versus canonical reset, Tier 1, 30 seeds.** Tier 2 did not run the C cells. Success, gross demos per hour, taut fraction and smoothness are from tier1/results.md; R, the measured reset wall time, is from each run's own stdout (`docs/experiments/raw/C_*/stdout.txt`, `R_s`) because results.md does not carry it.

| Profile | C success | Cr success | C gross demos/h | Cr gross demos/h | Ratio | C reset R, s | Cr reset R, s | C taut fraction | C SAL / LDLJ | Cr SAL / LDLJ |
|---|---|---|---|---|---|---|---|---|---|---|
| zero | 1.00 | 1.00 | 493.8 | 397.4 | 1.24 | 1.73 | 4.91 | 0.04 | −7.13 / −17.46 | −7.34 / −18.07 |
| direct_gs | 1.00 | 1.00 | 480.0 | 391.4 | 1.23 | 1.77 | 5.01 | 0.06 | −6.97 / −17.49 | −7.43 / −18.19 |
| leo_relay | 1.00 | 1.00 | 472.2 | 389.6 | **1.21** | 1.79 | 5.08 | 0.06 | −7.70 / −18.05 | −8.70 / −18.83 |
| sweep:250 | 1.00 | 1.00 | 415.9 | 329.4 | 1.26 | 2.06 | 5.73 | 0.12 | −8.03 / −18.33 | −8.82 / −19.21 |
| sweep:500 | 0.20 | 0.90 | 27.9 | 211.7 | 0.13 | 2.40 (n = 6) | 6.59 (n = 26) | 0.57 | −3.73 / −23.02 | −7.92 / −20.07 |
| sweep:1000 | 0.00 | 0.00 | 0.0 | 0.0 | | | | 0.99 | | |

| Reject clause | Measured at `leo_relay` | Result |
|---|---|---|
| chained gross demos/h < 1.10× canonical | 1.21× | pass |
| success < 0.90× canonical | 1.00× | pass |
| any unsafe-motion event | 0 | pass |
| SAL, LDLJ worse than the seed spread | −7.70 / −18.05 vs −8.70 / −18.83 | pass |

**Verdict: CONFIRMED at `leo_relay`, `direct_gs`, `zero` and 250 ms; REJECTED from 500 ms, where the chained design collapses (6/30 vs 27/30) because the release turns demonstrations into chases: the tether is taut in 57 % of rows and the box leaves reach.** The design replaces 4.9–5.7 s of teleoperated return per demonstration with a 1.7–2.1 s release segment. Caveats: the "free 6-DoF body" subset is not force-free while the tether reads slack (§7.6), and the pre-chain-fix run deadlocked at 3/30.

### 9.8 Block E: the human at 0.25 s

The one `tau_h` variant's main finding is about the baseline: on `peg` `leo_relay` it drops from 29/30 to 9/30 when the human reaction goes from 170 to 250 ms, while T (29/30), D (29/30), P (30/30) and G (25/30) hold (tier1/paired.md, p < 0.0001 for D, T, P). The insertion knee is close enough to the relay loop that 80 ms of human latency crosses it. On `capture` the baseline moves within the seed spread (0.67 → 0.63 at `leo_relay`) and T holds its lead. The peg verdicts strengthen and the capture verdicts do not change if the human is slower.

### 9.9 Smoothness

Reported, never gated. On the sidecar the baseline's SAL runs from −3.68 (`capture`, `zero`) to −4.56 (500 ms), LDLJ −18.5 to −22.4, `stall_frac` 0.02–0.07. Gain's SAL on `capture` degrades to −6.0 to −8.1 from 250 ms up, the signature of a slowed-then-chasing approach. Terminal on `peg` holds LDLJ at −17 to −19 out to 1000 ms where the baseline's collapses to −24; its `stall_frac` rises to 0.11–0.17 while the operator waits for the primitive. Block S at 12 s adds the frozen segment: `stall_frac` 0.29–0.40 (tier1/results.md).

### 9.10 Multi-arm scaling

From `docs/experiments/scaling.md`: baseline, `capture`, `leo_relay`, four independent triplets as threads in one process, 15 episodes per arm, telemetry padded with 8,192-byte frames at 30 Hz for a 2 Mb/s video budget per arm. No matrix block runs `--arms 4`; this is the appendix run.

| Run | Arms | Success | Demos/h | RTT p50 / p95 ms | Stalls | Link-unsafe | Wire up B/s | Wire down B/s |
|---|---|---|---|---|---|---|---|---|
| 1 arm | 1 | 0.67 (10/15) | 447.0 | 42.2 / 68.3 | 0 | 0 | 2,012 | 249,902 |
| 4 arms, aggregate | 4 | 0.75 (45/60) | 416.8 | 42.4 / 68.1 | 0 | 0 | 8,034 | 999,090 |
| 4 arms, arm 0 | | 0.67 (10/15) | 446.9 | 43 | 0 | 0 | | |

Arm 0 of the four-arm run reproduces the one-arm run seed for seed, so the concurrent arms do not disturb each other's control loop; RTT agrees within 0.2 ms. Bandwidth scales linearly: 2.0 kB/s up and 250 kB/s down per arm, consistent with multi_operator_bandwidth §3. The ceiling is the Python GIL: the maximum control-loop step rose from 0.02 s to 0.08 s, under the 0.2 s stall threshold. Eight arms were not run.

### 9.11 Outage-rate sensitivity, the H04 appendix

From `docs/experiments/outage_sweep.md`: baseline, `capture`, 30 seeds, the `leo_relay` structure with the Poisson outage rate at 1.7, 5 and 12 h⁻¹.

| Profile | Outages/h | Success | Demos/h | Holds | Retracts | Link-unsafe | Cage | RTT p50 ms |
|---|---|---|---|---|---|---|---|---|
| leo_relay | 1.7 | 0.67 | 459.6 | 0 | 0 | 0 | 10 | 41.4 |
| leo_relay_out5 | 5 | 0.63 | 467.9 | 0 | 0 | 0 | 15 | 42.2 |
| leo_relay_out12 | 12 | 0.60 | 470.4 | 1 | 0 | 0 | 13 | 44.1 |

Raising the outage rate seven-fold moves capture success by at most two seeds of 30 and leaves throughput within noise; one hold occurred with zero link-caused unsafe events. Outages are not the binding constraint on the relay profile. The dual-terminal hedge H02, deferred to this appendix, was not run.

### 9.12 Summary of verdicts

| Hypothesis | `capture` | `peg` | Reads as |
|---|---|---|---|
| H10 Twin (ground display) | CONFIRMED on success, knee 250 → 787 ms; PARTIAL on throughput clause | CONFIRMED, knee 97 → 510 ms | adopt on the ground client; no satellite cost |
| H12 DeadReckon (supervisor) | REJECTED, no knee shift | CONFIRMED, knee 97 → 256 ms | adopt on the supervisor for insertion-class tasks only |
| H14 Gain (operator speed) | REJECTED, harmful (3/100 at 400 ms) | PARTIAL: success strong, throughput and default-on clauses fail | a per-task option for insertion, never default-on |
| H11 Terminal (onboard-compute branch) | PARTIAL: +17 points at 500 ms, no throughput gain | REJECTED at the `leo_relay` ceiling by clause (a); CONFIRMED from 250 ms up, 100 % to 1000 ms; P − Pg +0.44 to +1.00 | the priced onboard upgrade; its ground-run form is harmful |
| H20 chained release | CONFIRMED to 250 ms, ×1.21 gross at `leo_relay`; REJECTED from 500 ms | not applicable | adopt for capture-class tasks on the relay link |

---

## 10. Verification

**Tests.** `uv run pytest --collect-only -q` collects 78 tests on 2026-09-13 across ten files (link, orbit, sat, sim/operator, proto/record, strategies, terminal/chain, e2e, matrix, smoke). The full suite ran the same day: 78 passed in 70 s on the M4 Pro. The tests pin, among other things, the two `sweep:0` delay means (T08), the twin's phantom being the setpoint sent `tau_h` ago (F3), the jaw-grasp angle re-derived from the MJCF, and the chain pinch predicate.

**Audits.** `docs/experiments/audit_testbed.md` (T01–T20) and `docs/experiments/audit_strategies.md` (F1–F13), summarised in §7.7, were adversarial reads of unmodified code under the same CPU load as the matrix. Both concluded that no strategy can read true state where it should not, move the arm in hold, or beat the velocity clamp. `docs/experiments/report_review.md` fact-checked the draft of this report claim by claim, 26 corrections and 13 missing topics, all applied here.

**Independent final verification** (`docs/experiments/final_verification.md`, a clean clone of commit 8c54d8f, no edits): 78/78 tests pass in 74 s; two headline Tier 2 cells re-run at 12 seeds each (peg and capture at 400 ms, baseline vs terminal and baseline vs twin) reproduce the Tier 2 success vectors seed for seed, 48/48, with zero unsafe events and no load stalls; Wilson intervals and exact McNemar p recomputed by hand from the standard library match the published tables (p bit-identical); three `curves.json` points match `results.md`; all 24 block S cells carry `move_in_hold = vel_over = keepout = 0` in `results.json`, and the hold and retract counts in §9.6 are confirmed from it; and a read of the final code finds no strategy that bypasses `move_in_hold`, while `vel_over` and `keepout` are computed independently of any strategy counter.

**Independently recomputed.**

| What | Against | Result |
|---|---|---|
| emulator delay, jitter SD, spike and end-bump means, GE loss over 2 M packets, burst fraction, Poisson rate over 5,000 h, outage mixture, pass duty | SYNTHESIS §7 | all within noise (audit_testbed E1) |
| `move_in_hold`, `vel_over` from the satellite sidecar, independent of the strategies' self-reports, 132 pre-fix cells | strategy counters | 0 and 0; hold flag disagreed with the gap test on 1 cycle in 311,409 (E3) |
| Wilson intervals, exact McNemar; SAL and LDLJ | closed forms; SPARC reference | match (T20, E5) |
| four-site polar geometry on a real TLE | network_emulation §1.4 | 21.4 % vs 21.3 % duty (appendix_geometry.md) |
| four-arm run, arm 0 | one-arm run | identical seed by seed (scaling.md) |
| smoothness columns in results.md | run output | recomputed by the aggregator from the sidecars |
| 48 seeds of four Tier 2 cells, on a clean clone | Tier 2 success vectors | 48/48 identical (final_verification.md) |

**Not independently verified.** The post-fix cells beyond the 48 reproduced seeds rest on the aggregator's own recomputation and the block S counts; no second sidecar recomputation of `move_in_hold` was run on them. H12's command-to-applied lag and H10's twin innovation are not in the results files. `vel_over = 0` is guaranteed by construction (F9) and is cited nowhere as evidence. Tier 2 did not run the H20 confirm cells, the `deadreckon30` arm or the H11 noise cell. The knee has no confidence interval. The H02 row of the outage appendix was not run.

---

## 11. Near-future upgrades and what they change

| Upgrade | When | What it changes |
|---|---|---|
| Starlink third-party laser terminal (Muon Space Halo) | Q1 2027 (leo_link_options §2 b1) | a measured latency settles SYNTHESIS §9 question 1; an RTT inside 30–90 ms changes nothing in §9, above 150 ms the capture task loses about a third of its throughput (§9.2) and the mission reverts to the pass regime, where the 16U variant becomes competitive |
| Kepler constellation | 2028 (leo_link_options §2 b2) | continuous coverage of a non-Kepler-plane satellite; a published latency makes it a real second path |
| Telesat Lightspeed, Amazon Leo | 2028 service; NASA demonstration (leo_link_options §2 b3, b4) | no product yet |
| Onboard compute branch | after a Jetson pose estimator and a Jetson-to-supervisor path exist | P − Pg is +0.44 on `peg` at the relay RTT and +1.00 at 400 ms (§9.7), so the terminal primitive is worth its flight cost for insertion-class tasks; no rad-tolerant board with hardware video encode exists off the shelf (hardware_landscape §5); the lower bound with estimator noise is unmeasured |
| Jitter distribution | now | only a 2–3 component Gaussian mixture is validated on Starlink (network_emulation §1.1); the emulator's `dist` switch has exp, gauss, lognormal and gamma with a fixed log-normal shape; a GMM sampler and a sweep re-run is the cheapest sensitivity check not yet done |
| Radiation-screened cameras | now | Teledyne e2v Ruby 1.3M USV, tested to 20 krad (hardware_landscape §4), replaces the IMX296 if COTS hot-pixel growth matters |
| Two-host operation | before any real-network test | RFC 7679 one-way delay with skew removal; RTT/2 is wrong by about 8 ms on Starlink (network_emulation §2) and 6 ms on the testbed's relay profile |
| Direct-pass density | now | a 46-site commercial network gives 61 % duty at 5°, ×2.85 the demonstrations per wall-hour of the four-site fallback (§13.3), but about 1× per operator-hour since it needs three regional teams (scores_V1.md) |

---

## 12. What this proves and what it does not

**What it proves, within the testbed.** A satellite that does nothing but sequence-keyed playout, hold, retract, ramp and clamp keeps 94–100 % of its zero-latency success and 98–102 % of its throughput on an emulated Starlink-class relay link on both proxy tasks, and records zero link-caused unsafe motion through 720 forced dropouts. Insertion fails from about 100 ms and capture from about 250 ms with that baseline. A ground twin display moves the capture knee past 750 ms; a supervisor-side extrapolator or an onboard terminal primitive moves the insertion knee to 250 ms or beyond; a chained-release design lifts gross throughput by a fifth at the relay RTT. Adaptive motion scaling is harmful on a moving target and strong on a fixed one.

**What it does not prove.**

- **Video is delay plus bytes.** No codec, frame content or perceptual loss; VISTA shows success falling from 97 % to 35 % as bandwidth, delay and loss co-vary (multi_operator_bandwidth §1.3).
- **The grasp is kinematic behind a physical-jaw gate.** Once the jaw closes on or pinches the box, the box rides the site; pad friction, restitution and grasp-impulse transients are absent, so capture results bound the approach, not the grasp event (SYNTHESIS §3).
- **The operator is a synthetic model.** Fixed 170 ms reaction, bounded speed, no move-and-wait, no learning. The knees land where the human-subject literature predicts, which is consistency, not validation; block E shows the peg knee is within 80 ms of the relay loop.
- **One machine, one clock, one interpreter.** One-way delay is not measured; `owd_up_ms` is RTT/2. The four-arm case measures the GIL as much as the link.
- **The Starlink third-party latency is unmeasured by anyone.** The 48 ms design point is one ISL hop on the consumer median (SYNTHESIS §2). If it is 150 ms, the sweep says what happens; if its jitter is not log-normal, the emulator has not been run that way.
- **Radiation.** No TID or SEE data for the servos, no Jetson reboot rate (hardware_landscape §3, §5); nothing here tests the supervisor's reboot assumption.
- **No force.** No wrist force/torque, so nothing on delayed contact detection as a safety risk (teleop_fundamentals §4).
- **Unique-value tasks are absent.** Granular, liquid and deformable tasks have no MuJoCo proxy; the testbed proves the loop and the envelopes on two rigid-body proxies.
- **`ramp_clip` is not a safety count.** A 1 kHz loop rendering a 50 Hz jittered stream clips thousands of times per episode even for the baseline; the decidable pair is `ramp_clip(P) ≤ ramp_clip(B)` and the sidecar velocity check.
- **No flight.** Nothing here has been on orbit.

**Open questions, ranked by design impact (SYNTHESIS §9).** (1) Measured latency and terms for a third-party satellite over Starlink mini-laser; this decides whether the primary path is real. (2) Kepler latency and coverage of a non-Kepler-plane satellite. (3) Radiation behaviour of COTS servos and the on-orbit Jetson reboot rate. (4) Does latency-collected demonstration data train worse policies? No study exists (data_pipeline §2.3); every row here carries its RTT so that study can be run. (5) Jitter distribution shape on Starlink. (6) Ground backhaul latency and continuous-transmit qualification of CubeSat X-band radios. (7) Packet reordering and ISL stage effects. (8) Capture task limits: safe release spin rate and target speed are rules of thumb `[unverified]` (unique_data_study §4). (9) LeRobot loader tolerance for a missing `stats/*` block and sidecar files (data_pipeline §1.5, §3.2).

---

## 13. Appendix

### 13.1 Repo map

```
docs/
  PROGRAM.md                 charter and settled decisions
  TESTBED_SPEC.md            the decision-independent testbed spec
  research/                  eight research reports + SYNTHESIS.md (decision record)
  hypotheses/                H01-H20, scores_V1-V5, selection.md
  experiments/
    tier1/                   canonical Tier 1: results.md, results.json, paired.md, curves.json (198 cells)
    tier2/                   Tier 2: results.md, results.json, paired.md, curves.json (34 cells)
    tier1_prefix/            archived pre-fix Tier 1 (174 cells); not cited as results
    results.md, results.json, paired.md, curves.json   copies of tier1/
    raw/<cell>/              stdout.txt + summary.json per Tier 1 cell (gitignored)
    raw_tier2/, raw_tier1_prefix/, raw_appendix/       same, per tier and appendix
    audit_testbed.md         Phase 5 audit T01-T20
    audit_strategies.md      Phase 5 audit F1-F13
    report_review.md         fact-check of the report draft
    final_verification.md    independent clean-clone verification: 78/78 tests, 48/48 seeds reproduced
    appendix_geometry.md     H01 check: contact geometry on a real TLE
    scaling.md               4-arm scaling run
    outage_sweep.md          H04 outage-rate appendix
  REPORT.md                  this document
  arms_in_orbit.html         results page (published artifact source)
spaceteleop/
  run.py                     runner: ground <-> link <-> sat over UDP, --profile --task --strategy --reset
  proto/                     struct-packed command and telemetry datagrams
  link/emulator.py           UDP proxy: delay, jitter, GE loss, 15 s structure, outages, passes, caps
  link/profiles.py           zero, direct_gs, leo_relay, leo_relay_drop1/drop12, leo_relay_out5/out12, geo_relay, sweep:<rtt>
  link/orbit.py              sgp4 contact windows for a station list
  ground/loop.py             operator loop, arrival-stamped RTT, LeRobot rows
  ground/operators.py        SyntheticOperator (tau_h, DLS servo), KeyboardOperator
  sat/controller.py          seq-keyed buffer, strategy call, MuJoCo stepping, telemetry, applied log
  sim/__init__.py            SO-100 at g=0: capture, capture_chain, peg; cage; predicates
  strategies/                base, baseline, twin, deadreckon (+deadreckon30), adaptive_gain, terminal (+terminal_ground), registry
  record/                    LeRobot-v2.1-shaped npz writer + sat sidecar
  metrics/                   success, demos/h (spec and gross), RTT, safety counts, SAL, LDLJ, stalls
experiments/
  matrix.py                  selection.md section 3 as data + resumable subprocess runner (blocks A, B, C, E, S; Tier 2 arm-map)
  aggregate.py               raw/*/summary.json -> results.md, results.json, paired.md, curves.json; --exclude-stalled, --legacy-deadreckon-lead
  appendix_geometry.py       the H01 geometry rerun
tests/                       78 tests: link, orbit, sat, sim/operator, proto/record, strategies, terminal/chain, e2e, matrix, smoke
```

### 13.2 Reproduce

Requirements: Python 3.12 via `uv`, macOS or Linux. The clock is realtime; Tier 1 is about 4 h on five to eight processes, Tier 2 about 2 h.

```
uv sync
uv run pytest -q                      # 78 tests, 70 s on an M4 Pro (2026-09-13)

# one cell by hand
uv run python -m spaceteleop.run --profile leo_relay --task capture --episodes 8 --seed 0 \
    --out docs/experiments/raw/demo
uv run python -m spaceteleop.run --profile sweep:500 --task peg --strategy terminal --episodes 8
uv run python -m spaceteleop.run --profile leo_relay_drop12 --task capture --episodes 8 --max-s 30
uv run python -m spaceteleop.run --task capture_chain --reset teleop --profile leo_relay --episodes 20

# Tier 1 (selection.md section 3 plus block S), resumable; one run.py process per cell
uv run python experiments/matrix.py --dry-run --tier 1 --strategies baseline,twin
uv run python experiments/matrix.py --tier 1 --blocks A,B \
    --strategies baseline,twin,deadreckon,gain,terminal,terminal_ground --ablations terminal_ground \
    --seeds 30 --jobs 5 --out docs/experiments/raw
uv run python experiments/matrix.py --tier 1 --blocks C --strategies baseline --seeds 30 --jobs 5
uv run python experiments/matrix.py --tier 1 --blocks E \
    --strategies baseline,twin,deadreckon,gain,terminal --seeds 30 --jobs 5
uv run python experiments/matrix.py --tier 1 --blocks S \
    --strategies baseline,twin,deadreckon,gain,terminal,terminal_ground --seeds 30 --jobs 5

# Tier 2 (100 paired seeds); unmapped labels are dropped, so map Pg explicitly
uv run python experiments/matrix.py --tier 2 \
    --arm-map T=twin,D=deadreckon,G=gain,P=terminal,Pg=terminal_ground \
    --seeds 100 --jobs 5 --out docs/experiments/raw_tier2
# to add the H20 confirm cells and the 30 ms dead-reckoning arm, extend the map:
#   --arm-map ...,C=baseline   and a second run with D=deadreckon30

# aggregate
uv run python experiments/aggregate.py --raw docs/experiments/raw --out docs/experiments/tier1
uv run python experiments/aggregate.py --raw docs/experiments/raw_tier2 --out docs/experiments/tier2

# appendices
uv run python experiments/appendix_geometry.py
uv run python -m spaceteleop.run --profile leo_relay --task capture --strategy baseline --arms 4 \
    --episodes 15 --seed 0 --max-s 20 --frame-bytes 8192
uv run python -m spaceteleop.run --profile leo_relay_out12 --task capture --strategy baseline \
    --episodes 30 --seed 0 --max-s 20
```

`matrix.py` skips any cell whose `summary.json` exists without an error and retries crashed cells; every cell uses the same seed base, so arms are paired seed by seed. `aggregate.py` writes the per-task tables, the block S table, the knees, the SYNTHESIS §6 acceptance readout, `curves.json` and `paired.md`; `--exclude-stalled` drops contaminated cells and `--legacy-deadreckon-lead` relabels a pre-fix DeadReckon arm with its true 90 ms lead.

### 13.3 Geometry appendix: direct-pass contact geometry, 550 km SSO, 7 days

From `docs/experiments/appendix_geometry.md`, generated by `experiments/appendix_geometry.py` on 2026-09-13 with `spaceteleop.link.orbit.contact_windows` (sgp4, TEME plus GMST rotation, spherical Earth), on the ICEYE-X37 TLE (NORAD 59102, Transporter-10 rideshare, 546 km, 97.84°), 10 s steps, 5° and 10° masks. Duty and gaps are on the union of all sites in a set.

| Site set | Sites | Mask | Duty | Passes/day | Mean pass, min | Median gap, min | Max gap, min |
|---|---|---|---|---|---|---|---|
| (a) 4-site polar | 4 | 5° | 21.4 % | 32.4 | 9.5 | 35.2 | 85 |
| (a) 4-site polar | 4 | 10° | 14.9 % | 33.3 | 6.5 | 39.0 | 87 |
| (b) single mid-latitude, Weilheim | 1 | 5° | 2.6 % | 5.6 | 6.7 | 87.9 | 684 |
| (b) single mid-latitude, Weilheim | 1 | 10° | 1.4 % | 3.4 | 5.9 | 547.5 | 780 |
| (c) commercial S/X network | 46 | 5° | 61.1 % | 61.6 | 14.3 | 6.9 | 48 |
| (c) commercial S/X network | 46 | 10° | 47.6 % | 74.4 | 9.2 | 8.0 | 52 |

The four-site cross-check reproduces network_emulation §1.4 (21.4 % here versus 21.3 % there) on a real TLE. The 46-site commercial union (KSAT, SSC, AWS, Leaf Space, Viasat RTE; 32 of 46 rows with provider-published coordinates) gives 61.1 % at 5°, inside H01's 54–69 % band, and 47.6 % at 10°, below it. If throughput is proportional to contact time, the commercial network yields ×2.85 the demonstrations per wall-hour of the four-site fallback at 5° and ×3.19 at 10°, inside H01's predicted ×2.6–3.4 before its handover deduction. Backhaul, handover, uplink licensing, antenna availability and operator headcount are outside this geometry and are the V1 objections that still stand.
