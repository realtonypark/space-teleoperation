# Appendix: multi-operator scaling (4 arms, one process)

Baseline strategy, task capture, `leo_relay`, tau_h 0.17 s, max_s 20 s, 15 episodes per arm, telemetry padded with 8192-byte frames at 30 Hz to model a ~2 Mb/s video budget per arm. Commands:

```
uv run python -m spaceteleop.run --profile leo_relay --task capture --strategy baseline --arms 4 --episodes 15 --seed 0 --max-s 20 --frame-bytes 8192
uv run python -m spaceteleop.run --profile leo_relay --task capture --strategy baseline --arms 1 --episodes 15 --seed 0 --max-s 20 --frame-bytes 8192
```

Raw stdout: docs/experiments/raw_appendix_scaling_arms4.txt, docs/experiments/raw_appendix_scaling_arms1.txt. Four independent ground/link/satellite triplets run concurrently as threads in one Python process on distinct localhost ports (arm k uses seeds 1000k..1000k+14).

| run | arms | success | demos/h | rtt p50 / p95 ms | stalls | link_unsafe | wire up B/s | wire down B/s |
|---|---|---|---|---|---|---|---|---|
| 1 arm | 1 | 0.67 (10/15) | 447.0 | 42.2 / 68.3 | 0 | 0 | 2,012 | 249,902 |
| 4 arms, aggregate | 4 | 0.75 (45/60) | 416.8 | 42.4 / 68.1 | 0 | 0 | 8,034 | 999,090 |
| 4 arms, arm 0 (seeds 0-14) | - | 0.67 (10/15) | 446.9 | 43 | 0 | 0 | - | - |

Reading: arm 0 of the 4-arm run reproduces the 1-arm run seed for seed (same 10 successes, same 5 failures, demos/hour 446.9 vs 447.0), so the concurrent arms do not disturb each other's control loop at this scale; measured RTT p50/p95 are identical within 0.2 ms and no control-loop stall occurred. Wire bandwidth scales linearly: 2.0 kB/s up and 250 kB/s down per arm (the 2 Mb/s video budget), 8.0 kB/s up and 1.0 MB/s (8 Mb/s) down for four, consistent with multi_operator_bandwidth section 3 (four operators at two 720p30 streams: 10.4 Mb/s with FEC). The ceiling of this test is the Python GIL: max control-loop dt rose from 0.02 s to 0.08 s with four arms in one process, still far below the 0.2 s stall threshold and the 0.3 s hold timeout. Eight arms were not run.
