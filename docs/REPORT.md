# Ground teleoperation in LEO: second-wave research report

Senior review, 2026-09-13. Same question and constraints as the [original charter](PROGRAM.md).
The [first-wave report](REPORT_WAVE1.md), including the report edits present when this review
started, is preserved. Its exploratory results remain useful; the claims below supersede its
feasibility, acceptance and confirmation language.

## 1. Finding

**The program supports continued prototype development. It does not yet establish a flight-ready
mission or a learning benefit from orbital demonstrations.** Low-delay collection and several
latency-mitigation mechanisms work in the implemented synthetic tasks. Hardware readiness,
physical task fidelity, human performance and incremental training value need separate evidence.

This is a narrower and more actionable conclusion than a single “conditional yes.” The original
work correctly identified promising control mechanisms, built a substantial reproducible testbed,
and exposed important operational constraints. The second wave strengthens that work by checking
its source evidence, fixing observable experiment defects, accounting for failed attempts, revisiting
every hypothesis against its own rejection clauses, and running independent task seeds.

The main changes are:

- Outcomes now stop at the episode deadline. Previously, simulation continued during a one-second
  reporting interval and could turn a timed-out failure into a success.
- Blackouts count as failed attempts, including the first episode. The old parser omitted four
  `NO_LINK` failures from the nominal 3,400-episode Tier-2 record.
- Recordings now pair commands with the observations that caused them and preserve actual
  simulated state, object pose, timestamps and terminal outcomes.
- Collection throughput includes failed-attempt time. Conditional successful-attempt speed is a
  separate diagnostic. Missing profiles or safety counters no longer produce an acceptance PASS.
- Relay latency, spacecraft fit and scientific novelty are treated at the level their sources
  support. In particular, 48 ms is an emulation scenario, and 100 kg is an Aries rideshare payload
  allowance, not its bus mass.

Detailed evidence: [source review](research/second_wave_evidence.md),
[testbed review](experiments/second_wave_testbed.md),
[statistical review](experiments/second_wave_statistics.md), and
[hypothesis reassessment](hypotheses/second_wave_selection.md).

## 2. What the program is testing

The original goal is to collect physical-AI demonstrations through ground teleoperation of simple
arms inside a rideshare-class LEO spacecraft. The engineering objective is low end-to-end delay;
the scientific objective is useful measured behavior that available simulation and physical data
do not adequately capture. These are related, distinct hypotheses.

| Claim | Evidence that can test it | Current scope |
|---|---|---|
| A delayed operator can complete useful tasks | Controlled latency comparisons, absolute success, accepted data rate | Tested with synthetic operators on rigid-body proxies |
| The architecture can operate on orbit | Qualified hardware, closed resource budgets, contracted communications and fault recovery | Architecture study; not qualified |
| Orbital demonstrations add learning value | Equal-budget training comparisons and held-out physical evaluation | Research design supplied; no training or physical evaluation performed |

The no-human-study and no-launch constraints remain. Four concurrent operators and four to eight
arms remain the intended scale. A single repeatable science cell should establish value before
scaling. This is a development sequence within the same goal, not a change of application.

For a data campaign, report:

`accepted demonstrations / calendar hour = attempted demonstrations / active hour × success fraction × QA acceptance fraction × operational duty fraction`

This is bookkeeping, not an assumption that the factors are independent. Estimate the product
from the actual campaign schedule and joint outcomes. Include setup, reset, recovery, telemetry
quality, contact availability and operator time. A high contact-conditioned task success rate
alone does not establish campaign yield or policy-learning value.

## 3. Evidence and method

The second wave used seven Astra subagents across source research, statistics, testbed validity,
hypothesis review, report presentation, independent integration review and recording verification. The senior
lead integrates the findings and owns the new experiment protocol. The initial unmodified test
suite passed 78 tests; new regressions target defects that this suite did not detect.

The [fixed protocol](experiments/second_wave_plan.md) specifies 15 cells × 30 episodes on seeds
1000–1029, outside the first wave's 0–99 range. It was recorded before new outcomes were inspected.
Each cell runs in its own process, with at most four concurrent processes. All paired strategies
use the same task seed range, deadlines, profiles and synthetic reaction delay. This pairing controls
scenario generation; it does not make wall-clock socket scheduling identical across arms.

