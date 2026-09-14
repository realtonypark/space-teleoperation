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
