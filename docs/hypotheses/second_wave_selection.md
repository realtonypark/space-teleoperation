# Second-wave hypothesis review and revised selection

Review date: 2026-09-13. Scope: all [H01–H20](selection.md), their original rejection clauses,
the selection amendments, the [charter](../PROGRAM.md), historical experimental artifacts and
the [second-wave evidence review](../research/second_wave_evidence.md),
[testbed audit](../experiments/second_wave_testbed.md) and
[statistical review](../experiments/second_wave_statistics.md). This document does not
report corrected-run outcomes. The [second-wave protocol](../experiments/second_wave_plan.md)
defines those runs separately. First-wave numbers below describe the old implementation and
remain useful for selecting what to test; they do not validate a changed implementation.

**Keep H10, H11 and H12 as the leading control experiments. Keep H20 as an operations experiment,
with independent chains as the unit of replication. Keep H14 as a useful task-dependent counterexample.**
The first wave found large differences between implemented controllers. It did not confirm all
the original hypotheses, qualify a flight architecture, or demonstrate incremental learning value.
The next research decision is which measurements can connect those controller differences to
accepted, useful demonstrations from repeatable microgravity tasks.

## How this review assigns status

An original hypothesis and a later discovery are separate claims. A success improvement on
`peg` can justify another experiment even when a hypothesis required a capture throughput gain
on `leo_relay`. A missing diagnostic is **untested**, not a pass. An observed point estimate below
a rejection threshold is recorded as a **gate miss**; it is not proof of a universal zero effect.
The original files sometimes set a stronger headline than their rejection gate: H10 predicts
15% throughput but gates at 10%; H20 predicts 40% but gates at 10%. Both levels remain visible.

The seven-point sweep, 170 ms reaction model and amended tasks in [selection.md](selection.md)
are protocol changes from the original files, which commonly specified 250 ms reaction delay
and different capture geometry. The historical report describes a final 25 mm capture envelope,
after earlier 50 mm and 20 mm versions. Estimates from those earlier models are not evidence
for the final task. Block E is a reaction-delay sensitivity experiment; it does not recreate
every original task and gate.

Use three distinct quantities:

- **Conditional completion speed:** `3600 / mean(duration of successful attempts)`, the original
  `demos_per_hour`. It omits the time spent failing and compares different sets of successes.
- **Collection rate:** `3600 * successes / sum(duration of every attempt)`. Charge reset and
  recovery where they are executed. This is the primary corrected-run rate.
- **Accepted data yield:** synchronized demonstrations that meet task and dataset requirements
  per booked hour or calendar day. This additionally charges operations and data rejection.

Improving collection rate can be valuable when conditional speed declines. That observation
does not retrospectively pass a hypothesis whose original gate required conditional speed.
Ratios with zero baseline successes are undefined; use an absolute collection-rate difference.
The narrow historical peg throughput intervals at 400 ms discarded roughly 37% of bootstrap
resamples because the baseline had only one success. They are not reliable evidence of a
precisely measured multiplicative speed gain. See [historical paired results](../experiments/tier2/paired.md)
and [second-wave reanalysis](../experiments/second_wave/statistics.json).

## Traceability across all twenty hypotheses

The next tests below are proposed decision tests, not completed work or an instruction to expand
the fixed corrected-run matrix. Small transport and UI effects should be reopened only when
the service, task or observations expose their mechanism.

