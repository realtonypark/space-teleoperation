# Experiment results

4 cells, 20 episodes. Baseline arm: `baseline`. Paired tests: `paired.md`. Curves: `curves.json`.

## Task `capture_chain`

**Success rate (95 % Wilson CI)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 1.00 [0.57,1.00] 5/5 |
| baseline [C3000] | 1.00 [0.57,1.00] 5/5 |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 489.1 [489.1] |
| baseline [C3000] | 511.4 [511.4] |

**RTT p50 / p95, ms**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 41 / 66 |
| baseline [C3000] | 41 / 65 |

**link_unsafe = move_in_hold + vel_over + keepout (historical narrow sum)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 0 |
| baseline [C3000] | 0 |

**cage contacts (included in strict safety)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 1 |
| baseline [C3000] | 0 |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | -9.64 / -17.96 / 0.05 [sat] |
| baseline [C3000] | -9.57 / -17.83 / 0.04 [sat] |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 0/5 |
| baseline [C3000] | 0/5 |

**knockaway**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 2.00 |
| baseline [C3000] | 3.00 |

**taut_frac**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 0.05 |
| baseline [C3000] | 0.00 |

## Task `capture_chain_teleop`

**Success rate (95 % Wilson CI)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 1.00 [0.57,1.00] 5/5 |
| baseline [C3000] | 1.00 [0.57,1.00] 5/5 |

**demos/hour (gross in brackets; direct_gs also per 9.2-min pass)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 396.5 [396.5] |
| baseline [C3000] | 418.6 [418.6] |

**RTT p50 / p95, ms**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 41 / 66 |
| baseline [C3000] | 41 / 66 |

**link_unsafe = move_in_hold + vel_over + keepout (historical narrow sum)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 0 |
| baseline [C3000] | 0 |

**cage contacts (included in strict safety)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 1 |
| baseline [C3000] | 0 |

**SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = observation.state)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | -10.43 / -18.50 / 0.04 [sat] |
| baseline [C3000] | -10.53 / -18.45 / 0.04 [sat] |

**Stalled episodes (satellite cycle > 0.2 s)**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 0/5 |
| baseline [C3000] | 0/5 |

**knockaway**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 2.00 |
| baseline [C3000] | 4.00 |

**taut_frac**

| arm | leo_relay |
|---|---|
| baseline [C2000] | 0.04 |
| baseline [C3000] | 0.00 |

## Contaminated cells (T06: >= 3 episodes with a satellite cycle > 0.2 s)

None.

## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell

| task | arm | zero success | threshold | knee (ms) |
|---|---|---|---|---|
| (no arm has a `zero` cell and >= 2 sweep points yet) |

## Historical link-only acceptance screen (leo_relay / own zero cell)

| task | arm | success frac | demos/h frac | link_unsafe on zero, direct_gs, leo_relay, geo_relay | cage | historical gate | strict safety |
|---|---|---|---|---|---|---|---|
| (no arm has both a `zero` and a `leo_relay` cell yet) |

Historical amended screen: both fractions >= 0.80 and zero events in the **historical narrow counter sum**, with all four named profiles and their safety counters present. The original SYNTHESIS section 6 also gates cage contacts; strict safety includes those. ZERO_OBSERVED means zero measured events, not a safety certification. This is a point-estimate screen, not an uncertainty-qualified acceptance claim. The historical operator/task-caused label for cage contacts does not establish causal attribution or satisfy the original safety criterion.

### Footnotes

- Durations: taken from `duration_active_s` / `linger_excluded` as reported; no linger correction applied here.
- Smoothness: `[sat]` cells are recomputed here from the satellite applied-setpoint sidecar at ~780 Hz (audit T05: `observation.state` is 30 Hz held at 50 Hz, which puts a floor of ~0.4 under `stall_frac`); SAL uses padlevel 4 (T13). `[obs]` cells are the run's own numbers.
- `direct_gs` per-pass throughput = demos/hour x 9.2/60 (SYNTHESIS section 6: window-limited, report per pass).
- ⚠ marks a cell with >= 3 stalled episodes (T06).
