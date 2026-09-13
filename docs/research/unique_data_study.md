# What orbit-only manipulation data is worth collecting

Question: which manipulation phenomena cannot be produced reliably in Earth simulators or Earth labs, so that teleoperated robot-arm demonstrations in LEO carry unique value for physical-AI training?

Method: primary sources (ISS experiment papers, ESA/NASA reports, simulator docs, sim-to-real studies). Ranking is by "residual gap": what remains unavailable after the best simulator and the best Earth analog are both used. Numbers without a source are marked `[unverified]`.

## 1. Earth analog capability envelope

| Analog | Residual g | Duration | DoF / notes | Source |
|---|---|---|---|---|
| ISS (orbit) | quasi-steady < 1e-6 g; vibratory 20–40 µg RMS structural band, up to >10 mg at high freq | unlimited | 6-DoF | [1] |
| Parabolic flight | measured 0.041 ± 0.005 g mean during "0 g" phase (727-200F, N=17); best-case ±0.01 g "sweet zone"; floor-mounted rigs ~1e-2 g | 17–24 s per parabola | 6-DoF, strong g-jitter | [2][3] |
| Drop tower (ZARM catapult / NASA GRC) | 1e-4 g (ZARM); <1e-5 g (GRC ZGF) | 9.3 s / 5.2 s | 6-DoF, no operator loop possible | [4][5] |
| Planar air bearing | 1e-3 to 1e-5 g | hours | **2 translational + 1 rotational only** | [6] |
| Neutral buoyancy | n/a | hours | water drag and added mass; tasks must be slow | [7] |
| Gravity-compensated robot holding "free-floating" target | n/a | hours | target is a robot end effector, not free | [8] |

Key point: no Earth analog gives 6-DoF free motion for longer than ~24 s, and the only long-duration analog (air bearing) is planar.

## 2. Phenomenon-by-phenomenon assessment