| ID and original claim | Actual evidence and original-gate coverage | Revised status | Exact next decisive test |
|---|---|---|---|
| [H01](H01.md): dense direct-pass network and three teams yield at least 2.5× demonstrations per wall-hour with low in-contact RTT. | [Geometry appendix](../experiments/appendix_geometry.md): 46-site union gives 61.1% visibility at 5° and 47.6% at 10°, versus 21.4% and 14.9% for four sites. This is uncapped visibility, not the original backhaul-constrained three-team duty. No 95 ms task gate, handover fold or safe end-of-pass trial was completed. | **Geometry supported conditionally; operational yield untested.** Preserve the direct-pass alternative and the original deferment. | Restrict sites to reservable compatible uplinks, apply measured backhaul and acquisition time, and run the original 30/80/95/130 ms task comparisons. Evaluate duty ≥45% under the 150 ms backhaul cap, success at 95 ms ≥80% of zero and ≥90% of 30 ms, folded yield ≥2× four-site and ≥50% relay. Test scheduled stow and report operator-hours separately. |
| [H02](H02.md): simultaneous dual-terminal first-arrival delivery lowers RTT p95 by >10% and removes most outage holds. | No dual-path experiment ran. [Outage appendix](../experiments/outage_sweep.md) changed a single path's outage rate. Independent emulator draws would measure assumed diversity; consumer reconfiguration synchrony does not establish complete outage correlation on a spacecraft. | **Deferred, untested.** No claim of redundancy failure or demonstrated gain. | Compare one path, independent paths, and paths with shared outages and correlated jitter. Require ≥10% p95 reduction and ≥50% reduction in exposed hold time without degraded task metrics, the original rejection gates. Then repeat with measured paired spacecraft-client traces before choosing two active terminals. |
| [H03](H03.md): no useful hypothesis for relay control plus direct-pass video. | This was an analytical scope rejection. Video is a byte budget; neither visual quality nor separate-path video loss was tested. A 25 Gbps optical line rate does not establish available application bandwidth. The stale-observation command stop is a baseline obligation. | **Reasonable deferment for this proxy; universal bandwidth/null claim unsupported.** | Reopen only if a measured service allocation cannot carry the required video. Hold image quality and offered load fixed, vary video path while leaving control fixed, and measure accepted yield and commands issued after video becomes stale. Otherwise implement no split-path feature. |
| [H04](H04.md): no >10% primary gain from independent links because outages rarely affect short episodes. | The single-link rate sweep at 1.7/5/12 outages per hour recorded only 0/0/1 holds. That is sparse exposure, not a diversity experiment or an equivalence result. It cannot establish that outages are non-binding for a longer campaign. | **Defer on current evidence; outage ceiling is scenario-dependent.** | Use continuous campaign time and identical scheduled outage traces with known overlap across links. Record actual exposure and recovery time; test whether diversity changes collection yield by 10%. Estimate natural rates separately from deliberately enriched fault trials. |
| [H05](H05.md): command repetition/FEC offers no >10% primary benefit. | The absolute-setpoint argument is useful engineering reasoning. Sequence rejection was adopted in the baseline; duplicate-send and FEC were not tested head to head. The quoted longest-gap sample does not prove a gap can never exceed the hold threshold. | **Baseline sequencing adopted; repetition benefit untested and low priority.** | If measured losses justify it, replay the same trace using single-send, repeat-send and one-packet history, with equal usable bandwidth. Compare applied-command age, holds and collection rate, including saturation. Retain the baseline without claiming a measured FEC null. |
| [H06](H06.md): windowed setpoints per packet cannot improve the main metrics. | No dedicated packet-history/window test. Early millimetre calculations used the old capture envelope. Applied-setpoint logging now permits a trajectory check, removing one original measurement objection. | **Merged transport investigation, not empirical rejection.** | In the H05 trace test, add one previous setpoint and preserve each command's timestamp and expiry. Measure delivered trajectory error before the hold deadline; never let future windows bypass stale-command limits. Reopen only for a measured loss/age problem. |
| [H07](H07.md): 100 Hz priority state separated from video reduces felt delay and protects saturated-task success. | No dedicated split-flow experiment ran. The synthetic operator consumes structured state, so a priority-state win would not establish a human video benefit. The controlled-queue mechanism itself remains testable. | **Deferred engineering option; original “REJECTED” overstates the experiment record.** | Compare 30 Hz bundled versus 100 Hz separate state at nominal load and the original 0.9× video-rate cap. Check ≥10 ms felt-delay reduction and ≥1.3× saturated success, then report actual video age/quality. Distinguish priority at an owned queue from provider treatment. |
| [H08](H08.md): sender-timestamp adaptive playout removes time distortion and improves capture throughput. | Sequence-keying removes stale command reversal, but does not make arrival-time interpolation identical to sender-time playout. No adaptive-depth/reorder sweep ran. H12's regression filter at L=0 is also not generally the baseline. | **Baseline ordering adopted; residual timestamp/jitter hypothesis untested.** | Compare current baseline, fixed sender-time playout and adaptive playout on identical nonlinear commands and the original 2/15/30/60 ms jitter sweep, with reorder on/off. Measure applied timing, ≥50% jerk reduction, direct-pass rate loss ≤5%, and safe hold/resume. Add separate-clock offset/drift before a hardware claim. |
| [H09](H09.md): newest-setpoint phantom plus object prediction improves delayed capture. | Its newest-setpoint proposal removes modeled human reaction from the arm channel. H10 instead uses commands from at least `tau_h` ago. The original object-off ablation was not run; a separate peg task does not estimate the object contribution to capture. | **Merge into corrected H10; original implementation unsuitable for causal inference.** | Run the four prediction conditions in the H10 test below with the reaction-history constraint enforced. Preserve H09's ≥10-point success and ≥10% throughput checks at 500 ms. Do not reject a useful object contribution merely because it contradicts an arm-only mechanism story. |
| [H10](H10.md): twin view raises throughput ≥15% at ≥500 ms without any success, safety or smoothness loss. | [Tier 2](../experiments/tier2/paired.md): capture at 400 ms 72/100 versus 44/100; original geo paired subset 60/99 versus 22/99. But the Tier 1 500 ms conditional-rate ratio was 0.98, below its 1.10 gate; some success point differences were negative; smoothness and safety clauses were not all closed. Zero capture 76/100 versus 69/100 is not equivalence. | **Strong delayed-task package effect; original joint claim not confirmed.** Retain as first ground-control priority. | Corrected baseline/twin runs at zero and 400 ms test repeatability. Decisive mechanism follow-up: neither prediction, arm only, object only, both, using matched seeds at zero, 500 ms and geo; preserve `tau_h`, perturb servo/object dynamics, and test the delay-by-strategy interaction. Apply every original rate, no-harm, hold and smoothness gate. |
| [H11](H11.md): a short onboard terminal primitive improves relay capture by ≥15 points and ≥15% throughput with little robot-executed data. | Tier 2 relay capture: 68/100 versus 65/100, conditional rate 0.97×. At 500 ms: 50/100 versus 33/100, rate 1.01×. Amended relay peg: 100/100 versus 97/100, rate 0.99×. All miss the original 1.10 throughput gate. Peg at 400 ms is a large discovery: 100/100 versus 1/100. Noise, successful-episode assist and several original safety/smoothness gates remain incomplete. | **Original relay claim fails observed gates; delayed-peg assistance package is promising.** Onboard location alone is not identified. | Corrected baseline/P/Pg at peg 400 ms tests package repeatability. Then match primitive rate and input state age between locations, and vary those factors separately; add the original 5 mm noise +33 ms lag condition. Measure assistance and blending on successful episodes, hand-back, all cage/keep-out events, SAL and LDLJ. |
| [H12](H12.md): bounded satellite extrapolation removes 45–65 ms and raises relay throughput ≥10%. | Tier 2 capture at 250 ms: 57/100 versus 52/100, conditional rate 1.02×. Relay peg rate 1.03× fails the 1.10 gate. Peg at 250 ms: 88/100 versus 11/100, a large package effect. The promised L/K sweep and measured command-to-applied lag were not completed; nominal L is not an exact closed-loop lag reduction. | **Original capture/relay claim unsupported at tested settings; delayed-peg filter remains a priority.** | Corrected peg 250 ms replication, then B and L={0,30,60,90} ms at K={4,8} on the same command timings. Separate filtering from prediction, measure requested and actual applied lag, and test ≥0.5L reduction, >10% relay rate, ≤3-point success loss, ≤2× jerk and safety. Select parameters on training seeds, then freeze them. |
| [H13](H13.md): no worthwhile latency-aware UI on the relay profile. | No human/UI experiment. The three-seed easy-task ceiling used for its null is stale. Its warning against bypassing reaction delay remains valid; link-state gating and resume protection belong to the baseline. | **Baseline obligations accepted; UI effectiveness outside this proxy's evidence.** | In current autonomous scope, audit observation age and the reaction-history constraint. If a later program includes users, compare raw video, calibrated phantom and link information with identical control and task conditions; measure errors, attention and accepted yield. Do not infer this human result from a state-consuming policy. |
| [H14](H14.md): RTT motion scaling improves high-delay capture success and throughput without hurting the relay case. | Tier 2 capture at 400 ms: 3/100 versus 44/100. Relay conditional-rate ratios in Tier 1 were 0.84 capture and 0.85 peg, failing the 0.90 default-on gate. Peg at 250 ms: 95/100 versus 11/100, but conditional rate 0.70×. Fewer knock-aways accompanied worse capture success. | **Reject tested capture strategy and default-on use; retain stationary-task slowdown as a distinct discovery.** | Corrected 400 ms capture replication, followed only if useful by stationary versus controlled target-speed trials using identical scaling and delay. Report ability to intercept, timeout failures and all-attempt rate. Compare adaptive scaling with a fixed slower operator to identify the value of RTT scheduling. |
| [H15](H15.md): two arms per operator, onboard reset macro and pass admission increase throughput >10%. | No two-arm switching/macro trial or pass-admission comparison ran. H20 changes reset demand; it does not test scheduling or hide an independently measured reset. An object-carrying macro adds autonomy beyond the passive baseline. | **Operations hypothesis deferred; only reset accounting merged into H20.** | First measure reset/recovery on a physically repeatable task. Then compare one/two arms with the original 2 s switch cost at measured reset time, require ≥1.10× relay yield, ≤5-point success loss, no unsafe handoff, and no loss of demos/pass from admission. Stop if reset time <0.1× episode time. |
| [H16](H16.md): six to eight arms pooled for four operators raise demonstrations/operator-hour >25%. | Four-arm simultaneous execution in the [scaling appendix](../experiments/scaling.md) has four independent operators; it does not test N>M pooling, resets or handoff. Arm count and session cost are unmeasured for this hypothesis. | **Deferred, independent of H20's mechanism.** | After measuring reset and handoff, compare N=4/6/8 with M=4 in matched continuous sessions and fixed camera bandwidth. Count operator time, reset failures and queue waits. Apply the original ≥10% eight-arm rejection gate and report separately whether the stronger 25% claim holds; stop if reset <3 s. |
| [H17](H17.md): no useful segmentation hypothesis near the assumed 333 ms loop. | The original toy-delay experiments motivated a jaw-scale task, a useful validity correction. They do not test segmentation on the final physical-jaw proxy or the selected media tasks. Later latency-sensitive failures invalidate the old universal easy-task ceiling. | **Useful task-validity warning; segmentation effectiveness remains task-dependent and untested.** | Choose a physical tolerance before tuning the policy. Compare continuous and segment/confirm control on the same validated capture/contact task around its observed failure interval, charging every confirmation wait. Retain segmentation only if accepted all-attempt yield improves. |
| [H18](H18.md): post-hoc relabeling cannot improve collection-time metrics, but recording applied actions is necessary. | A post-hoc transformation cannot change the already completed physical episode. That logical result holds. Satellite logging was added; no learned-policy comparison tested alignment quality. Logging an applied target is not the same as measuring actual motion. | **Collection-metric null valid by definition; data alignment is a high-priority unresolved learning question.** | On identical recordings, compare intent labels, timestamp-aligned applied commands and measured-state labels under a fixed learning protocol. Hold episode splits, budget and evaluation task fixed. Validate loader/schema and clock provenance first, and never silently replace observed motion with commanded motion. |
| [H19](H19.md): autonomous perturbed replays during pass gaps double ground-verified episodes per wall-hour. | Not implemented. Autonomous motion while the controller declares hold conflicts with the proposed baseline. Generated episodes also do not increase human demonstration count. These are scope/design conflicts, not experimental proof that autonomous physical data lack value. | **Reject the proposed hold-bypass implementation; defer a separate autonomous-data branch.** | Reopen only with an explicit locally supervised autonomous mode, abort semantics, measured physical reset and source labels. Test the original ≥25% replay success and ≥2× total yield, but decide value using held-out learning gain per collection cost. Trajectory noise above a floor alone does not establish useful diversity. |
| [H20](H20.md): release-as-reset plus slack tether raises gross relay yield ≥40%, retaining ≥90% success. | [Tier 1](../experiments/tier1/results.md): 472.2 versus 389.6 demos/hour, 1.21×, and 30/30 successes in each mode. This meets the 1.10 point gate, not the 1.40 headline. Each mode is a persistent trajectory; 30 episode labels are not 30 independent chains. Both modes use the tethered scene. Slack damping acts before the tether is taut. Tier 2 confirmation did not run. | **Promising within-chain operations result; headline missed and replicated inference absent.** No free-body or tether-effect confirmation. | Run independent matched chains from varied initial states at relay and 500 ms. Charge all resets, recovery, timeout failures and terminal unfinished recovery. Resample whole chains. Cross reset mode with tether force model, including zero force while slack, and report initial-state coverage, force exposure, safety, smoothness and the original 1.10/0.90 gates. |

