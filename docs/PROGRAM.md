# Program charter: space robot-arm teleoperation for physical-AI data collection

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


## Rules for every agent in this program

1. **Cite or mark unverified.** Every number carries a source (URL, paper, datasheet). If you cannot find a source, write `[unverified]` next to it. Never invent a figure.
2. **Abstain over padding.** If you have nothing strong to say on a sub-topic, say "no finding" in one line. Filler is worse than silence.
3. **Implication paragraph.** End every document with "Implication for our design", one paragraph, concrete.
4. **Numbers over adjectives.** "Round-trip 45–60 ms measured over N sessions" beats "low latency".
5. **Stay in your lane.** Write only to the output path you were given. Do not edit other agents' files.