The fresh study includes baseline zero/relay controls on both tasks, a zero-delay Twin control,
Capture at 400 ms with baseline/Twin/Gain, Peg at 250 ms with baseline/DeadReckon, Peg at 400 ms with
baseline/Terminal/TerminalGround, and baseline Capture through forced one- and twelve-second outages.
It is a targeted robustness study, not a replacement for the complete first-wave sweep.

The [manifest](experiments/second_wave/manifest.json) records source-content hashes, dependency
versions, platform, command and the external MuJoCo Menagerie revision. The runner refuses to
resume a cell if parameters, seeds, completeness or executable-source hashes differ. It also
rejects a cell if executable sources change during its run. The external model revision remains
an explicit reproduction requirement; the dependency lock alone does not pin downloaded assets.

First-wave Tier 1 is exploratory. Tier 2 reused seeds 0–29 and extended to 99, so it is an expanded
selected-cell study rather than a wholly independent confirmation. Reanalysis of seeds 30–99
provides an exploration-disjoint scenario check under the old code. It cannot validate corrected
outcome handling. Historical and corrected outcomes are never pooled. A difference between waves does not isolate
the effect of a code fix: both implementation and sampled scenarios changed.

## 4. Corrected experiment results

All **15 cells and 450 episodes** completed on the frozen execution revision `0f68e78`.
No episodes were omitted, no cells failed, and no control-cycle gaps exceeded the 0.2 s exclusion
threshold. The largest observed gap was 0.169 s; that threshold does not eliminate smaller
scheduler effects. Results use seeds 1000–1029 and are separate from all first-wave data.
[Complete tables and vectors](experiments/second_wave/fresh/results.md).

### Baseline relay target

| Task | Zero success | Relay success | Zero → relay gross demos/h | Relay/zero gross rate | Success-ratio lower 95% bound |
|---|---:|---:|---:|---:|---:|
| Capture | 21/30 | 17/30 | 212.4 → 153.9 | 72.5% | 0.439 |
| Peg | 30/30 | 30/30 | 833.3 → 819.4 | 98.3% | 0.884 |

Capture's observed success retention is 81.0%, but its failure-inclusive throughput retention is
72.5%. It does not meet the 80% throughput target at the point estimate, and these data do not
establish 80% population success retention. The bootstrap interval for relay gross rate minus
0.8 × zero rate is −63.2 to +25.2 demos/h, so the sample also does not establish that the population
throughput ratio is below 80%. Peg supports performance retention within this proxy. Neither task
completes the original four-profile safety/acceptance evidence set; this study omitted direct-GS
and GEO by design. Capture also recorded 19 cage-contact events across its zero and relay controls.

Success-ratio lower bounds use conservative exact binomial bounds with at least 95% coverage for
each ratio, including the all-success boundary. They are not simultaneous guarantees across tasks.
[Acceptance calculations](experiments/second_wave/statistics.json).

### Mechanism comparisons

Each row has 30 paired scenarios. Gross rate includes all failed-attempt time. The interval is a
pointwise paired bootstrap interval; Holm p adjusts the six success comparisons, including the
zero control. It does not adjust the throughput intervals.

| Task / nominal RTT | Arm | Baseline → arm successes | Gross demos/h difference [95% interval] | Holm success p |
|---|---|---:|---:|---:|
| Capture / zero | Twin | 21 → 24 | +72.7 [+0.1, +161.9] | 0.75 |
| Capture / 400 ms | Twin | 13 → 21 | +106.3 [+38.1, +187.5] | 0.0645 |
| Capture / 400 ms | Gain | 13 → 0 | −96.5 [−148.6, −54.1] | 0.000977 |
| Peg / 250 ms | DeadReckon | 0 → 27 | +397.7 [+242.6, +629.4] | 7.45e−8 |
| Peg / 400 ms | Terminal | 0 → 30 | +634.9 [+632.7, +637.2] | 1.12e−8 |
| Peg / 400 ms | TerminalGround | 0 → 0 | 0.0 [0.0, 0.0] | 1 |

The large insertion gains remain under corrected outcome handling and new seeds. Gain remains
harmful for this moving-target Capture task. Twin's Capture result is promising: gross rate rises
from 96.5 to 202.8 demos/h, but its success contrast does not cross .05 after Holm adjustment.
After subtracting the zero-cell success gain, Twin's 400 ms gain is +16.7 percentage points
[−3.3, +36.7]. Its conditional throughput ratio of ratios is 1.105 [0.941, 1.281]. Neither establishes
the original ≥10% latency-specific gain. [Paired results](experiments/second_wave/fresh/paired.md).

