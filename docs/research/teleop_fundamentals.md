# Teleoperation fundamentals for latency

> First-wave research note, retained for traceability. The [second-wave evidence review](second_wave_evidence.md) corrects consequential source claims; the [current synthesis](SYNTHESIS.md) governs decisions.

Scope: what measured human performance does as round-trip time (RTT) and jitter grow, per manipulation task class; which latency-hiding methods have quantified evidence; and what a ground teleop stack's latency budget actually looks like. Numbers carry a source or `[unverified]`. "Secondary" marks a figure taken from a survey or citing paper rather than the original.

## 1. Human performance versus RTT and jitter

### 1.1 Foundational results

- **Sheridan & Ferrell 1963, Ferrell 1965 (MIT/NASA TN D-2665).** 3-DoF "minimal manipulator" with delayed command and feedback. Operators universally adopt **move-and-wait**: open-loop move, then wait one RTT for confirmation. Completion time = (no-delay time) + (number of open-loop moves) × (delay), so it grows **linearly in delay**; the number of moves grows linearly with Fitts index of difficulty. Exact delays tested: `[unverified, ~1–3 s]`. Sources: Frontiers survey 2020; NTRS 19660064449; IEEE 1698160.
- **Black 1971 (MIT/NASA CR, 6-DoF extension).** 6-DoF manipulator, 3.5 s video-tape feedback delay, 3 subjects, block stacking / peg tasks at two scales. Task time with 3.5 s delay ≈ **10× the no-delay time** in all six task×scale cases (within 10 % in four). Trial-and-error alignment "was impossible"; the precision "position" segment took a larger share of the time than "get" and "transport". Move-and-wait was mandatory. Source: NTRS 19710009659.
- **Fitts-law lag (MacKenzie & Ware 1993).** Target acquisition with 0/25/75/225 ms lag. At 225 ms, movement time +64 % and errors +214 % vs zero lag; lag acts multiplicatively on index of difficulty (R² 0.94). Sources: yorku.ca CHI93b; ACM 169059.169431.
- **Onset latency vs slowness (Rakita, Mutlu & Gleicher, HRI 2020).** Mimicry (arm-tracking) control, 21 participants, base loop ≈90 ms at 80 Hz, added onset latency 250/500/750 ms and three robot-speed limits. Onset latency degraded every task and every perception measure; operators adapted to slowness but **no strategy emerged for onset latency**. 250 ms was chosen as the point where prior work shows degradation starts. Source: graphics.cs.wisc.edu RMG20.

### 1.2 Task-class studies with numbers

