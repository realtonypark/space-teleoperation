# Second-wave evidence review: what the mission can claim and what it must measure

Research cut-off: 2026-09-13. This review preserves the charter's goal: ground-operated arms inside a rideshare-class LEO spacecraft, producing useful physical-AI demonstrations. It independently checks consequential claims in the first-wave research and report against primary literature, agency publications, and supplier statements. A supplier statement verifies what the supplier advertises; it does not verify performance on this mission. No hardware was bought, no provider was contacted, and no flight measurement was made in this review.

The original program establishes a useful simulation and architecture trade study. The evidence supports continued development, but does not yet establish flight readiness, human performance, or incremental robot-learning value. These are three separate hypotheses. A favorable latency experiment cannot close all three.

## 1. Corrections that change decisions

| First-wave claim | Second-wave finding | Consequence |
|---|---|---|
| A Starlink relay makes the proposed architecture feasible with hardware buyable in 2026; 48/125 ms is its latency. | Primary announcements support commercial integration agreements and future deployment. They do not publish application-level latency, mission coverage, terminal power/mass, or an allocated end-to-end service for this spacecraft. The numerical profile is a scenario. | Keep relay as a conditional upgrade. A direct RF pass architecture is the conservative implementation reference; neither its scheduling nor its performance is guaranteed by orbital visibility alone. |
| Kepler cannot be continuous until 2028 because it has only 10–33 satellites. | Kepler announced commercial service on 24 August 2026. The cited material does not contain the client-orbit geometry needed to prove or disprove continuity. Ten optical satellites and 33 satellites launched over company history are different counts. | Treat mission continuity as unknown, not a demonstrated failure or a guaranteed 95% service. Obtain a mission-specific coverage and service proposal. |
| MuJoCo cannot simulate elastic collisions. | Official documentation explicitly supports perfectly elastic collisions with the direct `solref` format and zero damping. A direct coefficient-of-restitution field is a different matter. | Calibrate contact models. The existing simplified grasp cannot be assigned a conservative error direction without physical comparison. |
| A 100 kg Aries bus supports the launch and dynamics sketch. | Apex specifies a 125 kg base-model dry bus; 100 kg is the rideshare payload allowance. | Recompute total launch mass, base inertia, arm/base coupling and power against a selected configuration. |
| A 1-atm enclosure lets unmodified COTS hardware work with convection to the wall. | Pressure does not restore buoyancy-driven cooling in microgravity. | Provide conductive heat paths and/or forced circulation, and assess how that circulation disturbs the recorded physics. |
| Estimated dose below a generic COTS threshold makes a one-to-two-year servo mission acceptable. | Total dose and single-event effects are separate hazards; NASA requires mission-, application- and part-specific consideration. | Keep the independent supervisor, current limits and power control; add component qualification and fault-injection gates. |
| Orbit-only data has no substitute, and no one has collected orbital robot-learning demonstrations. | Long-duration repeatable microgravity is a credible advantage. A bounded search cannot establish a universal absence. Existing orbital physical data and shorter non-orbital experiments are comparators, not negligible alternatives. | Make the novelty claim narrow and test whether the proposed demonstrations improve learning over matched alternatives. |

Primary evidence and the necessary qualifications follow below.

## 2. Links: separate propagation, emulation and a purchasable service

### Optical relay status

