# Second-wave statistical review

The archived data support large task-specific effects at high latency. They do not establish general
mission acceptance, a 10% latency-specific throughput gain for Twin, or flight safety. The strongest
historical effects survive removal of the 30 scenarios reused from the screen and correction for
multiple success comparisons. Deadline and safety defects found in the second-wave testbed audit
limit every historical result below to that implementation. New seeds from the old implementation
are held-out scenarios, not validation of the corrected implementation.

## Evidence and reproduction

Inputs are the committed [Tier-1 vectors](tier1/results.json), [Tier-2 vectors](tier2/results.json),
and four [NO_LINK records](second_wave/no_link_records.json) recovered from existing raw stdout.
The recovery file records the exact failure line and SHA-256 of its source stdout. It permits
reproduction without the untracked multi-gigabyte sidecars. No simulation outcomes were invented.
The original published artifacts remain unchanged.

```sh
uv run python docs/experiments/second_wave/analyze.py
uv run pytest -q tests/test_aggregate.py tests/test_matrix.py
# After the corrected-run aggregate exists:
uv run python docs/experiments/second_wave/analyze.py --fresh-results PATH/TO/results.json
```

The script writes [statistics.json](second_wave/statistics.json), including input hashes, all
21 comparisons, the original and restored-outage analyses, zero-control adjustments, acceptance
bounds, and knee uncertainty. The optional corrected-run input produces a separate `corrected_run`
section. The archived analyses use the final post-fix Tier-1 dataset (198 cells, 5,940 episodes),
not `tier1_prefix`, which predates prior control fixes and has extensive CPU stalls.

Tier 2 requested 34 × 100 = 3,400 episodes but its parser retained only 3,396. Seed 69 produced a
30-second `NO_LINK` failure in each of four GEO cells. The ordinary episode regex discarded that
print format. Reinstating these four failed attempts reduces capture Twin GEO success from 60/99
to 60/100 in the complete sample. It does not reverse the result. Omitting outages from a study of
link performance is still a material accounting defect. The new matrix parser must retain them.

Tier-2 seeds start at 0, as do Tier-1 seeds. Scenarios 0–29 therefore participated in screen-cell
selection. The held-out analysis uses seeds 30–99, including the recovered outage. It also removes
a stalled seed from all arms of its task/profile/tau/block group. This leaves 70 paired scenarios
per held-out comparison. The 12-seed reproduction in `final_verification.md` reused seeds 0–11;
it tested reproducibility, not independent generalization.

## Estimands and uncertainty

Conditional demos/hour is `3600 / mean(duration | success)`. Gross attempt throughput is
`3600 × successes / sum(all attempt durations)`. They answer different questions. Conditional
throughput can remain high while almost every attempt fails. Gross throughput includes failure
and timeout costs; it includes reset time only where the recorded duration actually contains it.
Neither estimates mission wall-time collection yield without pass availability, operator staffing,
reset, curation and transfer costs.

Each paired bootstrap resamples seed indices jointly across arms. Success differences and gross
throughput differences use 2,000 deterministic resamples; the knee, acceptance and four-cell
zero-control analyses use 10,000. These are exploratory pointwise percentile intervals, not
simultaneous confidence guarantees. At an all-success or all-failure boundary an empirical bootstrap
cannot generate an unobserved outcome: `[0,0]` for identical success vectors is not proof of
population equivalence. Exact McNemar p-values use discordant pairs. Holm correction covers all
21 Tier-2 success comparisons, including controls and adverse effects. It allows dependent tests,
but cannot repair adaptive hypothesis selection or model error.
[Method: R statistical documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html).

The historical conditional throughput ratio for peg Terminal at 400 ms discards 747/2,000
resamples because the baseline has only one success. Its very narrow reported interval near 2.11
conditions on retaining that one successful scenario. It does not measure the uncertainty of
collection yield. The held-out gross difference remains estimable with the failed attempts intact.
Zero-baseline cells likewise require an absolute gross difference, not an undefined ratio.

## Results on held-out historical scenarios

All rows use 70 paired seeds after restoring the omitted outage. `pp` means percentage points.
The p-value adjusts the complete 21-comparison success family. Gross intervals remain pointwise.
The complete table, including null effects and controls, is in `tier2_recovered_fresh` in the JSON.