| Study | Task class | Delay levels | Result |
|---|---|---|---|
| Xu et al. 2014, dV-Trainer, 16 subjects (secondary via PMC13048677, VTT 2024) | Precision (needle driving, dissection) | 0–1000 ms, 100 ms steps | <200 ms "ideal"; 200–300 ms maximum acceptable; degradation "exponential" with latency; substantial precision drop above 500–700 ms |
| Peg transfer, FLS kit (secondary, Frontiers survey; DOI 10.1109/iembs.2009.5333120) | Coarse pick-and-place | 0, 250, 500 ms | Completion time ×1.45 at 250 ms, ×2.04 at 500 ms |
| Richter et al. 2019 (arXiv 1902.03290), 17 participants | Coarse pick-and-place (peg transfer, da Vinci) | 0 vs 750 ms RTT | Time 44.3 s → 92.5 s (×2.1); weighted error 4.5 → 13.2 (×3). Cites 50 ms as onset of overshoot/oscillation (secondary) and 300 ms as surgical safety limit |
| Du et al. 2024, Sci. Rep., 41 participants, VR arm pick-and-place | Coarse pick-and-place | visual delay 250/500/750/1000 ms | Time-on-task and placement accuracy both significantly worse than zero delay (p<0.001 / p<0.01) across the range; real-time haptic "anchoring" cue restored accuracy to control level (p=0.168) |
| Mobile-robot joystick, 10 participants (arXiv 2508.18074) | Free-space motion (driving) | 0–500 ms, 100 ms steps | First significant speed and accuracy loss between 200 and 300 ms; compensation plateau at 400 ms |
| Lane et al. 2002 (Ranger neutral-buoyancy) | Free-space 3-D flying | 0–5 s | Significant completion-time increase above 1.5 s |
| Kazanzides et al. 2021 (Frontiers) | Contact task (MLI cutting) | 0 vs 4 s | Cutting speed 2.04 → 1.76 mm/s; path error 0.92 → 1.44 mm (p<0.001); workload 18.9 → 23.0 |
| Delay vs bandwidth peg-in-hole with finger force feedback (ScienceDirect S1474667017585936) | Contact-rich insertion | delays via circular buffer | Time and error fall as delay falls; **little gain below 48 ms** delay or above 6 Hz force bandwidth |
| Bristol/ACM THRI 2024, haptic controller, IOSM tasks | Contact-rich | up to 2.6 s | Latency reduced every metric; haptics still lowered contact force and velocity at high delay but accuracy/trust gains vanished or reversed |
| Haptic delay detection (Rank et al. 2010; numbers secondary) | Force perception | — | Delay detectable from 15 ms (damper), 36 ms (spring), 72 ms (damped inertia) |
| Clinical telesurgery (PMC9923406) | Precision | measured RTT | Completed cases at 28, 53, 135–150, 155, 280 ms; impairment reported at 135 ms and even 50 ms; >700 ms "may not be feasible" |

### 1.3 Jitter

- **Beech et al. 2024 (ACM TAP).** Target acquisition at fixed mean latency: completion-time impairment starts at **67 ms jitter amplitude**, accuracy impairment at **134 ms**; jitter frequency had no effect; the jitter effect was "comparatively small" and shrank as mean latency rose. Mean latency dominates. Source: DOI 10.1145/3701984 (abstract).
- **Yang & Dorneich 2017.** Intermittent/variable lag in robot teleop raised frustration, anger and workload and cut performance; the variable-delay effect exceeded the effect of task complexity. No constant-vs-variable equal-mean comparison. Source: Springer s12369-017-0407-x.
- Kontur-2 measured the operational reality: ISS S-band 20–30 ms RTT with ~0.1 % loss and ±2 ms jitter; a UDP internet link 65 ms mean with 5–7 % loss and 0–10 ms jitter. Source: DLR elib 105317.
- No finding on jitter specifically for manipulation (as opposed to pointing) beyond the above.

### 1.4 Modern leader-follower budgets

ALOHA 2 records leader/follower joints at **50 Hz** and reports that this outperforms lower rates; no ms latency is given in the paper (arXiv 2405.02292). Secondary sources put the local Dynamixel-bus leader→follower latency at 3–8 ms and the "transparent" requirement at <10 ms (roboticscenter.ai, robotforge.org; unverified). GELLO's user study reports task success 0.5–0.92 for VR controllers vs higher for GELLO (arXiv 2309.13037, Table II). The Real-to-Sim shared-autonomy paper streams GELLO commands at only **15 Hz** (≈67 ms period) and still reaches 65–81 % on nut threading (arXiv 2603.17016). Takeaway: policy-grade demos are collected at 30–60 Hz with local RTT well under 50 ms; no published leader-follower dataset was collected over a >100 ms link.

## 2. Latency-hiding methods and how much they recover

