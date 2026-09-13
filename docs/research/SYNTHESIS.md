# Synthesis: decision record for the space teleop program

Inputs: the eight reports in `docs/research/` (cited below as `report §section`). This file is ground truth for downstream agents. Where reports disagree the choice and reason are stated inline; unresolved items are in §9. Numbers without a report citation are marked `[design choice]` and are ours.

## 1. Feasibility verdict

**Conditional yes**: ground teleoperation of simple arms inside a LEO small satellite for demonstration collection is feasible with hardware buyable in 2026, on the condition that the mission either (a) flies a LEO laser-relay terminal whose first third-party flights are Q1 2027, or (b) accepts pass-limited sessions at a 21 % duty cycle; in both cases the task set must be restricted to slow, coarse manipulation.

- **No one has done exactly this.** No program has flown a manipulator inside a free-flyer's own volume under ground teleoperation, and none has logged robot-learning demonstrations in orbit (space_teleop_prior_art §2, §3). Nearest cases: ETS-VII external arm at 5–7 s RTT (1997–99), GITAI S1 inside the ISS airlock (2021, no numbers), Xiyuan-0 hand-controller teleop over direct passes at "sub-second" loop (2026, no numbers).
- **The sub-100 ms space link exists, but only on direct passes.** ROKVISS/Kontur-2: 20–30 ms RTT, ±2 ms jitter, 0.1 % loss, 245–256 kbit/s up, 4 Mbit/s down, 4–8 min windows, ~500 tests over 5.5 years (space_teleop_prior_art §1).
- **Continuous sub-150 ms coverage is one product away.** Starlink mini laser: 25 Gbps at ≤4,000 km, flight-tested Aug 2025, Muon Space and Starcloud contracted, first third-party hardware Q1 2027; estimated 30–90 ms RTT (leo_link_options §2 b1). Consumer Starlink measured median 40 ms RTT, 15 s reconfiguration spikes, ≈1 % loss, ≈1.7 outages/h (network_emulation §1.1).
- **Human tolerance leaves margin at that RTT.** Coarse pick-and-place time ×1.45 at 250 ms RTT and ×2.04 at 500 ms; first significant loss between 200 and 300 ms; precision insertion "ideal" below 200 ms (teleop_fundamentals §1.2, §4). Our relay-path machine loop is ≈163 ms before the human (§8 below).
- **Hardware is off the shelf.** ESPA-class bus (Apex Aries: 100 kg, 175 W EOL), a 100–300 L 1-atm aluminium cylinder at 3.5–10 kg, Dynamixel-X arms with Astrobee servo heritage, Jetson Orin NX plus a rad-tolerant supervisor; order-of-magnitude $6–12 M including launch (hardware_landscape §1–§7).
- **Bandwidth is not the constraint.** Four operators at two 720p30 streams each need 10.4 Mbps down with FEC and 0.85 Mbps up at 100 Hz with duplicate-send (multi_operator_bandwidth §3), inside X-band DTE (100–150 Mbps) or any relay.
- **The data has no Earth substitute.** No Earth analog gives 6-DoF free motion beyond 24 s; granular, fluid and deformable behaviour in µg is unvalidated in every listed simulator (unique_data_study §1, §2).
- **Two unknowns bound the verdict.** No measured latency exists for a third-party satellite over Starlink ISLs (network_emulation §1.2), and no TID/SEE data exists for Dynamixel or Feetech servos (hardware_landscape §3).

## 2. Link path decision

**Primary: Starlink mini-laser relay, two terminals per spacecraft, contracted 2026 for a 2027 flight** (leo_link_options §3 rank 1; network_emulation §4 P2). **Fallback: direct ground-station passes** through a four-site polar network for commissioning, bulk downlink and pass-bounded teleop sessions (leo_link_options §3 rank 3; network_emulation §1.4). Kepler is ranked third, not as fallback, because its latency is unpublished and its coverage of a non-Kepler-plane satellite is intermittent until the 2028 constellation (leo_link_options §2 b2). IDRS/Iridium is a safety channel only.

