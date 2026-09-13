# Paired comparisons

Same seeds per cell, so success is a McNemar test on the discordant seeds (`b` = `baseline` only, `c` = arm only; two-sided exact binomial). demos/hour ratio is arm / baseline with a paired bootstrap 95 % CI (2000 resamples of the seed list); `drop` is how many resamples were thrown away because one arm had no success in them (audit T20 - the CI is narrowed by exactly those).

`deadreckon` leads the baseline by 90 ms, not the nominal 60 ms (audit_strategies F1).

| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | demos/h ratio [95 % CI] | drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| capture | sweep:0 | 0.17 | deadreckon | 30 | 0.70 | 0.77 | +0.07 | 1 | 3 | 0.6250 | 1.11 [0.91, 1.36] | 0 |
| capture | zero | 0.17 | deadreckon | 30 | 0.67 | 0.73 | +0.07 | 1 | 3 | 0.6250 | 1.03 [0.89, 1.14] | 0 |
| capture | sweep:0 | 0.17 | gain | 30 | 0.70 | 0.67 | -0.03 | 1 | 0 | 1.0000 | 1.10 [1.00, 1.26] | 0 |
| capture | zero | 0.17 | gain | 30 | 0.67 | 0.60 | -0.07 | 3 | 1 | 0.6250 | 0.96 [0.85, 1.04] | 0 |
| capture | sweep:0 | 0.17 | terminal | 30 | 0.70 | 0.73 | +0.03 | 1 | 2 | 1.0000 | 1.11 [0.91, 1.36] | 0 |
| capture | zero | 0.17 | terminal | 30 | 0.67 | 0.70 | +0.03 | 0 | 1 | 1.0000 | 1.03 [1.00, 1.08] | 0 |
| capture | sweep:0 | 0.17 | terminal_ground | 30 | 0.70 | 0.67 | -0.03 | 1 | 0 | 1.0000 | 1.16 [0.99, 1.39] | 0 |
| capture | zero | 0.17 | terminal_ground | 30 | 0.67 | 0.67 | +0.00 | 1 | 1 | 1.0000 | 1.03 [0.99, 1.09] | 0 |
| capture | sweep:0 | 0.17 | twin | 30 | 0.70 | 0.73 | +0.03 | 1 | 2 | 1.0000 | 1.13 [0.89, 1.40] | 0 |
| capture | zero | 0.17 | twin | 30 | 0.67 | 0.63 | -0.03 | 2 | 1 | 1.0000 | 1.18 [1.07, 1.34] | 0 |
| capture | direct_gs | 0.17 | deadreckon | 30 | 0.63 | 0.67 | +0.03 | 0 | 1 | 1.0000 | 1.13 [1.05, 1.25] | 0 |
| capture | direct_gs | 0.17 | gain | 30 | 0.63 | 0.67 | +0.03 | 1 | 2 | 1.0000 | 0.92 [0.80, 1.03] | 0 |
| capture | direct_gs | 0.17 | terminal | 30 | 0.63 | 0.70 | +0.07 | 0 | 2 | 0.5000 | 1.05 [0.99, 1.16] | 0 |
| capture | direct_gs | 0.17 | terminal_ground | 30 | 0.63 | 0.67 | +0.03 | 0 | 1 | 1.0000 | 1.05 [0.99, 1.14] | 0 |
| capture | direct_gs | 0.17 | twin | 30 | 0.63 | 0.70 | +0.07 | 1 | 3 | 0.6250 | 1.16 [1.03, 1.34] | 0 |
| capture | leo_relay | 0.17 | deadreckon | 30 | 0.63 | 0.67 | +0.03 | 0 | 1 | 1.0000 | 1.11 [1.04, 1.22] | 0 |
| capture | leo_relay | 0.25 | deadreckon | 30 | 0.60 | 0.67 | +0.07 | 1 | 3 | 0.6250 | 1.04 [0.95, 1.14] | 0 |
| capture | leo_relay | 0.17 | gain | 30 | 0.63 | 0.57 | -0.07 | 2 | 0 | 0.5000 | 0.95 [0.85, 1.04] | 0 |
| capture | leo_relay | 0.25 | gain | 30 | 0.60 | 0.57 | -0.03 | 2 | 1 | 1.0000 | 0.83 [0.75, 0.92] | 0 |
| capture | leo_relay | 0.17 | terminal | 30 | 0.63 | 0.63 | +0.00 | 1 | 1 | 1.0000 | 1.09 [1.00, 1.21] | 0 |
| capture | leo_relay | 0.25 | terminal | 30 | 0.60 | 0.70 | +0.10 | 1 | 4 | 0.3750 | 1.05 [0.95, 1.17] | 0 |
| capture | leo_relay | 0.17 | terminal_ground | 30 | 0.63 | 0.63 | +0.00 | 1 | 1 | 1.0000 | 1.00 [0.93, 1.09] | 0 |
| capture | leo_relay | 0.17 | twin | 30 | 0.63 | 0.67 | +0.03 | 1 | 2 | 1.0000 | 1.18 [1.05, 1.37] | 0 |
| capture | leo_relay | 0.25 | twin | 30 | 0.60 | 0.67 | +0.07 | 2 | 4 | 0.6875 | 1.12 [0.97, 1.29] | 0 |
| capture | sweep:100 | 0.17 | deadreckon | 30 | 0.63 | 0.73 | +0.10 | 0 | 3 | 0.2500 | 1.03 [0.95, 1.09] | 0 |
| capture | sweep:100 | 0.17 | gain | 30 | 0.63 | 0.60 | -0.03 | 2 | 1 | 1.0000 | 0.90 [0.85, 0.95] | 0 |
| capture | sweep:100 | 0.17 | terminal | 30 | 0.63 | 0.67 | +0.03 | 1 | 2 | 1.0000 | 0.99 [0.87, 1.10] | 0 |
| capture | sweep:100 | 0.17 | terminal_ground | 30 | 0.63 | 0.63 | +0.00 | 1 | 1 | 1.0000 | 0.93 [0.80, 1.03] | 0 |
| capture | sweep:100 | 0.17 | twin | 30 | 0.63 | 0.73 | +0.10 | 1 | 4 | 0.3750 | 1.06 [0.97, 1.17] | 0 |
| capture | sweep:250 | 0.17 | deadreckon | 30 | 0.53 | 0.53 | +0.00 | 2 | 2 | 1.0000 | 1.04 [0.88, 1.21] | 0 |
| capture | sweep:250 | 0.17 | gain | 30 | 0.53 | 0.53 | +0.00 | 4 | 4 | 1.0000 | 0.63 [0.57, 0.72] | 0 |
| capture | sweep:250 | 0.17 | terminal | 30 | 0.53 | 0.53 | +0.00 | 1 | 1 | 1.0000 | 1.01 [0.90, 1.14] | 0 |
| capture | sweep:250 | 0.17 | terminal_ground | 30 | 0.53 | 0.53 | +0.00 | 1 | 1 | 1.0000 | 1.00 [0.87, 1.14] | 0 |
| capture | sweep:250 | 0.17 | twin | 30 | 0.53 | 0.70 | +0.17 | 1 | 6 | 0.1250 | 1.11 [0.93, 1.32] | 0 |
| capture | sweep:400 | 0.17 | deadreckon | 30 | 0.37 | 0.40 | +0.03 | 1 | 2 | 1.0000 | 0.98 [0.85, 1.06] | 0 |
| capture | sweep:400 | 0.25 | deadreckon | 30 | 0.33 | 0.43 | +0.10 | 1 | 4 | 0.3750 | 1.07 [0.89, 1.27] | 0 |
| capture | sweep:400 | 0.17 | gain | 30 | 0.37 | 0.20 | -0.17 | 7 | 2 | 0.1797 | 0.55 [0.50, 0.61] | 2 |
| capture | sweep:400 | 0.25 | gain | 30 | 0.33 | 0.10 | -0.23 | 8 | 1 | 0.0391 | 0.60 [0.51, 0.73] | 76 |
| capture | sweep:400 | 0.17 | terminal | 30 | 0.37 | 0.47 | +0.10 | 0 | 3 | 0.2500 | 0.95 [0.88, 1.00] | 0 |
| capture | sweep:400 | 0.25 | terminal | 30 | 0.33 | 0.37 | +0.03 | 1 | 2 | 1.0000 | 1.02 [0.91, 1.17] | 0 |
| capture | sweep:400 | 0.17 | terminal_ground | 30 | 0.37 | 0.33 | -0.03 | 1 | 0 | 1.0000 | 1.01 [0.98, 1.05] | 0 |
| capture | sweep:400 | 0.17 | twin | 30 | 0.37 | 0.57 | +0.20 | 2 | 8 | 0.1094 | 0.97 [0.84, 1.12] | 0 |
| capture | sweep:400 | 0.25 | twin | 30 | 0.33 | 0.47 | +0.13 | 2 | 6 | 0.2891 | 1.10 [0.89, 1.32] | 0 |
| capture | sweep:500 | 0.17 | deadreckon | 30 | 0.30 | 0.37 | +0.07 | 3 | 5 | 0.7266 | 1.21 [1.00, 1.47] | 0 |
| capture | sweep:500 | 0.17 | gain | 30 | 0.30 | 0.20 | -0.10 | 6 | 3 | 0.5078 | 0.52 [0.41, 0.66] | 6 |
| capture | sweep:500 | 0.17 | terminal | 30 | 0.30 | 0.37 | +0.07 | 2 | 4 | 0.6875 | 1.07 [0.83, 1.38] | 0 |
| capture | sweep:500 | 0.17 | terminal_ground | 30 | 0.30 | 0.23 | -0.07 | 2 | 0 | 0.5000 | 0.88 [0.64, 1.19] | 1 |
| capture | sweep:500 | 0.17 | twin | 30 | 0.30 | 0.50 | +0.20 | 4 | 10 | 0.1796 | 1.08 [0.84, 1.42] | 0 |
| capture | geo_relay | 0.17 | deadreckon | 30 | 0.20 | 0.23 | +0.03 | 4 | 5 | 1.0000 | 1.05 [0.78, 1.43] | 3 |
| capture | geo_relay | 0.25 | deadreckon | 30 | 0.10 | 0.23 | +0.13 | 0 | 4 | 0.1250 | 0.76 [0.52, 1.12] | 85 |
| capture | geo_relay | 0.17 | gain | 30 | 0.20 | 0.10 | -0.10 | 6 | 3 | 0.5078 | 0.57 [0.43, 0.74] | 83 |
| capture | geo_relay | 0.25 | gain | 30 | 0.10 | 0.07 | -0.03 | 3 | 2 | 1.0000 | 0.44 [0.37, 0.50] | 306 |
| capture | geo_relay | 0.17 | terminal | 30 | 0.20 | 0.30 | +0.10 | 3 | 6 | 0.5078 | 1.09 [0.79, 1.50] | 1 |
| capture | geo_relay | 0.25 | terminal | 30 | 0.10 | 0.40 | +0.30 | 0 | 9 | 0.0039 | 0.91 [0.76, 1.03] | 85 |
| capture | geo_relay | 0.17 | terminal_ground | 30 | 0.20 | 0.17 | -0.03 | 4 | 3 | 1.0000 | 0.82 [0.58, 1.14] | 8 |
| capture | geo_relay | 0.17 | twin | 30 | 0.20 | 0.53 | +0.33 | 3 | 13 | 0.0213 | 1.30 [1.00, 1.71] | 1 |
| capture | geo_relay | 0.25 | twin | 30 | 0.10 | 0.53 | +0.43 | 0 | 13 | 0.0002 | 0.97 [0.81, 1.17] | 85 |
| capture | sweep:750 | 0.17 | deadreckon | 30 | 0.27 | 0.20 | -0.07 | 2 | 0 | 0.5000 | 0.83 [0.57, 1.13] | 1 |
| capture | sweep:750 | 0.17 | gain | 30 | 0.27 | 0.07 | -0.20 | 7 | 1 | 0.0703 | 0.51 [0.43, 0.62] | 256 |
| capture | sweep:750 | 0.17 | terminal | 30 | 0.27 | 0.40 | +0.13 | 1 | 5 | 0.2188 | 1.00 [0.79, 1.28] | 1 |
| capture | sweep:750 | 0.17 | terminal_ground | 30 | 0.27 | 0.30 | +0.03 | 1 | 2 | 1.0000 | 0.90 [0.76, 1.05] | 1 |
| capture | sweep:750 | 0.17 | twin | 30 | 0.27 | 0.47 | +0.20 | 4 | 10 | 0.1796 | 1.17 [0.93, 1.51] | 1 |
| capture | sweep:1000 | 0.17 | deadreckon | 30 | 0.17 | 0.13 | -0.03 | 4 | 3 | 1.0000 | 1.73 [1.39, 2.13] | 34 |
| capture | sweep:1000 | 0.17 | gain | 30 | 0.17 | 0.00 | -0.17 | 5 | 0 | 0.0625 | nan [nan, nan] | 2000 |
| capture | sweep:1000 | 0.17 | terminal | 30 | 0.17 | 0.27 | +0.10 | 2 | 5 | 0.4531 | 1.62 [1.29, 2.05] | 7 |
| capture | sweep:1000 | 0.17 | terminal_ground | 30 | 0.17 | 0.13 | -0.03 | 2 | 1 | 1.0000 | 1.03 [0.77, 1.44] | 43 |
| capture | sweep:1000 | 0.17 | twin | 30 | 0.17 | 0.50 | +0.33 | 4 | 14 | 0.0309 | 1.61 [1.23, 2.10] | 7 |
| peg | sweep:0 | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.04 [1.03, 1.04] | 0 |
| peg | zero | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.04 [1.03, 1.04] | 0 |
| peg | sweep:0 | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.00 [1.00, 1.00] | 0 |
| peg | zero | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.00 [1.00, 1.00] | 0 |
| peg | sweep:0 | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | zero | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | sweep:0 | 0.17 | terminal_ground | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | zero | 0.17 | terminal_ground | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.01 [1.01, 1.01] | 0 |
| peg | sweep:0 | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [0.99, 1.00] | 0 |
| peg | zero | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [1.00, 1.01] | 0 |
| peg | direct_gs | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.04 [1.04, 1.05] | 0 |
| peg | direct_gs | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 1.00 [0.99, 1.00] | 0 |
| peg | direct_gs | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.00 [1.00, 1.01] | 0 |
| peg | direct_gs | 0.17 | terminal_ground | 30 | 0.97 | 0.87 | -0.10 | 3 | 0 | 0.2500 | 1.01 [1.00, 1.01] | 0 |
| peg | direct_gs | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.01] | 0 |
| peg | leo_relay | 0.17 | deadreckon | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.04 [1.03, 1.05] | 0 |
| peg | leo_relay | 0.25 | deadreckon | 30 | 0.13 | 0.97 | +0.83 | 0 | 25 | 0.0000 | 1.12 [1.05, 1.32] | 24 |
| peg | leo_relay | 0.17 | gain | 30 | 0.97 | 0.97 | +0.00 | 0 | 0 | 1.0000 | 0.99 [0.99, 1.00] | 0 |
| peg | leo_relay | 0.25 | gain | 30 | 0.13 | 0.83 | +0.70 | 0 | 21 | 0.0000 | 0.91 [0.85, 1.07] | 24 |
| peg | leo_relay | 0.17 | terminal | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 0.99 [0.98, 0.99] | 0 |
| peg | leo_relay | 0.25 | terminal | 30 | 0.13 | 1.00 | +0.87 | 0 | 26 | 0.0000 | 1.02 [0.96, 1.21] | 24 |
| peg | leo_relay | 0.17 | terminal_ground | 30 | 0.97 | 0.23 | -0.73 | 22 | 0 | 0.0000 | 1.00 [0.99, 1.01] | 2 |
| peg | leo_relay | 0.17 | twin | 30 | 0.97 | 1.00 | +0.03 | 0 | 1 | 1.0000 | 1.01 [1.00, 1.02] | 0 |
| peg | leo_relay | 0.25 | twin | 30 | 0.13 | 0.97 | +0.83 | 0 | 25 | 0.0000 | 1.07 [0.99, 1.28] | 24 |
| peg | sweep:100 | 0.17 | deadreckon | 30 | 0.77 | 0.97 | +0.20 | 0 | 6 | 0.0312 | 1.05 [1.05, 1.06] | 0 |
| peg | sweep:100 | 0.17 | gain | 30 | 0.77 | 0.87 | +0.10 | 0 | 3 | 0.2500 | 0.91 [0.90, 0.92] | 0 |
| peg | sweep:100 | 0.17 | terminal | 30 | 0.77 | 1.00 | +0.23 | 0 | 7 | 0.0156 | 0.97 [0.97, 0.98] | 0 |
| peg | sweep:100 | 0.17 | terminal_ground | 30 | 0.77 | 0.00 | -0.77 | 23 | 0 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:100 | 0.17 | twin | 30 | 0.77 | 0.97 | +0.20 | 0 | 6 | 0.0312 | 1.02 [1.01, 1.03] | 0 |
| peg | sweep:250 | 0.17 | deadreckon | 30 | 0.07 | 0.97 | +0.90 | 0 | 27 | 0.0000 | 1.06 [1.05, 1.06] | 240 |
| peg | sweep:250 | 0.17 | gain | 30 | 0.07 | 0.60 | +0.53 | 2 | 18 | 0.0004 | 0.85 [0.83, 0.87] | 240 |
| peg | sweep:250 | 0.17 | terminal | 30 | 0.07 | 1.00 | +0.93 | 0 | 28 | 0.0000 | 1.15 [1.15, 1.16] | 240 |
| peg | sweep:250 | 0.17 | terminal_ground | 30 | 0.07 | 0.00 | -0.07 | 2 | 0 | 0.5000 | nan [nan, nan] | 2000 |
| peg | sweep:250 | 0.17 | twin | 30 | 0.07 | 0.97 | +0.90 | 1 | 28 | 0.0000 | 1.16 [1.14, 1.19] | 240 |
| peg | sweep:400 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | gain | 30 | 0.00 | 0.83 | +0.83 | 0 | 25 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | gain | 30 | 0.00 | 0.30 | +0.30 | 0 | 9 | 0.0039 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.17 | twin | 30 | 0.00 | 0.70 | +0.70 | 0 | 21 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:400 | 0.25 | twin | 30 | 0.00 | 0.77 | +0.77 | 0 | 23 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | gain | 30 | 0.00 | 0.27 | +0.27 | 0 | 8 | 0.0078 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:500 | 0.17 | twin | 30 | 0.00 | 0.80 | +0.80 | 0 | 24 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | gain | 30 | 0.00 | 0.23 | +0.23 | 0 | 7 | 0.0156 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | gain | 30 | 0.00 | 0.23 | +0.23 | 0 | 7 | 0.0156 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.17 | twin | 30 | 0.00 | 0.10 | +0.10 | 0 | 3 | 0.2500 | nan [nan, nan] | 2000 |
| peg | geo_relay | 0.25 | twin | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | gain | 30 | 0.00 | 0.23 | +0.23 | 0 | 7 | 0.0156 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:750 | 0.17 | twin | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | deadreckon | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | gain | 30 | 0.00 | 0.27 | +0.27 | 0 | 8 | 0.0078 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | terminal | 30 | 0.00 | 1.00 | +1.00 | 0 | 30 | 0.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | terminal_ground | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |
| peg | sweep:1000 | 0.17 | twin | 30 | 0.00 | 0.00 | +0.00 | 0 | 0 | 1.0000 | nan [nan, nan] | 2000 |