| Method | Evidence | Latency recovered |
|---|---|---|
| **Predictive display** (phantom overlay) | Bejczy/Kim 1990 phantom robot: "significant" gain in free motion, no number. Kim & Bejczy 1993: JPL↔Goddard, several-second delay, ±5 mm placement inside ±12 mm margin. SARPD telesurgery, 1 s delay, 10 participants: completion time −19 %, errors unchanged (arXiv 1809.08627). Low-cost PD at 500 ms: speed +29 %, path deviation −35 % (secondary, ResearchGate 343874282). Teledriving at 150 ms, 29 participants: **no measurable benefit** (PMC12788196). Intention-reflected PD at 0.8/1.2 s RTT: error significantly reduced (ROBOMECH 2023) | Makes 0.5–3 s workable for free-space and coarse tasks; buys nothing below ~150 ms; does not hide contact |
| **Model-mediated teleop** (local environment model, Mitra & Niemeyer 2008) | Visual-haptic MMT for remote ultrasound, 15 operators: at 500 ms one-way, completion time and effort **not different from zero delay**; at 1000 ms still significant gains; centering error 231 → 161 px (arXiv 2502.07922) | Fully hides ~1 s RTT for a modelled, quasi-static contact task; depends on model fidelity |
| **Wave variables / passivity** (Niemeyer & Slotine) | Stability for arbitrary constant delay; cost is transparency, wave reflection and position drift; with position compensation, good tracking to 500 ms RTT constant and variable (secondary, IEEE 10865230). Avatar XPRIZE 3rd-place system used enhanced wave variables (Springer s12369-023-01092-z) | Recovers stability, not performance; force feel already perceptibly degraded by tens of ms |
| **Time-domain passivity (TDPA)** (Hannaford & Ryu) | Kontur-2: 4-channel TDPA stable over 20–30 ms ISS link and 65 ms/7 %-loss internet; without a passivity controller the loop was unstable at 5 ms. TDPA tested to **3 s** delay with "sufficient" force feedback (DLR retrospective). GESR: transparent contact feel only when **one-way delay < 0.1 s** | Keeps force feedback stable to seconds; feel degrades past ~100 ms one-way |
| **Shared autonomy / onboard compliance** | Copilot + admittance control: nut threading 49 → 65–81 % success; downstream IL 7/20 → 18/20 grasps (arXiv 2603.17016). Jin et al. 2019: coarse teleop + local fine controller raised success 70 → 100 % and 70 → 90 % on a ~111 ms/KB link | Removes the fine-alignment phase, which is exactly the phase delay hurts most (Black 1971) |
| **Supervisory / subgoal commands** | SUPVIS-Justin, ISS→ground: RTT 832 ms mean (800–1132), 1 Mbit/s, scheduled loss-of-signal; task-level commands completed maintenance/assembly. ROTEX 1993: 5–7 s with predictive graphics plus onboard sensor loops. ISS MSS today: nominal 2.5 s RTT, telemetry to 5 s; JEMRMS worst case 10 s; practice is command-and-wait | Works at any delay; demo data is then robot-executed, not human motion |
| **Command buffering + interpolation / forecast** | FoReCo (802.11 with jammer, pick-and-place): ML-inferred missing commands cut trajectory error **×18 in sim, ×2 on hardware**. WebRTC jitter buffer adds ≈10 ms (Transitive) | Removes loss/jitter artefacts; adds a fixed delay equal to buffer depth. Beech 2024 implies buffering more than ~70 ms of jitter costs more than it saves |
| **Motion scaling** | 750 ms RTT: velocity scaling −29 to −43 % weighted error vs constant scale (arXiv 1902.03290) | Trades speed for accuracy; cheap |
| **Sensory anchoring** (immediate synthetic haptic cue) | Du 2024: accuracy restored to zero-delay level at 250–1000 ms visual delay; time still worse | Hides perceived delay for the grasp/release event |

## 3. Latency budget of a ground teleop stack