Muon's October 2025 announcement confirms integration of Starlink optical terminals into Halo and advertises up to 25 Gbps between satellites. The currently accessible announcement does not establish the first-wave Q1 2027 launch date or a numerical RTT. Starcloud's May 2026 company release describes a signed agreement for more than 50 terminals across more than 25 satellites, with first hardware expected within one year. It specifies two terminals per spacecraft and up to 25 Gbps across a 4,000 km intersatellite link. These are useful procurement precedents, not measured service on this mission. [Muon announcement](https://www.muonspace.com/starlink-lasers-halo/), [Starcloud company release](https://www.businesswire.com/news/home/20260526670395/en/Starcloud-to-Integrate-SpaceXs-Starlink-Mini-Lasers-Into-Its-Orbital-Data-Center-Constellation).

The 2024 Starlink measurement paper does support latency variation and synchronized 15-second reconfiguration in consumer access. It measures ground terminals, Internet endpoints and access paths. Its global analysis uses minimum RTT within speed tests; that statistic is not the loaded application's median RTT. Its authors also find that reconfiguration is likely independent of satellite handover. Consequently, neither the consumer latency distribution nor a two-terminal arrangement establishes a third-party spacecraft's handover distribution. A single 4,000 km hop takes about 13.3 ms one way, or 26.7 ms for symmetric traversal in both directions [calculation: distance divided by light speed]. Adding that hop to a consumer median is not a validated route model. [Mohan et al., WWW 2024, §§3–6](https://www.nitindermohan.com/documents/2024/pubs/starlinkWWW2024.pdf).

Kepler's January release identifies ten approximately 300 kg optical relay satellites entering commissioning. Its August release announces commercial operation, SDA-compatible optical demonstrations and links with more than ten optical ground stations. Expansion in 2028 is a capacity and performance plan. The releases supply neither a customer-orbit RTT distribution nor a guaranteed continuous bidirectional video service. Satellite count alone cannot establish visibility, route availability, terminal contention or optical acquisition time. [January launch release](https://kepler.space/kepler-successfully-launches-first-tranche-of-optical-relay-satellites/), [August service release](https://kepler.space/kepler-delivers-optical-infrastructure-for-real-time-space-operations/).

**Decision:** retain both relay candidates. Do not select between them using an unmeasured 48 ms RTT for one and an unproved continuity failure for the other. Label `leo_relay` as a consumer-informed synthetic low-latency relay scenario. Assess several latency/outage envelopes until spacecraft-client traces exist.

### Direct passes and operational time

KSAT offers a direct-to-Earth ground network. Its reported contact success or service availability is conditional on service delivery; it is not the fraction of the day that a particular spacecraft is in view. A pass union from a TLE measures geometric opportunity. Antenna reservations, elevation masks, RF compatibility, acquisition, link margin, backhaul, command authority and safe end-of-pass motion determine usable operations. Thus the first-wave approximately 21% geometric coverage must remain distinct from a booked teleoperation duty cycle. [KSATlite service](https://www.ksat.no/ground-network-services/ksatlite/).

The claim that *any* global ground network cannot approach continuous coverage is too broad. Coverage depends on orbit and site geometry; limited sites and ocean gaps constrain this design. The existing four-site calculation is a useful specific case, not an impossibility proof for every network.

Use the following bookkeeping [proposed operational definition]:

`usable demonstrations/day = sum_over_booked_passes(accepted_demonstrations_completed_in_that_pass)`

The pass interval must exclude acquisition, setup, validation, reset, abort and end-of-pass hold time. Overlapping station contacts must not be counted twice. Report accepted demonstrations per active hour, per booked hour and per calendar day separately. A contact-conditioned 80% latency result can coexist with a low calendar-time yield.

A GEO relay's propagation floor does exclude a sub-150 ms network RTT requirement. It does not make supervisory manipulation physically impossible. ETS-VII is a direct counterexample to conflating slow links with impossible robotics: ESA flew ground-controlled robotic experiments using interactive autonomy across a relay infrastructure. Keep GEO outside the low-latency direct-control baseline, while retaining it as a slower operational reference if mission availability becomes more valuable than responsiveness. [ESA ETS-VII flight account](https://www.esa.int/esapub/bulletin/bullet99/visen99.pdf).

An out-of-band low-rate link is useful for recovery and status. It cannot be the mechanism that guarantees a timely stop during loss of contact. Local containment and an independent safety controller remain necessary even if a provider advertises near-continuous coverage.

### Service acceptance gate

Before claiming a relay supports four simultaneous operators, require the following [proposed gate, not work completed]: client-orbit and attitude coverage; optical terminal mass, power and pointing allocation; sustained application goodput under eight video streams; uplink/downlink delay distributions measured separately; loss bursts and outage lengths; terminal acquisition and route-change traces; end-to-end timestamp uncertainty; and a quoted service allocation. Include current load, ground location, orbit and firmware in every trace. Optical line rate is not an application service guarantee.

## 3. Hardware: keep the proposed architecture, qualify the assembly

### Mass, volume and cooling

Apex's LEO Aries specification lists 125 kg base-model dry mass, payload capacity up to 150 kg with a 100 kg rideshare allowance, a payload envelope of 865 × 1170 × 550 mm, and 175+ W base orbit-average payload power at end of life (500 W high-power option). Therefore the first-wave 100 kg base-dynamics example is a hypothetical small bus, not the selected Aries specification. A full 100 kg payload plus the base bus is already 225 kg before propellant and other mass outside those categories [calculation]. No launch price is inferred here. [Apex LEO Aries specification](https://www.apexspace.com/platforms/leo-aries).

For the first-wave cylinder assumption `length = 2 × diameter`, a 300 L plain cylindrical interior has diameter approximately 576 mm and length 1,152 mm [calculation: `V = πD³/2`]. That diameter exceeds the cited 550 mm envelope dimension for the proposed axis-aligned layout even before walls, domes and mounts. A 100 L cylinder gives approximately 399 mm diameter and 798 mm length under the same assumptions. This does not qualify a vessel or solve packing; it identifies why “100–300 L fits” needs a CAD and structural check. Keep enclosure volume a design variable. Do not assign a new vessel TRL 9 because much smaller sealed biological payloads have flown.

Pressure classification also needs correction. SpaceX's guide defines a pressure vessel by stored energy above 20,000 J **or** maximum expected operating pressure above 100 psi differential (6.9 bar differential). It explicitly includes large containers sealed at atmospheric pressure if their stored energy crosses that threshold. Thus “1 atm, no proof test” cannot be transferred automatically from a small container to a 100–300 L enclosure. Compute stored energy for the actual gas volume and thermal conditions, establish the applicable classification, and apply its verification requirements. Table 5-6 gives non-DOT pressure vessels 1.5× maximum expected operating pressure for proof and 2.0× for burst qualification. Section 5.5.4 requires a vacuum test if a sealed container cannot be pressurized in test. [SpaceX Rideshare Payload User's Guide, §§5.5.1–5.5.4 and 6.8](https://storage.googleapis.com/rideshare-static/Rideshare_Payload_Users_Guide.pdf).

NASA's thermal guidance distinguishes natural convection, driven by gravity and buoyancy, from forced convection. A sealed atmosphere can support forced cooling but does not create normal terrestrial buoyant circulation. Use motor-to-structure conductive paths where practical, a heat exchanger if circulation is needed, temperature cutoffs and fan-failure derating. Pressure-vessel wall heat transfer still needs an external rejection path. [NASA Passive Thermal Control Engineering Guidebook, §4.2.2](https://ntrs.nasa.gov/api/citations/20220006584/downloads/NASAPassiveThermalGuidebookv5%201Public.pdf).

Cooling and scientific validity interact: fans can accelerate free objects, disturb fine particles and change evaporation or interface motion. Separate electronics airflow from sealed science cells where possible, and record pressure, temperature and relevant flow conditions. This is an inference from the mission's experiment design, not a measured disturbance level.

### Component heritage and safe recovery

The Astrobee perching-arm design is a valuable reference for a small compliant arm in a pressurized orbital environment. Its paper describes a research-capable arm and prototype tests; it is not evidence that every servo in the same product family, every replacement production lot, or a full six-axis arm has the same flight qualification. [NASA Astrobee arm paper record](https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20170009546.pdf).

NASA NESC distinguishes total ionizing dose, non-ionizing dose and single-event effects, with sensitivity dependent on the part, environment, lifetime and application. The first-wave argument that an estimated dose lies below an approximate COTS threshold cannot close the single-event risk. Absence of a public servo test report also does not prove no such report exists. [NASA NESC Technical Bulletin 19-01-1](https://ntrs.nasa.gov/citations/20210024100).

Retain separate video compute and deterministic safety control. Before flight, verify safe outcomes for loss of video, stale commands, supervisor restart, encoder disagreement, servo bus failure, current-limit trips, a stalled actuator and power interruption during grasp [proposed gate]. A retract command is safe only if its path and held-object state are known safe; a timeout by itself does not make retraction safe. Passive containment, conservative limits and a controlled recovery procedure carry the cases in which the model is uncertain.

## 4. Novelty and scientific value: a stronger hypothesis than “orbit only”

### What prior art actually establishes

GITAI reports ground teleoperation of switch and cable tasks inside the ISS Bishop airlock in October 2021, in addition to autonomous activities. That supports the basic feasibility of an interior orbital manipulator commanded from Earth. It does not report the latency or establish the same uncrewed free-flyer configuration. [GITAI mission account](https://gitai.tech/2021/10/28/iss-tech-demo-ja/).

DLR's 2022 TumbleDock/ROAM account describes autonomous Astrobee approach and synchronized positioning relative to a tumbling target. It explicitly places physical capture by an installed robotic arm in a future mission. Do not cite that article as a measured orbital contact-capture success rate. [DLR TumbleDock/ROAM account](https://www.dlr.de/en/latest/news/2022/01/20220322_mini-robots-practise-grasping-space-debris).

This review did not obtain a primary quantitative Xiyuan-0 teleoperation report. The first-wave secondary reports can remain as reported developments, but “sub-second” must not be converted to a 20–30 ms measurement. Nor does a short prior-art table support “the only sub-100 ms space link ever flown” or “nothing in between has been measured in orbit.” The defensible statement is: **the reviewed sources do not establish a public learning-demonstration dataset from this exact ground-operated, internal-arm free-flyer configuration.** This is a search result with a date and scope, not proof of world-first status.

### The comparison class includes short microgravity and existing orbital data

ZARM states better than `10^-6 g` for the Bremen drop tower, with 4.7 s drop or 9.3 s catapult operation; the first-wave `10^-4 g` entry understates that facility's quality. NASA Glenn specifies 5.18 s and below `10^-5 g`, with autonomous onboard control during the drop. Duration is a constraint, but these facilities can measure isolated contact events and calibrate material behavior. [ZARM facility specification](https://www.zarm.uni-bremen.de/de/research/labs-and-test-facilities), [NASA Glenn facility specification](https://www.nasa.gov/centers-and-facilities/glenn/zero-gravity-research-facility/).

Suborbital vehicles are an additional non-orbital comparator. NASA describes two minutes or more of continuous microgravity with protected pressurized payloads or exposure to space. They require flight access and do not replace a sustained orbital program, but omitting them makes the case for a dedicated satellite too strong. The orbital advantage is repeated, long-duration operation and accumulation of diverse episodes; it is not exclusive access to every low-gravity event. [NASA suborbital research capabilities](https://science.nasa.gov/researchers/suborbital/).

Brisset et al. show that regolith impact responses vary materially with gravity and impact speed. This supports collecting targeted low-gravity contact data; it does not establish that orbital teleoperation is the only acquisition method or that those data improve a learned manipulation policy. [Brisset et al., 2018](https://arxiv.org/abs/1810.01459).

The ISS Hourglass study is especially useful existing evidence. It tested 0.063–2.0 g using a centrifuge, used media in cells below 20 Pa, and provided image and material data. Its flow broadly followed Beverloo's law with low-gravity deviations. Thus it supports both model usefulness and specific remaining model errors. It does not validate zero-gravity scooping and pouring in a 1-atm cell. Use its public data as a calibration comparator; match gas pressure, grain properties and imposed acceleration, or state the domain difference. [Ozaki et al., 2023, methods and data availability](https://www.nature.com/articles/s41526-023-00308-w), [JAXA experiment account](https://www.isas.jaxa.jp/en/topics/003486.html).

NASA's FBCE work likewise motivates microgravity fluid measurements through a changed balance of inertia, surface tension and body forces. That is evidence for a physics gap, not evidence that every liquid task will be slow, observable, resettable or valuable for imitation learning. Task geometry, wetting, containment and measured recovery time must be part of selection. [NASA microgravity heat-exchange research](https://science.nasa.gov/science-research/biological-physical-sciences/optimizing-heat-exchange-flow-in-microgravity/).

### Correct the simulator argument

MuJoCo's official modeling documentation supports perfectly elastic contact using direct stiffness/damping parameters. The relevant limitation is calibration and fidelity for the task's materials, geometry, contact history and solver settings. The absence of a direct restitution coefficient does not make collision simulation impossible. [MuJoCo modeling documentation, solver parameters and restitution](https://mujoco.readthedocs.io/en/stable/modeling.html#restitution).

The testbed's kinematic grasp and simplified success predicate can introduce either optimistic or pessimistic bias. Additional real contact could cause an object to escape, or contact compliance could help acquisition. Therefore the measured capture success is **neither an established lower bound nor an established upper bound on flight success**. It is a result for the implemented proxy. Likewise, a digital twin that shares dynamics or privileged state with the simulator has not proved usefulness under the model errors that motivate collecting orbital data.

## 5. Added research design: prove the value of the demonstrations

The most useful new hypothesis is: **for specified target tasks and a fixed training budget, measured microgravity demonstrations improve held-out physical performance beyond calibrated simulation and available non-orbital data.** This preserves the original purpose while making it falsifiable. Success-rate retention under latency is an upstream collection metric, not a substitute for that learning result.

| Gate | Comparison or evidence required | What would change the decision |
|---|---|---|
| Task physics | Fit rigid contact/material parameters using existing data or short microgravity experiments; validate on held-out conditions. Record residual errors. | If a calibrated model already meets task accuracy needs, prioritize another orbital phenomenon. |
| Demonstration content | Log observations, measured robot state, actual applied commands, contact/force information where available, base motion and environmental state. Keep command intent separate from action after onboard assistance. | If successful runs lack observable action/state alignment or usable supervision, improving latency will not repair dataset quality. |
| Task operations | Measure reset, containment recovery, camera occlusion, contamination and degraded-contact cases, including expected end of pass. | If a task cannot be repeatedly reset without crew or uncontrolled media, redesign its cell before scaling arm count. |
| Model dependence | Perturb contact, inertia, friction, perception and timing separately from the controller's model. | If a latency hider loses its advantage under realistic mismatch, restrict its scope or obtain better calibration. |
| Learning value | Compare equal-budget training on simulation alone, simulation plus available physical data, and simulation plus new microgravity data. Hold policy class, optimizer, data count and evaluation protocol fixed. | If the added data do not improve a preregistered task metric at acceptable uncertainty and cost, do not claim a physical-AI advantage. |
| Generalization | Split by object/material, task geometry, collection session and environmental condition; keep correlated frames and episodes together. Evaluate on physical targets when available. | A gain only on the collection apparatus supports a narrow domain claim, not broad physical-AI utility. |

These are proposed next-stage gates, not completed physical or learning experiments. No launch or human study is required to correct the present report. Existing literature, reproducible proxy experiments and explicitly separated uncertainties are sufficient to make the current program more useful for that decision.

Report four outcomes separately: technical collection success; accepted and synchronized dataset yield; incremental learning benefit; and cost per accepted demonstration. Keep an absolute minimum task success criterion alongside the relative 80% criterion [threshold to be set before a physical trial]. Otherwise a controller with poor zero-delay performance can pass a relative threshold while remaining unsuitable for operations.

## Implication for our design

Keep the direct-pass reference, configurable relay scenarios, local deterministic safety controller, isolated video compute, and data recorder. Qualify the relay as a service for the actual orbit; qualify the assembled arm and pressure/thermal design for the actual mission. Use existing orbital and short-duration microgravity measurements to calibrate the proxy before treating simulated latency gains as predictions. Prioritize one repeatable task with measurable model error and a controlled learning comparison before assigning four arms to unvalidated media tasks. This retains the first wave's useful architecture and experiments while making flight readiness and scientific benefit explicit, testable conditions.
