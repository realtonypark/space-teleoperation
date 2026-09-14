# Independent second-wave review

Reviewed 2026-09-13 while the fixed 15-cell experiment was running. This review traced
the changed controller, ground loop, link, wire parser, recorder, runner and aggregation
code through their callers, inspected the new regressions, and compared the report with
the protocol and statistical artifacts. No simulation, bootstrap campaign, or other
CPU-heavy tests ran during the source-frozen experiment. The reviewer changed only this
review file. Report sections 4 and 10 were still pending; their eventual numbers and
completion claims are outside this review.

## Actionable findings

### R1 — Chained success must require completed release [P1, known, open at review]

`spaceteleop/sat/controller.py` returns `st["success"]` even when a chain reaches its
reset deadline with `st["done"] == False`. Telemetry already uses the stricter condition,
but `run_arm` takes the returned success for episode metadata and throughput. A task
that achieved the hold and failed to release is therefore credited as a reusable demo.
The report correctly discloses that historical chain results do not establish completed
reusable-demo rates. The fresh experiment does not contain chain cells.

After the frozen run, use the same terminal-success predicate in telemetry and the
returned summary: capture success, and for a chain also completed release. Keep
`success_wall` and the intermediate simulator success state for reset timing. Add a
small fake-clock check that achieves capture but never releases, then verify summary
success is false, release is false, and no final telemetry claims success. Include the
corresponding successful release case. Fresh chain evidence is required for a revised
chain performance claim; a unit correction cannot repair archived outcomes.

### R2 — Chained knockaway counts carry across episodes [P2, known, open at review]

The carried-state reset clears keep-out, cage and jam fields but retains `knockaway`
and `t_knock`. `_edge` consequently returns cumulative knockaway counts and can suppress
a new episode's first event using the previous episode's debounce timestamp. Summing
those episode counters is invalid. Reset both fields at the same boundary as the other
event counters. A small two-episode carried-state check should start the second episode
at zero and count its first disturbed-object event once.

### R3 — Retrying a cell mixes terminal metadata from different runs [P2, open at review]

`experiments/matrix.py:222` reruns incomplete or source-mismatched cells in the same
directory. `spaceteleop/record/__init__.py:126` appends `episodes.jsonl` while overwriting
the matching NPZ. A retry therefore leaves multiple outcomes for the same episode index;
an older, longer run can also leave obsolete later files. The new source check increases
the importance of making replacement behavior explicit.

A lightweight temporary-directory reproduction wrote episode 0 twice with different
outcomes: metadata contained two entries, while `info.json` reported one episode. Run
replacement cells in a fresh owned directory, or clear/archive only the prior cell's
generated outputs before restarting at episode 0. Preserve failure stdout as needed.
Check that a retry yields exactly one metadata entry and matching data file per expected
episode. This does not invalidate the fresh run if its destination started empty and
no cell needed a retry.

### R4 — Blackout labels are lost after optional diagnostics [P2, open at review]

`experiments/matrix.py:139` recognizes `no_link` only immediately after `frames`.
`run_arm` prints `reset=...` and `innov=...` before that field. The episode still enters
the summary as a failed attempt, but its `no_link` annotation becomes false. Three
lightweight parser checks returned true for `frames=0 no_link=True`, false when
`reset=0.0s` intervened, and false when `innov=1.0mm` intervened.

Read the optional label from the complete matched episode line, or permit the known
optional diagnostic fields before it. Extend the existing parser check with these
two suffix forms. No failure-count correction is needed for records already parsed
through the normal episode format; the defect concerns cause/exposure annotation.

### R5 — Legacy cage fallback could falsely report zero events [P2, fixed during review]

`acceptance` accepted a top-level `aggregate.cage` as measured evidence, while `_vectors`
read only `aggregate.events.cage`. A legacy cell with `aggregate.cage=1` and known zero
link counters therefore received `ZERO_OBSERVED`. The lead added the missing fallback
after this review reported the issue. An independent lightweight recheck over all four
named profiles now gives `strict_safety_status=FAIL` and `cage_named=4`, as required.
Current runner output puts cage in the event dictionary, so this was a legacy-input
edge case rather than a fresh-run numerical change.

