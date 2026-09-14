# Second-wave testbed audit

Date: 2026-09-13. Scope: the complete operator → command → UDP link → controller →
MuJoCo → telemetry → recording/metrics path, including all six strategy families.
Compared with [the first testbed audit](audit_testbed.md),
[the strategy audit](audit_strategies.md), and
[the earlier final verification](final_verification.md).

The testbed is useful for testing control and transport mechanisms under explicit
assumptions. It is not a validation of human performance, physical grasp reliability,
flight safety, or the learning value of an orbital dataset. The earlier successful
reproduction establishes repeatability of selected simulator outcomes. It does not
establish those external claims.

## Fixed defects and consequences

| ID | Verified defect | Correction | Effect on existing evidence |
|---|---|---|---|
| W1 | The controller continued physics during its one-second terminal-message linger. It returned the mutated `st.success`, so a failed deadline could become a success afterward. Chained scenes also advanced after the recorded endpoint. | Stop physics at the first terminal step or deadline. Retransmit the frozen final state during linger. Cap catch-up stepping at the allowed episode duration. | Re-run comparisons used for current conclusions. Historical timeout-adjacent outcomes and chain initial conditions cannot be certified from the old truncated setpoint-only sidecars. This does not prove that any specific historical headline changes. |
| W2 | Main-table `cmd_seq` was incremented before recording: wire command 0 appeared as row command 1. The recorded state was the newest telemetry, although the action used an older or predicted frame. | Record the transmitted sequence and action-causing observation. Add source telemetry sequence, source send/receive timestamps, command send timestamp, object pose, and a prediction flag. | Historical command IDs require a one-count correction before joining. Historical causal observations cannot in general be recovered, especially for the twin. Do not silently concatenate schemas. |
| W3 | Satellite sidecars contained commanded setpoints but no actual joint state, velocity, object pose, or simulation time. Episode metadata omitted the outcome and final state. | Add pre-step state/velocity/object/simulation-time and grasp/success masks to sidecars. Save terminal outcome, duration and final state in episode metadata. Set `recording_schema: 2`; use the configured command frequency in metadata. | New recordings permit state/action alignment checks and actual-velocity analysis. They do not turn old files into training-ready trajectories or prove policy-learning value. |
| W4 | A blackout in the first episode raised a harness error. A later short episode copied a previous episode's metrics, omitted its recording, and printed a row the matrix parser did not recognize. | Record zero-command episodes with empty `(0, 7)` arrays, the real satellite sidecar and metrics, and a standard result row ending in `no_link=True`. | Missing historical episodes must not disappear from attempted-demo denominators. Matrix completeness and parsing are checked separately in this wave. |
| W5 | UDP decoders accepted NaN and infinity. These values could enter the operator, extrapolator, or ramp arithmetic; Python `min`/`max` are not a finite-value validator. | Reject nonfinite values in every command setpoint and telemetry state/object field at decoding. | Does not change correctly formed historical packets. Prevents invalid numerical input from being treated as a valid control packet. |
| W6 | Bandwidth release time was `max(now + delay, serialization_end)`, which overlapped serialization with propagation. Equal FIFO release times also used a nonunique `sent + dropped` heap key, allowing payload bytes to decide ordering. | Release at `serialization_end + delay`; use a monotonically increasing receive counter to break ties. Floor the total delay at zero. | Re-run bandwidth-sensitive comparisons. The default small command/telemetry serialization correction is small but real; it grows with frame padding or queueing. |

W1 has a deterministic old-code reproduction, independent of the host scheduler. With
a 10 ms deadline and 20 ms linger, the old controller advanced a task that succeeded at
4 ms to 24 ms. A task that first succeeded at 12 ms was reported successful and advanced
to 32 ms. The regression test now leaves these at 4 ms/success and 10 ms/failure,
respectively, while still retransmitting terminal telemetry. Physics remains quantized
to the model timestep; this is not a claim of sub-timestep event precision.

W6 also has a deterministic check. Two one-byte packets arriving at time 10.0 s, with
500 ms propagation and a 100 B/s link, leave at 10.51 and 10.52 s. With unlimited
bandwidth and equal release times, payloads `z`, then `a`, retain that arrival order.

## What the experiment actually measures

**Operator.** `SyntheticOperator` is a fixed scripted visual-state policy with a
170 ms default reaction delay, a joint-space noise draw, and a Cartesian speed bound.
It gets exact simulator object pose over telemetry. It does not estimate pose from a
camera, learn a task, experience fatigue, change strategy after a dropout, or provide
human demonstrations. The per-profile parameter equality is a useful internal control;
it is not evidence that its response to delay matches people.

**Physics.** The arm base is fixed. Capture is a kinematic attachment, and carry reels
the position offset toward the grasp site. The peg is held upright and has a scripted
jam/regrasp rule. These are useful mechanism tests but exclude grasp friction,
orientation-sensitive insertion, floating-base reaction, and flight disturbances.
The capture predicate still accepts a closed jaw plus a spherical proximity envelope
without two-pad contact. A direct probe at 24 mm world-z offset returned
`grasped=True`, `bilateral_pad_contact=False`, `jaw_rad=0.0`. Thus T01's command-only
bug was fixed before this wave, but the stronger physical-grasp concern remains.

