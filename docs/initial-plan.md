# Space Robot-Arm Teleoperation for Physical-AI Data Collection — Research Program Plan

## Context

Goal: determine whether, and how, humans on Earth can teleoperate simple robot arms inside a LEO
satellite to collect physical-AI demonstration data that cannot be obtained in Earth-side simulation.
The engineering objective is minimum end-to-end latency; the acceptance metric is demonstration
quality and throughput relative to a zero-latency baseline. We cannot launch, so the proof is a
validated architecture plus a runnable testbed that reproduces realistic orbit-link behaviour over
real sockets and shows the numbers.

Repo `/Users/tpark/exp/teleoperation` is empty (README only). Everything is built from scratch.
Machine: M4 Pro, 24 GB, Python 3.9 system, `uv` available, Herdr available (HERDR_ENV=1).

## Settled decisions (from grilling)

| Topic | Decision |
|---|---|
| Deliverable | Architecture spec + testbed + experiments + final report (artifact + repo). Mission/hardware sketch as appendix. |
| Human in loop | None. Fully autonomous end to end. Agents review agents. Report findings to user at the end. |
| Link path, orbit, bus class, pressurization, onboard capability (B vs C), task set, hardware stack, input device | Research decides; report the choice and why. Constraint: rideshare-launchable small sat; technology buyable today; near-future upgrades as a separate section. |
| Operator interface | Leader-follower or VR, no force feedback. Testbed uses synthetic operators (policies + human reaction-delay model); keyboard client exists for later manual use. |
| Onboard baseline | At minimum (b): joint setpoints + short command buffer w/ interpolation + hold/retract on timeout. Research may pick (c) small deterministic safety logic. No models/vision on the satellite in the baseline; one hypothesis branch quantifies what onboard compute would buy. |
| Scale | 4–8 arms, 4 concurrent operators, bandwidth model that scales. |
| Sim stack | MuJoCo (g=0, free-floating objects), generic 6-DoF + parallel gripper from MuJoCo Menagerie, TLE-driven pass geometry (sgp4/skyfield), UDP link emulator on localhost injecting delay/jitter/loss/outages. Video modelled as delay+bandwidth budget, not a codec. |
| Data format | LeRobot dataset format. |
| Acceptance | Research sets threshold; default ≥80% of zero-latency success rate and demos/hour; zero unsafe motion on dropout. Report the full success-vs-latency curve. |
| Hypothesis pool | ~20 quality-gated hypotheses across 5 axes; verifiers rank; top 3–5 implemented head to head against a naive baseline. Quality over count. |
| Agents | Fable 5.1 for research/hypothesis/verification/synthesis; Opus 5 for mechanical implementation. Herdr panes for long independent tracks; built-in Agent tool for short fan-outs; SendMessage for hypothesis↔verifier exchanges. |
| Git | Commit to `main` at each phase boundary with clear messages. |
| Code style | Ponytail full: stdlib/MuJoCo/numpy first, one runnable check per non-trivial module, no frameworks. |

## Repo layout (target)

```
teleoperation/
  pyproject.toml            # uv-managed, py>=3.11 (uv python install), deps: mujoco, numpy, sgp4, lerobot (or minimal writer)
  docs/
    research/               # Phase 1 outputs, one .md per topic, with citations
    hypotheses/             # Phase 2: H01..Hnn.md (template below) + scores.md + selection.md
    experiments/            # Phase 4/5 results, plots, tables
    REPORT.md               # Final report (source of the artifact page)
  spaceteleop/
    sim/                    # MuJoCo scene, arm, tasks, zero-g objects
    link/                   # orbit geometry (TLE->pass windows), link emulator (UDP proxy), link profiles
    proto/                  # command/telemetry wire format, sequencing, timestamps
    sat/                    # satellite-side controller: setpoint buffer, interpolation, timeout policy
    ground/                 # operator clients: synthetic operators, keyboard client
    strategies/             # one module per implemented hypothesis (latency hiding / protocol / control)
    record/                 # LeRobot episode writer
    metrics/                # latency, success, throughput, safety
  experiments/              # runnable experiment scripts producing docs/experiments/*
  tests/                    # minimal self-checks
```

## Phases

### Phase 0 — Bootstrap (Opus, 1 agent, short)
- `uv init`, pin Python 3.11+, add mujoco/numpy/sgp4; verify MuJoCo headless renders and a Menagerie arm loads with gravity 0.
- Create layout above, `docs/PROGRAM.md` with this plan's settled table.
- Commit: `phase0: bootstrap testbed skeleton`.

