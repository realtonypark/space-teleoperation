# Audit: strategies, ground loop, runner (Phase 5 adversarial verification)

Scope: `spaceteleop/strategies/{base,baseline,twin,deadreckon,adaptive_gain,terminal}.py`,
`spaceteleop/ground/{loop,operators}.py`, `spaceteleop/run.py`, read against PROGRAM.md,
SYNTHESIS §5–§8 and selection.md §3–§4. Code at commit `8856bf9`, unmodified. Scratch scripts
and the under-load measurement cell are under the session scratchpad `audit/` directory
(`dr_lead.py`, `raw_compare.py`, `live_probe.py`, `terminal_hold.py`, `zero_load/`).

Date: 2026-09-12, while the Tier-1 matrix was running (12 `spaceteleop.run` processes, load
average 7.9–8.7 on 14 logical cores).

## Findings

| ID | file:line | Severity | What | Biases which strategy, how | Proposed fix |
|---|---|---|---|---|---|
| F1 | `strategies/deadreckon.py:43` | MAJOR | The line is evaluated at `seq_n/cmd_hz + age + L`, i.e. at "now" in sequence time plus `L`, while Baseline plays at `now − interp_s`. Effective lead over Baseline is **`L + 30 ms`**, not `L`: D = 90 ms, D30 = 60 ms. The selection.md amendment "L = 0 is now identical to the baseline" is false (L = 0 still leads by 30 ms). | Favours H12: the "lag reduction ≥ 0.5·L" and "knee moves right by ≥ 0.5·L" clauses are scored against L = 60 while the arm actually leads by 90 ms, a 1.5× easier bar. Also conflates "remove the playout buffer" with "extrapolate". | Do not touch the running matrix. In the readout, score H12 against `L_eff = L + interp_s` (90 / 60 ms). For Tier 2, either evaluate at `ts[-1] + age − self.interp_s + self.L − tm` so the lead is exactly `L`, or state `L_eff` in the hypothesis. |
| F2 | `run.py:123` with `sat/controller.py:127` (`linger_s=1.0`) | MAJOR | `duration_s` is `time.monotonic() − t0` around `episode()`, which waits for the satellite's 1.0 s linger after the success frame. Every episode's duration is inflated by a constant **+1.00 s** (printed 9.1/7.8/8.2/15.0 s vs last ground row 8.06/6.80/7.20/14.0 s). | Equal for every arm, but `demos_per_hour = 3600/mean(duration)` so every arm-vs-baseline ratio is compressed toward 1. On `zero` (true mean ≈ 6.9 s) a true 1.10× reads 1.087× and fails the H10/H12/H14/H20 ≥ 1.10× gates; the "not worse than 0.9×" gates get easier. The effect is largest on the short (fast) cells, i.e. exactly where hiders would show. | Compute the spec `demos_per_hour` from `rows[-1]["timestamp"]` (ground wall to the success frame) or from the controller's `duration` (sim time); keep the wall clock for `demos_per_hour_gross` and for R. Can be applied post hoc from the npz files without rerunning. |
| F3 | `strategies/twin.py:55` and selection.md §4 H10 amendment ("REJECT if T beats B on the zero cell") | MAJOR (readout) | The phantom is honest: it is the setpoint sent at `≤ now − tau_h` (unit-tested), it never reads true state, and it falls back on hold / stalled echo. But it removes the **link-independent** arm-channel lag too: playout 30 ms + telemetry sampling ≈ 27 ms + servo settling. Measured phantom-vs-seen grasp-site gap on `zero`: **9.5–9.9 mm p50** (≈ 140 ms at the 7 cm/s operator speed); on `sweep:250`: 25.7 mm. The partial `zero` cell (30 seeds, both arms) shows T/B demos/h ≈ 1.08 on the 18 both-success seeds, success 19 vs 20 (duration proxy). | The `zero`-cell rule as written cannot separate H13's artefact (using the newest setpoint would remove `tau_h` = 170 ms, ≈ 12 mm more gap) from a legitimate, link-independent gain. Read literally it rejects H10 for the wrong reason; read loosely it credits H10 with a gain it also has at zero latency. | Keep the honesty check (phantom ≤ now − tau_h; add the phantom-gap diagnostic ≈ 10 mm on zero as the fingerprint, ≈ 22 mm would be the artefact). Score H10 as a latency hider by the ratio of ratios: (T/B at profile) ÷ (T/B at `zero`). |
| F4 | `strategies/twin.py:51,66` | MINOR | `innov` compares a prediction made with horizon `lead = rtt/2 + dwell + interp_s` against the next frame, which arrives ≈ 33 ms later. It therefore measures ≈ v·(lead − 33 ms), not prediction error. Measured: `zero` lead 2.8 mm / innov 1.3 mm; `sweep:250` lead 9.5 mm / innov 8.8 mm. | Makes the twin's "error" look larger at high RTT and says nothing about extrapolation quality. Diagnostic only, no gate depends on it. | Store `(pred, t1 + lead)` and score it against the frame whose `t_send` is nearest that instant, or relabel the number "lead". |
| F5 | `strategies/adaptive_gain.py:28,53` | MINOR | `L0 = 0.29` is a constant, but the measured `zero` loop delay is **L̂ = 232 ms p50** at `tau_h` 0.17 (rtt_est 23 ms + dwell + 30 + 170). So Gain has a 58 ms dead band: on `leo_relay` `s` p50 = 1.000 (min 0.88), i.e. **G ≡ B on `leo_relay`**. At `tau_h` 0.25 (block E) L̂_zero = 312 ms > 290, so `s` ≈ 0.93 at zero-equivalent delay and ≈ 0.81 on `leo_relay`. | Block A: H14 clause (ii) ("demos/h < 0.9× baseline on leo_relay rejects default-on") passes trivially because G does not act there. Block E: G is a different controller than in block A (it scales where block A's does not), so E vs A is not a `tau_h` comparison. Neither direction inflates G at ≥ 400 ms (s ≈ 0.46 there). | Make `L0` `tau_h`-relative (`L0 = 0.12 + tau_h`, the measured machine loop plus the human) or pass it per cell; log `s` per episode so clause (ii) is read as "no effect" rather than "not worse". |
| F6 | `strategies/adaptive_gain.py:43-44,55` with `run.py:74,106` | MINOR (latent) | `speed0` is captured from `operator.speed` at the first `ground_step` of each episode. In `capture_chain` the operator instance persists across episodes and is left at the scaled speed, so a fresh Gain per episode compounds `s`. | Not in the current matrix (block C runs `baseline` only). Would bias a Gain × chain cell downward. | `speed0 = getattr(operator, "speed0", None) or operator.speed` and store it on the operator, or restore `operator.speed` at episode end. |
| F7 | `strategies/terminal.py:167`, `metrics/__init__.py:114` | MINOR | `assist_frac = _na / _n` where `_n` counts every satellite control cycle from the first command to `done_at`, hold cycles included; `_agg_ev` averages `_frac` over **all** episodes. H11 clause (c) is "robot-executed frames > 25 % of **successful** episodes". | Failures (which reach `max_s` with little assist) dilute the fraction, making P look less robot-driven than its successes are. | Score clause (c) from the sidecar `assist` column restricted to successful episodes. |
| F8 | `sat/controller.py:97`, `strategies/terminal.py:197-215` | MINOR | The sidecar `assist` column and the `F_ASSIST` telemetry flag come from the satellite-side `strategy.assist`. For Pg the primitive runs on the ground, the sat copy is a plain Baseline, so the recorded mask is all-False for every Pg episode. Only the `ev` max in `run.py:88-90` carries Pg's real `assist_frac`. | Dataset mislabel for Pg (robot-executed frames recorded as human). Does not affect the P − Pg success/throughput readout. | Set a command flag from `TerminalGround.ground_step` (proto has a spare `flags` byte) and let the controller OR it into `assist`. |
| F9 | `strategies/terminal.py` (hand-back), `metrics/__init__.py:107` | NOTE | `vel_over` cannot fire for any arm: `Baseline.sat_step` bounds Δq ≤ vmax·min(dt, 0.05) and `_vel_over` divides by the real dt ≥ that. The amendment already says B's resume peak is ≤ vmax; this confirms "vel_over = 0" is a tautology, not evidence, for P's hand-back too. `handback_peak` and `ramp_clip(P) ≤ ramp_clip(B)` are the informative pair. | None (equal), but do not cite `vel_over = 0` as a safety result. | Report `handback_peak` next to B's own peak on the same seeds. |
| F10 | `ground/loop.py:54`, `strategies/twin.py:48,64-65` | NOTE | `leo_relay`/`sweep` allow downlink reordering; `hist` is arrival-ordered, so `seen` can step back to an older frame for one tick. Same for every arm. Twin's finite-difference guard (`dt > 1e-6`) yields v = 0 for that frame. | None across arms. | None needed. |
| F11 | `strategies/deadreckon.py:39` | NOTE | Sequence time assumes exactly 1/cmd_hz between sends. Ground ticks measured p50 19.9 / p95 23.5 / max 33–65 ms, so after a slipped tick the fitted slope overestimates true velocity by the slip fraction for K = 8 packets (≤ ~5 % transiently). | Tiny, both directions, ramp-bounded. | None. |
| F12 | `sat/controller.py:127`, sidecar `hold` column | NOTE | After the success frame the ground stops sending and the satellite lingers 1 s, so the last ≈ 700 cycles of every sidecar log are flagged `hold` (2136 hold cycles across 4 `zero` episodes with `hold_s` = 0.00 on the ground). `ev` counters are frozen at `done_at`, so `hold`, `hold_s`, `move_in_hold` are unaffected. | None; cosmetic for a dataset consumer reading the sidecar. | Trim the sidecar at `done_at` or document the tail. |
| F13 | timing under load (`ground/loop.py:47`, `run.py`) | NOTE (no finding) | Measured with 13 concurrent `run.py` processes: `zero` baseline 4 episodes rtt_p50 **9.9 ms**, p95 18.6, success 4/4; the running matrix `zero` cell (30 episodes, same load) 10.2 / 19.1; the earlier sanity table 9 / 21. Seeds 0–3 durations match the matrix cell to 10 ms (8.06/6.80/7.20/14.0 s). Satellite cycle p50 1.28 ms in both. | Load does not inflate RTT, dwell or success. The ≈ 10 ms `zero` RTT is the ground loop's 20 ms tick quantisation (mean +10 ms), not scheduling. | None. Keep ≤ ~12 concurrent cells; sat-cycle max reaches 63 ms on `leo_relay` (ramp's `min(dt, 0.05)` absorbs it). |