| # | Phenomenon | Simulators (MuJoCo / Isaac / Genesis / Drake) | Earth analogs | Residual gap | Rank |
|---|---|---|---|---|---|
| A | Granular / regolith media in µg | DEM exists; cohesion-dominated regime unvalidated. Genesis MPM "Sand" material exists [9]; MuJoCo has none. | Parabolic flight and drop tower only; g-jitter (1e-2 g) is 100× larger than asteroid-level g where behaviour changes | Behaviour at <1e-4 g "cannot be extrapolated" from 1e-2 g; rebound and ejecta appear at 10 cm/s in µg but not at lunar g; restitution drops 10× from 5 to 100 cm/s [10]. ISS centrifuge study found mass-flow law "deviates" at low g because bulk density falls [11]. Only stable long-duration low-g data comes from ISS [11]. | **1** |
| B | Fluids: slosh, capillary, bubbles | SPH/MPM/PBD liquids in Genesis and PhysX [9][12]; moving contact line is an unresolved multiscale problem, macroscale solvers need sub-slip-length meshes [13]. MuJoCo/Drake: no fluids. | Drop towers too short for CFD validation; parabolic flight "imprecise low gravity" [14] | Before SPHERES-Slosh "little experimental data for long-duration zero-gravity slosh existed"; the ISS study reached only qualitative CFD comparison, and dead-reckoned tank pose diverged after ~30 s [14]. ISS boiling data show delayed bubble detachment and larger bubbles that standard VOF missed without added force terms [15]. | **2** |
| C | Deformables: cables, fabric, bags, nets | FEM/PBD cloth in Isaac and Genesis [9][12]; cloth sim-to-real gap is measurable even at 1 g [16] | Nets: 15+ parabolic deployments, 100 % capture, used to validate a lumped-mass simulator [17]. Nothing for long-duration bag/cable handling. | Astrobee cargo-bag work is simulation-only and states deformable dynamics "remains an open challenge" [18]. No sustained µg dataset of a gripper handling cable/fabric exists (no finding beyond [17][18]). | **3** |
| D | Free-floating / tumbling capture | Rigid dynamics at g = 0 is well modelled: Astrobee RL controller trained in Omniverse ran on ISS [19]; ETS-VII validated Generalized-Jacobian control on a 2.5 t base with a 2 m arm [20]. Contact transients at grasp are the weak part: MuJoCo has no restitution coefficient, "cannot simulate elastic collision" [21][22]; Drake hydroelastic captures no tangential compliance or wave effects [23]. | Air bearing is planar; Earth "free-floating target" studies actually held the target on a gravity-compensated robot and tested only stationary targets [8] | Real grasp impulses that push a free target away (documented failure mode [8]) at 6-DoF over minutes: orbit only. Measured µg restitution for cm glass spheres: 0.64 [24]; mm-particle sticking threshold ~1 cm/s [25]. | **4** |
| E | Arm–base momentum coupling | Exactly captured by rigid multibody sim (conservation laws); flight-verified on ETS-VII [20]. | Air bearing (planar) | Small for physics; the value is in **identification** of a real base (fuel slosh, flexible panels, wheel dynamics) rather than the coupling itself. For a 100 kg bus and a 4 kg arm moving its CoM 0.5 m, base translates ≈ 0.5·4/104 ≈ 19 mm `[calculation, unverified assumptions]`. | 5 |
| F | Tool use without gravity referencing | Same rigid physics as E | KC-135 study: unrestrained suited subjects; tool use "more effective inward toward the body" [26] | Data-poor but mostly a reaction-force problem, covered by D/E. No separate finding. | 6 |
| G | Vacuum / thermal contact (cold welding, lubrication, outgassing) | Not modelled in any listed simulator | **Fully reproducible in Earth thermal-vacuum chambers**: ESA STM-279 measured adhesion 0.1 N static, 0.96 N impact, 9.5 N fretting (Ti alloy vs 440C); worst self-pairs Al 7075 and SS17-7PH at 1744 mN [27]. MoS2 friction 0.01 in vacuum vs 0.15–0.30 in humid air [28]. | Orbit adds nothing over a vacuum chamber except duration and combined µg. | 7 |
| H | Lighting | Rendering exists; SPEED+ shows synthetic→real gap: orientation error 7.8° (synthetic) → 65° (lightbox) → 93° (sunlamp) for SPN [29] | Sunlamp (1 solar constant, 6000 K) and albedo lightboxes reproduce orbit lighting on Earth [29] | Inside a pressurized LED-lit volume there is nothing unique; exterior sun/eclipse cycling is reproducible in HIL labs. | 8 |

Verdict: the unique-value phenomena are A, B, C (non-rigid media without gravity), then D (real contact impulses on a truly free 6-DoF object). E–H are either exactly simulable or reproducible in Earth chambers.

## 3. Teleoperation constraint

Under delay, operators fall into move-and-wait and completion time grows roughly in proportion to delay; effects are already visible at ~300 ms [30][31]. ISS→ground direct S-band showed 20–30 ms with negligible loss (KONTUR-2) [32]. Consequence: tasks must tolerate a 0.1–0.3 s operator dead time, so objects must move slowly (order cm/s) and every task needs a hold-safe state on link loss (program baseline (b)).

## 4. Ranked candidate task list

All tasks: 6-DoF arm, parallel gripper, workspace enclosed by a cage or transparent cell so nothing drifts out of reach. "Sealed cell" means a small pressure vessel around the media; the bus itself may be unpressurized.

