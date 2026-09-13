# Appendix: outage-rate sensitivity (H04 residual, selection.md section 5)

Baseline strategy, task capture, 30 seeds (0-29), tau_h 0.17 s, max_s 20 s, leo_relay structure with the Poisson outage rate varied. Command: `uv run python -m spaceteleop.run --profile <profile> --task capture --strategy baseline --episodes 30 --seed 0 --max-s 20`. Raw stdout: docs/experiments/raw_appendix_outage_<profile>.txt. hold/retract/cage are the run's diagnostic totals.

| profile | outages/h | success | demos/h | hold | retract | link_unsafe | cage | rtt p50 ms |
|---|---|---|---|---|---|---|---|---|
| leo_relay | 1.7 | 0.67 | 459.6 | 0 | 0 | 0 | 10 | 41.4 |
| leo_relay_out5 | 5 | 0.63 | 467.9 | 0 | 0 | 0 | 15 | 42.2 |
| leo_relay_out12 | 12 | 0.60 | 470.4 | 1 | 0 | 0 | 13 | 44.1 |

Reading: raising the outage rate from 1.7/h to 12/h moves capture success by at most two seeds out of 30 and leaves demos/hour within noise; every hold resolves with zero link-caused unsafe events. Outages are not the binding constraint on the relay profile at 20 s episode length; H04's ceiling argument (1.4-5.7 % of episodes exposed at 1.7/h) holds even at 7x the consumer outage rate.
