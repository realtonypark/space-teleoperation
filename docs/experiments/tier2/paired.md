# Paired comparisons

Same seeds per cell, so success is a McNemar test on the discordant seeds (`b` = `baseline` only, `c` = arm only; two-sided exact binomial). demos/hour ratio is arm / baseline with a paired bootstrap 95 % CI (2000 resamples of the seed list); `drop` is how many resamples were thrown away because one arm had no success in them (audit T20 - the CI is narrowed by exactly those).

| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | demos/h ratio [95 % CI] | drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| capture | zero | 0.17 | gain | 100 | 0.69 | 0.69 | +0.00 | 7 | 7 | 1.0000 | 1.00 [0.91, 1.09] | 0 |
| capture | zero | 0.17 | twin | 100 | 0.69 | 0.76 | +0.07 | 4 | 11 | 0.1185 | 1.06 [0.97, 1.17] | 0 |
| capture | leo_relay | 0.17 | terminal | 100 | 0.65 | 0.68 | +0.03 | 1 | 4 | 0.3750 | 0.97 [0.94, 0.98] | 0 |
| capture | sweep:250 | 0.17 | deadreckon | 100 | 0.52 | 0.57 | +0.05 | 4 | 9 | 0.2668 | 1.02 [0.95, 1.08] | 0 |
| capture | sweep:400 | 0.17 | gain | 100 | 0.44 | 0.03 | -0.41 | 41 | 0 | 0.0000 | 0.65 [0.51, 0.81] | 95 |
| capture | sweep:400 | 0.17 | twin | 100 | 0.44 | 0.72 | +0.28 | 3 | 31 | 0.0000 | 1.12 [1.04, 1.20] | 0 |
| capture | sweep:500 | 0.17 | terminal | 100 | 0.33 | 0.50 | +0.17 | 4 | 21 | 0.0009 | 1.01 [0.90, 1.13] | 0 |
| capture | geo_relay | 0.17 | twin | 99 | 0.22 | 0.61 | +0.38 | 5 | 43 | 0.0000 | 1.24 [1.09, 1.42] | 0 |
| peg | zero | 0.17 | gain | 100 | 0.98 | 0.98 | +0.00 | 0 | 0 | 1.0000 | 0.97 [0.97, 0.98] | 0 |
| peg | leo_relay | 0.17 | deadreckon | 100 | 0.97 | 0.99 | +0.02 | 0 | 2 | 0.5000 | 1.03 [1.03, 1.04] | 0 |
| peg | leo_relay | 0.17 | terminal | 100 | 0.97 | 1.00 | +0.03 | 0 | 3 | 0.2500 | 0.99 [0.99, 1.00] | 0 |
| peg | leo_relay | 0.17 | terminal_ground | 100 | 0.97 | 0.56 | -0.41 | 42 | 1 | 0.0000 | 1.01 [1.00, 1.02] | 0 |
| peg | sweep:100 | 0.17 | deadreckon | 100 | 0.84 | 0.98 | +0.14 | 0 | 14 | 0.0001 | 1.04 [1.03, 1.04] | 0 |
| peg | sweep:250 | 0.17 | deadreckon | 100 | 0.11 | 0.88 | +0.77 | 0 | 77 | 0.0000 | 1.03 [1.02, 1.04] | 0 |
| peg | sweep:250 | 0.17 | gain | 100 | 0.11 | 0.95 | +0.84 | 3 | 87 | 0.0000 | 0.70 [0.70, 0.71] | 0 |
| peg | sweep:400 | 0.17 | terminal | 100 | 0.01 | 1.00 | +0.99 | 0 | 99 | 0.0000 | 2.11 [2.10, 2.11] | 747 |
| peg | sweep:400 | 0.17 | terminal_ground | 100 | 0.01 | 0.00 | -0.01 | 1 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | twin | 100 | 0.01 | 0.87 | +0.86 | 0 | 86 | 0.0000 | 1.84 [1.79, 1.89] | 747 |
| peg | sweep:500 | 0.17 | gain | 100 | 0.00 | 0.92 | +0.92 | 0 | 92 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | twin | 100 | 0.00 | 0.74 | +0.74 | 0 | 74 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | gain | 99 | 0.00 | 0.94 | +0.94 | 0 | 93 | 0.0000 | nan [nan, nan] | 2000 |

## Zero-cell control (audit_strategies F3)

A latency hider must not gain on the zero-latency cell: a gain there is against the operator model, not against the link (selection.md section 4, H10 and H14 amendments). Flagged when a CI excludes zero in the positive direction; read such an arm's profile gains as the ratio of ratios (arm/baseline at the profile) / (arm/baseline at zero).

| task | arm | n | success diff [95 % CI] | demos/h ratio [95 % CI] | drop | flag |
|---|---|---|---|---|---|---|
| capture | gain | 100 | +0.00 [-0.07, +0.08] | 1.000 [0.913, 1.095] | 0 | ok |
| capture | twin | 100 | +0.07 [-0.00, +0.15] | 1.062 [0.965, 1.170] | 0 | ok |
| peg | gain | 100 | +0.00 [+0.00, +0.00] | 0.974 [0.972, 0.976] | 0 | ok |