A `[0,0]` empirical interval at two all-failure cells is not population equivalence. Likewise,
Terminal's narrow interval reflects a highly repeatable synthetic task, not physical precision.
The aggregate duration vectors come from stdout rounded to 0.1 s; higher-resolution endpoints
remain in recording metadata. Conditional speed ratios with no successful attempts are undefined.
The targeted sweep does not estimate a new latency knee or establish the whole hypothesis clauses.

### Outages and actual motion

| Forced Capture outage | Successes | Episodes with observed hold | Episodes reaching command age >10 s in hold | Cage-contact events |
|---|---:|---:|---:|---:|
| 1 s | 18/30 | 29/30 | 0/30 | 8 |
| 12 s | 1/30 | 29/30 | 29/30 | 36 |

One episode in each condition finished before the outage and supplied no hold exposure. The
12-second condition uses a 30 s deadline; other Capture conditions use 20 s. These are fault-path
challenges, not an isolated estimate of outage duration's effect at a common deadline.

The independent recording audit checked **354,402 ground frames and 5,127,213 satellite cycles**,
plus all 450 terminal records. Sequence alignment, causal source times, finite recorded state,
terminal-outcome consistency and target-distance checks passed. There were zero setpoint-speed violations above
the 2 rad/s limit with its 5% numerical tolerance, and zero setpoint changes during hold before
retraction. These results verify the recorded command envelope.

**Actual simulated joint velocity reached 6.584 rad/s**: the Elbow in the 12-second outage condition,
seed 1024, at simulation time 19.914 s, after hold had ended. Actual motion also occurred during
hold; the audit records its duration and separates command age/retraction exposure. A held setpoint
does not imply a stationary mechanism. These are sampled simulation measurements, and unrecorded
integration steps could contain higher peaks. They do not measure hardware velocity or flight risk.
Cage contacts and this command/motion distinction prevent a broad zero-unsafe-motion conclusion.
[Frame-level verification record](experiments/second_wave/record_verification.json).

The audit does not independently replay the full insertion/contact predicate. A separate endpoint
review found six of 117 successful Peg endpoints up to 0.088 mm above the specified insertion
depth: the proxy completion test read tip height before its final kinematic pose update. The 450
results retain that execution version; this is a remaining boundary limitation, not evidence that
the large strategy effects reverse.

The audit does not reconstruct every accepted packet or interpolator input. Forced-window overlap
uses the first recorded controller cycle as a link-start proxy; direct drop-event timestamps were
not recorded. Actual hold entries and command ages provide the reported exposure counts.


### Supplemental chain regression

After the primary source freeze, revision `550e190` corrected chain completion and reset counters,
archived replaced cell outputs, and made recorder retries replace the matching metadata suffix.
All **four chains / 20 episodes** completed release under the separate fixed regression protocol.
Seeds 2000 and 3000 each started one five-episode chain per reset mode. Free-reset chains used
36.8 and 35.2 active seconds; teleoperated-reset chains used 45.4 and 43.0 seconds. These are
chain-level descriptive observations, not 20 independent replications or a confirmed H20 gain.
The unit regression separately exercises a capture that never completes release and must fail.
[Chain results](experiments/second_wave/chain/results.md) and
[execution manifest](experiments/second_wave/chain_manifest.json).

### Final endpoint regression

Revision `be7dd45` fixes Peg completion to read tip height and fixture contact after the kinematic
pose update, while retaining the existing jam/regrasp behavior. Three deterministic cases cover
a withdrawn tip, a newly inserted tip and new fixture contact. A separate **30-episode** check on
seeds 4000–4009 completed 10/10 each for baseline/zero, baseline/relay and Terminal/400 ms.
Reconstruction from saved final joint/object state verified lateral position, insertion depth and
absence of fixture contact for all 30 successful endpoints. This checks the corrected boundary;
it does not retroactively repair or pool the primary observations, or estimate another paired effect.
[Endpoint verification](experiments/second_wave/peg_verification.json),
[manifest](experiments/second_wave/peg_manifest.json) and
[results](experiments/second_wave/peg_endpoint/results.md).

## 5. What changes in the historical interpretation

These observations concern the archived implementation. They do not replace the fresh results.

**Throughput.** The first-wave headline used `3600 / mean(successful attempt durations)`. That
quantity can remain high even when most attempts fail. In Tier 2, baseline Capture at 400 ms has
350.9 conditional demos/hour but 100.8 successful demos per attempted hour; baseline Peg at 400 ms
has 302.5 conditional demos/hour but only 1.2 successful demos per attempted hour. Both numbers are
correct for their definitions. Only the latter charges failures. See the
[archived tables](experiments/tier2/results.md) and the statistical reanalysis.