Checked and clean (no finding):

- Twin never reads true state: inputs are `self.sent` (its own wire), `tel` fields, and the ground clock (`twin.py:41-67`). Hold and stalled-echo fallbacks return the raw frame. The sat-side Twin copy only runs the inherited Baseline `sat_step`.
- DeadReckon: fit in sequence time (`deadreckon.py:39`); `age` is from the highest-seq packet (`buf[-1]`, strictly increasing seq, stragglers dropped in `controller.py:78`); `_playout` is not called while held (`baseline.py:35`), so it cannot move the arm in hold; slope clipped to ±vmax and the result goes through the ramp; jaw unextrapolated; `age > H` returns the frozen baseline playout.
- Gain scales `operator.speed` only, never the wire (`adaptive_gain.py:55`, returns `target` unchanged); L̂ uses only echoed fields and the ground clock; `tau_h` subtracted from the echo and added once to L̂ (`:48-53`): net L̂ = (now − last_cmd_t_send) + interp_s, counted once. Sat copy has `operator=None` and is a no-op.
- Terminal: trigger needs the operator's newest jaw-close (`terminal.py:106`, `cmd = buf[-1][2]`) or commanded descent (`:100`); during a stale buffer (> timeout_s) the primitive stands down, `assist` = False, `held` = True, `move_in_hold` = 0, output == `last` (scratch `terminal_hold.py`); hand-back is crossfaded and ramp-limited. TerminalGround uses only `tel["q"]`, `tel["obj"]`, `tel["flags"]` and the model.
- No cross-episode state: `run.py:70,77` build fresh sat and ground strategy instances per episode; `_Prim`, `TerminalGround`, `Twin`, `Gain` state is per instance. Operator model is one class with no strategy knowledge; the carry-phase `qc` resync (`operators.py:107`) is unconditional, so every arm gets it.
- Seeds: `experiments/matrix.py:182` passes `--seed 0` to every cell; `run.py:104` derives `seed = 0 + 1000·arm + k`; Link, `sim.reset` and the operator are all seeded from it. Pairing is by seed (link RNG draws are per packet, so the 15 s structure realisation drifts with packet timing across arms, as expected).