## Verified strengths

- The controller now stops physics at terminal success or timeout and during reporting
  linger. The existing new fake-clock regression exercises a success before and after
  the deadline. Sidecars end at the terminal cycle; the final-state metadata supplies
  the post-step state that a pre-step sidecar cannot contain. Physics still uses discrete
  integration steps, so the deadline is subject to that time resolution.
- The ground loop records the actual delay-aged or Twin-substituted observation used
  by the operator, preserves its source telemetry identity, and logs the wire command
  sequence before incrementing it. Current `observe` implementations either return
  the original frame or a new Twin dictionary, so the identity-based prediction flag
  matches current behavior. Source time does not falsely claim to be prediction time.
- The link now adds propagation after serialization completion. The arrival counter
  is unique across queued packets and provides FIFO tie order independently of drain
  progress. The deterministic regression explicitly uses reverse lexical payload order,
  so it catches the old accidental payload-based ordering.
- Nonfinite command and telemetry components are rejected at the UDP decoder, before
  they enter interpolation or the simulator. The slices cover all seven command values
  and all 21 telemetry state, velocity and object values.
- A first complete blackout follows ordinary recording and metrics paths, with an empty
  `(0, 7)` action array, actual satellite state, and a terminal failed outcome. The new
  end-to-end regression checks that path instead of fabricating a previous episode.
- Source hashes include the executable package, matrix runner and dependency inputs;
  resume checks include complete ordered seed vectors and cell parameters. The manifest
  additionally records the external model revision and XML digest. It does not claim
  that the Python lock alone pins externally downloaded assets.

## Statistical and report assessment

The gross estimator retains every failed-attempt duration. Pairing now respects block,
task, profile, reaction delay and common seed, and all-stalled cells can become empty.
The Holm implementation uses the cumulative maximum of sorted adjusted p-values and
the report explicitly limits its family to the selected success comparisons. Inspection
of `statistics.json` confirmed 21 restored held-out comparisons, each with 70 pairs.

The exact success-retention lower bound uses the lower LEO probability divided by the
upper zero probability. The two one-sided 97.5% marginal bounds give a conservative
95% single-ratio bound by the union bound without requiring cross-profile independence.
The implementation handles the zero/all-success endpoints, and its self-checks encode
their closed forms. This does still assume the stated binomial sampling model within
a cell; it does not apply directly to dependent chain episodes.

Bootstrap limitations are stated correctly: success/throughput intervals are pointwise,
empirical boundary intervals can degenerate, ratios that discard undefined resamples
are conditional, and selected historical comparisons are not preregistered confirmation.
Knee uncertainty preserves beyond-sweep outcomes instead of silently dropping them;
conditional finite-knee shift intervals are labeled separately. The four-cell Twin
adjustment resamples common seed indices jointly across both strategies and profiles.

The main report appropriately separates synthetic task performance, physical fidelity,
hardware qualification, human performance and learned-policy value. It does not pool
historical and corrected outcomes. Its criticism of cage causal attribution, setpoint
safety, Terminal-versus-TerminalGround confounding, NPZ compatibility, and zero-cell
equivalence is consistent with the source inspected here. The external-evidence review
is the source for supplier and literature assertions; this code-focused review did not
independently reopen every cited publication.

Some source comments still assert the superseded cage causality, strict performance
upper-bound, and isolated compute-placement interpretations. Align those comments with
the revised report when editing those files after the frozen run. They should not be
used to override the report's narrower evidence claims.

Final integration should resolve R1–R4, retain the fresh source manifest, run the relevant
regressions after any executable edit, and verify the completed results and reproduction
sections against generated artifacts. Changes after the frozen run need their own
revision/provenance note; they must not be presented as the code that generated the
450 frozen-run episodes.

