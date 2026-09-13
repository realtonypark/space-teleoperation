# Selection: which hypotheses go head to head against the baseline

Inputs: PROGRAM.md, SYNTHESIS.md, TESTBED_SPEC.md, H01–H20, scores_V1–V5, and the **working tree** at
selection time (uncommitted diffs in 11 files). The working tree, not `71fbc13`, is the baseline every
verdict below is measured against, because it already contains most of what the verifiers said was
"owed to the baseline":

| Already in the working tree (verified by reading the code) | Source of the obligation |
|---|---|
| Buffer keyed on `seq`; stragglers dropped on arrival (`sat/controller.py`) | H05, H08, H12, V2, V3 |
| `interp_s` 0.030, `timeout_s` 0.300, `retract_s` 10, `vmax` 2.0 rad/s, per-tick ramp limit, joint clamp, `move_in_hold` / `ramp_clip` counters (`strategies/base.py`, `baseline.py`) | SYNTHESIS §5 items 1–5; V4 "resume jump not implemented" |
| Sat-side applied-setpoint log per control cycle, written as `sat_*.npz` (`record.write_sat`) | H18, V2 (jerk aliasing), V5 |
| `vel_over`, `keepout`, `cage`, `move_in_hold` unsafe-motion counts; SAL, LDLJ, `stall_frac` (`metrics`) | SYNTHESIS §6; V3 "SAL not in metrics" |
| `GRASP_TOL` 20 mm, drift 2–4.5 cm/s, tumble ≤1 rad/s, cage walls; `peg` task in `sim` **and** `SyntheticOperator._peg`; `--task peg` in `run.py` | H17 note; V3 "no peg operator" is now stale |
| SYNTHESIS §7 profiles verbatim incl. 15 s structure, Poisson outages, pass windows, `sweep:<rtt>` on the `leo_relay` structure | SYNTHESIS §7 |
| `--tau-h` default 0.17 s | SYNTHESIS §8 |