## Zero-cell control (audit_strategies F3)

A latency hider must not gain on the zero-latency cell: a gain there is against the operator model, not against the link (selection.md section 4, H10 and H14 amendments). Flagged when a CI excludes zero in the positive direction; read such an arm's profile gains as the ratio of ratios (arm/baseline at the profile) / (arm/baseline at zero).

| task | arm | n | success diff [95 % CI] | demos/h ratio [95 % CI] | drop | flag |
|---|---|---|---|---|---|---|
| capture | deadreckon | 30 | +0.07 [-0.07, +0.20] | 1.026 [0.892, 1.145] | 0 | ok |
| capture | gain | 30 | -0.07 [-0.20, +0.07] | 0.957 [0.851, 1.043] | 0 | ok |
| capture | terminal | 30 | +0.03 [+0.00, +0.10] | 1.027 [0.997, 1.075] | 0 | ok |
| capture | terminal_ground | 30 | +0.00 [-0.10, +0.10] | 1.030 [0.994, 1.088] | 0 | ok |
| capture | twin | 30 | -0.03 [-0.17, +0.07] | 1.175 [1.066, 1.341] | 0 | ⚠ gain at zero latency |
| peg | deadreckon | 30 | +0.03 [+0.00, +0.10] | 1.037 [1.033, 1.041] | 0 | ⚠ gain at zero latency |
| peg | gain | 30 | +0.00 [+0.00, +0.00] | 0.998 [0.996, 1.000] | 0 | ok |
| peg | terminal | 30 | +0.03 [+0.00, +0.10] | 1.008 [1.004, 1.012] | 0 | ⚠ gain at zero latency |
| peg | terminal_ground | 30 | +0.00 [+0.00, +0.00] | 1.010 [1.006, 1.014] | 0 | ⚠ gain at zero latency |
| peg | twin | 30 | +0.03 [+0.00, +0.10] | 1.003 [1.001, 1.006] | 0 | ⚠ gain at zero latency |
