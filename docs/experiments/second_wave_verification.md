# Second-wave verification

Completed 2026-09-13 local time (2026-09-14 UTC). This record concerns the second wave;
[the first-wave verification](final_verification.md) remains historical evidence.

## Executions and provenance

| Study | Execution revision | Cases | Result |
|---|---|---|---|
| Primary fixed protocol | `0f68e78319fc0cb15d0e64723a7e50d154fd189b` | 15 cells × 30 independent task seeds per cell, 1000–1029 | 450/450 retained; zero failed or scheduler-contaminated cells |
| Chain bookkeeping regression | `550e1908785bab8e9c82470ab16d39a428dcea7d` | Four five-episode chains; starting seeds 2000 and 3000, two reset modes | 20/20 released; zero failed cells; chain metadata/continuity checks passed |
| Final Peg endpoint regression | `be7dd45a300e309defcf2b2e460400e196c20039` | Three ten-episode cells, seeds 4000–4009 | 30/30 successful endpoints passed depth/lateral/contact reconstruction |

These **500 new episodes are not pooled**. Primary data retain the final-pose Peg limitation
discovered after that run; six of 117 successful Peg endpoints were up to 0.088 mm above the
depth threshold. The final revision fixes that predicate. The chain and endpoint studies are
regressions, not powered confirmations of the original mechanism effect sizes.

The [primary manifest](second_wave/manifest.json), [chain manifest](second_wave/chain_manifest.json)
and [Peg manifest](second_wave/peg_manifest.json) record executable hashes and the external model
revision. All used MuJoCo 3.13.0, Python 3.12.13 and Menagerie revision
`feadf76d42f8a2162426f7d226a3b539556b3bf5`. The dependency lock alone does not pin that model.
The primary manifest retains the pre-execution Git state and separately names the exact committed
execution revision. Its source-content hashes are the authority for the executed files.

## Tests and recording audits

- The initial suite passed 78 tests before second-wave changes.
- After the chain/retry fixes, a clean clone of `550e190` passed 95 tests in 70.24 s.
- After the final Peg correction, the same isolated clone checked out exact revision `be7dd45`
  and passed **98 tests in 65.78 s** with `uv run pytest -q`. Dependencies were installed by
  `uv sync --frozen`. Tests include real UDP episodes, blackout persistence, finite packet
  validation, frozen deadlines, chain completion, retry provenance and statistical edge cases.
- The primary recording audit checked 354,402 ground frames, 5,127,213 satellite cycles and all
  450 terminal records with zero integrity errors. Its checks cover causal observation timing,
  command sequence alignment, finite recorded state, outcome consistency and target distance.
  It does not replay every task predicate or reconstruct every accepted command/interpolator input.
- The chain audit checked all 20 metadata/seed/sequence records, final-to-next-start state
  continuity and reset-inclusive durations. Its self-check rejects success without release,
  wrong seed and inconsistent duration. The primary verifier self-check rejects shifted command
  IDs, noncausal timestamps and nonfinite action data.
- The final Peg check reconstructs joint/object pose and fixture contact from saved terminal
  state, independently of the reported success flag. All 30 successful endpoints satisfy the
  complete depth/lateral/contact predicate.

Audit artifacts: [primary](second_wave/record_verification.json),
[chains](second_wave/chain_verification.json), [Peg endpoints](second_wave/peg_verification.json).
Zero integrity errors do not establish physical fidelity, flight safety or learned-policy value.
The primary audit found actual sampled joint speed up to 6.584 rad/s while command envelopes
remained compliant. This is a substantive research finding, not a failed data-integrity check.

## Reproduce the analysis

Committed episode vectors permit statistical reproduction without local trajectory files:

```sh
uv sync --frozen
uv run python docs/experiments/second_wave/analyze.py \
  --fresh-results docs/experiments/second_wave/fresh/results.json
uv run python docs/experiments/second_wave/verify_records.py --self-check
uv run python docs/experiments/second_wave/verify_chains.py --self-check
```

The statistical script reproduces both historical reanalysis and the separate corrected-run
section, with deterministic resampling and input hashes. Undefined ratios serialize as JSON
`null`; censored knees use an explicit label. The original report present at task start is
preserved byte-for-byte in [REPORT_WAVE1.md](../REPORT_WAVE1.md).

For fresh simulations, use the study's execution revision and pin the external model:

```sh
git worktree add --detach ../teleoperation-chain-reproduction 550e190
cd ../teleoperation-chain-reproduction
uv sync --frozen
ROBOT_DESCRIPTION_COMMIT=feadf76d42f8a2162426f7d226a3b539556b3bf5 \
  uv run python docs/experiments/second_wave/chain_check.py
```

Return to the current checkout to audit that raw directory:

```sh
uv run python docs/experiments/second_wave/verify_chains.py \
  ../teleoperation-chain-reproduction/docs/experiments/raw_second_wave_chain \
  --out /tmp/teleoperation-chain-verification.json
```

The [report](../REPORT.md#10-reproduction-and-readiness) supplies the equivalent primary commands.
The final Peg runner is `uv run python docs/experiments/second_wave/peg_check.py`; pass
`--verify-only` to repeat its terminal audit on existing raw files. Use the same model pin for a
rerun. Real-time socket scheduling makes byte-identical timing unlikely. Raw NPZ files remain
local/ignored; independently rerun trajectories to repeat frame-level verification.

## Report and interface checks

Seven Astra subagents reviewed primary evidence, statistics, testbed validity, all 20 hypotheses,
presentation, integration and recordings. The [independent review](second_wave_review.md) checked
all primary numerical claims against the committed artifacts and traced the fixes through their
callers. The report preserves original gates, uncertainty, missing profiles and execution versions.

The results page uses static data with no external chart dependency. Its earlier second-wave
layout passed actual desktop (1280 px) and mobile (390 px) browser checks, with no overflow or
console errors. Final data rows and local links were checked statically. Final browser rechecking
was attempted but blocked by browser-connection timeouts; final visual/console verification is
therefore incomplete. This is disclosed rather than treating the earlier check as final evidence.

## Implication for our design

Use the corrected experiment and traceable data for further prototype research. Retain separate
qualification gates for physical task validity, actual motion/contact safety, a complete mission
configuration, accepted training-format export and incremental policy-learning value.