| Stage | Measured | Source |
|---|---|---|
| Camera exposure + ISP + USB | ~100 ms (webcam, 30 fps); ~120 ms | Transitive Robotics; arXiv 2602.17381 |
| Frame interval | 33 ms @30 fps, 17 ms @60 fps | Transitive |
| H.264 encode / decode | ~10 ms each | Transitive |
| Server-side pre-processing | ~39 ms | arXiv 2602.17381 |
| Transport (control RTT) | 6.6 ms LAN; 58 ms Wi-Fi+VPN; 115 ms 4G; 241 ms transatlantic | VTT 2024 |
| Transport (space) | 20–30 ms ISS S-band direct; 540–620 ms GEO relay (Astra/Artemis, 2.6–5.8 % loss); 832 ms ISS Ku relay | Kontur-2; SUPVIS-Justin |
| Jitter buffer | ~10 ms | Transitive |
| Display / render | 8–17 ms | arXiv 2602.17381; Transitive |
| Human visuomotor correction | 143–170 ms online correction; 190–260 ms (Keele & Posner); express responses 80–120 ms | PMC6730029; ResearchGate 17521619 |
| Input device polling | ~5 ms | arXiv 2602.17381 |
| Command path + IK | 4 ms IK; 10 ms pre/post | VTT 2024; arXiv 2602.17381 |
| Actuation | vehicle: ~270 ms; arm servo bus: 3–8 ms `[secondary]`; joint settling `[unverified]` | arXiv 2602.17381; roboticscenter.ai |

Reference totals: glass-to-glass 110–170 ms on a LAN/cloud WebRTC path (Transitive); 193 ms G2G and 499 ms end-to-end on 5G (arXiv 2602.17381); Anvari 2005 telesurgery 135–140 ms RTT of which **only 14 ms was network**, the rest MPEG codec (PMC9923406). The camera pipeline and the human, not the link, dominate a terrestrial stack; a LEO direct pass adds only 20–30 ms, whereas a GEO relay adds 500–850 ms and moves the system into a different regime.

## 4. Tolerable RTT by task class

| Task class | Degrades noticeably (RTT) | Unusable for continuous control (RTT) | Basis |
|---|---|---|---|
| Free-space motion | 75–225 ms (MT +64 % at 225 ms); 200–300 ms significant | ~1–1.5 s (Lane 2002; switch to move-and-wait) | MacKenzie & Ware; arXiv 2508.18074; Lane |
| Coarse pick-and-place | 250 ms (Rakita; Du; ×1.45 time) | 750 ms–1 s (×2 time, ×3 errors); ×10 at 3.5 s | Richter 2019; iembs 2009; Black 1971 |
| Precision insertion | 100–200 ms (overshoot from 50 ms secondary; <200 ms "ideal") | 500–700 ms (surgical precision drop-off) | Xu 2014 via PMC13048677; PMC9923406 |
| Contact-rich / force tasks with force feedback | 15–72 ms perceptible; little gain below 48 ms; feel lost >100 ms one-way | Unstable without passivity at ≥5 ms; with TDPA stable to 3 s but feel degraded | Rank 2010; S1474667017585936; GESR; Kontur-2 |
| Contact-rich, no force feedback (our case) | as precision insertion, plus safety risk from delayed contact detection | as precision insertion | Black 1971 position-segment result |

## Implication for our design

The link is not the dominant term on a direct LEO ground pass (20–30 ms RTT) but becomes the whole problem on a GEO/ISS-style relay (540–850 ms). With a 100–130 ms camera+codec floor and 150–250 ms human correction latency, a direct-pass stack lands around 200–300 ms effective RTT, which the literature places at the edge of "degrades noticeably" for coarse pick-and-place (×1.45 time at 250 ms) and past it for precision insertion. So the testbed should sweep 50–1000 ms with the human-reaction model fixed at ~150–200 ms, and the ≥80 % success acceptance will probably hold for coarse tasks only up to ~250–300 ms and for insertion only up to ~150 ms; a relay path will need a latency hider. The evidence-backed hiders for a no-force-feedback, joint-setpoint design are, in order of return: onboard admittance/compliance plus a subgoal-level "finish the insertion" primitive (removes the phase delay hurts most; 49 → 65–81 % success in the copilot study), a predictive phantom overlay on the operator side (−19 % time at 1 s, nothing below 150 ms), and a command buffer that absorbs at most ~50–70 ms of jitter into fixed delay, because mean latency costs more than jitter. Wave variables and TDPA are irrelevant without force feedback. Record demos at 50 Hz on the follower side regardless of link rate, and log the effective RTT per sample so the success-vs-latency curve can be built from real timestamps.

