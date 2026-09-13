# Experiment results

34 cells, 3396 episodes. Baseline arm: `baseline`. Paired tests: `paired.md`. Curves: `curves.json`.

## Task `capture`

**Success rate (95 % Wilson CI)**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 0.69 [0.59,0.77] 69/100 | 0.65 [0.55,0.74] 65/100 | 0.52 [0.42,0.62] 52/100 | 0.44 [0.35,0.54] 44/100 | 0.33 [0.25,0.43] 33/100 | 0.22 [0.15,0.31] 22/99 |
| deadreckon | - | - | 0.57 [0.47,0.66] 57/100 | - | - | - |
| gain | 0.69 [0.59,0.77] 69/100 | - | - | 0.03 [0.01,0.08] 3/100 | - | - |
| terminal | - | 0.68 [0.58,0.76] 68/100 | - | - | 0.50 [0.40,0.60] 50/100 | - |
| twin | 0.76 [0.67,0.83] 76/100 | - | - | 0.72 [0.63,0.80] 72/100 | - | 0.61 [0.51,0.70] 60/99 |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 445.3 [210.9] | 455.8 [192.8] | 396.3 [130.7] | 350.9 [100.8] | 308.6 [49.6] | 268.2 [30.4] |
| deadreckon | - | - | 402.4 [149.8] | - | - | - |
| gain | 445.5 [210.9] | - | - | 229.3 [5.4] | - | - |
| terminal | - | 440.5 [204.7] | - | - | 311.8 [86.7] | - |
| twin | 473.0 [258.5] | - | - | 392.4 [212.4] | - | 332.7 [118.7] |

**RTT p50 / p95, ms**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 2 / 3 | 42 / 68 | 244 / 270 | 394 / 420 | 494 / 520 | nan / nan |
| deadreckon | - | - | 244 / 270 | - | - | - |
| gain | 2 / 3 | - | - | 394 / 420 | - | - |
| terminal | - | 42 / 68 | - | - | 494 / 520 | - |
| twin | 2 / 3 | - | - | 394 / 420 | - | nan / nan |

**link_unsafe = move_in_hold + vel_over + keepout (the section 6 gate)**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 0 | 0 | 0 | 0 | 0 | 0 |
| deadreckon | - | - | 0 | - | - | - |
| gain | 0 | - | - | 0 | - | - |
| terminal | - | 0 | - | - | 0 | - |
| twin | 0 | - | - | 0 | - | 0 |

**cage contacts (operator/task-caused, reported not gated)**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 38 | 40 | 55 | 62 | 81 | 92 |
| deadreckon | - | - | 51 | - | - | - |
| gain | 38 | - | - | 30 | - | - |
| terminal | - | 42 | - | - | 66 | - |
| twin | 33 | - | - | 42 | - | 67 |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | -3.90 / -18.50 / 0.02 [sat] | -4.17 / -19.20 / 0.04 [sat] | -4.09 / -19.80 / 0.06 [sat] | -4.46 / -20.21 / 0.06 [sat] | -4.35 / -21.56 / 0.06 [sat] | -4.12 / -21.45 / 0.05 [sat] |
| deadreckon | - | - | -4.14 / -19.44 / 0.06 [sat] | - | - | - |
| gain | -3.81 / -18.52 / 0.02 [sat] | - | - | -6.74 / -20.73 / 0.05 [sat] | - | - |
| terminal | - | -4.22 / -19.25 / 0.04 [sat] | - | - | -4.62 / -20.94 / 0.07 [sat] | - |
| twin | -3.91 / -18.11 / 0.02 [sat] | - | - | -4.51 / -19.47 / 0.07 [sat] | - | -4.83 / -20.06 / 0.07 [sat] |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 0/100 | 0/100 | 0/100 | 0/100 | 0/100 | 0/99 |
| deadreckon | - | - | 0/100 | - | - | - |
| gain | 0/100 | - | - | 0/100 | - | - |
| terminal | - | 0/100 | - | - | 0/100 | - |
| twin | 0/100 | - | - | 0/100 | - | 0/99 |

**assist_frac**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | - |
| terminal | - | 0.07 | - | - | 0.04 | - |
| twin | 0.00 | - | - | 0.00 | - | 0.00 |

**handback_peak**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | - |
| terminal | - | 2.00 | - | - | 2.00 | - |
| twin | 0.00 | - | - | 0.00 | - | 0.00 |