## Final numerical review and resolution addendum

Reviewed the integrated primary results after all 450 episodes completed. The primary
execution snapshot is `0f68e78`; the subsequent corrections are in `550e190`. Supplemental
chain execution was still running during this addendum. The findings above are preserved
as the original review record; the resolution table below gives their later status.
No simulator or full recording audit was rerun by this reviewer during the chain run.

| Finding | Resolution checked in source and regressions |
|---|---|
| R1, chain release | Fixed in `550e190`: returned success and telemetry now both require release for a chain. The capture milestone and its timestamp remain separate. The fake-clock regression covers unfinished release, release within the extended total cap, and capture after the original deadline. |
| R2, chain event counts | Fixed in `550e190`: both `knockaway` and `t_knock` reset with the other per-episode counters. The carried-state regression begins with a prior count of seven and requires exactly one new event. |
| R3, retry metadata | Fixed in `550e190`: the matrix archives an existing cell under `_superseded` and starts a fresh output directory. The recorder also replaces metadata from a retried index onward, validates the retained prefix, and removes a replaced episode's obsolete sidecar. The matrix regression verifies preserved evidence and distinct complete/incomplete retry results. Direct writer use intentionally retains unindexed later files; consumers must follow metadata. |
| R4, blackout labels | Fixed in `550e190`: the parser permits intervening same-line diagnostics before `no_link`. Its regression includes reset/innovation suffixes, explicit false, and no label. |
| R5, legacy cage fallback | Fixed before the primary execution snapshot; independently checked earlier in this review. |

The lead reports 53 selected deterministic tests passed after integration. This review
inspected the tests and changes without duplicating that suite while timed experiments
were running. Supplemental chains are bookkeeping evidence, not 20 independent
replicates or a new estimate of the original H20 effect.

### Primary numerical checks

An independent lightweight calculation from `fresh/results.json` verified all 15
cells contain exactly seeds 1000–1029, have no cell error or stalled seed, and reproduce
`3600 × successes / total duration`. The input hash in `statistics.json.corrected_run`
matches the saved fresh result file. All six paired exact McNemar p-values were
recomputed from the discordant outcomes; paired gross differences match the cell rates.

Every displayed value in the integrated report's section 4 tables agrees with the
saved artifacts at its reported precision. This includes the following decision-relevant
figures:

- Capture baseline: 21/30 at zero, 17/30 on relay, 212.4 → 153.9 gross demos/h,
  72.5% rate retention, and a conservative success-retention lower bound of 0.439.
  Its gross margin interval is −63.2 to +25.2 demos/h. The report correctly distinguishes
  failure of the point-estimate target from proof that the population ratio is below it.
- Peg baseline: 30/30 in each control, 833.3 → 819.4 gross demos/h, 98.3% retention,
  and a conservative success-retention lower bound of 0.884. Both tasks still lack
  the complete four-profile acceptance evidence set.
- The six success comparisons and their Holm adjustments match the table. Capture
  Twin at 400 ms has adjusted p = 0.064453125; its zero-adjusted success difference
  is +16.7 percentage points [−3.3, +36.7], and its conditional throughput ratio of
  ratios is 1.105 [0.941, 1.281]. The report does not overstate these as a confirmed
  10% latency-specific benefit.
- The two forced outage conditions each have 29/30 observed hold exposures. Only the
  12-second condition has 29 episodes with hold command age above 10 seconds. Seed
  1011 ends at approximately 5.57 seconds in both conditions, before the scheduled
  outage. Success totals are 18/30 and 1/30; cage-event totals are 8 and 36.

Reading the verification summary independently gives 354,402 ground frames, 5,127,213
satellite cycles, 450 verified episodes, and zero reported audit errors. The largest
cycle gap is 0.169063542 s. Both reported command-envelope violation counts are zero.
The sampled actual-velocity peak is 6.584083557 rad/s at the Elbow in the 12-second
outage cell, seed 1024, simulation time 19.914 s, outside hold. The report correctly
separates this actual-motion result from the setpoint limit and notes unsampled peaks.

