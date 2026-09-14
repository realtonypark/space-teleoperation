# Second-wave research plan

Recorded 2026-09-13 before inspecting new experimental outcomes. This extends the original
[charter](../PROGRAM.md); the scientific question and autonomous, synthetic-operator constraint
stay the same. The target is evidence for collecting useful physical-AI demonstrations through a
space link, not just task completion in a simulator.

## Questions and design

1. Which architecture claims follow from primary evidence, and which remain assumptions?
2. Do strategy effects survive corrected outcome timing and independent task seeds?
3. Does the acceptance conclusion survive charging failed attempts to collection time?
4. Can recordings trace the observation, command and actual simulated state without ambiguity?
5. Which remaining tests would change the mission or data-collection decision?

Three concurrent Astra reviews cover external evidence, statistical inference, and executable
validity. Subsequent reviews cover the hypothesis pool and integrated outputs. The senior lead
owns the experiment protocol, provenance, integration and final verification.

Preserve first-wave results as historical artifacts. Corrected runs use a separate directory and
seeds starting at 1000, outside the original 0–99 range. Do not pool corrected and original outcomes.
Reanalysis of first-wave seeds 30–99 is a useful exploration-disjoint sensitivity check, but it is
not a new validation of the corrected implementation.

## Corrected-run protocol

Use 30 paired episodes per cell, seed range 1000–1029, one arm per process, at most four processes.
Record code hashes, exact commands, all attempted episodes and failures. Use the existing
20-second capture / 30-second peg deadlines, 170 ms synthetic reaction delay and existing profiles.
Run these fixed comparisons after executable corrections are stable:

| Task | Profiles | Strategies | Purpose |
|---|---|---|---|
| capture | zero, leo_relay | baseline | reference and relay acceptance |
| capture | zero | twin | zero-delay control for the prediction mechanism |
| peg | zero, leo_relay | baseline | reference and relay acceptance |
| capture | sweep:400 | baseline, twin, gain | prediction benefit and moving-target cost of slowing |
| peg | sweep:250 | baseline, deadreckon | corrected supervisor extrapolation |
| peg | sweep:400 | baseline, terminal, terminal_ground | local-assistance package and delayed counterpart |
| capture | leo_relay_drop1, leo_relay_drop12 | baseline | measured hold and retract exposure |

Total: 15 cells, 450 episodes. These are targeted robustness experiments, not a replacement for
all 198 first-wave cells. Additional focused checks, if needed after a demonstrated failure, must
be identified separately. Do not call a small null result equivalence or a point estimate a
confidence-qualified acceptance result.

Primary collection rate is `3600 * successes / sum(all attempt durations)`. It includes failed
attempts. Report conditional successful-attempt speed separately. This rate still excludes campaign
setup, human fatigue, unmodelled resets and ground-station availability; it is not a mission yield.
Report paired success differences and intervals, gross-rate differences, zero-reference ratios,
all discarded/missing seeds, scheduler stalls and actual outage exposure. Missing evidence is not
an acceptance pass. Original hypothesis rejection clauses remain visible even if an arm improves
a secondary task.

## Completion evidence

Relevant regression tests, corrected runs, independently checked report claims, inspectable
recording provenance, and a clean committed revision reproducible from the documented commands.
Push `main` only after integration and verification. Existing uncommitted report edits are retained.

## Implication for our design

Prefer measured simulator evidence and explicit mission gates to a stronger feasibility claim
than this testbed can support. Hardware qualification, human usability and downstream policy
learning remain separate empirical questions; the second wave must supply a concrete path to
answer them without pretending that local simulation answers them already.

## Supplemental regression study (added after independent code review)

The independent review found chain-only completion/counter defects and retry metadata mixing.
After the frozen 450-episode study finishes, apply these fixes and use two starting seeds (2000,
3000), both reset modes (`free`, `teleop`), five episodes per chain, on `leo_relay`: four chains,
20 episodes total, at most two concurrent processes. Capture keeps its 20 s deadline; timely
capture permits the existing total 28 s chain deadline. Record the second executable revision.

This study checks release-complete outcomes, per-episode counters, metadata consistency and reset
accounting. It is not powered to confirm H20's throughput or success-retention claims. Do not treat
the 20 linked episodes as independent replicates or pool them with the primary protocol. Also test
an intentionally unfinished release under a fake clock and retry the same output metadata in a
small regression test. These deterministic checks provide the evidence for those failure paths.

## Final Peg endpoint regression (added after endpoint review)

A final metadata check found six successful primary Peg endpoints slightly above the depth
threshold because completion used the pre-update tip height. Correct only the terminal predicate
to use tip height and contact after the kinematic pose update; preserve jam/regrasp behavior.
Record this third execution revision and retain the 450 primary outcomes under their original
revision. Do not retroactively relabel a trajectory that would have continued under the new code.

After the deterministic regression passes, run ten fresh scenarios (4000–4009) each for Peg
baseline/zero, baseline/leo_relay and Terminal/sweep:400, three processes, 30 s deadline and
170 ms reaction delay. These 30 episodes check the corrected terminal predicate, not a new paired
mechanism estimate. Independently reconstruct final Peg pose/contact from saved state and check
every successful endpoint against the complete terminal predicate. Keep these observations
separate from the primary study and chain regression.
