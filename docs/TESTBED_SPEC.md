# Testbed specification, second wave

This describes the current research implementation. The mission target is in [PROGRAM.md](PROGRAM.md);
measured findings and limitations are in [REPORT.md](REPORT.md). It is a local research testbed,
not flight software, a human interface or a qualified data exporter.

## Execution and communication

`spaceteleop.run` runs a ground operator, directional UDP emulator and satellite controller over
real localhost sockets. MuJoCo and network delay use elapsed wall time. One arm uses threads;
independent experiment cells use separate processes. `--arms` creates independent triplets rather
than mechanically coupled arms or a shared spacecraft link. A stall over 0.2 s flags scheduler
contamination; outcomes then require investigation or paired exclusion.

The ground sends joint setpoints at 50 Hz and receives telemetry at 30 Hz. The default synthetic
reaction delay is 170 ms. Strategy transformations receive the delayed observation selected for
the operator. Telemetry carries state and command echoes. The emulator supplies directional delay,
jitter, loss bursts, reordering, outages, contact windows and serialization. It models video as
padding bytes, not images, encode/decode or perceptual quality. Main experiments use no padding.

Commands have sequence numbers and timestamps. Satellite receipt rejects older command sequences
and nonfinite setpoints. Numeric/format validation is not authentication or authorization. Local
clocks are shared; `owd_up_ms` remains an explicitly approximate RTT/2 diagnostic, not a directional
measurement. Directional timestamp subtraction requires synchronized clocks outside this machine.

## Plant and tasks

The model is MuJoCo Menagerie's fixed-base SO-100: five arm joints and one jaw. The wire has seven
slots, including one spare. Gravity is zero. The spacecraft base does not move. The model revision
used for the second wave is recorded in the experiment manifest; `robot-descriptions` can otherwise
fetch assets independently of `uv.lock`.

- **Capture:** a 16 mm box with seeded 0.020–0.045 m/s drift and 0.3–1.0 rad/s tumble. The grasp
  predicate uses a closed/pinched jaw and a 25 mm proximity region; after capture the object follows
  the grasp site kinematically. A 50 mm target sphere requires 0.2 s dwell. This predicate can grant
  attachment without bilateral contact; it is not a physical grasp validation.
- **Peg:** a 60 mm peg, nominal 6 mm clearance per side, constrained upright orientation and a
  fixture-contact jam model. It tests delayed position control, not general contact-rich insertion.
- **Capture chain:** alternates targets with a tether and release/reset protocol. Spring slack does
  not remove tendon damping. Episodes share physical state; seed-wise IID inference is inappropriate.
  See the testbed review for chain-specific outcome/reset qualifications.

Typical deadlines are 20 s for Capture and 30 s for Peg; the sweep also allows 30 s for Capture at
500 ms and above. This timeout change is a confound for a causal latency curve. Task simulation
and outcome stop at termination; the following reporting interval repeats final state.

## Strategies and diagnostic safety

Baseline playout interpolates through a 30 ms buffer, holds after 300 ms command silence, retracts
after 10 s, and applies joint/rate bounds. The other strategies are ground Twin prediction,
supervisor DeadReckon extrapolation, operator Gain scaling, and local or ground Terminal assistance.
The Terminal comparison also changes sensing quality and update rate. It is not a pure placement
ablation. Strategy-specific parameters remain in their small implementation modules.

`move_in_hold`, emitted-setpoint `vel_over` and end-effector `keepout` are narrow diagnostics.
Cage contacts are reported separately and count toward the original full safety target. Zero
narrow diagnostic events do not validate safe physical retraction, contact forces, actuator faults
or flight-level containment. Count episodes actually exposed to an outage before interpreting
zero-event data.

## Record format

The versioned research format is compressed NPZ plus JSON metadata; it is **not loadable LeRobot**.
The main table preserves the action-causing observation, object pose, telemetry sequence and
source send/receive timestamps, prediction marker, command sequence and send timestamp, action,
relative timestamp, and assistance/hold diagnostics. The satellite sidecar records each applied
setpoint and its timestamp together with pre-step actual joint position/velocity, object pose,
simulation time and task flags. Episode metadata records terminal outcome and final state.

An operator command and a rate-limited or assisted applied setpoint are different supervision
targets. The sidecar sequence identifies the newest received command, not the unique source of an
interpolated or assisted setpoint; `t_applied_ns` is a legacy name for its receipt/control-cycle stamp.
Join with these semantics and timestamps; do not pair a delayed observation with a newer action
without documenting the intended training problem. Legacy rows had a one-command sequence offset
and paired the newest received state rather than the causal observation. Treat schemas separately.

Current Peg completion uses tip height and fixture contact after the kinematic pose update.
The primary second-wave execution predates that final boundary correction; its manifest and
report preserve that limitation. Later chain and Peg endpoint regressions have separate manifests.

## Metrics and experiment completeness

Report absolute success and Wilson intervals; paired success differences and McNemar tests;
gross attempted-hour throughput `3600 * successes / sum(all attempt durations)`; conditional
successful-attempt speed; smoothness from applied setpoints; scheduler stalls; cage contacts;
and actual hold/retract exposure. Gross throughput includes only overhead present in the recorded
duration, not every campaign expense. Smoothness is a proxy, not downstream learning validation.

A matrix cell must contain the complete requested episode/seed vector, including full blackouts.
Resume requires identical cell parameters, source-content hash and seed range. Errors produce a
nonzero matrix exit status. Current aggregate JSON preserves episode vectors for reanalysis without
large sidecars. Hypothesis claims require the original gate set, adequate controls, and uncertainty;
incomplete profiles or unknown safety data cannot pass.

## Implication for our design

Use the testbed to compare control mechanisms under stated synthetic conditions and to validate
timing/accounting invariants. Use physical calibration, perception, shared-resource, human and
learning trials for claims that these components do not model. Preserve the simple architecture
while keeping that boundary explicit in every result.
