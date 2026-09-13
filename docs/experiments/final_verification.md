# Final verification (Phase 5, independent)

Verifier: clean clone of `main` at `8c54d8f` (`git status` clean, 0 modified files) into a scratch
directory, `uv sync`, no edits to the working tree. Date: 2026-09-13.

## 1. Test suite

```
uv run pytest -q
78 passed in 73.57s (0:01:13)
```

## 2. Reproduction of two headline cells (12 seeds each, seeds 0-11)

Commands (clean clone, run 4-way concurrent; the matrix ran 9-way):

```
uv run python -m spaceteleop.run --profile sweep:400 --task peg     --strategy baseline --episodes 12 --seed 0 --max-s 30 --tau-h 0.17 --out <scratch>/rep_peg_baseline
uv run python -m spaceteleop.run --profile sweep:400 --task peg     --strategy terminal --episodes 12 --seed 0 --max-s 30 --tau-h 0.17 --out <scratch>/rep_peg_terminal
uv run python -m spaceteleop.run --profile sweep:400 --task capture --strategy baseline --episodes 12 --seed 0 --max-s 20 --tau-h 0.17 --out <scratch>/rep_capture_baseline
uv run python -m spaceteleop.run --profile sweep:400 --task capture --strategy twin     --episodes 12 --seed 0 --max-s 20 --tau-h 0.17 --out <scratch>/rep_capture_twin
```

Settings match the Tier-2 cells in `tier2/results.json` (`max_s` 30.0 peg / 20.0 capture, `seed0` 0,
`tau_h` 0.17, no extra args). Reference vectors are episodes 0-11 of the matching
`T2_<task>_<strategy>_sweep400_tau0.17` cells.

| cell | Tier-2 seeds 0-11 | this run seeds 0-11 | agree |
|---|---|---|---|
| peg / baseline | 0 0 0 0 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 0 0 0 0 | 12/12 |
| peg / terminal | 1 1 1 1 1 1 1 1 1 1 1 1 | 1 1 1 1 1 1 1 1 1 1 1 1 | 12/12 |
| capture / baseline | 0 0 1 0 0 0 0 1 0 0 0 1 | 0 0 1 0 0 0 0 1 0 0 0 1 | 12/12 |
| capture / twin | 1 0 1 0 0 1 1 1 1 0 0 1 | 1 0 1 0 0 1 1 1 1 0 0 1 | 12/12 |

Zero seed flips. Run summaries: peg terminal 12/12 at 637.9 demos/h (Tier-2 cell: 100/100, dph
ratio 2.11); peg baseline 0/12 (Tier-2: 1/100); capture twin 7/12 = 0.58 vs baseline 3/12 = 0.25
(Tier-2: 0.72 vs 0.44, +0.28). All four runs: `unsafe_events 0 (move_in_hold=0, vel_over=0,
keepout=0)`, `stalls 0`, `max_dt_s` <= 0.043 s (no T06 load contamination).

Direction and magnitude of both Tier-2 effects reproduce: peg terminal +12/12 over a 0/12 baseline,
capture twin +4 seeds net over baseline on the same 12 seeds (Tier-2 discordant: b=3, c=31).

## 3. Hand recompute of Wilson CI and exact McNemar p (stdlib `math` + `statistics.NormalDist`)

Wilson 95 % (z = 1.95996) for the four cells behind the two `paired.md` rows, vs `tier2/results.md`:

| cell | k/n | hand Wilson | results.md |
|---|---|---|---|
| peg sweep:400 baseline | 1/100 | [0.0018, 0.0545] | 0.01 [0.00,0.05] |
| peg sweep:400 terminal | 100/100 | [0.9630, 1.0000] | 1.00 [0.96,1.00] |
| capture sweep:400 baseline | 44/100 | [0.3467, 0.5377] | 0.44 [0.35,0.54] |
| capture sweep:400 twin | 72/100 | [0.6251, 0.7986] | 0.72 [0.63,0.80] |

Exact two-sided McNemar, `p = min(1, 2 * sum_{i<=min(b,c)} C(b+c, i) / 2^(b+c))`:

| paired.md row | b | c | hand p | results.json `mcnemar_p` | paired.md |
|---|---|---|---|---|---|
| peg sweep:400 terminal | 0 | 99 | 3.1554e-30 | 3.1554436208840472e-30 | 0.0000 |
| capture sweep:400 twin | 3 | 31 | 7.6601e-07 | 7.660128176212311e-07 | 0.0000 |

All match (bit-identical p; Wilson agrees at the 2-decimal precision printed).

## 4. `tier1/curves.json` vs `tier1/results.md` (3 points)