**Acceptance.** The original target is at least 80% of zero-delay success and throughput, with no
unsafe motion. A sample ratio above 0.8 is not evidence that the population ratio exceeds 0.8 at a
specified confidence. Some arms also lack the required reference/safety profiles. The updated
analysis distinguishes the observed ratios, uncertainty and incomplete evidence.

**Safety.** The first-wave implementation removed cage contact from the acceptance sum because
contacts occurred even at zero delay. That is a change from the original criterion. It does not
prove cage contact is harmless or unrelated to delay. Command-envelope counts remain useful
regression diagnostics; they do not establish collision safety, contact-force limits, safe retraction
with an object, or a zero physical-risk rate. Report actual outage exposure: episodes that end
before the forced outage cannot be counted as completed blackout challenges.

**Knees and multiple comparisons.** A seven-point curve supports a crossing bracket and an
exploratory interpolation. It does not justify a precise, universal 97 ms or 787 ms threshold.
Tasks, deadlines, synthetic reaction time, contact rules and zero-delay success all affect the
crossing. The reanalysis reports brackets, uncertainty and right-censoring, and uses Holm adjustment
for the selected family of paired success comparisons. A non-significant zero-delay contrast is
not an equivalence test.

**Missing failures and stalls.** Four seed-69 `NO_LINK` failures are absent from the historical
Tier-2 summaries. They are recoverable from the preserved console records and are examined in
sensitivity analysis. Scheduler-stalled episodes are reported; if excluded, their seed is removed
from both sides of the paired comparison. These issues are disclosed before interpreting effect
sizes rather than hidden in an “n=100” label.

## 6. Revised hypothesis conclusions

All 20 hypotheses are reassessed in the
[second-wave selection record](hypotheses/second_wave_selection.md), with original rejection
criteria, supporting evidence, unmet clauses and decisive next tests.

| Mechanism | Defensible interpretation |
|---|---|
| H10: ground Twin | A promising delayed-approach aid in this simulator. Establish a benefit beyond its zero-delay controller effect and test model mismatch before deployment. |
| H11: local Terminal | A promising local-assistance package for the insertion proxy. The ground counterpart changes rate, state age and sensing quality; P−Pg is not an isolated estimate of compute location. Original acceptance clauses and estimator-error tests remain relevant. |
| H12: DeadReckon | Supervisor-side prediction is promising for the delayed insertion task. Horizon and zero-lead behavior need matched comparisons; a linear lead calculation does not prove equivalence on nonlinear command streams. |
| H14: Gain | Slowing the operator can help static-target insertion and harm a moving-target chase. It is not justified as a universal default. |
| H20: chained release | Removing reset work can improve gross yield in the modeled task. Historical chained episodes share state, tether damping acts while slack, and post-deadline evolution changed; the original full claim is not confirmed by independent fresh chain runs here. |

Merged transport and workflow ideas remain useful baseline engineering where their mechanism is
already present. A null result at the nominal relay scenario does not prove redundancy, scheduling,
video prioritization or multi-link diversity never help. Reopen a deferred idea when its assumed
bottleneck is measured in the intended operating regime, not merely to increase the hypothesis count.

## 7. Architecture ready for the next development stage

Use a direct-pass RF reference with local deterministic hold and recovery. Retain Starlink and
Kepler as conditional continuous-relay options. Select a relay after measuring or obtaining a
mission-specific service allocation: client orbit and attitude, coverage, optical acquisition,
directional application latency, burst loss, sustained goodput and terminal resources. The published
optical line rate is not the ground application's allocated bandwidth.