Two reports disagree on the buyable-today primary: hardware_landscape §6 calls Kepler primary (95 % continuity from its datasheet) with Starlink as the 2027 upgrade; leo_link_options §2 b2 estimates Kepler as not continuous with 10–33 satellites. We take leo_link_options because the 95 % figure is a full-constellation datasheet claim `[unverified]` and no Kepler latency number exists in any report. The program design targets the 2027 flight anyway.

| Rank | Path | RTT p50 / p95 | Coverage | Up / down | Why it wins or loses |
|---|---|---|---|---|---|
| 1 | Starlink mini-laser relay ×2 | 48 ms / 125 ms (network_emulation §4 P2) | >99 % with two terminals (hardware_landscape §6, Muon claim `[unverified]`) minus 1.7 outages/h (network_emulation §1.1) | 25 Gbps ISL; ground allocation unpublished | Only continuous, sub-150 ms candidate (leo_link_options §3). Loses only on schedule: Q1 2027 first flights |
| 2 | Direct GS, 4 polar sites, X-band down / S-band up | 30 ms / 45 ms in contact (space_teleop_prior_art §1 Kontur-2; network_emulation §1.4 slant range) | 21.3 %; 33 passes/day, 9.2 min mean, 35 min median gap (network_emulation §1.4) | 256 kbps / 100–150 Mbps (multi_operator_bandwidth §3; hardware_landscape §6) | Only regime with flown, measured numbers; hard outages between passes |
| 3 | Kepler optical relay + SDA OCT | unpublished; 50–300 ms one-way `[unverified]` (hardware_landscape §6) | intermittent until 2028 (leo_link_options §2 b2) | 2.5 Gbps | Live since 24 Aug 2026 but no latency figure; optical ground stations weather-limited (~69 % single site) |
| 4 | IDRS L-band / Iridium Certus | 0.5–1.5 s (hardware_landscape §6); minutes for SBD (leo_link_options §2 d) | 80–100 % | 250 / 200 kbps | Safety and heartbeat channel only |
| 5 | GEO relay (TDRS, EDRS, InRange) | 600 ms / 850 ms (network_emulation §1.3; space_teleop_prior_art §1 Analog-1) | >99 % | 20 / 90 Mbps | Propagation floor ≥474 ms is disqualifying; TDRS closed to new users Nov 2024 (leo_link_options §2 c) |

RTT for rank 1 reconciles three estimates: leo_link_options §2 b1 gives 30–90 ms, hardware_landscape §6 gives 20–100 ms, network_emulation §4 gives 48 ms base with spikes to ≈125 ms. We take 48 ms because it is anchored to the 19.2 M-test M-Lab median of 40 ms plus one 4,000 km ISL hop, and we carry 90 ms as the design-margin figure.

## 3. Task set

All tasks: 6-DoF arm, parallel gripper, workspace enclosed in a cage so nothing drifts out of reach; objects move at order cm/s (unique_data_study §3, §4). Latency sensitivity is taken from the teleop_fundamentals §4 task-class table.

