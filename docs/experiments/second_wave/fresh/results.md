# Experiment results

15 cells, 450 episodes. Baseline arm: `baseline`. Paired tests: `paired.md`. Curves: `curves.json`.

## Task `capture`

**Success rate (95 % Wilson CI)**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 0.60 [0.42,0.75] 18/30 | 0.03 [0.01,0.17] 1/30 | - |
| baseline [W2] | 0.70 [0.52,0.83] 21/30 | 0.57 [0.39,0.73] 17/30 | - | - | 0.43 [0.27,0.61] 13/30 |
| gain | - | - | - | - | 0.00 [0.00,0.11] 0/30 |
| twin | 0.80 [0.63,0.90] 24/30 | - | - | - | 0.70 [0.52,0.83] 21/30 |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 432.6 [166.2] | 642.9 [4.1] | - |
| baseline [W2] | 429.5 [212.4] | 444.8 [153.9] | - | - | 323.0 [96.5] |
| gain | - | - | - | - | 0.0 [0.0] |
| twin | 471.9 [285.1] | - | - | - | 392.1 [202.8] |

**RTT p50 / p95, ms**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 40 / 65 | 43 / 63 | - |
| baseline [W2] | 2 / 2 | 40 / 66 | - | - | 392 / 419 |
| gain | - | - | - | - | 392 / 419 |
| twin | 2 / 2 | - | - | - | 393 / 419 |

**link_unsafe = move_in_hold + vel_over + keepout (historical narrow sum)**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 0 | 0 | - |
| baseline [W2] | 0 | 0 | - | - | 0 |
| gain | - | - | - | - | 0 |
| twin | 0 | - | - | - | 0 |

**cage contacts (included in strict safety)**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 8 | 36 | - |
| baseline [W2] | 10 | 9 | - | - | 17 |
| gain | - | - | - | - | 8 |
| twin | 4 | - | - | - | 13 |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | -6.71 / -19.14 / 0.12 [sat] | -11.11 / -21.79 / 0.39 [sat] | - |
| baseline [W2] | -3.91 / -18.59 / 0.02 [sat] | -4.23 / -19.58 / 0.04 [sat] | - | - | -4.49 / -20.45 / 0.06 [sat] |
| gain | - | - | - | - | -7.77 / -20.75 / 0.05 [sat] |
| twin | -3.60 / -18.09 / 0.02 [sat] | - | - | - | -4.14 / -19.64 / 0.07 [sat] |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 0/30 | 0/30 | - |
| baseline [W2] | 0/30 | 0/30 | - | - | 0/30 |
| gain | - | - | - | - | 0/30 |
| twin | 0/30 | - | - | - | 0/30 |

**knockaway**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 26.00 | 29.00 | - |
| baseline [W2] | 28.00 | 30.00 | - | - | 34.00 |
| gain | - | - | - | - | 10.00 |
| twin | 28.00 | - | - | - | 34.00 |

**taut_frac**

| arm | zero | leo_relay | leo_relay_drop1 | leo_relay_drop12 | sweep:400 |
|---|---|---|---|---|---|
| baseline [S] | - | - | 0.00 | 0.00 | - |
| baseline [W2] | 0.00 | 0.00 | - | - | 0.00 |
| gain | - | - | - | - | 0.00 |
| twin | 0.00 | - | - | - | 0.00 |

## Task `peg`

**Success rate (95 % Wilson CI)**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 1.00 [0.89,1.00] 30/30 | 1.00 [0.89,1.00] 30/30 | 0.00 [0.00,0.11] 0/30 | 0.00 [0.00,0.11] 0/30 |
| deadreckon | - | - | 0.90 [0.74,0.97] 27/30 | - |
| terminal | - | - | - | 1.00 [0.89,1.00] 30/30 |
| terminal_ground | - | - | - | 0.00 [0.00,0.11] 0/30 |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 833.3 [833.3] | 819.4 [819.4] | 0.0 [0.0] | 0.0 [0.0] |
| deadreckon | - | - | 629.5 [397.7] | - |
| terminal | - | - | - | 634.9 [634.9] |
| terminal_ground | - | - | - | 0.0 [0.0] |

**RTT p50 / p95, ms**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 2 / 2 | 40 / 64 | 243 / 270 | 393 / 419 |
| deadreckon | - | - | 242 / 268 | - |
| terminal | - | - | - | 392 / 418 |
| terminal_ground | - | - | - | 394 / 420 |

