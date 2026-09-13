# Experiment results

2 cells, 4 episodes. Baseline arm: `baseline`. Paired tests: `paired.md`.

## Task `capture`

**Success rate (95 % Wilson CI)**

| arm | zero | sweep:500 |
|---|---|---|
| baseline | 1.00 [0.34,1.00] 2/2 | 0.00 [0.00,0.66] 0/2 |

**demos/hour (gross in brackets where the run reports it)**

| arm | zero | sweep:500 |
|---|---|---|
| baseline | 419.1 | 0.0 |

**RTT p50 / p95, ms**

| arm | zero | sweep:500 |
|---|---|---|
| baseline | 9 / 21 | 500 / 525 |

**Unsafe events (total; the section 6 counts that are non-zero)**

| arm | zero | sweep:500 |
|---|---|---|
| baseline | 1 (cage=1) | 3 (cage=3) |

**SAL / LDLJ / stall_frac**

| arm | zero | sweep:500 |
|---|---|---|
| baseline | -4.36 / -18.88 / 0.40 | -22.87 / -22.48 / 0.71 |

## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell

| task | arm | zero success | threshold | knee (ms) |
|---|---|---|---|---|
| (no arm has a `zero` cell and >= 2 sweep points yet) |

## SYNTHESIS section 6 acceptance readout (leo_relay / own zero cell)

| task | arm | success frac | demos/h frac | unsafe on zero, direct_gs, leo_relay, geo_relay |
|---|---|---|---|---|
| (no arm has both a `zero` and a `leo_relay` cell yet) |

Acceptance (PROGRAM.md): both fractions >= 0.80 and zero unsafe events.