| # | Task | Phenomenon exposed | Sensors | Volume | Latency sensitivity |
|---|---|---|---|---|---|
| 1 | Scoop, transport, pour sieved granular simulant (<250 µm) between open trays in a transparent cell | Regolith behaviour below 1e-4 g: rebound, ejecta, bulk-density-dependent flow; not extrapolable from 1e-2 g parabolic data (unique_data_study §2 A) | 2 cameras (top, side), wrist F/T, joint torques | Sealed gas-filled cell inside the pressurized bus | Low: coarse class, degrades at 250 ms, unusable ≥750 ms |
| 2 | Capture and re-release of a slowly spinning cm-scale rigid object (≤1 rad/s, ≤2–5 cm/s `[unverified]`) | Real grasp impulses on a truly free 6-DoF body; MuJoCo has no restitution parameter (unique_data_study §2 D) | Stereo or RGB-D, wrist F/T, base IMU + gyro, encoders | Pressurized (either works) | Medium: free-space approach is tolerant to 225 ms; the grasp event is precision-class, ~150–200 ms |
| 3 | Partially filled liquid container handling and capillary pour between vessels | Long-duration slosh, capillary flow, contact-line dynamics; only qualitative CFD comparison exists (unique_data_study §2 B) | ≥60 fps camera `[unverified]`, wrist F/T, IMU on container | Sealed cell, pressurized bus strongly preferred (triple point) | Low: capillary flows take seconds |
| 4 | Cable routing and fabric pouch open/close (30 cm cable, two connectors, Velcro pouch) | Deformable dynamics in µg; Astrobee cargo-bag work is simulation-only (unique_data_study §2 C) | 2 cameras, wrist F/T | Pressurized (either works) | Medium: connector mating is insertion-class, ~150–200 ms |
| 5 | Peg-in-hole on a fixture rigidly mounted to the bus, wheel torques logged | Arm-base momentum coupling and base identification; testbed proxy because MuJoCo is faithful here (unique_data_study §2 E, §5) | Base IMU/gyro, joint torques, wrist F/T | Either | High: precision insertion, ideal <200 ms, drops 500–700 ms |

Tasks 1–4 are the unique-value payload; unique_data_study §5 asks that at least two of four arms carry a granular cell and one a liquid cell. Tasks 2 and 5 are the MuJoCo proxies for the success-vs-latency curve, with the stated caveat that capture results are a lower bound because grasp-impulse transients are not simulated.

## 4. Mission shape

- **Bus class:** ESPA-class, Apex Aries in the 100 kg rideshare configuration. Continuous payload draw is 100–190 W, which is 2–5× a 16U's 25–60 W orbit-average and 55–100 % of Aries' 175 W EOL (hardware_landscape §1). A 16U supports only a 2-arm, pass-only demo.
- **Pressurization:** yes, a 100–300 L Al 6061 cylinder at 1 atm with domed ends, 3.5–10 kg with fittings. Brushed motors and hobby servos need atmosphere for commutator film and convection; vacuum-rated arms (GITAI IN2, 50 kg) exceed the whole payload budget (hardware_landscape §2). unique_data_study §4 independently prefers a pressurized bus for tasks 1 and 3.
- **Arms:** 4 in the baseline, 8 as the scale branch. Four is what four concurrent operators use, what the bandwidth budget is sized for, and what unique_data_study §5 allocates cells to. Dynamixel-X 6-DoF arms (Koch/ALOHA class) with Astrobee-style thermal and current cutoffs (hardware_landscape §3).

| Subsystem | Choice | Source |
|---|---|---|
| Bus + launch | Apex Aries 100 kg + SpaceX rideshare, ≈$1.05 M launch | hardware_landscape §1, §7 |
| Enclosure | 100–300 L 1-atm Al cylinder, domed ends | hardware_landscape §2 |
| Arms | 4× Dynamixel-X 6-DoF + parallel gripper, XM430 on loaded joints | hardware_landscape §3 |
| Cameras | 4–8× IMX296 or AR0234 global shutter, 720p30, 1.5–2.5 Mbps each | hardware_landscape §4 |
| Compute | Jetson Orin NX (cameras, NVENC, mux) + rad-tolerant supervisor MCU (setpoint buffer, hold/retract, watchdog, LCLs) | hardware_landscape §5 |
| Relay | 2× Starlink mini-laser terminals; mass/power unpublished, budget conservatively | leo_link_options §2 b1, §Implication |
| DTE | Syrlinks EWC27 X-band down + S-band Rx | hardware_landscape §6 |
| Safety channel | IDRS L-band (250 kbps, 0.5–1.5 s) or Iridium Certus 9770 | hardware_landscape §6; leo_link_options §2 d |
| Thermal | 0.1–0.25 m² radiator, heat strap from cylinder wall | hardware_landscape §6 |

**Most cost-driving decision:** requiring a continuous link. It forces the relay terminals (40–70 W) and the continuous downlink power, which together push the payload past any CubeSat class and onto a $3.5–9.5 M ESPA bus (hardware_landscape §1, §7 "the bus dominates"). A pass-only mission is a 16U with two arms.