**knockaway**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 115.00 | 106.00 | 122.00 | 115.00 | 130.00 | 126.00 |
| deadreckon | - | - | 114.00 | - | - | - |
| gain | 106.00 | - | - | 38.00 | - | - |
| terminal | - | 118.00 | - | - | 132.00 | - |
| twin | 116.00 | - | - | 111.00 | - | 121.00 |

**taut_frac**

| arm | zero | leo_relay | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | - |
| terminal | - | 0.00 | - | - | 0.00 | - |
| twin | 0.00 | - | - | 0.00 | - | 0.00 |

## Task `peg`

**Success rate (95 % Wilson CI)**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0.98 [0.93,0.99] 98/100 | 0.97 [0.92,0.99] 97/100 | 0.84 [0.76,0.90] 84/100 | 0.11 [0.06,0.19] 11/100 | 0.01 [0.00,0.05] 1/100 | 0.00 [0.00,0.04] 0/100 | 0.00 [0.00,0.04] 0/99 |
| deadreckon | - | 0.99 [0.95,1.00] 99/100 | 0.98 [0.93,0.99] 98/100 | 0.88 [0.80,0.93] 88/100 | - | - | - |
| gain | 0.98 [0.93,0.99] 98/100 | - | - | 0.95 [0.89,0.98] 95/100 | - | 0.92 [0.85,0.96] 92/100 | 0.94 [0.87,0.97] 93/99 |
| terminal | - | 1.00 [0.96,1.00] 100/100 | - | - | 1.00 [0.96,1.00] 100/100 | - | - |
| terminal_ground | - | 0.56 [0.46,0.65] 56/100 | - | - | 0.00 [0.00,0.04] 0/100 | - | - |
| twin | - | - | - | - | 0.87 [0.79,0.92] 87/100 | 0.74 [0.65,0.82] 74/100 | - |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 841.0 [735.8] | 821.8 [678.2] | 801.5 [352.7] | 611.1 [14.5] | 302.5 [1.2] | 0.0 [0.0] | 0.0 [0.0] |
| deadreckon | - | 850.0 [793.2] | 830.7 [727.9] | 629.7 [367.0] | - | - | - |
| gain | 818.9 [718.8] | - | - | 428.5 [360.7] | - | 300.0 [246.4] | 268.5 [234.6] |
| terminal | - | 817.6 [817.6] | - | - | 636.9 [636.9] | - | - |
| terminal_ground | - | 828.9 [129.0] | - | - | 0.0 [0.0] | - | - |
| twin | - | - | - | - | 557.6 [329.1] | 418.1 [188.0] | - |

**RTT p50 / p95, ms**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 2 / 3 | 42 / 68 | 94 / 120 | 244 / 270 | 394 / 421 | 494 / 520 | nan / nan |
| deadreckon | - | 42 / 68 | 94 / 120 | 244 / 270 | - | - | - |
| gain | 2 / 3 | - | - | 244 / 271 | - | 494 / 520 | nan / nan |
| terminal | - | 42 / 68 | - | - | 394 / 420 | - | - |
| terminal_ground | - | 42 / 68 | - | - | 394 / 421 | - | - |
| twin | - | - | - | - | 394 / 420 | 494 / 520 | - |

**link_unsafe = move_in_hold + vel_over + keepout (the section 6 gate)**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| deadreckon | - | 0 | 0 | 0 | - | - | - |
| gain | 0 | - | - | 0 | - | 0 | 0 |
| terminal | - | 0 | - | - | 0 | - | - |
| terminal_ground | - | 0 | - | - | 0 | - | - |
| twin | - | - | - | - | 0 | 0 | - |