| Task / profile | Arm | Baseline → arm success | Difference, pp [bootstrap 95%] | Holm p | Gross demos/h difference [bootstrap 95%] |
|---|---|---|---|---|---|
| capture / sweep:400 | Twin | .471 → .714 | +24.3 [+11.4, +37.1] | .00537 | +98.6 [+54.3, +149.3] |
| capture / GEO | Twin | .257 → .643 | +38.6 [+25.7, +51.4] | 5.55e-6 | +97.4 [+63.1, +140.3] |
| capture / sweep:400 | Gain | .471 → .029 | −44.3 [−57.1, −32.8] | 1.30e-8 | −104.7 [−140.8, −71.0] |
| capture / sweep:500 | Terminal | .343 → .529 | +18.6 [+7.1, +30.0] | .072 | +42.5 [+14.7, +74.7] |
| capture / sweep:250 | DeadReckon | .514 → .571 | +5.7 [−2.9, +14.3] | 1 | +21.0 [−8.2, +51.5] |
| peg / sweep:100 | DeadReckon | .871 → .986 | +11.4 [+4.3, +18.6] | .072 | +350.3 [+182.1, +494.0] |
| peg / sweep:250 | DeadReckon | .100 → .871 | +77.1 [+67.1, +85.7] | 1.78e-15 | +341.7 [+248.4, +467.0] |
| peg / sweep:250 | Gain | .100 → .957 | +85.7 [+75.7, +94.3] | 4.64e-16 | +356.2 [+293.3, +415.9] |
| peg / sweep:400 | Terminal | .014 → 1.000 | +98.6 [+95.7, +100] | 7.12e-20 | +634.3 [+629.0, +638.3] |
| peg / sweep:400 | Twin | .014 → .886 | +87.1 [+78.6, +94.3] | 1.56e-17 | +346.3 [+261.0, +458.5] |
| peg / sweep:500 | Gain | .000 → .914 | +91.4 [+84.3, +97.1] | 2.06e-18 | +242.7 [+204.4, +279.6] |
| peg / sweep:500 | Twin | .000 → .714 | +71.4 [+60.0, +81.4] | 2.66e-14 | +175.5 [+126.7, +232.7] |

The large peg effects and capture Twin effects remain. The smaller capture Terminal and 100-ms
peg DeadReckon success comparisons do not cross .05 after this family adjustment. That is weaker
evidence, not evidence of no effect. Hypothesis acceptance also requires each original mechanism,
quality and safety clause; success significance alone does not satisfy those clauses.

## Zero-latency control changes the Twin conclusion

A nonsignificant zero-cell difference does not demonstrate equivalence. On held-out scenarios,
capture Twin improves zero-cell gross attempt throughput by 57.9 demos/h [13.1, 108.1], despite
its success McNemar comparison being inconclusive after adjustment. The published `ok` flag
therefore overstates what the control establishes.

Resample all four cells jointly on common seeds: arm and baseline at zero, and arm and baseline at
the target profile. Subtract the zero success gain from the target success gain; divide the target
conditional throughput ratio by the zero conditional throughput ratio. The following uses the
original paired vectors so it can be compared directly with the published ratio claims; GEO has
99 full-sample or 69 held-out pairs before the separate outage-restoration sensitivity.

| Twin / capture | All Tier-2 conditional ratio of ratios [95%] | Held-out conditional ratio of ratios [95%] | Held-out success difference-in-differences, pp [95%] |
|---|---|---|---|
| sweep:400 | 1.053 [.925, 1.189] | 1.057 [.906, 1.220] | +15.7 [0.0, +31.4] |
| GEO | 1.167 [.990, 1.372] | 1.203 [1.016, 1.430] | +30.4 [+14.5, +46.4] |

A pointwise held-out GEO signal remains after this control. Neither profile establishes a ≥10%
latency-specific conditional throughput gain: even GEO's lower bound is below 1.10. The result
supports further evaluation of Twin, not the original universal throughput claim. These controls
also retain the old operator and plant model; they cannot isolate real human benefit.

## Acceptance: retain the criterion, distinguish the historical amendment

The original SYNTHESIS section 6 includes cage contacts in unsafe events. The historical report
excluded cage after observing such contacts at zero latency. Calling them operator-caused does
not satisfy the original zero-unsafe requirement. The aggregator now reports the historical
link-only point screen separately from strict safety, which includes cage. `ZERO_OBSERVED` is an
observed counter result, not certification. Missing named profiles or safety counters are incomplete.

The original aggregator marked the two Tier-1 chain arms PASS without GEO and the two Tier-2
baseline arms PASS without direct-GS. These now read INCOMPLETE. A separate accounting problem
remains even for complete profiles:

