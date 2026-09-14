# Experiment results

3 cells, 30 episodes. Baseline arm: `baseline`. Paired tests: `paired.md`. Curves: `curves.json`.

## Task `peg`

**Success rate (95 % Wilson CI)**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 1.00 [0.72,1.00] 10/10 | 1.00 [0.72,1.00] 10/10 | - |
| terminal | - | - | 1.00 [0.72,1.00] 10/10 |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 833.3 [833.3] | 816.3 [816.3] | - |
| terminal | - | - | 634.9 [634.9] |

**RTT p50 / p95, ms**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 2 / 2 | 39 / 66 | - |
| terminal | - | - | 391 / 417 |

**link_unsafe = move_in_hold + vel_over + keepout (historical narrow sum)**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0 | 0 | - |
| terminal | - | - | 0 |

**cage contacts (included in strict safety)**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0 | 0 | - |
| terminal | - | - | 0 |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | -2.29 / -16.32 / 0.04 [sat] | -3.52 / -17.12 / 0.07 [sat] | - |
| terminal | - | - | -3.48 / -17.91 / 0.11 [sat] |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0/10 | 0/10 | - |
| terminal | - | - | 0/10 |

**assist_frac**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0.00 | 0.00 | - |
| terminal | - | - | 0.22 |

**handback_peak**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0.00 | 0.00 | - |
| terminal | - | - | 0.00 |

**knockaway**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0.00 | 0.00 | - |
| terminal | - | - | 0.00 |

**taut_frac**

| arm | zero | leo_relay | sweep:400 |
|---|---|---|---|
| baseline | 0.00 | 0.00 | - |
| terminal | - | - | 0.00 |

## Contaminated cells (T06: >= 3 episodes with a satellite cycle > 0.2 s)

None.

## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell

| task | arm | zero success | threshold | knee (ms) |
|---|---|---|---|---|
| (no arm has a `zero` cell and >= 2 sweep points yet) |

## Historical link-only acceptance screen (leo_relay / own zero cell)

| task | arm | success frac | demos/h frac | link_unsafe on zero, direct_gs, leo_relay, geo_relay | cage | historical gate | strict safety |
|---|---|---|---|---|---|---|---|
| peg | baseline | 1.00 | 0.98 | 0 (zero+leo_relay) | 0 | INCOMPLETE | INCOMPLETE |

Historical amended screen: both fractions >= 0.80 and zero events in the **historical narrow counter sum**, with all four named profiles and their safety counters present. The original SYNTHESIS section 6 also gates cage contacts; strict safety includes those. ZERO_OBSERVED means zero measured events, not a safety certification. This is a point-estimate screen, not an uncertainty-qualified acceptance claim. The historical operator/task-caused label for cage contacts does not establish causal attribution or satisfy the original safety criterion.

### Footnotes

- Durations: taken from `duration_active_s` / `linger_excluded` as reported; no linger correction applied here.
- Smoothness: `[sat]` cells are recomputed here from the satellite applied-setpoint sidecar at ~780 Hz (audit T05: `observation.state` is 30 Hz held at 50 Hz, which puts a floor of ~0.4 under `stall_frac`); SAL uses padlevel 4 (T13). `[obs]` cells are the run's own numbers.
- `direct_gs` per-pass throughput = demos/hour x 9.2/60 (SYNTHESIS section 6: window-limited, report per pass).
- ⚠ marks a cell with >= 3 stalled episodes (T06).