**cage contacts (operator/task-caused, reported not gated)**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 2 | 5 | 19 | 85 | 100 | 23 | 11 |
| deadreckon | - | 1 | 2 | 10 | - | - | - |
| gain | 2 | - | - | 5 | - | 5 | 3 |
| terminal | - | 0 | - | - | 0 | - | - |
| terminal_ground | - | 32 | - | - | 55 | - | - |
| twin | - | - | - | - | 9 | 12 | - |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | -2.27 / -16.50 / 0.04 [sat] | -3.39 / -17.28 / 0.06 [sat] | -3.25 / -18.21 / 0.07 [sat] | -2.23 / -23.02 / 0.06 [sat] | -2.29 / -23.61 / 0.05 [sat] | -2.87 / -24.14 / 0.04 [sat] | -3.00 / -23.84 / 0.03 [sat] |
| deadreckon | - | -3.65 / -16.26 / 0.05 [sat] | -3.67 / -16.38 / 0.06 [sat] | -4.00 / -18.00 / 0.08 [sat] | - | - | - |
| gain | -2.29 / -16.57 / 0.04 [sat] | - | - | -3.98 / -19.43 / 0.07 [sat] | - | -3.78 / -20.57 / 0.08 [sat] | -2.83 / -20.59 / 0.07 [sat] |
| terminal | - | -3.32 / -16.89 / 0.06 [sat] | - | - | -3.32 / -17.83 / 0.11 [sat] | - | - |
| terminal_ground | - | -2.86 / -19.72 / 0.06 [sat] | - | - | -2.91 / -23.35 / 0.04 [sat] | - | - |
| twin | - | - | - | - | -3.72 / -19.11 / 0.10 [sat] | -3.46 / -20.57 / 0.09 [sat] | - |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0/100 | 0/100 | 0/100 | 0/100 | 0/100 | 0/100 | 0/99 |
| deadreckon | - | 0/100 | 0/100 | 0/100 | - | - | - |
| gain | 0/100 | - | - | 0/100 | - | 0/100 | 0/99 |
| terminal | - | 0/100 | - | - | 0/100 | - | - |
| terminal_ground | - | 0/100 | - | - | 1/100 | - | - |
| twin | - | - | - | - | 0/100 | 0/100 | - |

**assist_frac**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | 0.00 | 0.00 | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | 0.00 | 0.00 |
| terminal | - | 0.24 | - | - | 0.23 | - | - |
| terminal_ground | - | 0.19 | - | - | 0.18 | - | - |
| twin | - | - | - | - | 0.00 | 0.00 | - |

**handback_peak**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | 0.00 | 0.00 | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | 0.00 | 0.00 |
| terminal | - | 0.00 | - | - | 0.00 | - | - |
| terminal_ground | - | 1.41 | - | - | 11.88 | - | - |
| twin | - | - | - | - | 0.00 | 0.00 | - |

**knockaway**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | 0.00 | 0.00 | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | 0.00 | 0.00 |
| terminal | - | 0.00 | - | - | 0.00 | - | - |
| terminal_ground | - | 0.00 | - | - | 0.00 | - | - |
| twin | - | - | - | - | 0.00 | 0.00 | - |

**taut_frac**

| arm | zero | leo_relay | sweep:100 | sweep:250 | sweep:400 | sweep:500 | geo_relay |
|---|---|---|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | 0.00 | 0.00 | 0.00 | - | - | - |
| gain | 0.00 | - | - | 0.00 | - | 0.00 | 0.00 |
| terminal | - | 0.00 | - | - | 0.00 | - | - |
| terminal_ground | - | 0.00 | - | - | 0.00 | - | - |
| twin | - | - | - | - | 0.00 | 0.00 | - |

## Contaminated cells (T06: >= 3 episodes with a satellite cycle > 0.2 s)

None.

## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell

| task | arm | zero success | threshold | knee (ms) |
|---|---|---|---|---|
| capture | baseline | 0.69 | 0.55 | 250 |
| peg | baseline | 0.98 | 0.78 | 112 |
| peg | gain | 0.98 | 0.78 | never (> 1000) |

## SYNTHESIS section 6 acceptance readout (leo_relay / own zero cell)

| task | arm | success frac | demos/h frac | link_unsafe on zero, direct_gs, leo_relay, geo_relay | cage (not gated) | gate |
|---|---|---|---|---|---|---|
| capture | baseline | 0.94 | 1.02 | 0 (zero+leo_relay+geo_relay) | 170 | PASS |
| peg | baseline | 0.99 | 0.98 | 0 (zero+leo_relay+geo_relay) | 18 | PASS |

Acceptance (PROGRAM.md, SYNTHESIS section 6): both fractions >= 0.80 and zero **link-caused** unsafe events. `cage` is the arm touching the cage while the operator chases a drifting box; it fires at zero latency on every arm (audit T07), so it is reported as operator/task-caused and does not gate.

### Footnotes

- Durations: taken from `duration_active_s` / `linger_excluded` as reported; no linger correction applied here.
- Smoothness: `[sat]` cells are recomputed here from the satellite applied-setpoint sidecar at ~780 Hz (audit T05: `observation.state` is 30 Hz held at 50 Hz, which puts a floor of ~0.4 under `stall_frac`); SAL uses padlevel 4 (T13). `[obs]` cells are the run's own numbers.
- `direct_gs` per-pass throughput = demos/hour x 9.2/60 (SYNTHESIS section 6: window-limited, report per pass).
- ⚠ marks a cell with >= 3 stalled episodes (T06).
