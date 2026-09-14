# Paired comparisons

Same seeds per cell, so success is a McNemar test on the discordant seeds (`b` = `baseline` only, `c` = arm only; two-sided exact binomial). demos/hour ratio is arm / baseline with a paired bootstrap 95 % CI (2000 resamples of the seed list); `drop` is how many resamples were thrown away because one arm had no success in them. With drops, this is a conditional interval and does not establish unconditional 95 % coverage. Gross throughput below retains failure durations. Holm p-values adjust all success comparisons in this file. Bootstrap intervals are exploratory, pointwise, and can degenerate at all-success/all-failure boundaries.

| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | demos/h ratio [95 % CI] | drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| capture | zero | 0.17 | twin | 30 | 0.70 | 0.80 | +0.10 | 1 | 4 | 0.3750 | 1.10 [1.00, 1.23] | 0 |
| capture | sweep:400 | 0.17 | gain | 30 | 0.43 | 0.00 | -0.43 | 13 | 0 | 0.0002 | - [-, -] | 2000 |
| capture | sweep:400 | 0.17 | twin | 30 | 0.43 | 0.70 | +0.27 | 1 | 9 | 0.0215 | 1.21 [1.08, 1.37] | 0 |
| peg | sweep:250 | 0.17 | deadreckon | 30 | 0.00 | 0.90 | +0.90 | 0 | 27 | 0.0000 | - [-, -] | 2000 |
| peg | sweep:400 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | - [-, -] | 2000 |
| peg | sweep:400 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | - [-, -] | 2000 |

## Failure-inclusive throughput and multiplicity

Gross demos/hour = 3600 × successes / total active attempt duration; reset wall time is included only when the recorded duration contains it.

| task | profile | arm | block | gross demos/h difference [95 % bootstrap CI] | Holm p |
|---|---|---|---|---|---|
| capture | zero | twin | W2 | +72.7 [+0.1, +161.9] | 0.75 |
| capture | sweep:400 | gain | W2 | -96.5 [-148.6, -54.1] | 0.000977 |
| capture | sweep:400 | twin | W2 | +106.3 [+38.1, +187.5] | 0.0645 |
| peg | sweep:250 | deadreckon | W2 | +397.7 [+242.6, +629.4] | 7.45e-08 |
| peg | sweep:400 | terminal | W2 | +634.9 [+632.7, +637.2] | 1.12e-08 |
| peg | sweep:400 | terminal_ground | W2 | +0.0 [+0.0, +0.0] | 1 |

## Zero-cell control (audit_strategies F3)

A latency hider must not gain on the zero-latency cell: a gain there is against the operator model, not against the link (selection.md section 4, H10 and H14 amendments). Flagged when a CI excludes zero in the positive direction; read such an arm's profile gains as the ratio of ratios (arm/baseline at the profile) / (arm/baseline at zero).

| task | arm | n | success diff [95 % CI] | demos/h ratio [95 % CI] | drop | flag |
|---|---|---|---|---|---|---|
| capture | twin | 30 | +0.10 [-0.03, +0.23] | 1.099 [1.000, 1.234] | 0 | ⚠ gain at zero latency |