The primary-source review found commercial agreements and Kepler's August 2026 service announcement,
but no mission-specific latency/continuity evidence that supports the original numerical ranking.
A symmetric extra 4,000 km optical hop contributes about 26.7 ms RTT by propagation alone; adding
an unexplained 8 ms to a consumer statistic does not construct a validated spacecraft route.
[Source review, §2](research/second_wave_evidence.md#2-links-separate-propagation-emulation-and-a-purchasable-service).

Keep the original simple ground/satellite division: one command authority per arm, timestamped
setpoints, bounded local playout, an independent safety supervisor, and video compute outside the
safety path. Recovery must remain local when both communications paths fail. A ten-second timeout
does not itself prove a retract path is safe. A low-rate backup is a recovery/status channel, not
a guarantee of timely emergency stopping.

The four-site TLE study gives **21.4% geometric visibility at a 5° mask and 14.9% at 10°** for its
specified orbit and week. The 46-site union gives 61.1% and 47.6%. These are reproducible geometric
opportunities, not booked service or measured operator duty. Do not multiply them by instantaneous
successful-attempt speed and call the result a demonstrated mission yield.
[Geometry appendix](experiments/appendix_geometry.md).

### Mission resource corrections

Apex specifies a **125 kg dry base bus**, a **100 kg rideshare payload allowance**, and a
865 × 1170 × 550 mm payload envelope. A full bus plus that payload is at least 225 kg before
propellant and other excluded mass categories. The first-wave 100 kg bus and associated launch
sketch are not a closed Aries configuration. No replacement launch quote or total mission price
was obtained. [Apex specification](https://www.apexspace.com/platforms/leo-aries).

Under the original `length = 2 × diameter` cylinder assumption, a 300 L interior requires about
576 mm diameter and 1,152 mm length; it exceeds the 550 mm axis-aligned envelope before walls,
domes and mounts. A 100 L plain cylinder is approximately 399 × 798 mm. These calculations identify
a packing constraint; they are not a pressure-vessel design. SpaceX's pressure-system criteria
also depend on stored energy, so a large one-atmosphere enclosure cannot be dismissed as requiring
no pressure qualification. [Source review, §3](research/second_wave_evidence.md#3-hardware-keep-the-proposed-architecture-qualify-the-assembly).

Pressure does not restore terrestrial buoyancy cooling in microgravity. Provide conductive paths
or controlled forced circulation and an external heat-rejection path. Cooling flows can disturb
the scientific experiment, so isolate electronics airflow from science media and log environmental
conditions. Qualify mission- and part-specific radiation effects, including single-event failures,
not only a total-dose estimate. Close peak and orbit-average power, eclipse energy, heat rejection,
terminal pointing and arm/base momentum budgets before claiming the assembly is ready.

## 8. Data and physical validity

The implemented robot is a fixed-base SO-100: five arm joints plus a jaw; the protocol has a
seventh spare slot. It is not the charter's generic six-DoF arm and does not model free-flying bus
recoil, attitude control or multi-arm mechanical coupling. The Capture grasp is kinematic after a
proximity/jaw rule. Peg orientation is constrained. Neither proxy establishes frictional grasp
quality, force-sensitive insertion, granular flow, fluid handling or deformable manipulation.

MuJoCo supports elastic contact through its solver settings. The relevant research question is
whether calibrated contact and material models predict the target task accurately, not whether
the simulator has a direct restitution coefficient. The proxy's flight-performance bias can have
either sign; “lower bound” and “upper bound” are not justified without comparison.
[Official MuJoCo restitution documentation](https://mujoco.readthedocs.io/en/stable/modeling.html#restitution).

The schema-2 recorder fixes command sequence alignment and preserves causal observation provenance,
actual simulated joint/object state, command timing and final outcome. Predicted observations and
onboard assistance remain identifiable. This enables later alignment and physics checks that the
original applied-setpoint-only sidecar could not support. The sidecar command ID is the newest
received command; its legacy `t_applied_ns` name denotes the receipt/control cycle. Interpolation
and assistance mean it does not identify a single command that alone caused the applied setpoint. It does not create calibrated camera,
force or human demonstrations.

**The output is research NPZ, not a LeRobot-compatible dataset.** Similar column names and metadata
do not make NPZ loadable by LeRobot. A training deliverable must export to a pinned supported format,
resample with documented timing rules, preserve raw monotonic timestamps and intervention labels,
and pass an actual loader/episode-boundary check. No such compatibility or learned-policy result
is claimed in this wave.

## 9. Added scientific-value study

The strongest remaining hypothesis is: **with the same training and evaluation budget, measured
microgravity demonstrations improve held-out physical task performance beyond calibrated simulation
and available physical data.** Sustained repeatability is the potential orbital advantage. Drop
towers, suborbital flights and published orbital datasets are valid comparators.

Use this staged design before a mission commitment:

1. Select one contained, resettable task with measurable model error and a specified target policy.
   Calibrate against available physical measurements; test held-out conditions before deciding
   additional orbital data are necessary.
2. Log observed and applied actions separately, measured robot/object state, base motion, relevant
   force/contact data, and pressure/temperature/flow conditions. Define QA acceptance independently
   of task success, then measure accepted demonstrations per attempted and booked hour.
3. Compare fixed-size training sets: simulation alone; simulation plus available physical data;
   and the same total data/training budget with additional microgravity demonstrations. Hold the
   policy class, optimizer and evaluation budget fixed. Include both equal-count and equal-cost
   comparisons when making a mission decision.
4. Split by object/material, geometry and collection session. Keep correlated frames and chained
   episodes together. Evaluate on held-out physical tasks when access exists, with uncertainty
   across independent training and evaluation runs.
5. Predeclare a practically meaningful improvement and acceptable cost per accepted demonstration.
   If calibrated simulation already meets that target or added data do not improve it, change the
   chosen phenomenon rather than asserting orbital uniqueness.

These are proposed physical/learning experiments. They were not performed by this autonomous
simulation review. They make the original scientific objective falsifiable and connect control
performance to the data product it is meant to enable.

## 10. Reproduction and readiness

The committed result vectors support analysis without the large raw recordings:

```sh
uv sync --frozen
uv run pytest -q
uv run python docs/experiments/second_wave/analyze.py \
  --fresh-results docs/experiments/second_wave/fresh/results.json
uv run python docs/experiments/second_wave/verify_records.py --self-check
```

To rerun the primary experiment using its exact execution source, use an isolated checkout of
`0f68e78`. The current checkout includes later chain/metadata and Peg-predicate fixes and is a distinct execution
version. The original protocol and source snapshot remain available in history:

```sh
git worktree add --detach ../teleoperation-wave2-reproduction 0f68e78
cd ../teleoperation-wave2-reproduction
uv sync --frozen
ROBOT_DESCRIPTION_COMMIT=feadf76d42f8a2162426f7d226a3b539556b3bf5 \
  uv run python docs/experiments/second_wave/run.py
```

`robot-descriptions` supports that commit environment variable; the first use can download the
pinned model to its separate cache. Record the platform and compare source/model hashes with the
manifest. Real-time scheduling means byte-identical timing is not expected. Return to the current
checkout to aggregate and audit those recordings:

```sh
uv run python experiments/aggregate.py \
  --raw ../teleoperation-wave2-reproduction/docs/experiments/raw_second_wave \
  --out /tmp/teleoperation-wave2-reproduced
uv run python docs/experiments/second_wave/verify_records.py \
  ../teleoperation-wave2-reproduction/docs/experiments/raw_second_wave \
  --out /tmp/teleoperation-wave2-record-verification.json
```

The supplemental chain regression ran on source `550e190`, before the final Peg-only correction,
using `uv run python docs/experiments/second_wave/chain_check.py`. Use an isolated checkout of that
revision and the same pinned model to reproduce its exact source, then use the current
`verify_chains.py RAW_DIRECTORY` to audit it. The final endpoint regression runs from the current
source with `uv run python docs/experiments/second_wave/peg_check.py`; `--verify-only` repeats its
endpoint audit without rerunning episodes. Both studies test corrections, not the original H20 or
latency effect size. Detailed commands and revision boundaries are in the verification record. Raw trajectory files remain local/ignored; the committed
aggregate vectors, recovered historical outage records, manifests and verification summaries make
the report's analysis inspectable in a clean clone. Recreate raw trajectories for an independent
frame-level audit. Final test and experiment counts are recorded in the
[second-wave verification record](experiments/second_wave_verification.md).

### Decision gates after this wave

| Gate | Status | Evidence still needed |
|---|---|---|
| Executable control comparison | Research prototype | Validate physical/perceptual mismatch and human transfer; retain independent uncertainty. |
| Original full safety target | Not established | Cage/contact severity, actual motion limits, fault recovery, safe held-object retraction and complete scenario coverage. |
| Flight assembly and communications | Not qualified | Closed budgets, environmental/pressure qualification and an allocated client-orbit service. |
| Traceable demonstration recording | Research format | Pinned training-format export, actual loader check and application-specific QA. |
| Incremental physical-AI learning value | Untested | Equal-budget controls and held-out physical policy evaluation. |

## Implication for our design

Retain the simple testbed, paired comparisons and promising prediction/local-assistance mechanisms.
Use corrected outcomes and complete attempt costs for claims. Treat spacecraft qualification,
physical fidelity and learning value as separate gates. The program is a stronger research
prototype and a clearer basis for deciding what to build and measure next; it is not a flight
qualification or proof that orbital demonstrations improve a learned policy.