## What the five selected experiments actually identify

### H10: keep the twin; separate prediction benefit from delay compensation

The large historical delayed-cell success differences justify keeping the twin. The zero-control
result does not establish that its entire gain comes from the link. In the original paired table,
the zero success difference is +7 points with a 95% interval reaching about +15 points, and the
conditional-rate ratio is 1.06 with interval 0.97–1.17. Failure to detect a zero effect is not a
test that the effect is small. A zero-delay emulator still has command sampling, playout,
telemetry age, actuator response and modeled reaction delay.

The [second-wave reanalysis](../experiments/second_wave/statistics.json), using the historical
data, estimates the capture success interaction as +21 points at 400 ms after subtracting the
zero-cell difference, with a paired bootstrap interval of +8 to +34 points. The conditional-rate
ratio of ratios is 1.05 [0.92, 1.19]. On the original geo paired subset it is 1.17 [0.99, 1.37].
These results favor a delay-related success benefit but do not establish the full original
throughput claim. The seeds 30–99 sensitivity subset is exploration-disjoint, not a validation
of corrected code; it gives weaker precision for the 400 ms success interaction.

The peg task removes free-object drift, but also changes the task, starting distribution,
geometry and controller phases. It shows that a twin can help without a moving target. It does
not prove that capture's benefit is mostly object prediction. Use within-capture arm-only and
object-only ablations for that conclusion. Perturb model parameters independently: an accurate
prediction within the same simulation is insufficient when the mission's purpose is to learn
physics the simulator does not capture. Do not interpret the current “innovation” diagnostic
as prediction error until prediction and reference refer to the same physical time.

