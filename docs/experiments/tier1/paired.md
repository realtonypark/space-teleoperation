# Paired comparisons

Same seeds per cell, so success is a McNemar test on the discordant seeds (`b` = `baseline` only, `c` = arm only; two-sided exact binomial). demos/hour ratio is arm / baseline with a paired bootstrap 95 % CI (2000 resamples of the seed list); `drop` is how many resamples were thrown away because one arm had no success in them (audit T20 - the CI is narrowed by exactly those).

| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | demos/h ratio [95 % CI] | drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| capture | sweep:0 | 0.17 | deadreckon | 30 | 0.67 | 0.60 | -0.07 | 2 | 0 | 0.5000 | 1.03 [0.92, 1.15] | 0 |
| capture | zero | 0.17 | deadreckon | 30 | 0.63 | 0.60 | -0.03 | 3 | 2 | 1.0000 | 1.04 [0.90, 1.20] | 0 |
| capture | sweep:0 | 0.17 | gain | 30 | 0.67 | 0.60 | -0.07 | 2 | 0 | 0.5000 | 0.96 [0.85, 1.11] | 0 |
| capture | zero | 0.17 | gain | 30 | 0.63 | 0.63 | +0.00 | 1 | 1 | 1.0000 | 0.94 [0.80, 1.06] | 0 |
| capture | sweep:0 | 0.17 | terminal | 30 | 0.67 | 0.63 | -0.03 | 2 | 1 | 1.0000 | 1.00 [0.86, 1.14] | 0 |
| capture | zero | 0.17 | terminal | 30 | 0.63 | 0.60 | -0.03 | 3 | 2 | 1.0000 | 0.98 [0.85, 1.11] | 0 |
| capture | sweep:0 | 0.17 | terminal_ground | 30 | 0.67 | 0.67 | +0.00 | 0 | 0 | 1.0000 | 1.01 [0.96, 1.09] | 0 |
| capture | zero | 0.17 | terminal_ground | 30 | 0.63 | 0.60 | -0.03 | 2 | 1 | 1.0000 | 1.04 [0.96, 1.14] | 0 |
| capture | sweep:0 | 0.17 | twin | 30 | 0.67 | 0.67 | +0.00 | 3 | 3 | 1.0000 | 1.05 [0.92, 1.21] | 0 |
| capture | zero | 0.17 | twin | 30 | 0.63 | 0.67 | +0.03 | 1 | 2 | 1.0000 | 1.03 [0.90, 1.16] | 0 |
| capture | direct_gs | 0.17 | deadreckon | 30 | 0.63 | 0.60 | -0.03 | 3 | 2 | 1.0000 | 1.13 [0.95, 1.31] | 0 |
| capture | direct_gs | 0.17 | gain | 30 | 0.63 | 0.57 | -0.07 | 2 | 0 | 0.5000 | 1.02 [0.90, 1.17] | 0 |
| capture | direct_gs | 0.17 | terminal | 30 | 0.63 | 0.63 | +0.00 | 2 | 2 | 1.0000 | 1.07 [0.90, 1.26] | 0 |
| capture | direct_gs | 0.17 | terminal_ground | 30 | 0.63 | 0.60 | -0.03 | 2 | 1 | 1.0000 | 1.13 [0.98, 1.30] | 0 |
| capture | direct_gs | 0.17 | twin | 30 | 0.63 | 0.67 | +0.03 | 3 | 4 | 1.0000 | 1.13 [0.93, 1.33] | 0 |
| capture | leo_relay | 0.17 | deadreckon | 30 | 0.60 | 0.63 | +0.03 | 1 | 2 | 1.0000 | 1.02 [0.91, 1.14] | 0 |
| capture | leo_relay | 0.25 | deadreckon | 30 | 0.60 | 0.67 | +0.07 | 1 | 3 | 0.6250 | 1.00 [0.92, 1.08] | 0 |
| capture | leo_relay_drop12 | 0.17 | deadreckon | 30 | 0.20 | 0.23 | +0.03 | 1 | 2 | 1.0000 | 1.06 [0.49, 2.17] | 0 |
| capture | leo_relay_drop1 | 0.17 | deadreckon | 30 | 0.60 | 0.60 | +0.00 | 2 | 2 | 1.0000 | 1.03 [0.90, 1.21] | 0 |
| capture | leo_relay | 0.17 | gain | 30 | 0.60 | 0.63 | +0.03 | 1 | 2 | 1.0000 | 0.79 [0.68, 0.93] | 0 |
| capture | leo_relay | 0.25 | gain | 30 | 0.60 | 0.53 | -0.07 | 3 | 1 | 0.6250 | 0.94 [0.88, 1.04] | 0 |
| capture | leo_relay_drop12 | 0.17 | gain | 30 | 0.20 | 0.13 | -0.07 | 4 | 2 | 0.6875 | 0.42 [0.23, 0.96] | 27 |
| capture | leo_relay_drop1 | 0.17 | gain | 30 | 0.60 | 0.67 | +0.07 | 1 | 3 | 0.6250 | 0.80 [0.73, 0.87] | 0 |
| capture | leo_relay | 0.17 | terminal | 30 | 0.60 | 0.73 | +0.13 | 0 | 4 | 0.1250 | 0.90 [0.76, 1.05] | 0 |
| capture | leo_relay | 0.25 | terminal | 30 | 0.60 | 0.60 | +0.00 | 2 | 2 | 1.0000 | 0.98 [0.92, 1.04] | 0 |
| capture | leo_relay_drop12 | 0.17 | terminal | 30 | 0.20 | 0.30 | +0.10 | 1 | 4 | 0.3750 | 0.66 [0.32, 1.44] | 0 |
| capture | leo_relay_drop1 | 0.17 | terminal | 30 | 0.60 | 0.60 | +0.00 | 3 | 3 | 1.0000 | 0.96 [0.82, 1.14] | 0 |
| capture | leo_relay | 0.17 | terminal_ground | 30 | 0.60 | 0.63 | +0.03 | 2 | 3 | 1.0000 | 1.01 [0.88, 1.14] | 0 |
| capture | leo_relay_drop12 | 0.17 | terminal_ground | 30 | 0.20 | 0.23 | +0.03 | 1 | 2 | 1.0000 | 0.92 [0.40, 2.10] | 2 |
| capture | leo_relay_drop1 | 0.17 | terminal_ground | 30 | 0.60 | 0.60 | +0.00 | 2 | 2 | 1.0000 | 1.04 [0.92, 1.20] | 0 |
| capture | leo_relay | 0.17 | twin | 30 | 0.60 | 0.67 | +0.07 | 2 | 4 | 0.6875 | 1.04 [0.90, 1.19] | 0 |
| capture | leo_relay | 0.25 | twin | 30 | 0.60 | 0.63 | +0.03 | 2 | 3 | 1.0000 | 1.05 [0.96, 1.14] | 0 |
| capture | leo_relay_drop12 | 0.17 | twin | 30 | 0.20 | 0.37 | +0.17 | 0 | 5 | 0.0625 | 0.94 [0.45, 2.03] | 0 |
| capture | leo_relay_drop1 | 0.17 | twin | 30 | 0.60 | 0.63 | +0.03 | 3 | 4 | 1.0000 | 1.10 [0.94, 1.29] | 0 |
| capture | sweep:100 | 0.17 | deadreckon | 30 | 0.60 | 0.63 | +0.03 | 2 | 3 | 1.0000 | 1.03 [0.92, 1.17] | 0 |
| capture | sweep:100 | 0.17 | gain | 30 | 0.60 | 0.60 | +0.00 | 5 | 5 | 1.0000 | 0.73 [0.63, 0.86] | 0 |
| capture | sweep:100 | 0.17 | terminal | 30 | 0.60 | 0.63 | +0.03 | 3 | 4 | 1.0000 | 0.98 [0.88, 1.11] | 0 |
| capture | sweep:100 | 0.17 | terminal_ground | 30 | 0.60 | 0.67 | +0.07 | 1 | 3 | 0.6250 | 0.98 [0.86, 1.13] | 0 |
| capture | sweep:100 | 0.17 | twin | 30 | 0.60 | 0.77 | +0.17 | 2 | 7 | 0.1797 | 1.01 [0.87, 1.16] | 0 |
| capture | sweep:250 | 0.17 | deadreckon | 30 | 0.50 | 0.53 | +0.03 | 2 | 3 | 1.0000 | 1.02 [0.94, 1.09] | 0 |
| capture | sweep:250 | 0.17 | gain | 30 | 0.50 | 0.23 | -0.27 | 8 | 0 | 0.0078 | 0.51 [0.46, 0.60] | 0 |
| capture | sweep:250 | 0.17 | terminal | 30 | 0.50 | 0.60 | +0.10 | 1 | 4 | 0.3750 | 0.89 [0.79, 0.98] | 0 |
| capture | sweep:250 | 0.17 | terminal_ground | 30 | 0.50 | 0.60 | +0.10 | 1 | 4 | 0.3750 | 0.88 [0.77, 0.99] | 0 |
| capture | sweep:250 | 0.17 | twin | 30 | 0.50 | 0.63 | +0.13 | 2 | 6 | 0.2891 | 0.96 [0.78, 1.18] | 0 |
| capture | sweep:400 | 0.17 | deadreckon | 30 | 0.43 | 0.40 | -0.03 | 2 | 1 | 1.0000 | 1.20 [1.04, 1.38] | 0 |
| capture | sweep:400 | 0.25 | deadreckon | 30 | 0.40 | 0.43 | +0.03 | 2 | 3 | 1.0000 | 1.06 [0.94, 1.21] | 0 |
| capture | sweep:400 | 0.17 | gain | 30 | 0.43 | 0.03 | -0.40 | 12 | 0 | 0.0005 | 0.86 [0.75, 0.96] | 742 |
| capture | sweep:400 | 0.25 | gain | 30 | 0.40 | 0.10 | -0.30 | 10 | 1 | 0.0117 | 0.60 [0.52, 0.67] | 76 |
| capture | sweep:400 | 0.17 | terminal | 30 | 0.43 | 0.30 | -0.13 | 5 | 1 | 0.2188 | 1.08 [0.96, 1.26] | 0 |
| capture | sweep:400 | 0.25 | terminal | 30 | 0.40 | 0.30 | -0.10 | 4 | 1 | 0.3750 | 1.07 [0.97, 1.23] | 0 |
| capture | sweep:400 | 0.17 | terminal_ground | 30 | 0.43 | 0.30 | -0.13 | 4 | 0 | 0.1250 | 1.10 [0.99, 1.23] | 0 |
| capture | sweep:400 | 0.17 | twin | 30 | 0.43 | 0.70 | +0.27 | 0 | 8 | 0.0078 | 1.21 [1.00, 1.46] | 0 |
| capture | sweep:400 | 0.25 | twin | 30 | 0.40 | 0.53 | +0.13 | 3 | 7 | 0.3438 | 1.17 [1.02, 1.33] | 0 |
| capture | sweep:500 | 0.17 | deadreckon | 30 | 0.30 | 0.43 | +0.13 | 1 | 5 | 0.2188 | 1.00 [0.86, 1.14] | 0 |
| capture | sweep:500 | 0.17 | gain | 30 | 0.30 | 0.07 | -0.23 | 8 | 1 | 0.0391 | 0.42 [0.36, 0.48] | 225 |
| capture | sweep:500 | 0.17 | terminal | 30 | 0.30 | 0.37 | +0.07 | 0 | 2 | 0.5000 | 0.97 [0.93, 1.00] | 0 |
| capture | sweep:500 | 0.17 | terminal_ground | 30 | 0.30 | 0.30 | +0.00 | 1 | 1 | 1.0000 | 0.87 [0.65, 1.14] | 0 |
| capture | sweep:500 | 0.17 | twin | 30 | 0.30 | 0.47 | +0.17 | 2 | 7 | 0.1797 | 1.16 [1.01, 1.34] | 0 |
| capture | geo_relay | 0.17 | deadreckon | 30 | 0.17 | 0.20 | +0.03 | 1 | 2 | 1.0000 | 1.48 [1.07, 2.00] | 9 |
| capture | geo_relay | 0.25 | deadreckon | 30 | 0.17 | 0.17 | +0.00 | 2 | 2 | 1.0000 | 0.96 [0.79, 1.10] | 19 |
| capture | geo_relay | 0.17 | gain | 30 | 0.17 | 0.03 | -0.13 | 5 | 1 | 0.2188 | 0.61 [0.42, 0.81] | 679 |
| capture | geo_relay | 0.25 | gain | 30 | 0.17 | 0.03 | -0.13 | 5 | 1 | 0.2188 | 0.48 [0.42, 0.52] | 717 |
| capture | geo_relay | 0.17 | terminal | 30 | 0.17 | 0.27 | +0.10 | 1 | 4 | 0.3750 | 1.38 [0.95, 1.89] | 9 |
| capture | geo_relay | 0.25 | terminal | 30 | 0.17 | 0.33 | +0.17 | 0 | 5 | 0.0625 | 0.96 [0.87, 1.06] | 13 |
| capture | geo_relay | 0.17 | terminal_ground | 30 | 0.17 | 0.23 | +0.07 | 3 | 5 | 0.7266 | 1.29 [0.88, 1.99] | 9 |
| capture | geo_relay | 0.17 | twin | 30 | 0.17 | 0.47 | +0.30 | 2 | 11 | 0.0225 | 1.59 [1.07, 2.16] | 9 |
| capture | geo_relay | 0.25 | twin | 30 | 0.17 | 0.50 | +0.33 | 2 | 12 | 0.0129 | 1.00 [0.81, 1.22] | 13 |
| capture | sweep:750 | 0.17 | deadreckon | 30 | 0.27 | 0.17 | -0.10 | 5 | 2 | 0.4531 | 1.29 [1.05, 1.58] | 14 |
| capture | sweep:750 | 0.17 | gain | 30 | 0.27 | 0.00 | -0.27 | 8 | 0 | 0.0078 | nan [nan, nan] | 2000 |
| capture | sweep:750 | 0.17 | terminal | 30 | 0.27 | 0.43 | +0.17 | 2 | 7 | 0.1797 | 1.12 [0.91, 1.42] | 1 |
| capture | sweep:750 | 0.17 | terminal_ground | 30 | 0.27 | 0.23 | -0.03 | 3 | 2 | 1.0000 | 1.18 [0.97, 1.43] | 5 |
| capture | sweep:750 | 0.17 | twin | 30 | 0.27 | 0.53 | +0.27 | 3 | 11 | 0.0574 | 1.29 [1.01, 1.69] | 1 |
| capture | sweep:1000 | 0.17 | deadreckon | 30 | 0.20 | 0.20 | +0.00 | 2 | 2 | 1.0000 | 1.01 [0.75, 1.36] | 2 |
| capture | sweep:1000 | 0.17 | gain | 30 | 0.20 | 0.00 | -0.20 | 6 | 0 | 0.0312 | nan [nan, nan] | 2000 |
| capture | sweep:1000 | 0.17 | terminal | 30 | 0.20 | 0.30 | +0.10 | 3 | 6 | 0.5078 | 1.13 [0.97, 1.34] | 2 |
| capture | sweep:1000 | 0.17 | terminal_ground | 30 | 0.20 | 0.17 | -0.03 | 3 | 2 | 1.0000 | 1.13 [0.89, 1.49] | 13 |
| capture | sweep:1000 | 0.17 | twin | 30 | 0.20 | 0.53 | +0.33 | 4 | 14 | 0.0309 | 1.43 [1.10, 1.88] | 2 |
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
| capture | deadreckon | 30 | -0.03 [-0.17, +0.13] | 1.042 [0.895, 1.197] | 0 | ok |
| capture | gain | 30 | +0.00 [-0.10, +0.10] | 0.940 [0.802, 1.057] | 0 | ok |
| capture | terminal | 30 | -0.03 [-0.17, +0.10] | 0.982 [0.849, 1.107] | 0 | ok |
| capture | terminal_ground | 30 | -0.03 [-0.13, +0.07] | 1.042 [0.964, 1.143] | 0 | ok |
| capture | twin | 30 | +0.03 [-0.07, +0.17] | 1.031 [0.899, 1.156] | 0 | ok |
| peg | deadreckon | 30 | +0.03 [+0.00, +0.10] | 1.021 [1.016, 1.025] | 0 | ⚠ gain at zero latency |
| peg | gain | 30 | +0.00 [+0.00, +0.00] | 0.972 [0.968, 0.976] | 0 | ok |
| peg | terminal | 30 | +0.03 [+0.00, +0.10] | 1.007 [1.002, 1.012] | 0 | ⚠ gain at zero latency |
| peg | terminal_ground | 30 | +0.00 [+0.00, +0.00] | 1.008 [1.003, 1.013] | 0 | ⚠ gain at zero latency |
| peg | twin | 30 | +0.03 [+0.00, +0.10] | 0.999 [0.994, 1.004] | 0 | ok |