**Timing and network.** Real sockets and wall-clock delay are genuine. Physics catches
up to wall time against one command per controller cycle. Large host stalls therefore
remain a contamination source; rejecting only gaps above 200 ms does not prove smaller
rate-dependent effects are absent. Link randomness is consumed per packet, so matching
seeds match initial conditions, not an identical timed network trace across strategies.
The up/down processes have independent phases and loss states; common link failures are
represented only when explicitly forced. Blackouts drop packets offered during their
window; they do not cancel every previously queued in-flight packet. Padding models
payload demand, not exposure, encoding, decoding, visual quality, or human perception.

**Onboard primitive comparison.** P uses current simulator state at the satellite
control rate; Pg uses delay-aged telemetry at the ground command rate. The latter frame
also includes the human reaction-delay selection used by the operator. P−Pg therefore
combines state freshness, measurement quality, update frequency, and placement. It is
an optimistic system comparison, not an isolated estimate of the value of moving the
same computer onboard. A placement ablation needs matched estimator quality and update
frequency, with the automated ground primitive using its own explicitly defined sensing
delay instead of inheriting a human delay by accident.

**Safety.** A zero `vel_over` checks the emitted setpoint limiter, not actual joint
velocity, torque, contact force, or collision severity. `move_in_hold` checks commanded
motion under the strategy's own hold state. A position servo can still move while its
setpoint is held. Actual state/velocity are now recorded, but the legacy safety aggregate
still uses setpoints. A cage contact at zero latency does not prove all cage contacts
are independent of the link. Report cage contacts separately without calling them
causally exonerated. The static position clamp is not an enforced Cartesian keep-out
controller, and the architecture's acceleration clamp is not implemented.

**Reset and throughput.** The short-episode rate excludes file I/O, link teardown and
terminal-message linger by design. It is an active-task rate, not observed campaign
throughput. In chained runs the simulator now freezes at release during harness
turnaround; this removes an unrecorded trajectory but is still a reset-time assumption.
The chain's targets and random stream depend on previous outcomes, so later chain
episodes are not independent paired trials. The tether's spring dead band does not
remove its damping while slack. No result from this task measures an unconstrained,
force-free object throughout the episode.

Two additional chain-only defects were found outside the source-frozen non-chain rerun:
the returned `success` can be true at a reset timeout even when `released` is false,
although a reusable chained demonstration requires the release; and the carried state
resets cage/keep-out/jam counts but leaves `knockaway` and its debounce timestamp
cumulative. Do not interpret historical chain success rates as completed reusable-demo
rates or sum those per-episode knockaway counts as independent events. A chain-specific
correction and fresh chain evidence are required before that claim. Revision `550e190` now
requires completed release, charges the allowed reset extension, and resets both knockaway fields.
Deterministic regressions cover capture without release, timely release and late capture. The
supplemental four-chain study checks bookkeeping, not the original H20 effect size.

The same revision archives replaced matrix cells under `_superseded`, replaces retried recorder
metadata suffixes, retains blackout labels after optional diagnostics, normalizes the gross-rate
field name and saves each scenario seed in outcome metadata. The 450 primary recordings retain
their original source version and use the summary seed; they are not rewritten.

The complete primary recording audit passed all 450 episodes and found a sampled actual joint
speed maximum of 6.584 rad/s (Elbow, drop12, seed 1024, simulation time 19.914 s). Command-envelope
violations remained zero. This is direct evidence that setpoint compliance is not actual-motion
safety. See the [audit artifact](second_wave/record_verification.json).

## Status of previous findings

