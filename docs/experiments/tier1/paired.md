# Paired comparisons

Same seeds per cell, so success is a McNemar test on the discordant seeds (`b` = `baseline` only, `c` = arm only; two-sided exact binomial). demos/hour ratio is arm / baseline with a paired bootstrap 95 % CI (2000 resamples of the seed list); `drop` is how many resamples were thrown away because one arm had no success in them (audit T20 - the CI is narrowed by exactly those).

| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | demos/h ratio [95 % CI] | drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| capture | sweep:0 | 0.17 | deadreckon | 30 | 0.67 | 0.67 | +0.00 | 0 | 0 | 1.0000 | 1.05 [1.02, 1.09] | 0 |
| capture | zero | 0.17 | deadreckon | 30 | 0.67 | 0.70 | +0.03 | 0 | 1 | 1.0000 | 1.01 [0.93, 1.08] | 0 |
| capture | sweep:0 | 0.17 | gain | 30 | 0.67 | 0.70 | +0.03 | 1 | 2 | 1.0000 | 0.89 [0.78, 0.97] | 0 |
| capture | zero | 0.17 | gain | 30 | 0.67 | 0.77 | +0.10 | 0 | 3 | 0.2500 | 0.86 [0.74, 0.98] | 0 |
| capture | sweep:0 | 0.17 | terminal | 30 | 0.67 | 0.73 | +0.07 | 0 | 2 | 0.5000 | 0.92 [0.79, 0.99] | 0 |
| capture | zero | 0.17 | terminal | 30 | 0.67 | 0.67 | +0.00 | 0 | 0 | 1.0000 | 0.99 [0.99, 1.00] | 0 |
| capture | sweep:0 | 0.17 | terminal_ground | 30 | 0.67 | 0.63 | -0.03 | 1 | 0 | 1.0000 | 1.04 [0.99, 1.15] | 0 |
| capture | zero | 0.17 | terminal_ground | 30 | 0.67 | 0.63 | -0.03 | 1 | 0 | 1.0000 | 1.04 [0.98, 1.16] | 0 |
| capture | sweep:0 | 0.17 | twin | 30 | 0.67 | 0.80 | +0.13 | 1 | 5 | 0.2188 | 0.92 [0.77, 1.07] | 0 |
| capture | zero | 0.17 | twin | 30 | 0.67 | 0.77 | +0.10 | 0 | 3 | 0.2500 | 0.94 [0.80, 1.07] | 0 |
| capture | direct_gs | 0.17 | deadreckon | 30 | 0.70 | 0.67 | -0.03 | 1 | 0 | 1.0000 | 1.11 [1.04, 1.25] | 0 |
| capture | direct_gs | 0.17 | gain | 30 | 0.70 | 0.70 | +0.00 | 1 | 1 | 1.0000 | 0.89 [0.83, 0.93] | 0 |
| capture | direct_gs | 0.17 | terminal | 30 | 0.70 | 0.67 | -0.03 | 1 | 0 | 1.0000 | 1.06 [0.99, 1.19] | 0 |
| capture | direct_gs | 0.17 | terminal_ground | 30 | 0.70 | 0.63 | -0.07 | 2 | 0 | 0.5000 | 1.11 [0.99, 1.26] | 0 |
| capture | direct_gs | 0.17 | twin | 30 | 0.70 | 0.67 | -0.03 | 2 | 1 | 1.0000 | 1.18 [1.06, 1.35] | 0 |
| capture | leo_relay | 0.17 | deadreckon | 30 | 0.67 | 0.70 | +0.03 | 0 | 1 | 1.0000 | 1.02 [0.99, 1.05] | 0 |
| capture | leo_relay | 0.25 | deadreckon | 30 | 0.63 | 0.67 | +0.03 | 1 | 2 | 1.0000 | 1.04 [0.97, 1.12] | 0 |
| capture | leo_relay_drop12 | 0.17 | deadreckon | 30 | 0.20 | 0.30 | +0.10 | 0 | 3 | 0.2500 | 0.58 [0.35, 1.05] | 3 |
| capture | leo_relay_drop1 | 0.17 | deadreckon | 30 | 0.70 | 0.70 | +0.00 | 1 | 1 | 1.0000 | 1.02 [0.88, 1.17] | 0 |
| capture | leo_relay | 0.17 | gain | 30 | 0.67 | 0.67 | +0.00 | 1 | 1 | 1.0000 | 0.84 [0.79, 0.87] | 0 |
| capture | leo_relay | 0.25 | gain | 30 | 0.63 | 0.63 | +0.00 | 2 | 2 | 1.0000 | 0.86 [0.80, 0.92] | 0 |
| capture | leo_relay_drop12 | 0.17 | gain | 30 | 0.20 | 0.10 | -0.10 | 5 | 2 | 0.4531 | 0.31 [0.23, 1.01] | 82 |
| capture | leo_relay_drop1 | 0.17 | gain | 30 | 0.70 | 0.67 | -0.03 | 3 | 2 | 1.0000 | 0.87 [0.79, 1.00] | 0 |
| capture | leo_relay | 0.17 | terminal | 30 | 0.67 | 0.73 | +0.07 | 0 | 2 | 0.5000 | 0.92 [0.82, 0.99] | 0 |
| capture | leo_relay | 0.25 | terminal | 30 | 0.63 | 0.67 | +0.03 | 1 | 2 | 1.0000 | 1.00 [0.95, 1.08] | 0 |
| capture | leo_relay_drop12 | 0.17 | terminal | 30 | 0.20 | 0.27 | +0.07 | 0 | 2 | 0.5000 | 0.60 [0.38, 1.00] | 3 |
| capture | leo_relay_drop1 | 0.17 | terminal | 30 | 0.70 | 0.63 | -0.07 | 2 | 0 | 0.5000 | 1.10 [0.99, 1.27] | 0 |
| capture | leo_relay | 0.17 | terminal_ground | 30 | 0.67 | 0.70 | +0.03 | 1 | 2 | 1.0000 | 0.98 [0.88, 1.11] | 0 |
| capture | leo_relay_drop12 | 0.17 | terminal_ground | 30 | 0.20 | 0.20 | +0.00 | 0 | 0 | 1.0000 | 1.00 [0.99, 1.00] | 3 |
| capture | leo_relay_drop1 | 0.17 | terminal_ground | 30 | 0.70 | 0.63 | -0.07 | 2 | 0 | 0.5000 | 1.04 [0.96, 1.18] | 0 |
| capture | leo_relay | 0.17 | twin | 30 | 0.67 | 0.73 | +0.07 | 1 | 3 | 0.6250 | 1.04 [0.96, 1.12] | 0 |
| capture | leo_relay | 0.25 | twin | 30 | 0.63 | 0.73 | +0.10 | 1 | 4 | 0.3750 | 1.00 [0.85, 1.13] | 0 |
| capture | leo_relay_drop12 | 0.17 | twin | 30 | 0.20 | 0.40 | +0.20 | 0 | 6 | 0.0312 | 0.66 [0.42, 1.08] | 3 |
| capture | leo_relay_drop1 | 0.17 | twin | 30 | 0.70 | 0.60 | -0.10 | 3 | 0 | 0.2500 | 1.23 [1.08, 1.45] | 0 |
| capture | sweep:100 | 0.17 | deadreckon | 30 | 0.67 | 0.73 | +0.07 | 0 | 2 | 0.5000 | 0.98 [0.87, 1.06] | 0 |
| capture | sweep:100 | 0.17 | gain | 30 | 0.67 | 0.60 | -0.07 | 5 | 3 | 0.7266 | 0.71 [0.63, 0.82] | 0 |
| capture | sweep:100 | 0.17 | terminal | 30 | 0.67 | 0.73 | +0.07 | 0 | 2 | 0.5000 | 0.98 [0.90, 1.04] | 0 |
| capture | sweep:100 | 0.17 | terminal_ground | 30 | 0.67 | 0.70 | +0.03 | 0 | 1 | 1.0000 | 1.01 [0.99, 1.05] | 0 |
| capture | sweep:100 | 0.17 | twin | 30 | 0.67 | 0.73 | +0.07 | 1 | 3 | 0.6250 | 1.07 [0.96, 1.17] | 0 |
| capture | sweep:250 | 0.17 | deadreckon | 30 | 0.53 | 0.53 | +0.00 | 1 | 1 | 1.0000 | 1.10 [1.05, 1.18] | 0 |
| capture | sweep:250 | 0.17 | gain | 30 | 0.53 | 0.27 | -0.27 | 8 | 0 | 0.0078 | 0.57 [0.51, 0.66] | 0 |
| capture | sweep:250 | 0.17 | terminal | 30 | 0.53 | 0.60 | +0.07 | 0 | 2 | 0.5000 | 0.99 [0.94, 1.03] | 0 |
| capture | sweep:250 | 0.17 | terminal_ground | 30 | 0.53 | 0.53 | +0.00 | 3 | 3 | 1.0000 | 0.97 [0.84, 1.09] | 0 |
| capture | sweep:250 | 0.17 | twin | 30 | 0.53 | 0.73 | +0.20 | 1 | 7 | 0.0703 | 1.05 [0.89, 1.22] | 0 |
| capture | sweep:400 | 0.17 | deadreckon | 30 | 0.37 | 0.40 | +0.03 | 0 | 1 | 1.0000 | 1.13 [1.04, 1.28] | 0 |
| capture | sweep:400 | 0.25 | deadreckon | 30 | 0.40 | 0.43 | +0.03 | 2 | 3 | 1.0000 | 0.97 [0.88, 1.07] | 0 |
| capture | sweep:400 | 0.17 | gain | 30 | 0.37 | 0.03 | -0.33 | 10 | 0 | 0.0020 | 0.81 [0.72, 0.90] | 742 |
| capture | sweep:400 | 0.25 | gain | 30 | 0.40 | 0.10 | -0.30 | 10 | 1 | 0.0117 | 0.58 [0.52, 0.68] | 76 |
| capture | sweep:400 | 0.17 | terminal | 30 | 0.37 | 0.43 | +0.07 | 0 | 2 | 0.5000 | 0.97 [0.84, 1.12] | 0 |
| capture | sweep:400 | 0.25 | terminal | 30 | 0.40 | 0.37 | -0.03 | 1 | 0 | 1.0000 | 1.01 [0.98, 1.08] | 0 |
| capture | sweep:400 | 0.17 | terminal_ground | 30 | 0.37 | 0.30 | -0.07 | 2 | 0 | 0.5000 | 1.05 [0.98, 1.18] | 0 |
| capture | sweep:400 | 0.17 | twin | 30 | 0.37 | 0.67 | +0.30 | 0 | 9 | 0.0039 | 1.23 [1.07, 1.42] | 0 |
| capture | sweep:400 | 0.25 | twin | 30 | 0.40 | 0.63 | +0.23 | 1 | 8 | 0.0391 | 0.97 [0.85, 1.11] | 0 |
| capture | sweep:500 | 0.17 | deadreckon | 30 | 0.33 | 0.40 | +0.07 | 2 | 4 | 0.6875 | 1.06 [0.90, 1.22] | 0 |
| capture | sweep:500 | 0.17 | gain | 30 | 0.33 | 0.10 | -0.23 | 9 | 2 | 0.0654 | 0.43 [0.36, 0.51] | 81 |
| capture | sweep:500 | 0.17 | terminal | 30 | 0.33 | 0.43 | +0.10 | 0 | 3 | 0.2500 | 0.97 [0.80, 1.14] | 0 |
| capture | sweep:500 | 0.17 | terminal_ground | 30 | 0.33 | 0.33 | +0.00 | 2 | 2 | 1.0000 | 0.88 [0.68, 1.15] | 0 |
| capture | sweep:500 | 0.17 | twin | 30 | 0.33 | 0.67 | +0.33 | 1 | 11 | 0.0063 | 0.98 [0.80, 1.18] | 0 |
| capture | geo_relay | 0.17 | deadreckon | 30 | 0.10 | 0.23 | +0.13 | 1 | 5 | 0.2188 | 1.30 [0.94, 1.90] | 82 |
| capture | geo_relay | 0.25 | deadreckon | 30 | 0.23 | 0.27 | +0.03 | 3 | 4 | 1.0000 | 1.02 [0.82, 1.29] | 1 |
| capture | geo_relay | 0.17 | gain | 30 | 0.10 | 0.03 | -0.07 | 3 | 1 | 0.6250 | 0.54 [0.42, 0.77] | 726 |
| capture | geo_relay | 0.25 | gain | 30 | 0.23 | 0.07 | -0.17 | 7 | 2 | 0.1797 | 0.56 [0.46, 0.68] | 226 |
| capture | geo_relay | 0.17 | terminal | 30 | 0.10 | 0.27 | +0.17 | 1 | 6 | 0.1250 | 1.33 [0.98, 1.99] | 82 |
| capture | geo_relay | 0.25 | terminal | 30 | 0.23 | 0.33 | +0.10 | 0 | 3 | 0.2500 | 1.16 [0.94, 1.46] | 1 |
| capture | geo_relay | 0.17 | terminal_ground | 30 | 0.10 | 0.27 | +0.17 | 1 | 6 | 0.1250 | 1.03 [0.71, 1.49] | 83 |
| capture | geo_relay | 0.17 | twin | 30 | 0.10 | 0.53 | +0.43 | 1 | 14 | 0.0010 | 1.27 [0.83, 2.00] | 82 |
| capture | geo_relay | 0.25 | twin | 30 | 0.23 | 0.53 | +0.30 | 1 | 10 | 0.0117 | 1.26 [0.96, 1.67] | 1 |
| capture | sweep:750 | 0.17 | deadreckon | 30 | 0.27 | 0.23 | -0.03 | 4 | 3 | 1.0000 | 0.96 [0.68, 1.34] | 1 |
| capture | sweep:750 | 0.17 | gain | 30 | 0.27 | 0.00 | -0.27 | 8 | 0 | 0.0078 | nan [nan, nan] | 2000 |
| capture | sweep:750 | 0.17 | terminal | 30 | 0.27 | 0.33 | +0.07 | 2 | 4 | 0.6875 | 1.05 [0.89, 1.30] | 1 |
| capture | sweep:750 | 0.17 | terminal_ground | 30 | 0.27 | 0.13 | -0.13 | 5 | 1 | 0.2188 | 1.15 [0.96, 1.43] | 30 |
| capture | sweep:750 | 0.17 | twin | 30 | 0.27 | 0.63 | +0.37 | 2 | 13 | 0.0074 | 1.19 [0.96, 1.48] | 1 |
| capture | sweep:1000 | 0.17 | deadreckon | 30 | 0.17 | 0.20 | +0.03 | 1 | 2 | 1.0000 | 0.99 [0.92, 1.05] | 8 |
| capture | sweep:1000 | 0.17 | gain | 30 | 0.17 | 0.00 | -0.17 | 5 | 0 | 0.0625 | nan [nan, nan] | 2000 |
| capture | sweep:1000 | 0.17 | terminal | 30 | 0.17 | 0.33 | +0.17 | 1 | 6 | 0.1250 | 1.09 [0.97, 1.25] | 7 |
| capture | sweep:1000 | 0.17 | terminal_ground | 30 | 0.17 | 0.17 | +0.00 | 2 | 2 | 1.0000 | 0.96 [0.85, 1.10] | 16 |
| capture | sweep:1000 | 0.17 | twin | 30 | 0.17 | 0.50 | +0.33 | 2 | 12 | 0.0129 | 1.27 [1.08, 1.52] | 7 |
| peg | sweep:0 | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.03 [1.02, 1.03] | 0 |
| peg | zero | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.02 [1.02, 1.02] | 0 |
| peg | sweep:0 | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.95 [0.94, 0.95] | 0 |
| peg | zero | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.97 [0.97, 0.98] | 0 |
| peg | sweep:0 | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [1.00, 1.01] | 0 |
| peg | zero | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | sweep:0 | 0.17 | terminal_ground | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | zero | 0.17 | terminal_ground | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | sweep:0 | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | zero | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [0.99, 1.00] | 0 |
| peg | direct_gs | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.03 [1.03, 1.03] | 0 |
| peg | direct_gs | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.90 [0.89, 0.90] | 0 |
| peg | direct_gs | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [1.00, 1.01] | 0 |
| peg | direct_gs | 0.17 | terminal_ground | 30 | 0.97 | 0.90 | -0.07 | 2 | 0 | 0.5000 | 1.00 [1.00, 1.01] | 0 |
| peg | direct_gs | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | leo_relay | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.03 [1.03, 1.04] | 0 |
| peg | leo_relay | 0.25 | deadreckon | 30 | 0.30 | 0.97 | +0.67 | 0 | 20 | 0.0000 | 1.04 [1.03, 1.05] | 0 |
| peg | leo_relay_drop12 | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.03 [1.03, 1.04] | 0 |
| peg | leo_relay_drop1 | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.03 [1.03, 1.04] | 0 |
| peg | leo_relay | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.85 [0.85, 0.86] | 0 |
| peg | leo_relay | 0.25 | gain | 30 | 0.30 | 0.83 | +0.53 | 0 | 16 | 0.0000 | 0.89 [0.89, 0.90] | 0 |
| peg | leo_relay_drop12 | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.85 [0.85, 0.86] | 0 |
| peg | leo_relay_drop1 | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.85 [0.85, 0.86] | 0 |
| peg | leo_relay | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [0.99, 1.00] | 0 |
| peg | leo_relay | 0.25 | terminal | 30 | 0.30 | 1.00 | +0.70 | 0 | 21 | 0.0000 | 0.97 [0.96, 0.98] | 0 |
| peg | leo_relay_drop12 | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [0.99, 1.00] | 0 |
| peg | leo_relay_drop1 | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [0.99, 1.00] | 0 |
| peg | leo_relay | 0.17 | terminal_ground | 30 | 0.97 | 0.63 | -0.33 | 11 | 1 | 0.0063 | 1.00 [1.00, 1.01] | 0 |
| peg | leo_relay_drop12 | 0.17 | terminal_ground | 30 | 0.97 | 0.53 | -0.43 | 13 | 0 | 0.0002 | 1.01 [1.00, 1.01] | 0 |
| peg | leo_relay_drop1 | 0.17 | terminal_ground | 30 | 0.97 | 0.63 | -0.33 | 10 | 0 | 0.0020 | 1.01 [1.00, 1.01] | 0 |
| peg | leo_relay | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | leo_relay | 0.25 | twin | 30 | 0.30 | 0.97 | +0.67 | 0 | 20 | 0.0000 | 1.03 [1.02, 1.04] | 0 |
| peg | leo_relay_drop12 | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | leo_relay_drop1 | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | sweep:100 | 0.17 | deadreckon | 30 | 0.77 | 0.97 | +0.20 | 0 | 6 | 0.0312 | 1.04 [1.04, 1.05] | 0 |
| peg | sweep:100 | 0.17 | gain | 30 | 0.77 | 0.97 | +0.20 | 0 | 6 | 0.0312 | 0.75 [0.75, 0.76] | 0 |
| peg | sweep:100 | 0.17 | terminal | 30 | 0.77 | 1.00 | +0.23 | 0 | 7 | 0.0156 | 0.97 [0.97, 0.98] | 0 |
| peg | sweep:100 | 0.17 | terminal_ground | 30 | 0.77 | 0.00 | -0.77 | 23 | 0 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:100 | 0.17 | twin | 30 | 0.77 | 1.00 | +0.23 | 0 | 7 | 0.0156 | 1.02 [1.01, 1.03] | 0 |
| peg | sweep:250 | 0.17 | deadreckon | 30 | 0.17 | 0.83 | +0.67 | 0 | 20 | 0.0000 | 1.03 [1.02, 1.05] | 9 |
| peg | sweep:250 | 0.17 | gain | 30 | 0.17 | 0.93 | +0.77 | 2 | 25 | 0.0000 | 0.70 [0.69, 0.71] | 9 |
| peg | sweep:250 | 0.17 | terminal | 30 | 0.17 | 1.00 | +0.83 | 0 | 25 | 0.0000 | 1.15 [1.13, 1.16] | 9 |
| peg | sweep:250 | 0.17 | terminal_ground | 30 | 0.17 | 0.03 | -0.13 | 5 | 1 | 0.2188 | 1.05 [1.04, 1.06] | 750 |
| peg | sweep:250 | 0.17 | twin | 30 | 0.17 | 0.97 | +0.80 | 1 | 25 | 0.0000 | 1.16 [1.13, 1.19] | 9 |
| peg | sweep:400 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | gain | 30 | 0.00 | 0.93 | +0.93 | 0 | 28 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | gain | 30 | 0.00 | 0.27 | +0.27 | 0 | 8 | 0.0078 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | twin | 30 | 0.00 | 0.97 | +0.97 | 0 | 29 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | twin | 30 | 0.00 | 0.57 | +0.57 | 0 | 17 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | gain | 30 | 0.00 | 0.93 | +0.93 | 0 | 28 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | twin | 30 | 0.00 | 0.83 | +0.83 | 0 | 25 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | gain | 30 | 0.00 | 0.93 | +0.93 | 0 | 28 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | gain | 30 | 0.00 | 0.23 | +0.23 | 0 | 7 | 0.0156 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | twin | 30 | 0.00 | 0.03 | +0.03 | 0 | 1 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | twin | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | gain | 30 | 0.00 | 0.97 | +0.97 | 0 | 29 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | twin | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | gain | 30 | 0.00 | 0.93 | +0.93 | 0 | 28 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | twin | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |

## Zero-cell control (audit_strategies F3)

A latency hider must not gain on the zero-latency cell: a gain there is against the operator model, not against the link (selection.md section 4, H10 and H14 amendments). Flagged when a CI excludes zero in the positive direction; read such an arm's profile gains as the ratio of ratios (arm/baseline at the profile) / (arm/baseline at zero).

| task | arm | n | success diff [95 % CI] | demos/h ratio [95 % CI] | drop | flag |
|---|---|---|---|---|---|---|
| capture | deadreckon | 30 | +0.03 [+0.00, +0.10] | 1.011 [0.926, 1.075] | 0 | ok |
| capture | gain | 30 | +0.10 [+0.00, +0.20] | 0.859 [0.735, 0.978] | 0 | ok |
| capture | terminal | 30 | +0.00 [+0.00, +0.00] | 0.991 [0.986, 0.996] | 0 | ok |
| capture | terminal_ground | 30 | -0.03 [-0.10, +0.00] | 1.036 [0.981, 1.156] | 0 | ok |
| capture | twin | 30 | +0.10 [+0.00, +0.20] | 0.939 [0.796, 1.073] | 0 | ok |
| peg | deadreckon | 30 | +0.03 [+0.00, +0.10] | 1.021 [1.016, 1.025] | 0 | ⚠ gain at zero latency |
| peg | gain | 30 | +0.00 [+0.00, +0.00] | 0.972 [0.968, 0.976] | 0 | ok |
| peg | terminal | 30 | +0.03 [+0.00, +0.10] | 1.007 [1.002, 1.012] | 0 | ⚠ gain at zero latency |
| peg | terminal_ground | 30 | +0.00 [+0.00, +0.00] | 1.008 [1.003, 1.013] | 0 | ⚠ gain at zero latency |
| peg | twin | 30 | +0.03 [+0.00, +0.10] | 0.999 [0.994, 1.004] | 0 | ok |
