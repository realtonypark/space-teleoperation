# Second-wave synthesis: decision record

Research cut-off: 2026-09-13. This replaces the first-wave decision record, preserved in
[SYNTHESIS_WAVE1.md](SYNTHESIS_WAVE1.md). The original [program](../PROGRAM.md) question is unchanged.
Read the [current report](../REPORT.md) for measured second-wave outcomes and the
[primary-source review](second_wave_evidence.md) for citations and claim-level corrections.

## 1. Decision

Proceed with a ground prototype and a qualified mission trade study. The current evidence does
not establish a flight-ready system or a learning benefit from orbital demonstrations. Three
claims require separate evidence: controllability through delay, viable spacecraft operation,
and useful training data that improve physical performance over available alternatives.

The first wave provides strong exploratory evidence for the first claim on two synthetic tasks.
The corrected 450-attempt study retains large insertion gains and a promising Capture Twin effect.
Baseline relay gross-rate retention is 72.5% for Capture and 98.3% for Peg. Actual simulated joint
velocity reaches 6.584 rad/s despite compliant setpoints. Hardware readiness, full safety and
incremental learning value remain separate evidence gates.

## 2. Architecture choices

| Element | Second-wave choice | Why and remaining condition |
|---|---|---|
| Initial link reference | Direct RF passes, with an explicit end-of-pass hold/recovery procedure | Flown teleoperation precedent exists; geometric visibility does not guarantee booked contacts or usable video service. |
| Continuous relay | Retain Starlink and Kepler as conditional candidates | Obtain orbit-specific coverage, goodput, directional delay and terminal mass/power before selecting. The 48 ms emulator profile is a scenario. |
| Ground control | One writer per arm; 50 Hz setpoints; synthetic operator for present experiments | Human behavior, display pipeline and session authority remain architecture work, not validated testbed capabilities. |
| Local safety | Independent deterministic supervisor, command freshness, bounds, controlled hold and recovery | Timeout retraction requires a safe path and grasp-state assessment; telemetry-only safety counts do not qualify hardware. |
| Ground prediction | Candidate for delayed moving-target approach | Require a zero-delay control and model/perception mismatch trials before interpreting it as a latency-specific benefit. |
| Local assistance | Explicit optional autonomy branch | Present comparison bundles state quality, age and update rate. Test equal-rate ablations and estimator errors before assigning the effect to compute location. |
| Payload | Start with one repeatable, contained science task; four-operator architecture remains the scale target | Resetability, usable-data yield and scientific effect should justify scaling to four or eight arms. |
| Bus and enclosure | ESPA-class candidate; configuration open | Aries base dry bus is 125 kg, distinct from 100 kg rideshare payload allowance. Close mass, volume, thermal and pressure requirements before claiming fit. |
| Recorder | Versioned research NPZ, causal observation/command and actual-state sidecar | It is not a loadable LeRobot dataset. Export and validate with a pinned loader before a training claim. |

The primary-source evidence supports these changes without requiring the original testbed to be
replaced. Preserve its simple sockets, MuJoCo proxies and strategy seams.

## 3. Acceptance and evidence rules

Keep the original target of at least 80% zero-delay success and useful demonstration throughput.
Report absolute success too. A weak zero-delay controller must not become operationally acceptable
merely because a ratio is high.

Use `3600 * successes / sum(all attempt durations)` as the collection-rate readout. Label
`3600 / mean(successful durations)` as conditional completion speed. Neither includes every
mission overhead. Actual mission yield also includes reset/recovery, setup, quality rejection,
contact booking, downlink availability and human availability.

A sample ratio above 0.8 is a point-estimate result. A population-retention claim needs an interval
or a predeclared noninferiority test. Missing control or safety profiles yield incomplete evidence,
not PASS. Keep exploratory sweeps separate from independent confirmation and disclose reused
seeds, multiple comparisons, dropped failures and scheduler stalls.

The original safety target included cage contacts. The first-wave narrow counter excludes them;
that exclusion changes the acceptance rule. Report cage contact and command-envelope diagnostics
separately. Zero observed diagnostic events cannot establish zero physical risk, nor show that
contact was unrelated to latency. Do not claim the original full safety target is met when cage
contacts remain or tests are absent.

## 4. Scientific task selection

The advantage to test is sustained, repeatable microgravity data under controlled conditions.
Drop towers, suborbital flights and existing orbital datasets are real comparison sources.
Contact calibration may eliminate some supposed simulation gaps. Conversely, long-duration
fluid, granular and deformable phenomena may retain substantial model error.

Select a task by measured model error, observability, containment, reset time and relevance to a
target learned policy. Record gas conditions and cooling disturbances; a 1-atm granular cell does
not reproduce vacuum regolith. A kinematic grasp and upright peg are useful control proxies with
unknown bias relative to flight. The fixed-base SO-100 model does not simulate spacecraft recoil
or attitude-control coupling.

## 5. Completed and remaining evidence gates

1. Completed: corrected outcome timing, complete failure accounting and data provenance, plus
   all 450 attempts in the [fixed fresh-seed protocol](../experiments/second_wave_plan.md).
   The [recording audit](../experiments/second_wave/record_verification.json) passed all episodes;
   the report retains model and sampling limits.
2. Test model and perception mismatch, matched-rate assistance, camera delay/content, and all
   original rejection clauses before accepting a strategy for deployment.
3. Close a mission-specific mass/power/volume/link/pressure/thermal design; qualify parts and
   fault recovery. Supplier heritage alone does not qualify the assembly.
4. Demonstrate synchronized, accepted data yield and pinned LeRobot-loader compatibility.
5. Compare equal-budget policy training on simulation, available physical data and additional
   microgravity data, with held-out physical evaluation. Only this tests incremental learning value.

## Implication for our design

Retain the useful first-wave prototype and its strongest candidate mechanisms. Replace premature
flight and learning conclusions with explicit evidence gates, correct the experiment boundary and
recording defects, and make failed attempts part of throughput. This makes the same research
question testable without confusing simulation success, mission feasibility and scientific value.