### Scope correction requested during numerical review

The initial integrated report said “task-goal geometry passed.” The recording verifier
checks Capture's final target radius and Peg's final lateral distance; it does not
replay the full Peg insertion-depth/contact predicate or Capture's dwell/grasp history.
Use “terminal target-distance checks passed,” or state those limits explicitly, rather
than imply independent reconstruction of every success predicate.

A metadata-only diagnostic found 6 of 117 successful Peg endpoints with final tips
slightly above the insertion-depth threshold, by at most 0.0878 mm. `_peg` evaluates
the tip before updating the kinematic object pose, so its tested tip and final recorded
pose need not be identical. This is consistent with the already disclosed discrete
contact/predicate timing limitation; it is not evidence of an effect-size reversal or
proof that those trajectories never met the criterion. It reinforces why the final
audit claim must describe the checks actually performed. The lead was notified before
final report integration.

At the lead's request, this reviewer prepared a two-line correction that recomputes
tip height and fixture contact after the kinematic pose update, immediately before
the success predicate. It preserves the existing pre-update jam/regrasp behavior.
The proposed regression checks a withdrawn tip, a newly inserted tip and a new
final-pose contact. All three cases fail the current function and pass the candidate
in an isolated in-memory check; no model or timed simulation was needed. The patch
was supplied for integration separately. Fresh post-correction Peg checks and an
updated source identifier are needed before claiming that final-runtime evidence;
the 450-episode study remains attached to its original predicate and revision.

The research scope remains explicit and adequate for this wave: corrected synthetic
mechanism comparisons, complete attempt accounting, recording provenance and a revised
research plan. Physical task validation, human transfer, contact safety, complete
mission acceptance and incremental learned-policy value remain untested. Pending final
chain and test-count paragraphs require their own completion evidence; they are not
certified by this primary numerical review.

## Final Peg correction resolution

The proposed final-pose correction was integrated in `be7dd45`. The lead reports all
nine tests in `test_sim_operator.py` passed, including the three new boundary/contact
cases. This reviewer inspected `peg_check.py`, its manifest, the saved endpoint evidence
and the three raw cell summaries without repeating timed experiments or the full suite.

The checker restores the recorded final robot joint positions and object position and
orientation into the Peg model, calls `mj_forward`, then checks lateral position,
insertion depth and fixture contact at that common final pose. This addresses the
specific stale-tip/contact defect. Its completeness, seed, outcome and execution-hash
checks agree with the saved data. It intentionally checks successful endpoints and
does not claim independent replay of the full trajectory or validation of failed cases.

All 30 supplemental episodes succeeded: ten baseline-zero, ten baseline-relay and ten
Terminal-at-400-ms episodes, each on seeds 4000–4009. Every reconstructed endpoint meets
the final predicate and has no fixture contact. The smallest positive insertion-depth
margin is approximately 0.000000713 m; the largest lateral error is approximately
0.004699 m, below the implemented 0.014 m threshold. These are synthetic geometry
checks at the model's numerical resolution, not physical tolerances or a new estimate
of latency benefit. The result, manifest and current executable source hashes match.

The supplemental chain evidence separately reports 20 verified episodes, complete
coverage and no errors. Thus the saved studies contain 500 episodes in total, split
as 450 primary comparisons on `0f68e78`, 20 dependent chain-regression episodes on
`550e190`, and 30 Peg endpoint-regression episodes on `be7dd45`. Their distinct
purposes and revisions must remain visible. The primary results are neither changed
retroactively nor pooled with either supplemental study.

No unresolved endpoint-correction finding remains from this review. The broad physical,
human, mission-safety and policy-learning limits stated above still apply. Final full-suite
completion was pending at this review point and belongs in the lead's verification record.