### Phase 1 — Research (Fable, ~8 parallel agents via Herdr, web-enabled)
Each agent writes `docs/research/<topic>.md`: findings, numbers with sources, open questions, and a one-paragraph "implication for our design".
1. Teleoperation fundamentals: latency/jitter tolerance by task class, known latency-hiding methods (predictive display, model-mediated, wave variables, shared autonomy, subgoal teleop), measured human-performance curves.
2. Space teleop prior art: ROKVISS, Kontur-2, Haptics-1/2, METERON/SUPVIS-Justin, Analog-1, Canadarm2 ground ops, Robonaut, Astrobee, OSAM-1/MEV — what link, what latency, what worked.
3. LEO link options with measured latencies and availability: direct ground station (pass windows, GS networks like AWS/KSAT/Leaf), commercial LEO relay (Starlink laser ISL for third parties, status & terms), GEO relay (TDRSS/EDRS), Iridium/Kepler, hosted-payload options. Bandwidth up/down per option, cost class.
4. Unique-data study: which manipulation phenomena are genuinely unavailable or unreliable in Earth sim/labs (microgravity contact, free-floating objects, fluids, granular, tethered/deformables, thermal/vacuum effects), and which tasks expose them. Produces the candidate task set and the pressurized-vs-vacuum implication.
5. Hardware landscape: small-sat buses (12U–16U vs ESPA-class), space-tolerant simple arms, cameras, edge compute, radios/optical terminals; what is buyable today. Produces the hardware stack recommendation inputs.
6. Multi-operator & bandwidth: video encoding latency budgets, per-operator streams, scheduling/isolation of arms across operators.
7. Data pipeline: LeRobot/ALOHA data conventions, what makes teleop demos useful for policy training, quality metrics.
8. Network emulation & measurement: public Starlink/LEO latency traces, how to calibrate the emulator, TLE-based visibility modelling.

Synthesis agent (Fable) → `docs/research/SYNTHESIS.md`: feasibility verdict ("possible today? under what link?"), chosen link path, task set, bus class/pressurization, onboard capability (b or c), acceptance thresholds, link profiles to emulate (numbers). This is the program's decision record.
- Commit: `phase1: research + synthesis`.

### Phase 2 — Hypotheses (Fable, ~20 independent agents via Herdr; 5 verifier agents)
Axes: link path / transport protocol / latency-hiding control scheme / operator interface & workflow / task & data design. Each hypothesis agent reads SYNTHESIS.md and writes `docs/hypotheses/Hxx.md` using the template:
`Claim · Mechanism · Expected effect (quantified) · How the testbed falsifies it · Cost/complexity · Risks`.
Agents are told to abstain rather than pad: a weak idea returns "no hypothesis on this axis" instead of filler.
Verifiers (Fable) score each on evidence, testability, expected gain, cost; exchange objections with the author via SendMessage (one round); write `docs/hypotheses/scores.md`.
Selection agent writes `docs/hypotheses/selection.md`: top 3–5 plus the naive baseline (direct setpoint streaming), with the experiment matrix.
- Commit: `phase2: hypotheses + ranking + selection`.

### Phase 3 — Testbed build (Opus, 4–5 agents, TDD-lite: each module has one self-check)
Parallel tracks, integrated by a lead agent:
- `sim/`: zero-g MuJoCo scene, arm + gripper, task set from SYNTHESIS (e.g., free-floating object capture, peg insertion, deformable handling), success predicates, fixed-seed resets.
- `link/`: TLE → contact windows (sgp4); UDP proxy with per-profile delay, jitter, loss, outage; profiles from SYNTHESIS (direct-GS, LEO-relay, GEO-relay, zero-latency).
- `proto/` + `sat/`: timestamped sequenced setpoint stream; satellite controller with buffer/interpolation/timeout hold; telemetry back.
- `ground/`: synthetic operator = policy over telemetry with configurable human reaction delay + noise; keyboard client.
- `record/` + `metrics/`: LeRobot episode writer; end-to-end latency, success, demos/hour, safety violations.
- Integration test: one episode end to end over the UDP emulator, recorded, metrics computed.
- Commit: `phase3: testbed`.

### Phase 4 — Implement selected hypotheses + experiments (Opus implements, Fable designs experiments)
- One `strategies/<name>.py` per selected hypothesis; same interface as baseline.
- Experiment matrix: strategy × link profile × task × operator-delay setting; N seeds sufficient for CIs.
- Outputs: success-vs-latency curves, demos/hour, safety counts, bandwidth per operator, 4-operator scaling run. Written to `docs/experiments/`.
- Commit: `phase4: strategies + experiments`.

### Phase 5 — Verification & iteration (Fable verifiers, independent of implementers)
- Re-run experiments from clean checkout; audit for bugs that flatter a strategy (leaked state, wrong timestamps, emulator bypass); statistical sanity; adversarial review of each surviving hypothesis.
- Findings go back to implementers via SendMessage; fix and re-run. Loop until verifiers sign off or a hypothesis is rejected with evidence.
- Commit: `phase5: verification`.

### Phase 6 — Final report
- `docs/REPORT.md`: feasibility verdict; recommended end-to-end architecture (link, protocol, satellite controller, ground client, data pipeline); measured numbers and curves; hardware stack recommendation; near-future upgrades section; what remains unproven without flight.
- Publish as artifact page; commit `phase6: final report`.

## Orchestration rules
- Herdr panes for Phase 1/2/5 long tracks; built-in Agent for short lookups. Use `herdr` skill for pane control, `SendMessage`/`ListAgents` for cross-agent messaging.
- Every agent gets: the settled-decisions table, its output path, the abstain rule, and a "cite or mark as unverified" rule.
- Lead re-reads each phase's outputs before the next phase starts; no phase relies on unverified numbers.

## Verification (how we know it worked)
- `uv run pytest -q` (or `python -m` self-checks) green at each phase boundary.
- End-to-end: one recorded LeRobot episode over the emulated LEO-relay profile, with logged one-way and round-trip latencies matching the profile.
- Experiments reproducible from `experiments/*.py` with fixed seeds; verifier re-run matches within CI.
- Final report numbers trace to files in `docs/experiments/`.