| Historical arm | Conditional LEO/zero throughput | Gross LEO/zero throughput | Success ratio lower 95% bound | Interpretation |
|---|---|---|---|---|
| Tier-1 capture baseline | .973 | .988 | .571 | Point retention only; 70 named-profile cage contacts |
| Tier-1 capture Gain | .948 | .773 | .524 | Gross retention fails the .80 threshold at the point estimate |
| Tier-1 peg baseline | .979 | .983 | .829 | Success retention supported within this model; 6 cage contacts |
| Tier-1 peg Terminal | .969 | .969 | .884 | Performance supported within this model; zero measured named-profile unsafe events |
| Tier-2 capture baseline | 1.023 | .914 | .704 | Incomplete profile set; success retention not established |
| Tier-2 peg baseline | .977 | .922 | .917 | Incomplete profile set |

Success-ratio lower bounds use a one-sided 97.5% exact binomial lower bound for LEO divided by a
one-sided 97.5% exact upper bound for zero. The union bound gives at least 95% coverage for that
single ratio without assuming independence across the two profiles. This conservative construction
retains uncertainty at all-success boundaries; it is not adjusted across arms. The script inverts the
binomial CDF directly and checks its zero/all-success closed forms.
[Method: NIST exact binomial confidence limits](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm).

Zero observed unsafe events also leaves a nonzero population bound. Under independent,
representative Bernoulli exposure trials, 0/30 yields a one-sided exact 95% upper failure probability
`1 − .05^(1/30) = .0950`; 0/100 yields .0295. These values do not apply to unexposed trials or shared
scenarios counted repeatedly across profiles. In the original dropout block several peg strategies
finished before the fixed 6-second outage, so their zero counters do not establish outage behavior.
A corrected exposure experiment and independently observed safety invariants are required.

## Knee estimates are sampled crossings

The estimator's interpolated crossing is not a measured physical latency limit. It depends on a
noisy zero-cell reference, a coarse RTT grid, nonmonotone success estimates and profile structure.
Nominal `zero` and `sweep:0` differ in jitter/outage settings. The timeout also changes from 20 to
30 seconds for capture at 500 ms, so that part of its curve changes both latency and allowed time.
Each arm's own zero-cell threshold further complicates between-arm comparisons.

The new code exposes the bracketing sampled points and reports no crossing only through the
actual maximum tested RTT. A zero-success reference is undefined. The analysis resamples the
same seeds jointly across profiles and strategies, including the zero threshold. Crossings beyond
the sampled grid remain censored; they are not silently dropped from knee intervals.

| Historical Tier-1 arm | Interpolated crossing, ms | Sampled bracket, ms | Bootstrap crossing interval, ms |
|---|---:|---|---|
| capture baseline | 250 | 250–400 | 154–350 |
| capture DeadReckon | 230 | 100–250 | 156–360 |
| capture Twin | 787.5 | 750–1000 | 190–beyond 1000 |
| peg baseline | 96.7 | 0–100 | 54.5–123.5 |
| peg DeadReckon | 256 | 250–400 | 190–275.9 |
| peg Twin | 510 | 500–750 | 450–543.1 |
| peg Gain / Terminal | Not observed through 1000 | — | Censored beyond sweep |

The capture Twin crossing exceeds the sweep in 5.54% of bootstrap samples. A precise knee-shift
claim is not supported: even conditioning on both crossings, its shift interval is approximately
−75 to +725 ms. The peg DeadReckon shift interval is +87.7 to +207.0 ms, and peg Twin's is +356.7
to +463.2 ms. These are exploratory evidence for task-specific delay tolerance. The degenerate
TerminalGround crossing near 20 ms reflects interpolation from an abrupt 0-to-100-ms success
collapse; it is not 20-ms measurement precision. A denser fixed-budget sweep is required to
estimate a physical knee or confirm a minimum shift.

## Code corrections and limits

`experiments/aggregate.py` now keeps empty cells empty after stall exclusion, pairs within the same
block, rejects incomplete or unmeasured safety gates, shows strict safety separately, exposes knee
brackets and censoring, adds gross throughput differences and Holm p-values, and replaces zero-control
`ok` with `no detected gain; equivalence untested`. Full-run event and smoothness diagnostics remain
explicitly labeled when success/throughput vectors are filtered; they are not falsely recomputed
from unavailable episode event dictionaries. The new regression checks cover these failure modes.

These changes repair inference and reporting. They do not remove the simulated operator, perfect
state access, coarse timing, shared seeded model assumptions or historical deadline defects. The
held-out scenarios were not registered before this second review. Treat this as an audit and
sensitivity analysis; use the fixed second-wave experiment plan for prospective validation.

## Implication for our design

Use gross attempt throughput and success jointly when deciding what to implement. Keep Twin as a
capture candidate and preserve the peg-specific DeadReckon, Gain and Terminal comparisons for the
corrected-run test. Do not promote a universal Twin throughput gain, a precise capture knee shift,
or the historical link-only PASS to mission acceptance. Require complete profile coverage, actual
outage exposure and the original cage-inclusive safety criterion before making that decision.