## Evidence

### F1 DeadReckon leads by L + interp_s

`dr_lead.py`: a 16-packet buffer, joint 0 at 1 rad/s, so an output offset in rad reads as
lead in seconds. `Baseline._playout(buf, now − 0.03)` vs `DeadReckon._playout` at the same `t`:

```
age=   0ms L=  0ms  lead over baseline =   30.0 ms
age=   0ms L= 30ms  lead over baseline =   60.0 ms
age=   0ms L= 60ms  lead over baseline =   90.0 ms
age=  30ms L= 60ms  lead over baseline =   90.0 ms   (age-invariant, 10 ms row identical)
```

Code: `now = t + self.interp_s` (`:34`) then `out = pm + slope * (ts[-1] + age + self.L - tm)`
(`:43`). The `+ interp_s` added at `:34` is never taken back out of the evaluation instant.

### F2 Linger in `duration_s`

`run.py:108-123`: `t0` before `episode()`, `duration = time.monotonic() − t0` after it.
`episode()` runs `th.join(5.0 + grace)` and the controller exits only when
`now − done_at > linger_s` (`controller.py:127`, `linger_s=1.0`).

Under-load `zero` cell, printed vs last ground row `timestamp`:

| seed | printed duration_s | last row t | delta |
|---|---|---|---|
| 0 | 9.1 | 8.06 | +1.04 |
| 1 | 7.8 | 6.80 | +1.00 |
| 2 | 8.2 | 7.20 | +1.00 |
| 3 | 15.0 | 14.00 | +1.00 |