The original requirement of no success loss anywhere needs a declared noninferiority margin
and simultaneous uncertainty if it is to support deployment over multiple conditions. A
nonsignificant negative cell cannot be counted as a demonstrated no-harm pass. Smoothness
must retain its original gating role; the historical report's later “never gated” language
contradicts H10 and several other original hypothesis files.

### H11: retain local assistance as a package, with an honest comparison

The delayed-peg result is the strongest historical package effect. The onboard arm combines
fresh simulator state, control at the satellite cycle rate, local command application and
task-specific triggering. Pg uses delayed and sampled telemetry, executes at the ground command
rate and sends its result through uplink and playout. Sharing `_Prim` code does not hold those
other factors constant. P−Pg therefore measures a package difference; it is not the isolated
value or economic worth of placing compute onboard. At relay delay P improved peg success
from 97% to 100%, while Pg fell to 56%. The 44-point P−Pg gap is mostly a comparison with a
degraded counterpart, not a 44-point increment over the baseline.

Use a matched-rate local-versus-ground primitive to isolate placement, then independently vary
state age, sampling rate and pose error. A true-pose implementation is an **oracle-state reference**.
Its observed outcome is not a mathematical upper bound: no proof establishes monotonicity of
task success in pose accuracy for this controller, trigger, contact model and deadline. A single
5 mm/33 ms noisy condition is a sensitivity point, not a lower bound on arbitrary flight hardware.
MuJoCo supports elastic-contact parameterizations; the original argument that it lacks
restitution and must understate benefit is incorrect. See the [evidence review](../research/second_wave_evidence.md)
and [MuJoCo's official restitution documentation](https://mujoco.readthedocs.io/en/stable/modeling.html#restitution).

Apply the assistance gate to successful episodes, and distinguish active primitive time from
blended hand-back, whose actions are also modified. The historical peg fractions of 0.25–0.26
at some delays cannot be called a clean pass of a strict 0.25 limit. Capture's all-episode
average cannot settle the successful-episode requirement. The original safety clause explicitly
includes cage contact; zero “link-unsafe” counts do not discharge that clause when other contact
events exist. Even if these gates fail, the result may motivate a more autonomous collector.
That is a different dataset policy and must be labeled accordingly.

### H12: a useful filter is not an exactly measured latency removal

The historical correction subtracted the 30 ms interpolation term from the prediction time.
That repairs a nominal accounting error. It does not make the outputs equivalent to baseline
at L=0: H12 fits a line to multiple sequence-indexed samples, while the baseline interpolates
arrival-time samples; the gripper path also differs. On curved trajectories, packet loss,
irregular sends or an active ramp limit, a nominal lead is not an exact measured lead.
The original lag diagnostic and the L=0 filtering control are necessary for causal attribution.

The peg success increase at 250 ms is a strong reason to test this small supervisor-side option.
The relay conditional-speed gain of about 3% and missing parameter sweep cannot confirm the
original best-L ≥10% claim. Likewise, one tested L that did not help capture cannot reject all
bounded prediction schemes. Keep the specific setting and task attached to each conclusion.
Measure imposed trajectory changes, error during reversals, stale-data fallback and actual joint
motion alongside command lag; the shared clamp can hide requested overshoot without eliminating
its task consequences.

### H14: the failed capture prediction is useful evidence

The negative capture result directly contradicts the proposed universal benefit of slowing
the loop. Fewer knock-aways and fewer successes are compatible: an arm can avoid hitting a
moving target because it never intercepts it. The static-peg gain supports a different mechanism,
trading speed for acquisition stability. It does not rescue H14's original moving-target claim.

Evaluate fixed slow control alongside RTT scheduling. Otherwise the experiment cannot tell
whether estimating delay is useful or whether the synthetic policy simply needed a lower gain
on the stationary task. Conditional successful speed can decline while all-attempt yield rises
because failures disappear. Use the latter for choosing a collector, while continuing to report
the original throughput gate as failed. Ground freeze and ramp-limited resume are already
baseline properties; their adoption cannot be credited as H14's incremental safety benefit.

### H20: estimate campaign yield, not thirty independent successes

Chaining changes the distribution of future attempts. In the runner, simulation state and the
operator persist, so the release and any failed recovery shape the next attempt. Pairing episode
number 12 between two modes does not recreate a matched initial state after eleven different
outcomes. The independent unit must be a newly initialized chain, with mode assigned and seed
paired at that level. Report within-chain behavior and between-chain uncertainty separately.

The actual comparison uses `capture_chain` with free versus teleoperated reset, so both arms
have the tether. It tests reset policy under that scene, not tether versus no tether. The
historical 6% taut-row fraction on the relay profile does not imply 94% force-free data:
the tendon applies damping while slack. This directly affects the physics the dataset would
claim to contain. Label force exposure, or change the physical tether model and rerun before
describing a free-body subset.

Reset start/end, successful release, failed reset and deadline are outcome-defining events.
The [testbed audit's W1 finding](../experiments/second_wave_testbed.md) establishes that old
physics continued during the one-second terminal-message linger: a timeout could become a
late success, and a chain advanced after its recorded endpoint. The correction freezes the
outcome and state during linger, so new chains begin from a different state and timing policy.
It still freezes a real-world moving scene during harness turnaround, an operations assumption
that must be charged or modeled explicitly. Two further chain-only defects remain: a reset
timeout can return success without a completed release, and knock-away counts persist between
episodes. A reusable-demo success predicate must require release, with per-episode event counts
separate from campaign totals. Old 1.21× results cannot be silently carried over. The fixed second-wave matrix contains no
independent-chain confirmation, so this review leaves H20 pending even if the other control
replications succeed. The original 40% forecast missed at the relay point, and the collapse
at 500 ms is a result for the historical chain and reset policy, not a universal boundary for
self-resetting task design.

## Baseline obligations and common evidence limits

Sequence rejection, a short playout buffer, command expiry, observation-age gating, bounded
resume, local safety supervision and faithful action/state logging are baseline responsibilities.
They are not evidence that FEC, a UI, a twin or a scheduler improved safety. Test them with real
loss of commands, fresh observations with a stale command echo, stale observations with a live
uplink, and recovery while holding an object. A counter proving the emitted setpoint obeys a
software clamp is useful as a regression check but does not demonstrate bounded physical joint
velocity or a collision-free retract.

The 720 historical forced-outage episodes are not 720 exposed safety trials: many peg episodes
finished before the outage began. Report active outage exposure, hold and retract transitions,
and actual state/velocity during the exposed interval. Also keep cage contacts separate from
the narrower link counter. Reclassifying cage contact as a task fault can be defensible for an
engineering analysis, but it cannot silently remove it from an original “any unsafe event” gate.

The historical reference success of 69/100 on zero-delay capture is a baseline performance
measurement, not a universal physical ceiling. A reachability argument under one policy is not
proof that no policy can succeed. Report both absolute success and retention against that
baseline. The relative 80% charter bar alone can admit an operationally poor collector.

Physical validity also limits every ranking. The [testbed audit](../experiments/second_wave_testbed.md)
demonstrated acceptance of a closed jaw and a nearby object without bilateral pad contact;
subsequent carry is a kinematic attachment. The fixed arm base and constrained peg orientation
omit the original task's proposed arm/base identification. Record these as proxy differences,
not validated representations of free-flying grasp or insertion. Schema-2 recordings provide
new actual-state and causal-observation provenance; the historical NPZ dataset cannot be
retroactively treated as equivalent or directly LeRobot-compatible.

The first-wave study selected confirmation cells after a screen and reused seeds 0–29 in
Tier 2's 0–99 range. Those tiers are not independent replications. Historical reanalysis with
seeds 30–99 and multiplicity correction is useful, but only corrected runs on new seeds test
the corrected implementation. A sweep's interpolated “knee” depends on the zero reference,
grid, threshold convention and interpolation rule. A crossing between tested points is a
bracket, not a measured delay limit at millisecond precision. Report no-crossing cases as
right-censored beyond the sweep, not an infinite safe operating range.
The historical capture deadline also changes from 20 to 30 seconds at 500 ms, so that portion
of its curve varies both latency and allowed completion time. Use a fixed deadline or show
both deadline curves before estimating an operational latency boundary.

## Revised short research program

Keep the original physical-AI objective. Rank work by whether the result would change the
task, collection architecture or value of the dataset, not by which strategy can win another
synthetic completion cell. The following priorities reuse the best first-wave work.

| Priority | Research decision | Minimum comparison and decision gate |
|---|---|---|
| 1. Trust the collection experiment | Do the main controller effects survive corrected timing, complete outcomes and independent seeds? | Complete the fixed 15-cell/450-attempt [protocol](../experiments/second_wave_plan.md). Preserve code hashes and every attempt; report paired success, all-attempt rate, absolute zero/relay results and exposed safety events. This decides which simulator results remain usable, without claiming to close unrun original gates. |
| 2. Choose one scientifically useful task | Which repeatable low-gravity behavior leaves a consequential error after simulation calibration? | Use existing physical data to fit a baseline model, then evaluate unseen conditions. Select one phenomenon with measurable residual error and feasible containment/reset, before increasing task or arm count. Existing low-gravity granular observations provide a comparator, not proof that this task is already solved or orbit-only: [Ozaki et al.](https://www.nature.com/articles/s41526-023-00308-w). |
| 3. Choose the least costly collector | Can the selected task be collected through direct passes or a qualified relay without requiring unnecessary onboard autonomy? | First test H10 with model mismatch and its prediction ablations; test H12 on the stationary/contact case. Retain H11 if local assistance adds accepted yield after matched-rate and noisy-pose controls. Keep H14 off for moving capture. Choose using success, recovery, accepted yield and assistance provenance, not knee alone. |
| 4. Establish operational yield | Does the task repeatedly recover and reset over a booked pass or continuous session? | Replicate H20 by independent chain, add safe pass end and explicit recovery cost, then evaluate H15/H16 only if measured reset time justifies spare arms. Qualify actual goodput, path delay and availability before promoting a relay profile from scenario to service. Direct visibility is not booked operating time; see the [evidence review](../research/second_wave_evidence.md). |
| 5. Test incremental learning value | Does physical microgravity data improve a policy beyond calibrated simulation and available physical alternatives? | Fix policy, optimizer, training budget and task metric before comparing simulation alone, simulation plus existing physical data, and simulation plus newly collected data. Split by object/material, geometry and whole collection session/chain. Evaluate on held-out physical conditions when available; report data count, cost and uncertainty. A proxy learning result establishes only proxy value until the physical comparison exists. |

Priorities 2–5 define the next empirical program; they are not reported as completed flight,
human or learning work. The evidence review supplies a concrete calibration route through
existing orbital and short-duration microgravity measurements, and separate mission gates for
power/thermal control, pressure containment, component faults and client-orbit service. These
gates can invalidate a satellite configuration even if every latency cell passes. Conversely,
a slower supervisory link may remain useful if repeated physical observations, rather than
unassisted human imitation, are the data objective. That trade must be explicit.

## Implication for our design

Retain the deterministic satellite baseline and ground-first architecture, with direct-pass
operation as the implementation reference and relay performance as a qualified scenario.
H10, H12 and H11 justify targeted control research; H14 rules out indiscriminate slowing of
moving-target capture; H20 makes reset and physical disturbance part of the dataset decision.
Adopt none as a flight-validated solution from the current evidence. The program succeeds when
it connects measurable model error to repeatable, correctly recorded physical demonstrations
and then to incremental learning value at an acceptable collection cost. The second wave should
make that chain of evidence testable, while preserving the first wave's useful measured effects
and clearly identifying every original claim that remains unmet.