**link_unsafe = move_in_hold + vel_over + keepout (historical narrow sum)**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0 | 0 | 0 | 0 |
| deadreckon | - | - | 0 | - |
| terminal | - | - | - | 0 |
| terminal_ground | - | - | - | 0 |

**cage contacts (included in strict safety)**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0 | 0 | 28 | 33 |
| deadreckon | - | - | 3 | - |
| terminal | - | - | - | 0 |
| terminal_ground | - | - | - | 15 |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | -2.26 / -16.35 / 0.04 [sat] | -3.40 / -17.15 / 0.07 [sat] | -1.98 / -23.51 / 0.06 [sat] | -2.29 / -23.59 / 0.05 [sat] |
| deadreckon | - | - | -4.08 / -17.78 / 0.08 [sat] | - |
| terminal | - | - | - | -3.28 / -17.83 / 0.11 [sat] |
| terminal_ground | - | - | - | -2.94 / -23.35 / 0.05 [sat] |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0/30 | 0/30 | 0/30 | 0/30 |
| deadreckon | - | - | 0/30 | - |
| terminal | - | - | - | 0/30 |
| terminal_ground | - | - | - | 0/30 |

**assist_frac**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - |
| terminal | - | - | - | 0.22 |
| terminal_ground | - | - | - | 0.18 |

**handback_peak**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - |
| terminal | - | - | - | 0.00 |
| terminal_ground | - | - | - | 12.44 |

**knockaway**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - |
| terminal | - | - | - | 0.00 |
| terminal_ground | - | - | - | 0.00 |

**taut_frac**

| arm | zero | leo_relay | sweep:250 | sweep:400 |
|---|---|---|---|---|
| baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| deadreckon | - | - | 0.00 | - |
| terminal | - | - | - | 0.00 |
| terminal_ground | - | - | - | 0.00 |

## Contaminated cells (T06: >= 3 episodes with a satellite cycle > 0.2 s)

None.

## Block S: forced dropout (leo_relay_drop1 / leo_relay_drop12)

Hold and retract are the counts the run reports; `link_unsafe` is the historical narrow counter sum. Cage is also required by the original safety gate.

| task | arm | profile | hold | retract | link_unsafe | cage | success |
|---|---|---|---|---|---|---|---|
| capture | baseline | leo_relay_drop1 | 29 | 0 | 0 | 8 | 0.60 18/30 |
| capture | baseline | leo_relay_drop12 | 29 | 29 | 0 | 36 | 0.03 1/30 |

## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell

| task | arm | zero success | threshold | knee (ms) |
|---|---|---|---|---|
| peg | baseline | 1.00 | 0.80 | ≤ 250 |

## Historical link-only acceptance screen (leo_relay / own zero cell)

| task | arm | success frac | demos/h frac | link_unsafe on zero, direct_gs, leo_relay, geo_relay | cage | historical gate | strict safety |
|---|---|---|---|---|---|---|---|
| capture | baseline | 0.81 | 1.04 | 0 (zero+leo_relay) | 19 | INCOMPLETE | FAIL |
| peg | baseline | 1.00 | 0.98 | 0 (zero+leo_relay) | 0 | INCOMPLETE | INCOMPLETE |

Historical amended screen: both fractions >= 0.80 and zero events in the **historical narrow counter sum**, with all four named profiles and their safety counters present. The original SYNTHESIS section 6 also gates cage contacts; strict safety includes those. ZERO_OBSERVED means zero measured events, not a safety certification. This is a point-estimate screen, not an uncertainty-qualified acceptance claim. The historical operator/task-caused label for cage contacts does not establish causal attribution or satisfy the original safety criterion.

### Footnotes

- Durations: taken from `duration_active_s` / `linger_excluded` as reported; no linger correction applied here.
- Smoothness: `[sat]` cells are recomputed here from the satellite applied-setpoint sidecar at ~780 Hz (audit T05: `observation.state` is 30 Hz held at 50 Hz, which puts a floor of ~0.4 under `stall_frac`); SAL uses padlevel 4 (T13). `[obs]` cells are the run's own numbers.
- `direct_gs` per-pass throughput = demos/hour x 9.2/60 (SYNTHESIS section 6: window-limited, report per pass).
- ⚠ marks a cell with >= 3 stalled episodes (T06).