Ratio compression: for the 18 both-success seeds of the partial `zero` cell (F3), true means
B 6.94 s / T 6.41 s give 1.083×; with +1 s each they give 7.94/7.41 = 1.072×.

### F3 Twin gain on `zero`

`live_probe.py` (an instrumented `Twin` subclass over the real runner; probe only, code unmodified):

```
zero      seed 0  phantom-vs-seen grasp-site gap mm: p50=9.5  p90=11.0   obj lead mm: p50=2.84  rtt_p50=12.0
zero      seed 1  phantom-vs-seen grasp-site gap mm: p50=9.9  p90=11.1   obj lead mm: p50=3.30  rtt_p50=9.1
sweep:250 seed 0  phantom-vs-seen grasp-site gap mm: p50=25.7 p90=28.8   obj lead mm: p50=9.50  rtt_p50=255.9
```

Partial matrix cells `A_capture_baseline_zero_tau0.17` and `A_capture_twin_zero_tau0.17`
(30 episodes each, success proxied by last-row time < 19 s since `stdout.txt` is written only
at cell end):

```
baseline zero: 20/30 success proxy   twin zero: 19/30
discordant seeds: 3 (B ok, T fail), 5 (B ok, T fail), 15 (T ok, B fail)
both-success (18 seeds): mean end  B 6.94 s   T 6.41 s   T/B demos/h 1.083
```

Where the gap comes from: the seen frame is the newest with `ts ≤ now − tau_h` (`loop.py:54`),
so it is on average ≈ 10 ms (tick) + ≈ 17 ms (telemetry period) older than `tau_h`, its `q`
was applied `interp_s` = 30 ms behind the newest arrival (`baseline.py:36`), and the position
servo settles behind the applied setpoint. None of that is link delay; all of it is what the
phantom (the setpoint at `now − tau_h`) skips. The artefact the amendment names (newest
setpoint) would additionally skip `tau_h` = 170 ms ≈ 12 mm more; the unit test
`test_twin_phantom_is_the_setpoint_sent_tau_h_ago` guards that.

### F4 Innovation measures the lead

Same probe: `innov_m` (mean |pred − next seen|) vs the applied object lead (|pred − seen|):
`zero` 1.3 mm vs 2.8 mm; `sweep:250` 8.8 mm vs 9.5 mm. `twin.py:51` scores `self.pred` (made
at horizon `lead`, `:62`) against the next distinct frame (≈ 33 ms later, `:48-52`).

### F5 Gain dead band and `tau_h` coupling

`live_probe.py` (instrumented `Gain`, logs `rtt`, L̂, `s` per tick):

```
zero       rtt_est p50= 23 ms  lhat p50=232 ms  s p50=1.000  s min=1.000   loop rtt_p50=12.3 ms
leo_relay  rtt_est p50= 65 ms  lhat p50=278 ms  s p50=1.000  s min=0.882   loop rtt_p50=51.7 ms
sweep:400  rtt_est p50=419 ms  lhat p50=631 ms  s p50=0.459  s min=0.414   loop rtt_p50=404.9 ms
```

`L0 = 0.29` (`adaptive_gain.py:28`) vs L̂_zero = 0.232: `s = min(1, 0.29/L̂)` stays 1 until
L̂ > 290 ms, i.e. until RTT ≈ 80 ms. With `tau_h = 0.25` passed in (`run.py:77`) L̂ shifts by
+80 ms while `L0` does not: L̂_zero = 312 ms → s = 0.93; L̂_leo ≈ 358 ms → s = 0.81. The
`rtt_est` exceeding the loop's `rtt_p50` by ≈ 11 ms is the seen frame's staleness beyond
`tau_h`, which the operator really does look at, so L̂ is honest.

### F6 Chained operator reuse

`run.py:105-107`: `if op is None or not chain: op = SyntheticOperator(...)`, so under
`capture_chain` the same operator serves every episode. `run.py:77` builds a new ground
strategy per episode; `adaptive_gain.py:43-44` sets `speed0 = operator.speed` on its first
call, which is the previous episode's `speed0 · s`. Block C is baseline-only, so unexercised.