| task / arm / profile | curves.json | results.md |
|---|---|---|
| capture / baseline [A] / sweep:400 | success 0.3667 [0.2187, 0.5449], dph 340.8, n 30 | `0.37 [0.22,0.54] 11/30`, dph `340.8 [79.8]` |
| peg / terminal [B] / sweep:400 | success 1.0000 [0.8865, 1.0000], dph 638.7, n 30 | `1.00 [0.89,1.00] 30/30`, dph `638.7 [638.7]` |
| peg / terminal_ground [B] / sweep:400 | success 0.0000 [0.0000, 0.1135], dph 0.0, n 30 | `0.00 [0.00,0.11] 0/30`, dph `0.0 [0.0]` |

All three consistent.

## 5. Block S table (`tier1/results.md` + `tier1/results.json`)

`results.md` link_unsafe rows for every `[S]` arm (baseline, deadreckon, gain, terminal,
terminal_ground, twin) read `0` at both `leo_relay_drop1` and `leo_relay_drop12`. Confirmed in
`results.json`: all 24 S cells have `move_in_hold = vel_over = keepout = 0`, `unsafe = 0`,
`episodes = 30` and 30 episode records.

hold / retract (from `results.json` `aggregate.events`; `results.md` does not print these):

| task | arm | drop1 hold / retract | drop12 hold / retract |
|---|---|---|---|
| capture | baseline | 24 / 0 | 24 / 24 |
| capture | deadreckon | 23 / 0 | 23 / 23 |
| capture | gain | 29 / 0 | 29 / 29 |
| capture | terminal | 24 / 0 | 24 / 24 |
| capture | terminal_ground | 24 / 0 | 24 / 24 |
| capture | twin | 20 / 0 | 20 / 20 |
| peg | baseline | 1 / 0 | 1 / 1 |
| peg | gain | 1 / 0 | 1 / 1 |
| peg | terminal_ground | 11 / 0 | 14 / 14 |
| peg | deadreckon | 0 / 0 | 0 / 0 |
| peg | terminal | 0 / 0 | 0 / 0 |
| peg | twin | 0 / 0 | 0 / 0 |

Every capture arm matches the expected pattern (drop1: hold > 0, retract = 0; drop12: hold > 0,
retract > 0, and retract = hold since the 12 s blackout exceeds `retract_s` = 10 s). Three peg arms
show hold = 0 in both profiles. That is consistent, not a defect: the drop profiles blackout at
`drop_at_s = 6.0` (`link/profiles.py`), and peg deadreckon / terminal / twin finish every one of
their 30 episodes in 4.1-4.5 s, before the outage starts. peg baseline and gain each have one 30 s
failed episode that saw the drop (hold = 1), terminal_ground has 11-14 failures that did.
hold counts are per S-cell episodes that reached 6 s, never above 30.

## 6. Safety-counter audit (final code)

`move_in_hold` is the only one of the three that a strategy could in principle evade. It is
booked inside `Baseline.sat_step` (`strategies/baseline.py:52-53`) from the strategy's own
`held` flag, and the controller reads `strategy.held` too (`sat/controller.py:90`); a subclass that
overrode `sat_step` without setting `held` would emit motion during silence with `move_in_hold`
staying 0. On the final code no strategy does that: Gain, Twin and TerminalGround override only
`ground_step`, DeadReckon overrides only `_playout` (called inside the baseline tail, and it
falls back to the frozen newest setpoint after `H` = 0.1 s < `timeout_s`), and Terminal's
substituted one-entry buffer `[(now, 0, out)]` (`terminal.py:195`), which zeroes the hold gap, is
only produced while `alive = now - buf[-1][0] <= timeout_s`; on a stale link `_step` returns
`None`, the real buffer is passed through and hold/retract engage as in baseline. `vel_over`
cannot be evaded: `metrics._vel_over` differences the satellite's applied-setpoint sidecar,
which the controller logs from `sat_step`'s return value every control cycle
(`controller.py:103`), independent of any strategy counter, with the same 2.0 rad/s clamp
(`vmax * 1.05`). `keepout` cannot be evaded: `sim.step` counts it from the true grasp-site
position against the cage box (`sim/__init__.py:_edge`) and the controller copies `st["keepout"]`
into the frozen event dict at `done_at` (`controller.py:130`). One residual gap worth noting:
both `move_in_hold` and `vel_over` skip the jaw joint (index 6), so a jaw command during hold is
not counted; that is by design (the jaw stays the operator's) and does not affect the arm.

## Verdict

REPRODUCED — 78/78 tests pass on a clean clone, 48/48 reproduced seeds match the Tier-2 vectors
with zero unsafe events, hand-recomputed Wilson and McNemar statistics match the published
tables, curves.json and the block S table are internally consistent, and the three link-caused
safety counters are either strategy-independent or, for `move_in_hold`, not bypassed by any
strategy in the final code.
