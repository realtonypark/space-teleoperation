# Testbed audit (Phase 5, adversarial verification)

Scope: `spaceteleop/link/{emulator,profiles,orbit}.py`, `proto/`, `sat/controller.py`, `sim/__init__.py`,
`record/`, `metrics/`, `experiments/{matrix,aggregate}.py`, against PROGRAM.md, TESTBED_SPEC.md,
SYNTHESIS §5–§8 and network_emulation.md. No file under `spaceteleop/` or `experiments/` was modified.
Scratch scripts: `scratchpad/audit/{audit_emu,audit_sim,audit_metrics,audit_peg}.py`, run with
`uv run python` from the repo root while the Tier‑1 matrix was running (8 `run.py` processes), so every
timing number below was taken under the same CPU load as the experiments themselves. Recorded cells
under `docs/experiments/raw/` (blocks A, B, C as of 2026‑09‑12 21:00) were read, never written.

## Findings

| ID | file:line | Severity | What | Effect on results | Proposed fix |
|---|---|---|---|---|---|
| T01 | `sim/__init__.py:272,283-284` | CRITICAL | Capture is keyed on the jaw **command** (`d.ctrl[JAW] < 0.6`) inside a 20 mm sphere, never on the physical jaw or the box's position relative to the pads. Measured: box 18 mm from the site, jaw `qpos` = 0.0 rad (fully open), `grasped=True` at step 0 of the close command; also true for 19 mm below, beside or in front of the site. | `capture` success means "operator sent close while the box centre was within 20 mm in any direction", not a grasp. Physical close takes 0.19 s (to half) / 0.31 s (fully) plus the 2 rad/s ramp; a moving box would leave a real jaw. Success is inflated at every latency, most for arms that time the close (Terminal) and least for the ones that must chase. | Require `d.qpos[JAW] < thr` (actual) AND the box inside the pad gap in the site frame (|x|,|z| < pad half‑width, y within the finger reach), or two pad contacts. Keep the 20 mm envelope as the trigger, not the predicate. |
| T02 | `link/emulator.py:111-112`, `matrix.py:38-50` | CRITICAL (for the safety claim) | The hold/retract path is never exercised by the matrix. Poisson 1.7 h⁻¹ gives P(outage in a 20 s episode) = 0.9 % per direction; for seeds 0–29 exactly 2 of 60 direction‑schedules contain a blackout inside 30 s, both starting at 24.83 s (after the 20 s episode). GEO LOS: 0/30 seeds. Every completed cell reports `hold=0`, `safety_hold_s 0.00`; the satellite log of the leo cell has 14 844 hold cycles, all in the post‑episode linger, 0 inside an episode. | "Zero unsafe motion on dropout" (PROGRAM.md acceptance) is untested: `move_in_hold=0` and `vel_over=0` are vacuous because no hold ever started while an operator was driving. | Add a dropout block: a profile field `outage_at_s`/`outage_len_s` (deterministic blackout inside every episode), or a `stress` profile with `outage_rate_per_h` ≈ 600 so each episode sees ~3 outages; report the four §6 counters from that block. |
| T03 | `link/emulator.py:68-70,116-132` | MAJOR | The 15 s structure is phase‑locked to `Link.start()` (`t0` = link start, no random phase; measured phase at start 0.0004 s). The first command reaches the satellite 0.23–0.33 s after start, after the 0.140 s spike; the next boundary is at 15 s, and every successful leo episode ended ≤ 14 s. 11/30 leo episodes crossed 15 s, all of them 20 s failures. | On `leo_relay` (the acceptance profile) the +74 ms spike, the end bump and the 31 % burst‑loss second never touch a live command in a successful episode: the profile the results are gated on is effectively "P2‑clean + jitter + 0.5 % loss". The spike layer is verified to work (table below) but contributes nothing to the numbers. | `self.t0 -= rng.random() * p["period_s"]` in `_Dir.__init__` (same idea as `self.phase` for the periodic outage), so each episode samples a uniform period phase. |
| T04 | `ground/loop.py:47,67-72` | MAJOR | `rtt_ms` subtracts the satellite dwell but not the ground's own poll dwell: telemetry arriving during `time.sleep(slack)` is stamped at the next 50 Hz tick. Zero cell, 18 k rows: rtt p5/p25/p50/p75/p95 = 2.6/5.0/10.0/14.0/19.1 ms with a measured link OWD of 0.6 ms/direction, i.e. U(0, 20) + 0.6. direct_gs p50 39.5 vs 30 nominal (+32 %), leo 51.8 vs 48 (+8 %, masked because the log‑normal median is 3.5 ms below the mean), geo 610 vs 600. | `rtt_p50` is not the link RTT the docstring claims; it is link RTT + 10 ms mean. Absolute RTT columns and the knee's x‑axis (nominal) disagree by 10 ms; `tests/test_e2e.py:48` (±30 %) and `:56` (±25 %) pass by tolerance, the spec's ±20 % would fail on direct_gs. | Replace the sleep with `select.select([sock], [], [], slack)` and stamp on wake, or record `t_rx` in the drain and subtract `now - t_rx` like the satellite dwell. |
| T05 | `metrics/__init__.py:84,95-96` | MAJOR | SAL, LDLJ and `stall_frac` are computed on `observation.state` at 50 Hz, which is a sample‑and‑hold of 30 Hz telemetry: 40–47 % of consecutive rows are exact repeats in every recorded cell. Synthetic check: the same minimum‑jerk movement read through the hold gives stall_frac 0.51 vs 0.24, LDLJ −14.5 vs −5.2, SAL −2.07 vs −1.38. | `stall_frac` has a floor of ≈0.4 (zero cell 0.47) that has nothing to do with waiting; LDLJ is dominated by the hold artefact; SAL is shifted. Cross‑profile ordering may survive, magnitudes and the "stall" reading do not. | Build the speed profile from frames where the telemetry changed (dedupe on `tel seq`, dt = 1/tel_hz), or from the satellite log setpoints (1 kHz). |
| T06 | `sat/controller.py:100`, `matrix.py:214-235` | MAJOR | Control‑loop stalls under CPU contention: 8 cells contain 39–47 satellite cycles with dt > 0.2 s (max 2.4 s) in 3–5 episodes each, and 40–62 ground gaps > 0.1 s: `deadreckon` geo/sweep250/400/500/750/1000, `gain` direct_gs/geo/leo/**zero**, `twin` sweep750/1000. Baseline and terminal cells: 0. | After a stall the buffered commands drain in one burst (gap ≈ 0, no hold), the sim is stepped 1–2 s at once against one setpoint, and the ramp then chases. Those episodes are neither the profile nor the strategy; `gain`'s own zero cell is affected, so its acceptance ratio is biased. | Re‑run the 8 cells (they are resumable by deleting `summary.json`); have `run.py` assert `max(diff(satlog.t_ns)) < 0.1 s` and mark the episode `stalled`; lower `--jobs` while other work runs. |
| T07 | `sim/__init__.py:41-42,207-210,263`, `aggregate.py:165-182` | MAJOR | `cage` (arm touching the cage) is non‑zero at zero latency: baseline zero 12 events, direct_gs 12, leo 12, geo 32, sweep0 11; twin zero 13. The box spawns 10–16 cm from the −y wall and drifts 2–4.5 cm/s, so the operator's chase runs the arm into the wall. | SYNTHESIS §6 "zero unsafe‑motion events on all four profiles" is failed by every arm on every profile, so `unsafe_named` cannot discriminate strategies and the acceptance readout is always "fail". The three link‑caused counters are all 0 everywhere (vacuously, see T02). | Report `cage` and `keepout` split by cause (during hold/resume vs. operator‑driven); gate §6 on the link‑caused window; or move the spawn box off the wall. |
| T08 | `link/profiles.py:75-77`, `link/emulator.py:158` | MINOR | `sweep:0` clips the log‑normal jitter at 0 ms: realised base OWD 6.5 up / 5.4 down (RTT ≈ 12 ms, nominal 0), SD 10.5/8.3 instead of 14/11. sweep:0 cells read rtt_p50 16 ms vs zero 10 ms. | The first sweep point is not at 0 ms and has a different jitter shape; knee interpolation uses the nominal 0. Small (12 ms). | Label the sweep x‑axis with measured RTT, or shift `sweep(r)` so the jitter floor is not clipped (e.g. min base 20 ms) and say so. |
| T09 | `run.py:108,123` | MINOR | `duration_s` = wall time from before `Link.start()` to after the npz write: includes the 1 s linger, thread join and the write. Failed episodes read 21.0 s for a 20 s cap. | `demos_per_hour` and `_gross` are biased low by ≈1 s per episode (≈10 % at 9 s); the leo/zero ratio bias is < 2 %. | Use `success_wall - t_first_cmd` for successes (both already in the summary) and `max_s` for failures. |
| T10 | `aggregate.py`, `metrics/__init__.py:120-136` | MINOR | SYNTHESIS §6 asks for `direct_gs` throughput per pass; nothing reports it. The pass layer works (duty cycle 20.6 %, 33 passes/day, first gap at 540 s) but a 20 s episode never leaves the first pass. | `direct_gs` demos/hour is reported as if the link were continuous (×4.85 too high as a wall‑clock rate). | Print `demos_per_pass = demos_per_hour × pass_on_s / 3600` for `direct_gs` in `metrics.table`. |
| T11 | `record/__init__.py:63,76-82` | MINOR | Not loadable by `lerobot` v2.0/v2.1 as written: `info.json` lacks `total_tasks`, `total_videos`, `total_chunks`, `chunks_size`, `splits`, `data_path`, `video_path`; features lack `names` and there is no `task_index` feature; no `meta/tasks.jsonl`; no `meta/stats.json` (v2.0) or `meta/episodes_stats.jsonl` (v2.1); data is `.npz`, not `data/chunk-000/episode_*.parquet`; `timestamp` is wall clock and drifts from `frame_index/fps` by 0.19–0.75 s per episode (loader tolerance 1e‑4 s); declared `fps: 50`, realised 46.4–49.6 frames/s. | A real loader fails at `info["data_path"]` before touching data; after fixing that, at the missing parquet, then `tasks.jsonl`, then `check_timestamps_sync`. The module docstring calls this "‑shaped", which is accurate; the TESTBED_SPEC wording "LeRobot‑v2‑compatible" is not. | Write `timestamp = frame_index / fps` and keep the wall clock in `t_wall`; add `tasks.jsonl`, `task_index`, the missing info keys and per‑episode stats; convert npz→parquet in the promised converter. |
| T12 | `link/emulator.py:61-62` | NOTE | Down direction seeds `Random(seed+1)`: episode k's downlink stream is episode k+1's uplink stream (seed 14 down and seed 15 up draw the identical outage at 24.83–25.39 s). | Adjacent episodes share phase/shift/outage draws across directions; no effect on the paired design, slight loss of independence. | `Random(2*seed)`, `Random(2*seed+1)`. |
| T13 | `metrics/__init__.py:46` | NOTE | SAL uses `padlevel` 2; the SPARC reference uses 4. Minimum‑jerk: −1.376 vs −1.406; two sub‑movements −2.210 vs −2.245. LDLJ matches the reference to 0.03. | Constant offset ≈ 0.03; ordering preserved. | Use `+ 4`. |
| T14 | `link/emulator.py:175-177` | NOTE | Bandwidth is a serialisation model with `rel = max(rel, next_free)`: propagation is dropped while queued. At 2.5 kB/s commands against 32 kB/s (direct_gs up) it never queues. | None at these rates. | `rel = max(now, next_free) + len/bw + delay` if a video budget is ever driven through it. |
| T15 | `sim/__init__.py:328-343` | NOTE | Peg predicate uses the previous step's contacts and tip with the newly placed position (one 2 ms step lag), and `inside` is a 14 mm Euclidean disc where the real bound (6 mm per axis) comes from contact. Honest in continuous motion: 0 mm lateral inserts to tip 0.045; 8.7–18 mm lateral jams at the mouth (tip 0.070) with `success=False`; a teleport test can trip the lag. | None for episodes (peg moves continuously). | Compute `inside` per axis with `CLEAR`; evaluate contact after placement. |
| T16 | `sim/__init__.py:207-218`, `ground/operators.py:34` | MINOR | Zero‑latency ceiling: baseline zero 20/30 (Wilson [0.49, 0.81]). No seed is unreachable at spawn (max IK error 4.4 mm), but 7 seeds (3, 4, 10, 13, 14, 24, 25) drift out of reach within 10 s on their straight cage‑clipped path; 5 of the 10 zero failures (4, 10, 13, 24, 25) are in that set. Peg: 0 unreachable (hole 1.0 mm / 2.8 mm IK error). | The 80 % threshold is 0.53 with a ±0.16 CI at n = 30; the knee is decided by ≈5 seeds. Failures at zero are partly the task (7 cm/s operator vs 4.5 cm/s box), not the link. | Report the reachability tag per seed; consider a faster operator or a bounded drift box; or 60 seeds. |
| T17 | `metrics/__init__.py:92`, `sat/controller.py:78-80` | NOTE | `cmd_loss` 0.101 on leo is 8.4 % seq‑stale reordered packets (1 534 / 18 233) plus ≈1.2 % link loss; measured emulator inversion rate 5.9 % on an unloaded 20 s run. | Correct per the docstring, but "loss" columns must be read as "reordered + lost". | Print `stale` next to `cmd_loss` in the table (it is in diagnostics already). |
| T18 | `ground/loop.py:65` | NOTE | `owd_up_ms = rtt/2`; the acceptance profile is 30/18 ms. Documented. | `owd_up_ms` is off by 6 ms on leo. | Drop the column or compute from `t_cmd_applied - last_cmd_t_send` (same host). |
| T19 | `metrics/__init__.py:100-107`, `sim/__init__.py:37` | NOTE | `vel_over` is measured on the applied setpoint stream. Actuator check: a 2 rad/s setpoint ramp gives 1.94–1.97 rad/s true joint speed; even an unramped 0.3 rad step peaks at 2.03 rad/s (kp 50, 3.5 N·m limit). | The clamp is real on the command; the arm cannot physically exceed it by much. Fine. | None. |
| T20 | `aggregate.py:32-70` | NOTE | Wilson and exact McNemar match closed‑form references at every case tried. `boot_ratio` drops all‑failure resamples (NaN), which narrows the CI at low success. | None at success ≥ 0.2. | Report the dropped‑resample count. |

Verified correct (no finding): gravity is `[0, 0, 0]` after the `<option>` patch (the SO‑100 MJCF has
`<option cone="elliptic" impratio="10"/>`, so the replace fires); no contact at the home pose; the
ramp limiter cannot continue an old trajectory in hold (`tgt = self.last`); Terminal's primitive stands
down when `now - buf[-1][0] > timeout_s` and the hand‑back blend is gated by `alive`; independent
recomputation from the satellite sidecar (setpoint change while `t_ns - t_applied_ns > 0.3 s`, and
|Δsetpoint|/dt > 2.1 rad/s) gives `move_in_hold = 0`, `vel_over = 0` on all 132 recorded cells, and the
logged `hold` flag disagrees with the independent gap test on 1 cycle in 311 409 (leo cell); seeds are
reproducible and identical across arms (`seed = seed0 + 1000·arm + k`, `default_rng(seed)`); GE loss,
Poisson rate, duration mixture, burst fraction, spike, end bump, jitter SD, AR(1), FIFO and pass windows
all match SYNTHESIS §7 (table below); `demos_per_hour` = 3600 / mean successful wall time (TESTBED_SPEC,
selection.md §3) and `demos_per_hour_gross` = 3600·successes / Σ wall (data_pipeline §3.2) are
implemented as specified, modulo T09; `max_s` and the Tier‑1 cell list match selection.md §3.

## Evidence

### E1. Emulator fidelity (T02, T03, T08, T12, T14, T17)

Socket‑driven: `Link` fed 120 s of 49 B commands at 50 Hz (up) and 123 B telemetry at 30 Hz (down),
all nine profiles concurrently, OWD from a `monotonic_ns` stamp in the payload, under the running
matrix's load. `core` = packets outside the first 1 s and last 0.2 s of each 15 s period (profiles
without structure: all packets). `spike+` = mean excess over `core` inside the first 140 ms of each
period (linear decay 74→0 predicts 37 up / 18.5 down); `end+` = excess in the last 75 ms (20 nominal);
`loss1s` = loss inside the first second of periods (0.31·0.30 + 0.005 = 9.8 % predicted).

| profile | dir | nominal | mean | core mean | SD nom | SD core | min | p50 | p95 | p99 | max | loss % | spike+ | end+ | loss1s % | loss rest % | sent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| zero | up | 0 | 0.63 | 0.63 | 0 | 1.74 | 0.08 | 0.6 | 0.9 | 1.6 | 69.5 | 0.00 | – | – | – | – | 6000 |
| zero | down | 0 | 0.62 | 0.62 | 0 | 1.46 | 0.07 | 0.6 | 0.9 | 1.4 | 59.5 | 0.00 | – | – | – | – | 3600 |
| direct_gs | up | 15 | 15.94 | 15.94 | 2 | 2.55 | 6.7 | 15.7 | 19.6 | 21.1 | 73.3 | 0.13 | – | – | – | – | 6000 |
| direct_gs | down | 15 | 15.96 | 15.96 | 2 | 2.54 | 9.1 | 15.6 | 19.7 | 21.5 | 68.2 | 0.17 | – | – | – | – | 3600 |
| leo_relay | up | 30 | 30.34 | 30.02 | 14 | 14.41 | 3.9 | 27.0 | 58.8 | 82.4 | 154.5 | 1.20 | 36.2 | 15.0 | 11.00 | 0.50 | 6000 |
| leo_relay | down | 18 | 18.89 | 18.61 | 11 | 11.21 | 0.3 | 16.2 | 40.1 | 59.8 | 123.8 | 0.97 | 18.8 | 18.2 | 7.92 | 0.48 | 3600 |
| geo_relay | up | 300 | 301.05 | 301.05 | 2 | 2.90 | 292.1 | 300.9 | 304.5 | 306.5 | 377.7 | 1.25 | – | – | – | – | 6000 |
| geo_relay | down | 300 | 301.03 | 301.03 | 2 | 2.60 | 292.5 | 300.9 | 304.6 | 306.6 | 338.5 | 0.92 | – | – | – | – | 3600 |
| sweep:0 | up | 0 | 6.54 | 6.18 | 14 | 10.49 | 0.2 | 1.7 | 28.9 | 54.1 | 124.5 | 1.20 | 36.5 | 16.8 | 11.00 | 0.50 | 6000 |
| sweep:0 | down | 0 | 5.38 | 5.10 | 11 | 8.26 | 0.1 | 1.3 | 22.4 | 41.4 | 105.7 | 0.97 | 18.7 | 17.4 | 7.92 | 0.48 | 3600 |
| sweep:100 | up | 62.5 | 62.88 | 62.56 | 14 | 14.44 | 37.1 | 59.5 | 91.7 | 115.6 | 187.4 | 1.20 | 37.4 | 15.0 | 11.00 | 0.50 | 6000 |
| sweep:100 | down | 37.5 | 38.40 | 38.10 | 11 | 11.20 | 19.3 | 35.8 | 59.6 | 79.3 | 143.3 | 0.97 | 18.7 | 18.2 | 7.92 | 0.48 | 3600 |
| sweep:250 | up | 156.2 | 156.66 | 156.34 | 14 | 14.49 | 130.6 | 153.3 | 185.4 | 209.8 | 280.6 | 1.20 | 37.3 | 15.0 | 11.00 | 0.50 | 6000 |
| sweep:250 | down | 93.8 | 94.69 | 94.41 | 11 | 11.28 | 75.6 | 92.1 | 116.0 | 135.4 | 200.0 | 0.97 | 18.6 | 17.9 | 7.92 | 0.48 | 3600 |
| sweep:500 | up | 312.5 | 312.89 | 312.57 | 14 | 14.52 | 286.5 | 309.5 | 341.4 | 367.6 | 436.7 | 1.20 | 36.9 | 15.2 | 11.00 | 0.50 | 6000 |
| sweep:500 | down | 187.5 | 188.41 | 188.13 | 11 | 11.20 | 168.8 | 185.9 | 209.4 | 228.6 | 293.7 | 0.97 | 18.2 | 18.1 | 7.92 | 0.48 | 3600 |
| sweep:1000 | up | 625 | 625.35 | 625.03 | 14 | 14.47 | 599.6 | 621.9 | 653.9 | 678.6 | 749.7 | 1.20 | 35.8 | 14.6 | 11.00 | 0.50 | 6000 |
| sweep:1000 | down | 375 | 375.93 | 375.65 | 11 | 11.26 | 356.6 | 373.4 | 397.2 | 417.3 | 480.5 | 0.97 | 18.4 | 18.0 | 7.92 | 0.48 | 3600 |

Reading: mean OWD = nominal + 0.3–1.0 ms of scheduler overhead in every profile; jitter SD = nominal
+ 0.2–0.5 ms (timer noise); p99 of `zero` 1.6 ms with rare 60–70 ms outliers under load. The 8 period
samples per direction put the spike/end‑bump means within noise of prediction (SE ≈ 2.6 ms). Loss
matches the stationary GE + burst layer (see below); FIFO profiles show 0 inversions. Loss with the
`sweep:` family is identical to `leo_relay` by construction. The `sweep:0` rows show the clipping of T08.

Pure‑function checks (no sockets, seeds fixed):

| quantity | measured | nominal (SYNTHESIS §7) |
|---|---|---|
| GE loss direct_gs / leo_relay / geo_relay, 2 M packets | 0.153 % / 0.493 % / 1.302 % | 0.149 % / 0.501 % / 1.306 % |
| leo burst: fraction of periods forced bad | 30.2 % (960 periods) | 31 % |
| leo long‑run loss GE + burst at 50 Hz, 4 h | 1.12 % | ≈1.1 % |
| Poisson outage rate, 5000 h, seeds 1 and 2 | 1.703 / 1.723 h⁻¹ (SE 0.018) | 1.7 |
| outage duration: mean, frac < 2 s, frac > 5 s, max | 1.85 s, 87.4 %, 2.7 %, 30.7 s | 1.89 s, 87 %, 3 %, 31 s |
| outage time fraction | 0.084 % | – |
| direct_gs duty cycle, passes/day, first gap | 20.6 %, 33, at 540 s | 21.3 %, 33.4 |
| seeds 0–29, either direction, any blackout in the first 30 s: leo / geo | 2 of 60 (both at 24.83 s) / 0 of 30 | – (T02) |
| 15 s period phase at `Link.start()` | 0.0004 s, every episode | should be U(0, 15) (T03) |
| `sweep:0` realised base RTT without structure (200 k draws) | 9.0 ms (clipped log‑normal) | 0 (T08) |
| leo uplink reorder, 20 s at 50 Hz, arrival order | 5.9 % inversions = 5.8 % seq‑stale | – (T17) |

The 15 s clock: `Link.start()` sets `t0` for both directions and `structure()` uses `t - t0`; nothing
randomises the phase. From the leo cell's satellite logs the first command was applied 0.232–0.332 s
after the loop started (spike 0–0.140 s), successful episodes lasted 5.1–14.0 s, the 11 episodes that
reached 15 s all timed out at 20 s.

### E2. RTT measurement (T04, T18)

`rtt = now − last_cmd_t_send − (t_send_tel − t_cmd_applied)`. All four stamps come from one host's
`monotonic_ns`; `t_cmd_applied` is stamped on the first control cycle that saw the newest command and
`t_send_tel ≥ t_cmd_applied`, so the value cannot go negative and the `max(0, ·)` is only defensive.
What it does contain is the ground's own poll dwell, because telemetry is only read at the top of the
50 Hz tick after `time.sleep(slack)`:

| cell | rtt rows p5 / p50 / p95 | mean | nominal | measured link RTT (E1, up+down mean) |
|---|---|---|---|---|
| baseline zero | 2.6 / 10.0 / 19.1 | 10.1 | 0 | 1.25 |
| baseline direct_gs | – / 39.5 / – | 40.4 | 30 | 31.9 |
| baseline leo_relay | – / 51.8 / – | 52.4 | 48 | 49.2 (median 43.2) |
| baseline geo_relay | – / 610.4 / – | – | 600 | 602.1 |

The zero‑cell distribution is U(0, 20 ms) + 0.6 ms: the ground dwell, not the link. `rtt_p50` equals
base up + down within jitter only after removing ≈10 ms, and on leo the log‑normal median (−3.5 ms up,
−2.75 ms down) happens to cancel most of it. The e2e tests tolerate ±25–30 %, so they pass.

### E3. Safety metrics (T02, T06, T07, T19)

Definitions vs SYNTHESIS §6: `move_in_hold` = emitted setpoint changed while `held and not retracting`
(strategy self‑report, `baseline.py:52-53`); `vel_over` = |Δsetpoint|/dt > 2.1 rad/s on the satellite's
own applied‑setpoint log (`metrics.py:100-107`, independent of the strategy); `keepout` = grasp site
outside the cage box (`sim.py:261`); `cage` = any non‑object geom in contact with a cage wall
(`sim.py:263`), both debounced at 0.25 s. Independent recomputation from the sidecar
(`indep_move_in_hold`: setpoint moved while `t_ns − t_applied_ns` ∈ (0.3 s, 10 s); `indep_vel_over` as
above) returned 0 and 0 on all 132 recorded cells (294 k–731 k control cycles each), and the logged
`hold` flag matched the gap test on all but 1 cycle of the leo cell. Evasion paths checked: Baseline
freezes at the last *emitted* value, so no residual ramp; DeadReckon only overrides `_playout`, which is
not called in hold; Terminal returns `None` (→ baseline hold) when `alive` is false and gates the
hand‑back blend on `alive`; a one‑entry `[(now, 0, out)]` buffer resets `held` only while the primitive
is legitimately driving on a live link. No evasion found. But: no hold ever occurred inside an episode
(E1, T02), so the two link‑caused counters have never been exercised; the counters that are non‑zero
(`cage`) are operator‑caused and fire at zero latency (12/30 episodes), which makes the §6 gate fail
everywhere (T07). Stalls (T06): per cell, satellite cycles with dt > 0.2 s / episodes affected:
deadreckon geo 44/3, sweep1000 42/3, sweep250 46/4, sweep400 47/5, sweep500 43/3, sweep750 45/3;
gain direct_gs 42/4, geo 42/3, leo 41/5, zero 42/4; twin sweep1000 39/5, sweep750 42/4; max single gap
2.38 s; all other cells 0–2.

### E4. Simulation (T01, T15, T16)

`m.opt.gravity = [0, 0, 0]`, timestep 2 ms, `ncon = 0` at the home pose, no cage contact at home.
Capture: box placed 18 mm from the grasp site, `ctrl[JAW] = 0` with `qpos[JAW] = 0.0` rad (open) →
`grasped = True` on the first step; same for offsets of 19 mm along −z, +y and +x. The physical jaw
under a step command reaches 0.6 rad at 0.186 s and 0.05 rad at 0.306 s. Peg: continuous 2 cm/s
descent with 0 mm lateral error inserts (tip 0.0450 ≤ 0.045, `success=True`); with 8.7, 10.9, 11.6,
11.9, 12.4, 13.1 and 18.2 mm true lateral error the peg jams at the mouth (tip 0.0700) with
`success=False`; contact geometry bounds the lateral error at 6 mm (wall inner face 14 mm, peg
half‑width 8 mm). Reachability (DLS IK from home, 400 iterations, joint limits): all 30 capture spawns
reachable (IK residual 0.6–4.4 mm), target A 1.4 mm, target B 3.5 mm, peg hole 1.0 mm (align) /
2.8 mm (insert); 7 seeds leave reach along their drift path within 10 s. Zero‑cell failures: baseline
{4, 9, 10, 13, 15, 16, 21, 24, 25, 26}, sweep0 {5, 9, 10, 13, 16, 21, 24, 25, 26}, twin
{3, 4, 5, 9, 10, 13, 16, 21, 24, 25, 26}: 8 seeds fail under all three, so the zero ceiling is a task
property and the pairing works.

### E5. Metrics (T05, T09, T10, T13, T20)

Synthetic signals at 50 Hz (`sal(ours)` / SPARC reference with padlevel 4 / `ldlj(ours)` / reference):
minimum‑jerk −1.376 / −1.406 / −5.19 / −5.22; minimum‑jerk + white noise (SD 0.03 on peak 0.28) −1.368 /
−1.406 / −12.31 / −15.10 (SAL is insensitive to sub‑threshold noise by design; LDLJ catches it); two
sub‑movements −2.210 / −2.245 / −8.03 / −8.05. Sample‑and‑hold artefact: the same minimum‑jerk position
sampled at 30 Hz and re‑read at 50 Hz has 40 % zero‑speed samples, stall_frac 0.51 vs 0.24, SAL −2.07
vs −1.38, LDLJ −14.5 vs −5.2. Recorded cells: fraction of consecutive identical `observation.state`
rows 0.40–0.47 in all 132 cells; reported `stall_frac` 0.47 (zero) → 0.60 (geo). Wilson: (0,30) →
[0, 0.1135]; (15,30) → [0.3315, 0.6685]; (24,30) → [0.6269, 0.9049], identical to the closed form.
McNemar exact: (0,5) 0.0625, (2,8) 0.1094, (3,10) 0.0923, (5,5) 1.0, identical to
2·Binomial tail capped at 1. `demos_per_hour` = 3600 / mean successful `duration_s` and
`demos_per_hour_gross` = 3600·successes / Σ`duration_s` (`metrics.py:128-129`), where `duration_s`
is `run.py:123`'s wall clock (T09). No per‑pass figure exists for `direct_gs` (T10).

### E6. Recorder (T11)

`meta/info.json` present keys: `codebase_version` "v2.0", `robot_type`, `fps` 50, `total_episodes`,
`total_frames`, `features` (dtype + shape only). `meta/` contains only `episodes.jsonl` and
`info.json`; `data/` contains `episode_%06d.npz` and `episode_%06d_sat.npz`, no parquet. Per‑frame keys
present: `observation.state` (7, float32), `action` (7, float32), `timestamp` (float32),
`frame_index`, `episode_index`, `index` (int64), `next.done` (bool), plus extras. A `lerobot` v2.x
`LeRobotDataset` would fail, in order: `KeyError: 'data_path'`/`'splits'` when parsing `info.json`;
no files matching `data/chunk-000/episode_*.parquet`; missing `meta/tasks.jsonl` and the `task_index`
column; missing `meta/stats.json` (v2.0) or `meta/episodes_stats.jsonl` (v2.1); and, once past those,
`check_timestamps_sync` on `timestamp − frame_index/fps` reaching 0.19–0.75 s against a 1e‑4 s
tolerance (realised rate 46.4–49.6 frames/s versus the declared 50). `episodes.jsonl` lines
(`{"episode_index", "tasks", "length"}`) are the v2.0 shape.

## Implication for the results

The link emulator does what SYNTHESIS §7 says (E1), the safety envelopes hold on every recorded cycle
(E3) and the statistics are right (E5). What the Tier‑1 numbers actually measure is different from
what the acceptance text implies: `capture` success is a 20 mm proximity‑plus‑close‑command event
(T01), the acceptance profile never exposes a live command to its 15 s structure or to an outage
(T02, T03), the §6 safety gate fails everywhere for an operator‑caused reason and is untested for the
link‑caused ones (T02, T07), and the smoothness columns mostly measure telemetry repeats (T05). The
RTT columns read ≈10 ms high (T04) and eight cells carry load stalls (T06). Fix T01, T03 and T05 and
re‑run blocks A/B before the success‑vs‑latency curve is read; add a dropout block for T02; re‑run the
eight T06 cells; report `cage` separately from the link‑caused counters (T07).
