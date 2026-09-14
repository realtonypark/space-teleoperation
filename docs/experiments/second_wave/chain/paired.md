# Paired comparisons

Same seeds per cell, so success is a McNemar test on the discordant seeds (`b` = `baseline` only, `c` = arm only; two-sided exact binomial). demos/hour ratio is arm / baseline with a paired bootstrap 95 % CI (2000 resamples of the seed list); `drop` is how many resamples were thrown away because one arm had no success in them. With drops, this is a conditional interval and does not establish unconditional 95 % coverage. Gross throughput below retains failure durations. Holm p-values adjust all success comparisons in this file. Bootstrap intervals are exploratory, pointwise, and can degenerate at all-success/all-failure boundaries.

| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | demos/h ratio [95 % CI] | drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (no non-baseline arm has a paired baseline cell yet) |

## Failure-inclusive throughput and multiplicity

Gross demos/hour = 3600 × successes / total active attempt duration; reset wall time is included only when the recorded duration contains it.

| task | profile | arm | block | gross demos/h difference [95 % bootstrap CI] | Holm p |
|---|---|---|---|---|---|

## Zero-cell control (audit_strategies F3)

A latency hider must not gain on the zero-latency cell: a gain there is against the operator model, not against the link (selection.md section 4, H10 and H14 amendments). Flagged when a CI excludes zero in the positive direction; read such an arm's profile gains as the ratio of ratios (arm/baseline at the profile) / (arm/baseline at zero).

| task | arm | n | success diff [95 % CI] | demos/h ratio [95 % CI] | drop | flag |
|---|---|---|---|---|---|---|
| (no arm has a paired `zero` cell yet) |