### F7 / F8 Assist accounting

`terminal.py:132,136,167`: `_n` increments on every `_step` call, `_na` when the primitive
returns a setpoint; `_step` is called on every satellite cycle with a non-empty buffer
(`terminal.py:179-186`), hold cycles included. `metrics/__init__.py:113-114` averages `_frac`
over all episodes. `controller.py:97` reads `strategy.assist` on the satellite instance; for
`terminal_ground` that instance never sets it (`TerminalGround` only overrides
`ground_step`), so `satlog[...][5]` and `F_ASSIST` are False for Pg. `run.py:88-90` recovers
`assist_frac` from the ground instance by `max`, which is why the printed fraction is right.

### F9 `vel_over` tautology

`baseline.py:41-45`: `dt = min(now − t_prev, 0.05)`, `lim = vmax·dt`, every emitted joint moves
≤ `lim`. `metrics/__init__.py:104-107`: velocity = Δq / real dt, real dt ≥ `min(dt, 0.05)`,
threshold `vmax·1.05`. Every strategy's output passes through this tail (`terminal.py:192`
feeds the primitive's output back through `super().sat_step`).

### F12 Sidecar hold tail

Under-load `zero` cell, sidecar logs: 2136 `hold` cycles across 4 episodes while the ground
`hold_s` is 0.00 and `ev["hold"] = 0`; per episode ≈ 530 cycles at 1.3 ms ≈ 0.7 s = linger
(1.0 s) − timeout (0.3 s).

### F13 Timing under load

Under-load measurement: `uv run python -m spaceteleop.run --profile zero --task capture
--strategy baseline --episodes 4 --seed 0` with 12 matrix processes running (load average
7.89 at start, 8.73 at end, 14 logical cores):

```
arm 0 ep 0 seed 0 success=True 9.1s rtt_p50=9ms  hold=0.00s unsafe=1 frames=396
arm 0 ep 1 seed 1 success=True 7.8s rtt_p50=10ms hold=0.00s unsafe=0 frames=333
arm 0 ep 2 seed 2 success=True 8.2s rtt_p50=11ms hold=0.00s unsafe=0 frames=353
arm 0 ep 3 seed 3 success=True 15.0s rtt_p50=10ms hold=0.00s unsafe=1 frames=693
rtt_p50_ms 9.9   rtt_p95_ms 18.6   rtt_max_ms 25.7   success_rate 1.00   demos_per_hour 359.3
```

Comparison from the raw npz files (`raw_compare.py`):

| cell | n | rtt50 mean | rtt95 mean | tick p50 / p95 / max ms | sat cycle p50 / p95 / max ms |
|---|---|---|---|---|---|
| audit `zero`, under load | 4 | 9.9 | 18.6 | 19.9 / 23.5 / 33.3 | 1.29 / 1.43 / 16.8 |
| matrix `zero` seeds 0–3 (same load) | 4 | 9.8 | 19.3 | 19.9 / 23.5 / 31.7 | 1.28 / 1.40 / 24.1 |
| matrix `zero` all | 30 | 10.2 | 19.1 | 19.9 / 23.4 / 40.4 | |
| matrix `sweep:0` all | 30 | 16.2 | 35.2 | 19.9 / 23.5 / 65.5 | |
| matrix `leo_relay` all | 30 | | | | 1.28 / 1.41 / 62.7 |
| results.md sanity (2 ep, earlier) | 2 | 9 | 21 | | |

Seeds 0–3 end times: audit 8.06 / 6.80 / 7.20 / 14.00 s; matrix 8.06 / 6.80 / 7.20 / 14.02 s.
`sweep:0` reads 16 ms because it carries the relay jitter (SD 14 / 11 ms) at zero base delay,
which is the intended "structure minus base" point. Load does not inflate RTT, dwell or
success on `zero`; the ≈ 10 ms floor is the ground loop's 20 ms tick (`loop.py:33,47`: the
echo is timestamped when the tick drains the socket, mean +10 ms).

## Implication for the readout

Nothing found lets a strategy read true state, move the arm in hold, or beat the velocity
clamp. Three things bias the numbers the gates read: the H12 arm leads by 30 ms more than its
label (F1), every demos/hour ratio is compressed toward 1 by a constant +1 s per episode
(F2), and the twin's `zero`-cell gain is link-independent by construction rather than the
newest-setpoint artefact, so it must be subtracted, not used as a rejection (F3). All three
are fixable in the aggregation from the npz files already on disk without rerunning Tier 1;
the Gain `L0` coupling (F5) means block E's G is a different controller than block A's and
should be re-pointed before Tier 2.
