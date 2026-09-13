# Testbed spec (vertical slice, decision-independent core)

Pure Python 3.12, deps: mujoco, numpy, sgp4 only (pytest for tests). Ponytail rules: stdlib first,
no frameworks, fewest files, one runnable self-check per non-trivial module.

## Processes (each a plain function runnable in-process or as a subprocess)
- **ground** (`spaceteleop/ground/`): operator loop. Reads telemetry, runs an *operator* to produce a
  target joint-setpoint (7 floats: 6 joints + gripper), sends command packets at `cmd_hz` (default 50).
  Operators: `SyntheticOperator` = scripted policy toward task goal with modeled human reaction delay
  `tau_h` (default 0.25 s) and per-step noise; `KeyboardOperator` = stdin-based, optional, minimal.
- **link** (`spaceteleop/link/emulator.py`): UDP proxy on localhost. Two independent directions
  (up/down), each with delay distribution (constant + jitter, log-normal or gamma), Gilbert-Elliott
  loss, periodic outages, optional reordering, bandwidth cap (bytes/s token bucket). Profiles in
  `spaceteleop/link/profiles.py` as plain dicts: `zero`, `direct_gs`, `leo_relay`, `geo_relay`
  (placeholder numbers now; research will replace values, NOT structure).
  `spaceteleop/link/orbit.py`: sgp4 TLE -> contact windows for a station list (lat/lon/alt, min elev).
- **sat** (`spaceteleop/sat/controller.py`): receives command packets, keeps a small buffer keyed by
  sequence/timestamp, interpolates setpoints at the sim rate, on `timeout_s` (default 0.5) without
  fresh commands -> HOLD (freeze setpoint) and flag `safety_hold`. Drives the sim. Emits telemetry at
  `tel_hz` (default 30): joint positions/velocities, gripper, object poses, echo of last cmd seq +
  timestamps for RTT measurement, optional low-res camera frame bytes (off by default; a `frame_bytes`
  field sized to the video budget so the bandwidth cap bites).
- **sim** (`spaceteleop/sim/`): MuJoCo, SO-100 from `robot_descriptions` (`so_arm100_mj_description`),
  gravity 0, scene adds one free-floating object (box) with initial small drift/tumble and a target
  region. Task v0: "capture": grasp the drifting object and bring it to the target region. Success
  predicate + fixed-seed reset. Keep the scene as an XML string patched onto the arm model.
- **proto** (`spaceteleop/proto/`): `struct`-packed little-endian messages. Command: magic, seq(u32),
  t_send(f64 monotonic ns as int64), 7 x f32 setpoints, flags(u8). Telemetry: magic, seq(u32),
  t_send, last_cmd_seq, last_cmd_t_send, t_cmd_applied, 7 x f32 q, 7 x f32 qd, object pose 7 x f32,
  flags, frame_len(u16) + bytes.
- **record** (`spaceteleop/record/`): minimal LeRobot-v2-compatible writer: per episode a parquet-free
  fallback = `.npz` + `meta/info.json` + `meta/episodes.jsonl` (keys: `observation.state`, `action`,
  `timestamp`, `frame_index`, `episode_index`, `next.done`, plus our extras `cmd_seq`, `rtt_ms`,
  `owd_up_ms`, `safety_hold`). Document the exact mapping to LeRobot in the module docstring.
- **metrics** (`spaceteleop/metrics/`): from an episode: success, duration, RTT stats (p50/p95/max),
  command loss fraction, safety_hold count/time, path smoothness (sum of squared joint jerk), and
  demos/hour = 3600 / mean successful-episode wall time.

## Runner
`spaceteleop/run.py`: `uv run python -m spaceteleop.run --profile leo_relay --task capture --episodes 3 --seed 0 --out docs/experiments/raw/<name>`
runs ground/link/sat in threads (or subprocesses) over real UDP sockets on 127.0.0.1, records
episodes, prints a metrics table. Wall-clock realtime is NOT required: run sim faster than realtime
with a shared logical clock ONLY if latency injection is expressed in logical time consistently;
otherwise realtime. Choose the simpler correct option and document it.

## Tests (tests/)
- link: injected delay distribution matches profile within tolerance; loss fraction matches; outage
  drops everything during the window.
- sat: on missing commands for > timeout, setpoint freezes and safety_hold flag set.
- e2e: one `zero` and one `leo_relay` episode run headless in < 60 s; measured RTT p50 within ±20% of
  profile mean; recorder output loads back; metrics computed.

## Strategy hook
`spaceteleop/strategies/base.py`: `class Strategy` with `ground_step(telemetry, operator_target) -> command_setpoint`
and `sat_step(buffer, now) -> setpoint`. `baseline.py` = pass-through + interpolation/hold as above.
Hypotheses later subclass this without touching the runner.