| Earlier finding | Status after inspection and this wave |
|---|---|
| T01 physical jaw | Command-only acceptance was fixed before this wave; physical pad containment is still incomplete, as the 24 mm probe shows. |
| T02 dropout exposure | Forced dropout profiles exist. Exposure must still be counted per episode: fast peg strategies can finish before the six-second blackout and supply no dropout evidence. |
| T03, T04, T12, T13 | Random structure phase, arrival-stamped RTT, independent adjacent-direction seeds, and SPARC padding fixes remain present. |
| T05 smoothness | Telemetry sample-and-hold artifact was removed by using a resampled setpoint sidecar. Those scores still measure commanded motion, not actual physical smoothness or learned-policy quality. |
| T06, F13 load | Stall reporting is present. F13's earlier blanket reassurance about concurrency does not supersede the measured contaminated cells in T06. |
| T07 cage causality | Separate reporting is useful; the label “operator/task-caused, not link-caused” is stronger than the evidence. |
| T08, T17, T18 | Still applicable: sweep zero retains clipped jitter; command-buffer loss includes stale reordered packets; `owd_up_ms` remains RTT/2, not a measured asymmetric uplink delay. |
| T09/F2, F12 endpoint handling | Durations and sidecars were trimmed before this wave, but physics was not stopped. W1 fixes this separate remaining error. |
| T10 duty-cycle reporting | Short direct-GS episodes intentionally start in a contact window. They cannot by themselves measure whole-day availability. Geometry/duty-factor conversion needs its own assumptions. |
| T11 dataset compatibility | Metadata was improved earlier. `.npz` files and jittered timestamps still do not directly satisfy a LeRobot loader. W2/W3 add scientific provenance, not a claimed loader conversion. |
| T14 bandwidth | W6 fixes serialization/propagation composition and additionally fixes FIFO tie ordering. |
| T15 peg contact timing | Final revision `be7dd45` recomputes completion depth/contact after the kinematic update. All 30 separate fresh endpoint checks pass. The primary 450 outcomes predate this final fix; physical/contact-model limits remain. |
| T16 reachability | A task-imposed zero-latency ceiling remains. Normalize only with explicit absolute success and uncertainty; a fraction of a weak baseline is not an absolute feasibility threshold. |
| T19 physical speed | A few benign ramp/step checks do not establish velocity/force safety under all contacts. New sidecars enable broader actual-state checks. |
| T20 statistics | Statistical estimator and aggregation corrections are handled by the separate second-wave evidence audit. |
| F1 DeadReckon lead | The extra 30 ms evaluation offset was removed earlier. Exact equality with Baseline at L=0 is not general: least-squares smoothing differs from interpolation on nonlinear or irregular streams. A quadratic-stream probe gives 0.0315 versus 0.0305 rad. The ideal constant-velocity lead interpretation survives. |
| F3 twin zero-cell gain | Still applies. The twin also removes machine delay present at zero network latency; a zero-cell gain alone is not proof that human reaction delay was bypassed. |
| F4 twin innovation | Still unresolved. A prediction at one horizon is compared with the next frame at another horizon; `twin_innov_m` is not a time-aligned prediction-error score. |
| F5/F6 gain reference | Tau-relative reference delay and persistent unscaled speed fixes remain present. Gain still estimates delay from the already-aged frame and acts on subsequent operator steps. |
| F7/F8 assistance | Ground assistance is propagated over the wire. Fractions still need an explicit successful-episode denominator and a choice of frame versus elapsed-time weighting. A fresh flag describes the newest command even while earlier commands are being played out. |
| F9 velocity clamp | Still a useful implementation invariant, not an independent system-safety result. |
| F10/F11 ordering and nominal ticks | Still limitations: downlink frames can regress in sequence; DeadReckon fits nominal sequence time despite slipped ground ticks. These can interact differently with prediction strategies. |

One factual correction to the earlier final verification: SO-100's jaw is joint index
5, and slot 6 is unused. The `[:6]` velocity check includes the jaw; the hold comparison
compares the complete setpoint list. The stated “jaw index 6 excluded from both checks”
gap was incorrect.

## Recording contract and remaining data gaps

Schema 2 observations are what caused the operator action, including twin substitutions.
`observation.t_send_ns`, `observation.t_rx_ns`, and `observation.tel_seq` identify the
source telemetry; `observation.predicted` distinguishes a transformed observation. They
do not claim that a twin estimate represents the source measurement's physical time.
`command.t_send_ns` is the actual packet timestamp and `cmd_seq` matches the wire.

The satellite's new `state`, `velocity`, `object`, and `sim_time` are sampled before the
cycle's catch-up integration. `setpoint` is the control target used for that integration.
The final state lives in episode metadata, because the last pre-step sidecar row can
precede the terminal state. Existing `t_applied_ns` means the first controller cycle that
saw the newest command; interpolation can mix older commands, so it is not proof that
the newest command was applied unmodified at that instant.

Remaining requirements before a learning-value claim: train and evaluate an actual
policy against a matched terrestrial/synthetic control, define train/test separation
and success criteria before selection, validate observation/action timing and quality,
and show that the target task benefits from the proposed microgravity conditions.
There are still no real image streams, force measurements, human demonstrations,
validated pose estimation, or direct LeRobot conversion here. External robot-description
assets also need an origin revision/content digest; a Python dependency lock alone
does not pin that separately downloaded model.

## Verification

Commands completed on the corrected code:

```text
uv run pytest tests/test_proto_record.py tests/test_sat.py tests/test_link.py -q
30 passed in 18.75s

uv run pytest tests/test_e2e.py -q
3 passed in 30.29s

uv run pytest tests/test_e2e.py -q -k blackout
1 passed, 3 deselected in 3.23s
```

The first e2e command preceded addition of the blackout test; together the two commands
cover all four current e2e tests. These include real-socket zero, relay and 250 ms sweep
episodes; command sequence and source-observation age; actual-state recording; and a
first-episode total blackout with a persisted failed outcome. No new dependency was
added. Fresh paired strategy results and source/model provenance are reported by the
second-wave experiment run, separately from these correctness checks.