| Rank | Task | Phenomena | Volume | Sensors | 100–300 ms teleop |
|---|---|---|---|---|---|
| 1 | **Scoop, transport, pour granular simulant** (<250 µm sieved, per [10]) between two open trays inside a transparent cell | A, D | sealed cell (gas-filled to keep electrostatics and thermal environment sane; works inside pressurized bus or as its own vessel in vacuum) | 2 cameras (top, side), wrist F/T, joint torques | Yes: slow scooping, no time-critical step |
| 2 | **Free-floating object capture** (cm-scale rigid blocks/spheres, released with slow spin ≤ 1 rad/s `[unverified]`) and re-release | D, E | vacuum or pressurized | stereo/RGB-D, wrist F/T, base IMU + gyro, joint encoders | Yes if target speed ≤ 2–5 cm/s `[unverified rule of thumb]`; faster only with onboard assist (hypothesis branch) |
| 3 | **Partially filled liquid container handling and capillary pour** between vessels of different geometry | B, D | sealed cell, must stay above water triple point; pressurized bus strongly preferred | high-rate camera (≥60 fps `[unverified]`), wrist F/T, IMU on container | Yes: capillary flows are slow (seconds) |
| 4 | **Cable routing and fabric pouch open/close** (Velcro pouch, 30 cm cable with two connectors) | C | either | 2 cameras, wrist F/T | Yes |
| 5 | **Peg-in-hole on a fixture rigidly attached to a light bus**, with attitude control disabled or wheel torques logged | E, D | vacuum or pressurized | base IMU/gyro/star tracker, joint torques, wrist F/T | Yes; slow insertions |
| 6 | **Two-part assembly with detent/magnet**, then release and re-grasp of the drifting assembly | D, C (if soft parts) | either | stereo, F/T | Yes |
| 7 | **Metal-on-metal repeated grasp cycles** (bare Al 7075 and SS17-7PH coupons, per [27]) logging pull-off force drift | G | vacuum only | wrist F/T, temperature | Yes (repetitive) — low uniqueness, cheap add-on |
| 8 | **Exterior tasks under sun/eclipse transitions** (repeat 2 or 6 in view of an external camera) | H | vacuum, exterior | HDR camera, event camera optional | Yes — low uniqueness |

Tasks 1–4 are where orbit data has no substitute. Tasks 5–8 are good testbed proxies precisely because MuJoCo reproduces their physics.

## 5. Implication for our design

Build the testbed and the latency curve on rigid-body proxies (tasks 2, 5, 6) because MuJoCo at g = 0 is faithful for them and the ETS-VII and Astrobee results show sim-trained control transfers for rigid free-floating dynamics; state clearly in the report that MuJoCo has no restitution parameter and cannot reproduce grasp-impulse transients, so success-vs-latency for capture is a lower bound. Rank the satellite payload so that at least two of the four arms carry a sealed granular cell (task 1) and one carries a sealed liquid cell (task 3): these produce the only demonstrations that Earth cannot, and both are slow tasks that tolerate 100–300 ms. Prefer a pressurized bus or, if unpressurized, self-contained pressure cells for tasks 1 and 3. Log base IMU and gyro on every demonstration at ≥100 Hz `[unverified]` so the free dataset also serves base-dynamics identification. Drop cold-welding and lighting from the unique-value claim; keep them as cheap secondary logs.

## Sources