## Sources

- https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2020.578805/full
- https://ntrs.nasa.gov/citations/19660064449
- https://ieeexplore.ieee.org/document/1698160/
- https://ntrs.nasa.gov/api/citations/19710009659/downloads/19710009659.pdf
- https://www.yorku.ca/mack/CHI93b.html
- https://dl.acm.org/doi/10.1145/169059.169431
- https://graphics.cs.wisc.edu/Papers/2020/RMG20/rmg-hri2020.pdf
- https://dl.acm.org/doi/10.1145/3319502.3374838
- https://pmc.ncbi.nlm.nih.gov/articles/PMC13048677/
- https://link.springer.com/article/10.1007/s00464-014-3504-z
- https://doi.org/10.1109/iembs.2009.5333120
- https://arxiv.org/html/1902.03290
- https://www.nature.com/articles/s41598-024-54734-1
- https://arxiv.org/pdf/2310.08788
- https://arxiv.org/html/2508.18074v1
- https://ieeexplore.ieee.org/document/1013668
- https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.747917/full
- https://www.sciencedirect.com/science/article/pii/S1474667017585936
- https://dl.acm.org/doi/10.1145/3651993
- https://direct.mit.edu/pvar/article-abstract/19/5/389/18779/Perception-of-Delay-in-Haptic-Telepresence-Systems
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9923406/
- https://dl.acm.org/doi/10.1145/3701984
- https://link.springer.com/article/10.1007/s12369-017-0407-x
- https://elib.dlr.de/105317/1/07487246.pdf
- https://arxiv.org/html/2405.02292
- https://arxiv.org/abs/2309.13037
- https://arxiv.org/html/2603.17016v2
- https://www.roboticscenter.ai/learn/aloha-robot
- https://robotforge.org/tutorials/learning/teleop-rigs
- https://ieeexplore.ieee.org/document/126037/
- https://ntrs.nasa.gov/citations/19920000396
- https://ieeexplore.ieee.org/document/258061/
- https://arxiv.org/abs/1809.08627
- https://www.researchgate.net/publication/343874282_A_low-cost_predictive_display_for_teleoperation_Investigating_effects_on_human_performance_and_workload
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12788196/
- https://robomechjournal.springeropen.com/articles/10.1186/s40648-023-00258-8
- https://arxiv.org/html/2502.07922v1
- https://journals.sagepub.com/doi/10.1177/0278364904045563
- https://ieeexplore.ieee.org/document/10865230/
- https://link.springer.com/article/10.1007/s12369-023-01092-z
- https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.611251/full
- https://www.globalspaceexploration.org/wordpress/docs/Telerobotic%20Control%20of%20Systems%20with%20Time%20Delay%20Gap%20Assessment%20Report.pdf
- https://arxiv.org/pdf/1903.09189
- https://elib.dlr.de/130830/1/RA-L2019_final_Schmaus-Meteron_Supvis_Justin.pdf
- https://www.dlr.de/en/rm/research/robotic-systems/hands/rotex-1988-1993
- https://arxiv.org/pdf/2205.04189
- https://transitiverobotics.com/blog/webrtc-latency-breakdown/
- https://arxiv.org/html/2602.17381
- https://cris.vtt.fi/ws/portalfiles/portal/109010051/futureinternet-16-00457-v2.pdf
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6730029/
- https://www.researchgate.net/publication/17521619_PROCESSING_OF_VISUAL_FEEDBACK_IN_RAPID_MOVEMENTS