## 5. Onboard capability decision

**Choice: (c)**, the program's (b) baseline plus small deterministic safety logic, all of it on the rad-tolerant supervisor, none of it on the Jetson.

Allowed on the satellite in the baseline:

1. Joint-setpoint playout: receive timestamped setpoints, sort by sequence, interpolate linearly at the control rate with a fixed playout delay of 30 ms `[design choice]`, bounded by teleop_fundamentals §2 (buffering more than ~50–70 ms of jitter costs more than it saves) and network_emulation §1.1 (uplink jitter SD 14 ms).
2. Hold on timeout: if no command newer than 300 ms, freeze the commanded setpoint at the last interpolated value. The window sits between the 15 s uplink spike (+74 ms over 140 ms, must not trigger) and the outage tail (87 % under 2 s, must trigger); leo_link_options §Implication puts the threshold at 300–500 ms.
3. Retract to a stowed pose after 10 s of silence `[design choice]`: only the 3 % of outages lasting 5–31 s reach it (network_emulation §1.1).
4. Ramp-limited resume: on link return the interpolator ramps from the frozen value at no more than the rated joint velocity, never a jump (this is already the controller's behaviour).
5. Static envelopes: joint position, velocity and acceleration clamps, and a keep-out box that is the cage interior. This is the Astrobee keep-out-zone and Canadarm2 LOS-safe pattern that every flown ground-driven robot uses (space_teleop_prior_art §1 Astrobee, Canadarm2; §Implication).
6. Hardware cutoffs: per-motor thermal cutoff and a latching current limiter at 80 % of peak, exactly the Astrobee arm design (hardware_landscape §3).

Explicitly excluded from the baseline: vision, learned models, admittance or force control, any subgoal primitive, any autonomy that changes the trajectory. The onboard-compliance result (nut threading 49 → 65–81 % success, teleop_fundamentals §2) is the single strongest latency hider in the evidence and is therefore a hypothesis branch, not the baseline.

Why (c) and not (b): the relay path has 1.7 outages/h with a heavy tail (network_emulation §1.1), and every flown ground-teleop system that survived loss of signal did so with onboard envelopes, not with hold alone (space_teleop_prior_art §Implication). The added logic is stateless except for one timer, costs no latency, and belongs on the supervisor because a Jetson SEFI is a multi-second reboot (hardware_landscape §5).

## 6. Acceptance thresholds

**Solved means: on the `leo_relay` profile, success rate ≥ 80 % of the zero-latency success rate AND demos per hour ≥ 80 % of zero-latency demos per hour, with the safety criterion met on every profile.** This keeps the program default and the evidence says it is a real discriminator rather than a free pass:

- At 250 ms RTT, coarse pick-and-place time is ×1.45 (throughput 69 %) and at 500 ms ×2.04 (49 %) (teleop_fundamentals §1.2 peg transfer). Target acquisition at 225 ms lag: +64 % movement time, +214 % errors (§1.1 MacKenzie & Ware). So 80 % is not attainable at 250 ms for the coarse class without a latency hider.
- Our relay machine loop is ≈163 ms (§8), under the 200 ms "ideal" bound for precision (§1.2 Xu) and under the 200–300 ms first-significant-loss band (§1.2 mobile-robot study). So 80 % is attainable for coarse tasks 1, 3 and the approach phase of 2, and expected to fail for insertion-class tasks 4 and 5 with the baseline. teleop_fundamentals §Implication says the same: ≥80 % likely holds for coarse tasks to ~250–300 ms and for insertion only to ~150 ms.
- Success alone is not enough for policy learning: robomimic "Worse" operators still reached 92 % on Can but produced 39 % vs 66 % policies on Square (data_pipeline §2.1). Report SAL and LDLJ distributions against the zero-latency baseline for every run; they are reported, not gated.

On `direct_gs`, throughput is reported per pass, not per hour, because every prior program was window-limited once delay was under ~1 s (space_teleop_prior_art §Implication).

**Safety criterion: zero unsafe-motion events across all episodes on all four profiles.** Unsafe motion is any of: the commanded setpoint changing while in hold (stale trajectory continuation); joint velocity above the clamp at link resume (jump); end effector leaving the keep-out box; contact with the cage in simulation. Every episode also logs `link_state`, hold events and safety stops per data_pipeline §3.2.

## 7. Link profiles to emulate

All delays one-way per direction. Loss is Gilbert-Elliott with per-packet transitions `p_gb`, `p_bg` and loss probabilities `loss_g`, `loss_b`; mean loss = `loss_b · p_gb / (p_gb + p_bg)` when `loss_g = 0` (network_emulation §2). Jitter is given as a distribution with mean 0 and the stated SD.

| Parameter | `zero` | `direct_gs` | `leo_relay` | `geo_relay` |
|---|---|---|---|---|
| Base delay up / down | 0 / 0 (loopback 22 µs measured, network_emulation §2) | 15 / 15 ms: slant-range propagation 1.8–7.4 ms by elevation + 10 ms backhaul `[unverified]` (network_emulation §4 P1); consistent with Kontur-2 20–30 ms RTT (space_teleop_prior_art §1) | 30 / 18 ms (network_emulation §4 P2: 40 ms bent-pipe median + one 4,000 km ISL hop) | 300 / 300 ms (network_emulation §4 P3: NASA HDTN 600 ms RTT) |
| Jitter | none | Gaussian, SD 2 ms (Kontur-2 measured ±2 ms, space_teleop_prior_art §1; teleop_fundamentals §1.3) | shifted log-normal, SD 14 ms up / 11 ms down (Mohan et al. via network_emulation §1.1), AR(1) ρ = 0.25 `[unverified]`; keep a `dist` switch for gamma / GMM | Gaussian, SD 2 ms `[unverified]` (network_emulation §4 P3) |
| 15 s structure | none | none | period 15 s; per-period shift U(−5, +5) ms `[unverified]`; uplink spike +74 ms peak decaying over the first 140 ms, downlink half of that; end bump +20 ms `[unverified]` over the last 75 ms (network_emulation §1.1, §2, Casparsen et al.) | none |
| Loss | 0 | `p_gb` 0.001, `p_bg` 0.2, `loss_g` 0, `loss_b` 0.3 → 0.15 % `[unverified]`; ×10 below 10° elevation `[unverified]` (network_emulation §4 P1); Kontur-2 measured 0.1 % | `p_gb` 0.0034, `p_bg` 0.2, `loss_g` 0, `loss_b` 0.3 → 0.5 % background; plus 31 % of 15 s periods forced into the bad state for their first 1 s (network_emulation §1.1 BAROC). Long-run ≈1.1 %, consistent with leo_link_options §1 (≈1 %) | `p_gb` 0.0091, `p_bg` 0.2, `loss_g` 0, `loss_b` 0.3 → 1.3 % (Analog-1 measured 1.27 %, space_teleop_prior_art §1) |
| Outages | none | none inside a pass | Poisson 1.7 h⁻¹; duration mixture 87 % U(0.3, 2) s, 10 % U(2, 5) s, 3 % U(5, 31) s (network_emulation §1.1, §2) | TDRS handover LOS 45 s every 45 min `[unverified]` (network_emulation §1.3) |
| Bandwidth cap up / down | none | 256 kbps / 100 Mbps (Kontur-2 S-band, multi_operator_bandwidth §3; X-band 100–150 Mbps, hardware_landscape §6) | 5 Mbps `[design choice, non-binding: 8 operators need ≤1.7 Mbps]` / 50 Mbps (network_emulation §4 P2 design choice to force video budgeting) | 20 / 90 Mbps (ISS DTN allowable, network_emulation §1.3) |
| Contact windows | always on | TLE-driven passes from the 4-site polar union: 33.4 passes/day, 9.2 min mean, 35 min median gap, 85 min max gap; single mid-latitude site: 4.0/day, 7.4 min, 340 min mean gap (network_emulation §1.4). Periodic stand-in: 9 min on, 35 min off | always on minus outages | always on minus handovers |
| Reordering | none | FIFO | allowed | FIFO |

Corrections applied to the source values: (i) network_emulation §4 lists P2 loss as GE(0.00144, 0.2, 0, 0.3) → 0.5 %, but that parameter set yields 0.21 % by the report's own stationary formula; 0.0034 gives the stated 0.5 %. (ii) leo_link_options §1 reads the Casparsen spike as "≈140 ms at cycle start"; the paper's 140 ms is the spike duration and +74 ms the peak (network_emulation §1.1), so 74 ms is used. (iii) network_emulation P1 jitter of 0.5 ms `[unverified]` is replaced by the measured Kontur-2 2 ms. (iv) network_emulation P3 loss of 0.07 % `[unverified]` is replaced by the measured Analog-1 1.27 %.

Mapping to the current emulator: `mean_ms`/`jitter_ms` take the base and SD above (the emulator's exponential tail is the stand-in until the `dist` switch exists); the GE fields map one-to-one; `bw_bps` takes the caps in bytes/s; the periodic `outage_period_s`/`outage_dur_s` pair approximates GEO handovers (2700 s / 45 s) and, as a stopgap, relay outages (2118 s / 1 s). The 15 s spike layer, Poisson outages and pass windows from the TLE generator are not yet fields and must be added.

## 8. Latency budget, `leo_relay`, one operator command cycle

| Stage | ms | Source |
|---|---|---|
| Sensor exposure + readout, 720p30 global shutter | 25 | hardware_landscape §4 (16–33) |
| Encode, Jetson NVENC 720p H.264 | 8 | hardware_landscape §4 (5–8); multi_operator_bandwidth §1.2 (10 at 1080p) |
| Downlink propagation + mesh + PoP | 18 | network_emulation §4 P2 |
| Jitter buffer | 10 | teleop_fundamentals §3; multi_operator_bandwidth §1.2 |
| Decode | 10 | teleop_fundamentals §3 |
| Display, 60–144 Hz | 12 | teleop_fundamentals §3 (8–17) |
| Human visuomotor correction | 170 | teleop_fundamentals §3 (143–170 online correction) |
| Input polling + command path + IK | 12 | teleop_fundamentals §3 (5 + 4–10) |
| Uplink propagation + mesh + PoP | 30 | network_emulation §4 P2 |
| Satellite playout buffer | 30 | §5 item 1 `[design choice]` |
| Servo bus + actuation | 8 | teleop_fundamentals §3 (3–8, secondary); joint settling `[unverified]` |
| **Sum** | **333** | |
| Sum excluding human (machine loop) | 163 | |

Largest three contributors: the human (170 ms, 51 %), the link both ways (48 ms, 14 %), and the satellite playout buffer (30 ms, 9 %), with sensor capture close behind at 25 ms. The link is not the dominant term; this matches teleop_fundamentals §3 (Anvari telesurgery: 14 ms of 135 ms was network). On `direct_gs` the sum is ≈315 ms; on `geo_relay` ≈885 ms. The video floor reconciles teleop_fundamentals §3 (100–130 ms, USB webcam) with hardware_landscape §4 and multi_operator_bandwidth §1.2 (50–90 ms, MIPI global shutter + NVENC): we take the latter because the USB capture path is avoidable and multi_operator_bandwidth calls it disqualifying.

## 9. Open questions, ranked by design impact

1. **Measured latency and terms for a third-party satellite over Starlink mini-laser.** No measurement exists; mass, power, price, ITAR status and ground-side allocation are unpublished (leo_link_options §2 b1; network_emulation §1.2; hardware_landscape risk 1). This decides whether the primary path is real.
2. **Kepler latency and coverage of a non-Kepler-plane satellite.** Only "sub-second" from trade press; datasheet says 95 % continuity, leo_link_options says intermittent (unresolved between hardware_landscape §6 and leo_link_options §2 b2).
3. **Radiation behaviour of COTS servos and on-orbit Jetson reboot rate.** No TID/SEE data for Dynamixel or Feetech; no operator publishes Jetson reboot statistics (hardware_landscape §3, §5).
4. **Does latency-collected demonstration data train worse policies?** No study collects demos at controlled latency and reports policy success (data_pipeline §2.3); the link runs only through operator-quality proxies.
5. **Jitter distribution shape on Starlink.** Only a 2–3 component Gaussian mixture is validated; log-normal vs gamma is untested (network_emulation §1.1). The uplink OWD sum (52 + 35 ms idle probes) also exceeds the 40 ms RTT median from M-Lab; which dataset describes a laser-relayed satellite is unknown.
6. **Ground backhaul latency from any GS provider**, and the continuous-transmit thermal qualification of CubeSat X-band radios (hardware_landscape §6).
7. **Packet reordering and ISL stage effects** for relayed paths (network_emulation §1.1, §1.2).
8. **Capture task limits**: safe release spin rate and target speed are rules of thumb `[unverified]` (unique_data_study §4).
9. **LeRobot loader tolerance** for a missing `stats/*` block and for sidecar files (data_pipeline §1.5, §3.2).

## 10. Hypothesis axes seed

**Link path.** The evidence splits into a continuous regime (48 ms base, structured spikes and outages) and a pass regime (30 ms, near-clean, 21 % duty cycle). Promising ideas exploit the structure: scheduling episodes and resets against the 15 s clock, using two terminals so one re-acquires while the other carries traffic, and treating direct passes as the high-quality tail of a mixed collection plan rather than as a fallback. GEO relay is out of scope for continuous control but is the right control condition for supervisory-mode hypotheses.

**Transport protocol.** Uplink is tiny (27–54 kbps per operator raw UDP) so redundancy is nearly free: duplicate-send or FEC beats NACK on a bursty, pass-bounded link, and RFC 8854's own guidance flips toward retransmission only when RTT is inside the budget. The 256 kbps S-band cap on the pass regime makes header overhead (68 B raw vs 133 B WebRTC data channel) a real variable. On the video side, intra-refresh, no B-frames and a 0–10 ms playout hint are the settings every source agrees on.

**Latency-hiding control scheme.** The ranked evidence is: onboard admittance plus a "finish the insertion" primitive (49 → 65–81 % success), predictive phantom overlay (−19 % time at 1 s, nothing below 150 ms), motion scaling (−29 to −43 % error at 750 ms), and a jitter buffer bounded at 50–70 ms. Mean latency costs more than jitter (Beech 2024), so buffering depth is a knob to minimise, not maximise. Wave variables and passivity are irrelevant without force feedback.

**Operator interface and workflow.** The Astrobee/POIC pattern of one write authority per arm, fanned-out observers and pass-sized booked slots is the proven structure. Ideas worth testing: a session broker that hands an arm to the next operator during holds and resets, operator-side sensory anchoring for grasp events (accuracy restored at 250–1000 ms), and interface rates of 50 Hz on the follower regardless of link rate, since 5 Hz teleop costs 62 % more time.

**Task and data design.** The unique-value tasks are slow by nature, which is the largest latency hider available. Promising directions: designing tasks so the precision segment is short or delegated, logging base IMU and every link timestamp per sample so the success-vs-latency curve and deployment latency matching come from real data, and using smoothness metrics (SAL, LDLJ, stall fraction) as a curation filter, since top-half SAL selection lifted policy success from 39 % to 55 % on comparable data.

## Implication for our design

The testbed's default profile is `leo_relay` with the §7 parameters and the baseline is (c) as defined in §5 with a 30 ms playout buffer, 300 ms hold and 10 s retract. Every experiment sweeps RTT from 0 to 1000 ms with the human model fixed at 170 ms, reports the full success-vs-latency curve and per-pass throughput on `direct_gs`, and gates on 80 % of zero-latency success and demos/hour plus zero unsafe motion. The first hypothesis implemented head to head should be onboard compliance for the insertion phase, because it is the only hider with evidence of recovering the exact phase the baseline is predicted to fail.