1. NASA, ISS Acceleration Environment mini-book (2016) — https://www.nasa.gov/wp-content/uploads/2016/06/acceleration-environment-iss-mini-book_detail-508c.pdf
2. Carr et al., "Acceleration profiles and processing methods for parabolic flight", npj Microgravity 2018 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6081456/
3. ESA, Microgravity and parabolic flights — https://www.esa.int/Education/Fly_Your_Thesis/Microgravity_and_parabolic_flights
4. ZARM drop tower / catapult (science.gov summary) — https://www.science.gov/topicpages/z/zarm+drop+tower
5. Drop tower overview (NASA GRC 2.2 s and Zero-G facility) — https://www.sciencedirect.com/topics/physics-and-astronomy/drop-tower
6. Rybus & Seweryn, "Planar air-bearing microgravity simulators", Acta Astronautica 2016 — https://www.sciencedirect.com/science/article/abs/pii/S0094576515004634
7. "Vection underwater illustrates the limitations of neutral buoyancy as a microgravity analog", npj Microgravity 2023 — https://www.nature.com/articles/s41526-023-00282-3
8. "Domain Randomization in RL for Pre-Capture of Free-Floating Moving Targets", arXiv 2406.06460 — https://arxiv.org/pdf/2406.06460
9. Genesis physics engine API (solvers and materials) — https://genesis-world.readthedocs.io/en/latest/api_reference/engine/index.html
10. Brisset et al., "Regolith behavior under asteroid-level gravity conditions", PEPS 2018 — https://arxiv.org/abs/1810.01459
11. "Granular flow experiment using artificial gravity generator at ISS", npj Microgravity 2023 — https://www.nature.com/articles/s41526-023-00308-w
12. Isaac Lab framework paper (PhysX deformables) — https://arxiv.org/pdf/2511.04831
13. Snoeijer & Andreotti, "Moving Contact Lines: Scales, Regimes, and Dynamical Transitions", Annu. Rev. Fluid Mech. 2013 — https://www.annualreviews.org/content/journals/10.1146/annurev-fluid-011212-140734
14. NASA NTRS 20170006556, "Progress Towards a Microgravity CFD Validation Study Using the ISS SPHERES-SLOSH Experiment" — https://ntrs.nasa.gov/citations/20170006556
15. Mudawar & Lee, computational study validated against ISS FBCE — https://www.sciencedirect.com/science/article/abs/pii/S1359431125032557
16. "Benchmarking the Sim-to-Real Gap in Cloth Manipulation" — https://arxiv.org/pdf/2310.09543
17. Medina et al., "Validation results of satellite mock-up capturing experiment using nets", Acta Astronautica 2017 — https://www.sciencedirect.com/science/article/pii/S0094576516300406
18. "Deformable Cargo Transport in Microgravity with Astrobee", arXiv 2505.01630 — https://arxiv.org/html/2505.01630v1
19. "Crossing the Sim2Real Gap ... Space Deployment of Autonomous Free-flyer Control", arXiv 2512.03736 — https://arxiv.org/abs/2512.03736
20. Yoshida, ETS-VII experiments (Tohoku Univ.) — https://astro.mech.tohoku.ac.jp/~yoshida/ETS-VII/index.html
21. MuJoCo discussion #2081, coefficient of restitution — https://github.com/google-deepmind/mujoco/discussions/2081
22. SimBenchmark bouncing test — https://leggedrobotics.github.io/SimBenchmark/bouncing/
23. Drake hydroelastic contact user guide — https://drake.mit.edu/doxygen_cxx/group__hydroelastic__user__guide.html
24. "Free Collisions in a Microgravity Many-Particle Experiment IV" — https://arxiv.org/html/1412.3236
25. NanoRocks ISS, "Multi-Particle Collisions in Microgravity", A&A 2019 — https://arxiv.org/abs/1909.06417
26. NASA NTRS 19940016133, "Loads produced by a suited subject performing tool tasks without the use of foot restraints" — https://ntrs.nasa.gov/citations/19940016133
27. ESA STM-279, "Assessment of Cold Welding between Separable Contact Surfaces due to Impact and Fretting under Vacuum" — http://esmat.esa.int/Publications/Published_papers/STM-279.pdf
28. "Frictional Behavior of MoS2 Coatings ... in Vacuum and Inert Gases", Coatings 2025 — https://www.mdpi.com/2079-6412/15/5/500
29. Park et al., SPEED+ dataset, arXiv 2110.03101 — https://ar5iv.labs.arxiv.org/html/2110.03101
30. Ferrell / Sheridan, "Factorial study of remote manipulation with transmission time delay", NASA 1971 — https://ntrs.nasa.gov/api/citations/19710009659/downloads/19710009659.pdf
31. "Every Move You Make: Visualizing Near-Future Motion Under Delay for Telerobotics", CHI 2026 — https://doi.org/10.1145/3772318.3791452
32. Artigas et al., "KONTUR-2: Force-feedback Teleoperation from the ISS", ICRA 2016 — https://elib.dlr.de/105317/1/07487246.pdf

Also consulted (no figures taken): DLR Astrobee tumbling-target grasp news (https://www.dlr.de/en/latest/news/2022/01/20220322_mini-robots-practise-grasping-space-debris); gecko gripper on Astrobee, 3.15 N manual perching (https://ieeexplore.ieee.org/document/9783137/); Astrobee orbital hopping ground-vs-flight comparison (https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2022.1004165/full); Guo et al., "Benchmarking Rigid Body Contact Models", L4DC 2023 (https://proceedings.mlr.press/v211/guo23b/guo23b.pdf); DexCoHand gripper for Astrobee (https://arxiv.org/abs/2605.17851).