Still missing and required before the matrix runs (shared infrastructure, ~40 lines, not a hypothesis):
`--strategy` flag in `run.py` (every hypothesis needs it); a `Strategy.observe(tel, now)` identity seam
called in `ground/loop.py` before `operator.step` (H10 needs it); a ground-side freeze when telemetry
age exceeds `timeout_s` (V1 on H03, H14 criterion iii: the ground keeps commanding into a blackout
today); `demos_per_hour_gross = 3600·successes / Σ(episode + reset wall)` (data_pipeline §3.2; H20,
H15, H16 all need it); a knock-away counter in `sim._capture` (box speed > 3 cm/s while ungrasped;
H14's mechanism check). Commit the working tree first: every number in the hypothesis files was
written against the 50 mm / placeholder-profile tree and is stale.

**The fact that shapes the whole selection (V3, V4, V5):** on `leo_relay` the baseline sits at
100 % success and 98 % of `zero` throughput (3 seeds, 20 mm envelope). No latency hider can clear a
+10 % bar on the acceptance profile with task `capture`. The discriminating cells are the RTT sweep
from ≈250 ms up, `geo_relay`, and the `peg` task (insertion class, SYNTHESIS §6's predicted failure).
Every hider is therefore read primarily as a **shift of the success-vs-RTT knee**, and a `leo_relay`
null rejects nothing unless the hypothesis's own file says it does.

## 1. Master ranking

Verifier total is the sum of the five 1–5 columns from `scores_V*.md`. Adjusted score moves a
hypothesis only for a stated reason; unchanged otherwise. Axes: L = link path, T = transport,
C = latency-hiding control, O = operator interface / workflow, D = task and data design.

| ID | Title | Axis | Verifier | Adjusted | Reason for the move | Status |
|---|---|---|---|---|---|---|
| H13 | NULL: latency-aware UI (phantom, RTT readout, link gating) | O | 19 | 19 | — | NO-HYPOTHESIS (its `zero`-cell control rule is adopted for H10 and H14) |
| H05 | NULL: uplink FEC / command repetition | T | 17 | 17 | — | NO-HYPOTHESIS (seq-keying already in baseline) |
| H17 | NULL: task segmentation at ≈333 ms | D | 17 | 17 | — | NO-HYPOTHESIS (its jaw-scale envelope is already applied) |
| H06 | NULL: windowed setpoints per packet | T | 16 | 16 | — | NO-HYPOTHESIS (V2: merge with H05) |
| H10 | Ground digital twin as operator view | C | 15 | 16 | +1: the `peg` task now exists and isolates the arm-twin half (no free object), which answers V3's "the gain is all object prediction" objection with a cell instead of an ablation | SELECTED |
| H20 | Release-is-reset chaining with slack tether | D | 16 | 15 | −1: the ≥40 % is against a reset the author models; success cost at the 20 mm envelope was derived for 50 mm (V5) | SELECTED |
| H14 | RTT-scheduled motion scaling | O | 16 | 15 | −1: the Strategy hook is the wrong seam (V4); the honest version scales operator speed through a strategy→operator handle, so it is partly an operator change | SELECTED |
| H11 | Onboard terminal-grasp / terminal-insert primitive | C | 14 | 15 | +1: only candidate that attacks SYNTHESIS §6's insertion-class failure; PROGRAM.md requires one onboard-compute branch quantified; re-scoped to `peg` + ≥500 ms where V3 says it is falsifiable | SELECTED (**onboard-compute branch**) |
| H12 | Satellite-side dead reckoning of the command stream | C | 15 | 15 | — (V3's Expected-gain 1 is for `leo_relay`; on the sweep it is a clean 60 ms knee-shift test at 45 lines, the cheapest hider in the pool) | SELECTED |
| H01 | Dense commercial direct-pass network, 3 teams | L | 15 | 14 | −1: per operator-hour the gain is ≈1× (V1); the only testbed-falsifiable part is a 20-line `orbit.py` rerun, not a strategy | DEFERRED (geometry rerun as an appendix; `PassScheduled` stow folded into the ground-side freeze obligation) |
| H03 | NULL: relay control + direct-GS video | L | 15 | 15 | — | NO-HYPOTHESIS |
| H18 | NULL: post-hoc relabeling | D | 15 | 15 | — | NO-HYPOTHESIS (sat-side log already in baseline) |
| H04 | NULL: two independent links, first-arrival | L | 14 | 14 | — | NO-HYPOTHESIS (its outage-rate sweep is adopted as an appendix row) |
| H07 | Priority state stream decoupled from video | T | 14 | 13 | −1: V2 showed the saturated arm measures the emulator queue, not the operator; nominal gain 16 ms of 333 | REJECTED (state/video datagram split kept as a transport-baseline note) |
| H08 | Send-timestamp scheduled playout, adaptive D | T | 14 | 12 | −2: the "12 → 0 reversals" row is the seq-keying the baseline now has; adaptive D re-introduces a 60 ms step at every 15 s spike (V2) | MERGED-INTO-H12 (send-time ordering is H12's L = 0 case) |
| H09 | Ground-side phantom arm | C | 14 | 12 | −2: implementation removes `tau_h` from the arm channel (V3); criterion (d) rejects its own success | MERGED-INTO-H10 |
| H15 | Pass-synchronous scheduler, 2 arms/operator, onboard reset macro | O | 14 | 12 | −2: R is author-chosen so >10 % is tautological; onboard macro that carries an object is the excluded branch in all but name (V4) | MERGED-INTO-H20 (reset accounting only) |
| H02 | Dual-terminal hedged send | L | 13 | 12 | −1: iid emulator jitter flatters hedging; spike synchrony confirmed (V1) | DEFERRED (one row of the H04 outage-rate appendix sweep) |
| H16 | Arm pool N > M with ground-scripted resets | O | 12 | 11 | −1: session-mode controller + subprocess launcher is a rewrite, 7.5 h realtime per sweep (V4) | MERGED-INTO-H20 (reset accounting only) |
| H19 | Seed-and-replay in pass gaps | D | 11 | 10 | −1: `Replay.sat_step([])` moving the arm is an unsafe-motion event by construction (V5); replays are not teleop demonstrations | REJECTED |

## 2. Selected set

Five hypotheses, three axes (C, O, D). No link-path or transport hypothesis survives its verifier on
a primary metric; both axes reduce to baseline engineering already in the tree plus one appendix
sweep. Each selected item fits the existing `Strategy` seams with ≤ ~100 lines and is falsified by
the same matrix.

| # | Strategy (arm label) | Merges | What it attacks | Why it is in |
|---|---|---|---|---|
| H10 | `Twin` (T) | H09 | The entire machine loop on the operator's view: link 48 + playout 30 + dwell 17 ms = the largest attackable terms in §8 (the human's 170 ms is not attackable); object chase error, the mechanism that actually fails capture at the 20 mm envelope | Best-specified hider; exact for the arm; `peg` cell isolates the arm half, `capture` cell the object half |
| H12 | `DeadReckon` (D) | H08 | Uplink + playout (60 of the 163 ms machine loop), from the satellite side, supervisor-MCU-feasible | Cheapest hider (45 lines, `sat_step` only); the only one that could fly inside decision (c) hardware; orthogonal implementation to H10 even though it targets the same 60 ms |
| H14 | `Gain` (G) | — | The overshoot-and-chase instability past K·L ≈ 1 (V4 re-derived: failure from ≈250 ms at 20 mm) | Only operator-interface candidate with a testable mechanism; cheap; V4's "implement if the new sim shows a knee ≤400 ms" is exactly what the sweep measures |
| H11 | `Terminal` (P) + `TerminalGround` (Pg) ablation | — | SYNTHESIS §6's predicted failure: the insertion / grasp event, a 100–200 ms-class segment inside a 333 ms loop | **Onboard-compute branch**, labelled as such. Strongest mechanism evidence in the pool; the one thing SYNTHESIS §Implication says to run first; P − Pg is the measured value of onboard compute that PROGRAM.md asks for |
| H20 | task `capture_chain` under `Baseline` (C) vs canonical teleop reset charged (Cr) | H15, H16 | Throughput: reset wall time, which the current `demos_per_hour` charges at zero | Only task/data candidate; supplies the honest reset model that the gross throughput metric needs for every other arm |

Onboard-compute justification: H11's verifier total (14) is mid-table, but its Expected-gain column
(3) is joint-highest among positive hypotheses, its cost score (2) is what pulled the total down, and
no other candidate touches the insertion class. The branch is included as one arm plus its ground
ablation; the flight cost (Jetson pose estimator + Jetson→supervisor path, SYNTHESIS §5 exclusion)
is reported next to the result, never hidden in it. H12 alters the commanded trajectory on the
satellite but needs no perception and runs on the supervisor; it is labelled "supervisor-side
extrapolation", not the branch.

Merges: H09 → H10 (same mechanism, same seam, same sources; H10's `now − tau_h` phantom is the
correct one). H08 → H12 (sequence-time playout is H12 at L = 0; the baseline already keys on `seq`, so
H08's residual is nothing). H15, H16 → H20 (all three are "hide or remove the reset"; H20 removes it,
and the gross-throughput metric they share is built once).

## 3. Experiment matrix

**Common settings.** `cmd_hz` 50, `tel_hz` 30, `frame_bytes` 0, `--max-s` 20 (30 for `peg` and for
every ≥500 ms cell, so the timeout does not truncate the slow tail). Operator `tau_h` = **0.17 s**
(SYNTHESIS §8) for every primary cell; the hypothesis files all say 0.25, and that value is the one
extra `tau_h` variant so their quoted numbers remain comparable. Same seeds across arms within a
cell (paired design). Each cell is one `run.py` invocation in its own process; do **not** use
`--arms` for parallelism across cells (threads share the GIL and inflate dwell, V4). `direct_gs`
starts at a pass and its pass is 540 s realtime, so cap a `direct_gs` invocation at 30 episodes and
report it per pass.

**Link profiles.** `zero`, `direct_gs`, `leo_relay`, `geo_relay`, plus `sweep:{0,100,250,400,500,750,1000}`
(the `leo_relay` structure at that base RTT; `sweep:0` separates structure from base delay). 11
profiles.

**Tasks.** `capture` (SYNTHESIS §3 task 2) and `peg` (task 5). Both exist in the working tree with an
operator policy and are runnable via `--task`; `peg` is uncommitted and must be committed first. H20
uses `capture_chain` (new) and `capture` + charged teleop reset.

**Arms.** B = `Baseline`; T = H10; D = H12 (L = 60 ms, K = 8); G = H14; P = H11 onboard; Pg = H11
ground ablation; C = H20 chained; Cr = H20 canonical reset charged.

### Tier 1: screen (30 seeds per cell)

| Block | Task | Arms | Profiles | tau_h | Cells |
|---|---|---|---|---|---|
| A | capture | B, T, D, G, P, Pg | all 11 | 0.17 | 66 |
| B | peg | B, T, D, G, P, Pg | all 11 | 0.17 | 66 |
| C | capture_chain / capture+reset | C, Cr | zero, direct_gs, leo_relay, sweep:250, sweep:500, sweep:1000 | 0.17 | 12 |
| E | capture, peg | B, T, D, G, P | leo_relay, sweep:400, geo_relay | **0.25** | 30 |

174 cells × 30 = 5,220 episodes at ≈12 s mean realtime ≈ 17 h serial, ≈ 4 h on 5 concurrent
processes. Output: the full success-vs-RTT and demos/hour-vs-RTT curves per arm and task; the
baseline knee (first RTT at which B success < 80 % of `zero`) per task.

### Tier 2: confirm (100 seeds per cell, paired)

Chosen after Tier 1: for each hypothesis, the sweep cell nearest the baseline knee plus the cell its
file gates on. Provisional list, to be re-pointed once the knee is known:

| Hypothesis | Confirm cells |
|---|---|
| H10 | capture sweep:400, capture geo_relay, peg sweep:400 (arm-only), capture zero (control: must show no gain) |
| H12 | capture sweep:250, peg leo_relay, plus D at L = 30 on the same two cells |
| H14 | capture sweep:400, capture geo_relay, capture zero (control) |
| H11 | peg leo_relay, peg sweep:400, capture sweep:500, each with B / P / Pg; one P cell with 5 mm pose noise + 33 ms lag |
| H20 | leo_relay, sweep:500 |

≈ 27 arms × 100 ≈ 2,700 episodes ≈ 9 h serial, ≈ 2 h on 5 processes.

### Why 30 and 100

Detecting a 10-point success difference unpaired at p ≈ 0.8, α 0.05 two-sided, power 0.8 needs ≈250
episodes per arm (n = [1.96·√(2·0.8·0.2) + 0.84·√(0.75·0.25 + 0.85·0.15)]² / 0.1² ≈ 250). That is not
affordable across 174 cells. Same-seed pairing turns it into a McNemar test on discordant seeds: with
a 10-point net shift the discordance rate is at least 12 %, and at 12–20 % discordance the required
n is 64–154. **100 paired seeds** therefore gives ≥80 % power for 10 points when discordance ≤ 15 %
and ≈65 % at 20 %; state the achieved CI, never just pass/fail. **30 seeds** detects ≈30 points per
cell, which is enough for the screen because the knee is estimated from the trend across seven RTT
points, not from one cell. For demos/hour (continuous, duration CV ≈ 0.3, paired ρ ≈ 0.5), 30 seeds
detects ≈20 % and 100 seeds ≈10 % at 80 % power.

### Metrics per cell

`success_rate` (95 % Wilson CI); `demos_per_hour` (spec: 3600 / mean successful wall) and
`demos_per_hour_gross` (data_pipeline §3.2, charges resets and failures; the only one H20 moves);
`rtt_p50`, `rtt_p95` measured from the echo minus sat dwell; safety = the four §6 counts
(`move_in_hold`, `vel_over`, `keepout`, `cage`) plus `hold` count and `hold_s` as diagnostics;
smoothness = SAL, LDLJ, `stall_frac`, `jerk_sum_sq` on the sat-side applied log (not on
`observation.state`, which is 30 Hz aliased to 50 Hz rows, V2). Per hypothesis: knock-away count
(H14, H10), measured command→applied lag by cross-correlation of `action` against `sat_*.npz`
`setpoint` (H12), `F_ASSIST` frame fraction and hand-back velocity peak (H11), tether-taut row
fraction (H20). Acceptance readout per SYNTHESIS §6 for every arm: success and demos/hour on
`leo_relay` as a fraction of that arm's own `zero` cell, and zero unsafe-motion events on all four
named profiles.

### Pass/fail readout per hypothesis

Quoted from each file's "How the testbed falsifies it"; the selection amendment says how the quoted
clause is evaluated against the working tree.

**H10** — "Profiles `zero`, `leo_relay`, `geo_relay` plus a symmetric sweep at 0/100/200/300/500/750/1000
ms; task capture (and peg-in-hole when it exists); `tau_h` 0.25; seeds 0–19; `Baseline` vs `Twin` on
identical seeds. REJECT if any of: (a) at `geo_relay` or any sweep point ≥ 500 ms, twin demos/h
< 1.10 × baseline; (b) twin success below baseline anywhere; (c) any unsafe-motion event or hold-count
increase; (d) twin jerk or SAL worse by > 20 % (smoothness is a curation signal, data_pipeline §2).
A null on `leo_relay` does not reject." Merged H09 clauses kept: "(b) on `leo_relay` nominal phantom is
worse than baseline by >5 points on either metric; (c) any unsafe-motion event appears under
phantom but not baseline on the same seed."
*Amendment:* sweep points are 250/400 instead of 200/300 (no criterion depends on them); `tau_h`
0.17 primary; SAL now exists. Added control (H13, V3, V4): REJECT if T beats B on the `zero` cell by
more than the seed-to-seed spread, because a gain there is against the operator model, not the link.
Read `peg` as the arm-twin result and `capture` as the object-extrapolation result.

**H12** — "Profiles `leo_relay`, `direct_gs`, `geo_relay`; task `capture`; seeds 0–29; `tau_h` 0.25;
`cmd_hz` 50. Arms: Baseline vs H12 with L ∈ {0, 30, 60, 90} ms and K ∈ {4, 8}. L = 0, K = 8 isolates
smoothing/ordering from extrapolation. Effective latency is measured offline as the cross-correlation
lag between `action` and `observation.state` in the recorded episode (both already logged);
prediction: H12 lag = baseline lag − L ± 10 ms. REJECT if, at the best L on `leo_relay`, demos/hour is
not ≥10 % above baseline with the 95 % bootstrap CI excluding zero, or success rate falls by >3 pts, or
any unsafe-motion event occurs (setpoint changes while `F_SAFETY_HOLD` is set; joint velocity above
clamp at resume), or `jerk_sum_sq` exceeds 2× baseline. Also reject if the measured lag reduction is
<0.5 L: the extrapolation is then being clamped, not applied."
*Amendment:* L = 0 is now identical to the baseline (seq-keyed), so the L set is {30, 60} with K = 8 (D
at 60 in Tier 1, 30 added in Tier 2). The lag is measured against the sat-side applied log, not
`observation.state`. The ≥10 % clause on `leo_relay` is expected to reject (2 % headroom, V3); report
it as written, and report the knee shift on the sweep and `peg` as the informative result. The
hypothesis is confirmed as a hider only if the knee moves right by ≥ 0.5·L with the CI excluding zero.

**H14** — "Task `capture`, `--tau-h 0.25`, `--cmd-hz 50`, seeds 0–19 per cell, baseline vs H14.
Profiles: `zero`, `leo_relay`, `geo_relay`, plus symmetric profiles at RTT 100, 250, 400, 500, 750, 1000
ms with `leo_relay` jitter. Log knock-away events (box speed > 3 cm/s while ungrasped) as the
mechanism check. Reject if: (i) at RTT ≥ 400 ms, H14 success ≤ baseline + 10 pp or demos/hour < 1.1×
baseline; (ii) on `leo_relay`, H14 demos/hour < 0.9× baseline, which rejects it as default-on; (iii)
after a forced 1 s outage, H14's resume joint-velocity peak equals the baseline's. Confirmation also
requires knock-away counts to fall where success rises."
*Amendment:* (iii) is void: the ramp limiter and the ground-side freeze are baseline properties now,
so B's resume peak is already ≤ `vmax`; report `vel_over` = 0 for both instead. Added `zero`-cell
control as for H10. Evaluate (i) at both 400 and 500 ms and on `peg`.

**H11** — "Task `capture`, seeds 0–49 per cell, `--max-s 30`, τ_h 0.25, cmd 50 Hz, tel 30 Hz. Cells:
{baseline, H11, H11-ground} × four profiles, plus an RTT sweep 0–1000 ms in 100 ms steps. H11-ground
runs the same primitive in `ground_step` from delayed telemetry; H11 − H11-ground is the measured value
of onboard compute. One cell adds 5 mm noise and 33 ms lag to the pose the primitive sees
(onboard-vision stand-in). REJECT if any of: (a) on `leo_relay`, success gain < 10 points with the 95 %
binomial CI covering zero, or demos/hour gain < 10 %; (b) any SYNTHESIS §6 unsafe-motion event
(setpoint change in hold, velocity above clamp at hand-back, keep-out exit, cage contact); (c)
robot-executed frames > 25 % of successful episodes; (d) H11-ground within 5 points of H11 on
`leo_relay`; (e) SAL/LDLJ of H11 successes worse than baseline's."
*Amendment:* the sweep is the seven-point one. Clause (a) is evaluated on **`peg` `leo_relay`** as the
headline (the insertion segment SYNTHESIS §6 predicts to fail) and on `capture` ≥ 500 ms; on `capture`
`leo_relay` it is expected to fail from the ceiling (V3) and is reported, not decisive. Clause (d) is
evaluated on the same cells. The result is labelled "onboard-compute branch, ground-truth pose = upper
bound; noise cell = lower bound" wherever it appears.

**H20** — "Profiles `zero`, `direct_gs`, `leo_relay`; seeds 0–19; `tau_h` 0.25 s; 20 chained episodes
per run versus 20 canonical episodes with a scripted teleop reset charged to wall time; RTT sweep
0–1000 ms. Metric: `demos_per_hour_gross = 3600 · successes / Σ(episode + reset wall)` per data_pipeline
§3.2. **Reject** if the chained design's gross demos/hour at `leo_relay` is < 1.10× the baseline's, or
its success rate < 0.90× the baseline's, or any unsafe-motion event, or if chained SAL/LDLJ
distributions are worse than the baseline's by more than the seed-to-seed spread (the release must not
turn demonstrations into chases)."
*Amendment:* the comparison is tether-in-cage vs cage-only (the cage exists); the ≥40 % claim in the
file is reported against the measured reset time, and the 1.10× clause is the gate. Report the
tether-taut row fraction so the "free 6-DoF" subset is countable.

## 4. Implementation notes per selected hypothesis

**H10 `Twin`** — `spaceteleop/strategies/twin.py`, `class Twin(Baseline)`. Interface: `ground_step(tel,
sp)` appends `(now, sp)` to a deque and returns `sp` unchanged; new `observe(tel, now)` (identity default
added to `Strategy`, one call added in `ground/loop.py` before `operator.step`) returns a copy of `tel`
with `q` replaced by the setpoint logged at `now − tau_h` and `obj[:3]` advanced by the finite-difference
velocity of the last two frames over `rtt/2 + dwell + interp_s`, OWD taken from the echoed
`last_cmd_t_send`; when `tel.flags & F_SAFETY_HOLD` or the echoed `last_cmd_seq` has not advanced for
two telemetry periods, return `tel` unchanged. `sat_step` inherited. Skip the keep-out clipping (V3:
theatre). Measured: success, demos/h, knock-aways, twin innovation (|predicted − next seen| per
frame). ≈70 lines + 4 for the seam. **Trap:** the phantom must be the setpoint sent at `now − tau_h`,
never the newest setpoint. The ground loop hands the operator a frame ≥ `tau_h` old; substituting the
newest setpoint removes the modelled human delay from the arm channel and wins on `zero` by the same
margin as on `leo_relay` (H13's artefact, confirmed by V3 and V4). The `zero` control cell exists to
catch exactly this.

**H12 `DeadReckon`** — `spaceteleop/strategies/deadreckon.py`, `class DeadReckon(Baseline)`, `sat_step`
only, kwargs `L=0.060, K=8, H=0.100`. Keep the last K entries (already seq-ordered); time base `t_i =
seq_i / cmd_hz`; eval time `t* = seq_n/cmd_hz + age + L` where `age = now − t_arr_n` of the **highest-seq**
packet; per joint a least-squares line over K points, slope clipped to ±`vmax`, evaluated at `t*`; jaw
passes through unextrapolated; if `age > H` return the baseline playout (freeze at newest), and let
the inherited hold/retract/ramp/clamp tail run on the result so `move_in_hold` and `vel_over` stay
baseline-guaranteed. Plumb `cmd_hz` into the strategy (1 line in `run.py`). Measured: lag by
cross-correlating `action` with `sat_*.npz` `setpoint`; success; demos/h; jerk on the applied log.
≈45 lines. **Trap:** the age must be measured from the arrival of the highest-seq packet, and the
fit must never see an arrival time. The controller now drops stragglers, but a burst of K packets
arriving together (post-spike drain) has near-identical arrival times and distinct seqs; fitting in
arrival time makes the slope explode, fitting in seq time makes it right. Also do not extrapolate
past `H`: a stale line continued for 300 ms would walk the arm into the hold at full speed, and the
freeze-then-ramp is the property §6 gates.

**H14 `Gain`** — `spaceteleop/strategies/adaptive_gain.py`, `class Gain(Baseline)`, kwargs
`L0=0.29, tau_h=0.17`. `ground_step` estimates `L̂ = rtt_ema + dwell + interp_s + tau_h` from the echo
(EMA 0.2 s) and sets `self.operator.speed = speed0 · min(1, L0/L̂)`; `run.py` passes the operator in
(`strategy_cls(operator=op)`, `Strategy.__init__` already takes kwargs). Sent setpoint unchanged.
Measured: success, demos/h, knock-aways, `s` time series. ≈35 lines + 5 (runner) + 5 (knock-away
counter in `sim._capture`). **Trap:** do not scale the joint increment in `ground_step`. The
operator's `servo` integrates its own `qc` and linearises the Jacobian there; scaling what is sent
leaves `qc` running (1 − s) of the travel ahead of the arm, so the DLS step is computed at a pose the
arm never visits and the strategy measures windup, not gain scheduling (V4). Scale the operator's
speed, and take `tau_h` as a known constant: the timestamp difference `now − last_cmd_t_send` contains
it only through the testbed's stale-frame mechanism and would read ≈0.07 s in flight.

**H11 `Terminal` / `TerminalGround`** (onboard-compute branch) — `spaceteleop/strategies/terminal.py`.
`Terminal(Baseline).sat_step` runs the baseline playout first; controller adds one line after
`sim.reset`: `strategy.sat = (m, d, st)`. Trigger, `capture`: newest setpoint has the jaw closed, not
grasped, true box-to-grasp-site distance < 0.08 m. Trigger, `peg`: newest setpoint's tip is below
`FIX_TOP + PEG_H` and the true lateral error is < 3·`CLEAR`. Action: one damped-least-squares step
per cycle from true `d.qpos` toward the box (or toward `HOLE − off` then down to `INSERT_Z`) at
≤ 0.07 m/s, jaw as commanded. Exit: grasped / inserted, 2 s elapsed, distance > 0.08 m, or the buffer
is empty (hold). On exit blend from the primitive's last output to the operator's newest setpoint
under the inherited ramp. Telemetry flag `F_ASSIST = 1 << 4` set while active and recorded per row
(3 lines in `proto`, 1 in `record`). `TerminalGround(Baseline)` runs the same code in `ground_step`
from the delayed `tel`. Add one line in `SyntheticOperator._capture`: on entering `carry`, `self.qc =
tel["q"]` (a human watching video re-anchors to what it sees). Measured: success, demos/h, assist
frame fraction, hand-back velocity peak, P − Pg. ≈70 + 20 + 5 lines. **Trap:** the hand-back. While
the primitive moves the arm, the operator's `qc` stays where it was, so the first post-primitive
setpoint is several centimetres away; without the blend and the `qc` resync the ramp limiter clips
for many cycles (`ramp_clip` climbs), the seen arm snaps back toward the stale `qc`, the box is
knocked out again, and the gain is cancelled by a chase, or `vel_over` fires and the arm fails §6.
Verify with `ramp_clip` ≈ 0 and `vel_over` = 0 on every P episode before reading the success column.

**H20 `capture_chain`** — `spaceteleop/sim/__init__.py`: a dead-band tendon on the box
(`springlength="0 0.20"`, stiffness 0.005, damping 0.01), targets A and B, a release that gives the box
the arm's velocity plus a seeded 2–4 cm/s push and swaps the target without touching the box;
`ground/operators.py`: a `release` phase after success (chained) and a `return_to_spawn` + release
phase (canonical reset) driven by the **same** `SyntheticOperator` instance with the same `speed`,
`tau_h` and `noise`; `metrics`: `demos_per_hour_gross`; `run.py`: `--task capture_chain` and
`--reset teleop|free`. Strategy is `Baseline` throughout, so this composes with every other arm.
Measured: gross demos/h, success, SAL/LDLJ, tether-taut row fraction, reset wall time. ≈30 + 25 + 10
+ 10 lines. **Trap:** the canonical reset must go through the link and the operator model. A reset
scripted at zero latency, at the velocity clamp, or by `sim.reset` teleport makes R a free parameter
and the ≥1.10× gate tautological (V4 on H15, V5 on H20). R is measured, on every profile, as the
wall time from success to the next episode's first command.

## 5. Rejected, deferred and no-hypothesis, one line each

- **H01** DEFERRED: the ×2.5 is a duty-cycle fold with 12 operators; the testbed can only check the geometry, so run the 20-line `orbit.py` rerun as an appendix and stop.
- **H02** DEFERRED: −14 ms of jitter on a 333 ms loop, spikes are synchronous across terminals, emulator iid jitter flatters it; one row of the outage-rate appendix sweep.
- **H03** NO-HYPOTHESIS: relay-video swap gains 9 ms during 21 % of the time and opens a blind-commanding window; the ground-side telemetry-silence freeze it exposed is adopted.
- **H04** NO-HYPOTHESIS: outage exposure caps any dual-link gain at 1.4–5.7 % of episodes; its outage-rate sensitivity sweep (1.7, 5, 12 h⁻¹) is adopted as an appendix.
- **H05** NO-HYPOTHESIS: `leo_relay` loss never produces a gap over 160 ms against a 300 ms hold; seq-keying is already in the baseline.
- **H06** NO-HYPOTHESIS: a lost 50 Hz command costs ≤1.4 mm of path; piggybacking K = 1 is a transport-baseline note, not a hypothesis.
- **H07** REJECTED: nominal gain is 16 ms of 333; the saturated arm measures the emulator queue against a state-consuming operator, not a human watching late video.
- **H08** MERGED-INTO-H12: its whole effect table is the seq-keying the baseline now has; adaptive D adds a 60 ms playout step at every 15 s spike.
- **H09** MERGED-INTO-H10: same mechanism and sources, but its phantom removes `tau_h` and its criterion (d) rejects its own success.
- **H13** NO-HYPOTHESIS: correct null on `leo_relay`; its `zero`-cell artefact rule is now a rejection clause for H10 and H14.
- **H15** MERGED-INTO-H20: reset time is author-chosen so >10 % is guaranteed; an onboard macro that carries the object is the excluded branch; zero effect on the gated ratio.
- **H16** MERGED-INTO-H20: same mechanism as H15 with a session-mode controller and subprocess launcher it does not budget; 7.5 h realtime per sweep.
- **H17** NO-HYPOTHESIS: measured null for segmentation below 0.75 s; its jaw-scale envelope recommendation is already in the tree.
- **H18** NO-HYPOTHESIS: relabeling moves no collection-time metric; the sat-side applied log it asked for is already in the tree.
- **H19** REJECTED: replays are robot-executed and `Replay.sat_step([])` moving the arm is an unsafe-motion event by the §6 definition; the reset it depends on is a teleport.
