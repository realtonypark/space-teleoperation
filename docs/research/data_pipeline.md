# Data pipeline for teleop demonstrations

> First-wave research note, retained for traceability. The [second-wave evidence review](second_wave_evidence.md) corrects consequential source claims; the [current synthesis](SYNTHESIS.md) governs decisions.

Scope: (1) LeRobot dataset format v2.1/v3.0 and how ALOHA/SO-100 data is recorded, (2) what makes a teleop demonstration useful for policy learning, with the latency/jitter evidence that exists, (3) the metrics and minimal schema our recorder must emit.

## 1. LeRobot dataset format

### 1.1 Layout, v2.1 vs v3.0

| | v2.1 (`lerobot<0.4`) | v3.0 (`lerobot>=0.4`, current) |
|---|---|---|
| Tabular | `data/chunk-{XXX}/episode_{XXXXXX}.parquet`, one file per episode | `data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet`, many episodes per file (default cap 100 MB) |
| Video | `videos/chunk-{XXX}/{key}/episode_{XXXXXX}.mp4` | `videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4`, episodes concatenated (default cap 200 MB in source; 500 MB in the HIL-SERL example) |
| Episode meta | `meta/episodes.jsonl`, `meta/episodes_stats.jsonl`, `meta/tasks.jsonl` | `meta/episodes/chunk-000/file-000.parquet`, `meta/tasks.parquet` |
| Global | `meta/info.json`, `meta/stats.json` | same, plus `chunks_size` (1000), `data_files_size_in_mb`, `video_files_size_in_mb`, `data_path`, `video_path` templates |

Sources: LeRobot v3 docs and blog, `lerobot_dataset.py` docstring at tag v0.3.3, `datasets/utils.py` constants, and the `lerobot/example_hil_serl_dataset` files I downloaded and read with pyarrow.

### 1.2 Schema, verified against a real v3 dataset

`meta/info.json` keys: `codebase_version` ("v3.0"), `robot_type`, `fps`, `total_episodes`, `total_frames`, `total_tasks`, `chunks_size`, `data_files_size_in_mb`, `video_files_size_in_mb`, `splits` (`{"train": "0:15"}`), `data_path`, `video_path`, `features`. Each feature is `{dtype, shape, names}`; video features also carry `info` with `video.fps`, `video.codec`, `video.pix_fmt`, `video.height`, `video.width`, `video.channels`, `video.is_depth_map`, `has_audio`.

Mandatory per-frame columns, auto-added by `add_frame()`: `timestamp` (float32), `frame_index`, `episode_index`, `index`, `task_index` (int64). The user supplies `observation.state`, `action`, `observation.images.*`, and a `task` string. Sim datasets also use `next.reward`, `next.done`, `next.success`; HIL-SERL uses `complementary_info.<name>` for extras. Parquet stores vectors as `list<double>` even when `info.json` says float32.

Two facts that matter for us:

- `timestamp` is synthetic: `if timestamp is None: timestamp = frame_index / self.fps`. The loader checks `timestamp` against `fps` with `tolerance_s = 1e-4` and rejects jittery wall-clock stamps. Real wall-clock and link timing must therefore live in extra columns.
- `meta/episodes` parquet columns (v3): `episode_index`, `tasks` (list<string>), `length`, `data/chunk_index`, `data/file_index`, `dataset_from_index`, `dataset_to_index`, `videos/<key>/chunk_index`, `videos/<key>/file_index`, `videos/<key>/from_timestamp`, `videos/<key>/to_timestamp`, `stats/<feature>/{min,max,mean,std,count}`, `meta/episodes/chunk_index`, `meta/episodes/file_index`. Episode boundaries are resolved from this table, not filenames. `finalize()` must be called or parquet footers are missing.

### 1.3 Video handling

Default encoder (`configs/video.py`): `libsvtav1`, `yuv420p`, `crf=30`, `g=2`, `preset=12`; `vcodec=auto` prefers hardware encoders (`h264_videotoolbox` first on macOS) and falls back to `libsvtav1`. Decoding is by timestamp (`torchcodec` if available, else `pyav`). Frames of one episode are always in one file; per-camera shards.

### 1.4 How ALOHA and SO-100 record

| System | Rate | Cameras | Episode | Notes |
|---|---|---|---|---|
| ALOHA / ACT | 50 Hz teleop and recording | 4× 480×640 RGB | 8–14 s = 400–700 steps | Original HDF5: `/action (T,14)`, `/observations/qpos (T,14)`, `/observations/images/<cam> (T,480,640,3)`. 50 demos/task; "10–20 minutes of data per task, 30–60 minutes wall-clock because of resets and teleoperator mistakes". |
| Mobile ALOHA | 50 Hz | 3× 480×640 | up to 75 s (Cook Shrimp) | 50 demos/task (20 for the two hardest). |
| SO-100/101 via `lerobot-record` | 30 fps typical | OpenCV webcams | `episode_time_s=60`, `reset_time_s=60`, `num_episodes=50` defaults | Loop paces with a 1/fps timer; frame = `{**observation, **action, "task"}`. Docs recommend ≥50 episodes, 10 per object location. |
| DROID | 15 Hz | 3 stereo ZED at 1280×720 | ~16.5 s mean | Quest 2 controllers; 76k successful of ~92k recorded (16k failures excluded). |
| GR00T N1 (GR-1) | 20 Hz | – | – | 88 h real teleop; low-quality trajectories filtered before post-training. |

### 1.5 Recording without the full lerobot stack

No maintained standalone LeRobot writer exists as of this search (`lero-core` edits existing datasets; phospho's docs rely on lerobot tooling). The format is simple enough to write directly: `pyarrow` for parquet (we verified the full v3 schema loads with pyarrow alone), `json` for `info.json`/`stats.json`, and an `ffmpeg` subprocess for optional video. Cost: ~150 lines, no torch dependency. Risk [unverified]: whether `LeRobotDataset` tolerates a missing `stats/*` block in `meta/episodes`; emit per-episode min/max/mean/std/count with numpy to be safe.

## 2. What makes a demonstration useful

### 2.1 Quality metrics with measured effect on policy success

| Source | Metric | Evidence |
|---|---|---|
| robomimic (Mandlekar 2021) | Operator proficiency; lower quality = longer trajectories | BC-RNN success, Can: Worse 92.0%, Okay 95.3%, Better 99.3%; Square: Worse 39.3%, Okay 45.3%, Better 66.0%. Square PH (200 demos, one proficient operator) 84.0% vs MH mixes 55.3–74.0%. Mean Square length: Better 185 steps, Worse 357. |
| Belkhale 2023 | Action divergence (variance of actions at a state) and transition diversity | Consistent actions beat broader state coverage with noisy actions. |
| RINSE (Kulkarni 2026) | Spectral arc length (SAL) on end-effector speed; trajectory-envelope distance (TED) | Keeping top 50/300 by SAL on robomimic Transport MH: 55% vs 39% on full set. Real xArm Push Block: TED top 100/200 → 88% vs 68% full. Smoother demos map to lower operator-reported difficulty. |
| DQAF (Narayanan 2026) | Log dimensionless jerk (LDLJ), static fraction (stalls), action-range saturation, gripper chatter, sub-task progress | Failure detection recall 85.7%; operator receiving automated feedback: 93.3% success vs 66.7% without. |
| DemInf (Hejna 2025) | State–action mutual information per trajectory | Up to 10% success gain from curation on robomimic, ALOHA, Franka. |
| ACT (Zhao 2023) | Teleop rate | 5 Hz instead of 50 Hz: 62% longer teleop time. Human demos are stochastic even from one operator; CVAE needed. |
| DROID, GR00T N1 | Binary success label at collection; drop failures | DROID dropped ~17% of recorded episodes. |

Industry norms are vendor claims, not measurements: 20–40 episodes/h simple pick-place, 10–20 complex (Claru); novices 8–12/h, trained 25–40/h, budget 10–30% QA rejection (Dexset); Trossen states jitter makes "the model learn the shake".

### 2.2 Throughput norms

| Setting | Demos per wall-clock hour | Basis |
|---|---|---|
| ALOHA, 8–14 s tabletop tasks | 50–100 | 50 demos in 30–60 min including resets and mistakes |
| SpaceMouse teleop, cup arrangement | ~64 [derived] | UMI paper: UMI did 48 in 15 min and was "3× faster than teleoperation" |
| RoboTurk (sim, phone, many concurrent workers) | ~100 successful platform-wide | 2218 successful of 3224 in 22 h; per-operator rate not reported |
| Vendor tabletop norms | 10–40 | see above, [vendor claims] |

### 2.3 Latency and jitter

No study was found that collects demonstrations at controlled latency levels and reports downstream policy success. The evidence is on human task performance, which transfers through the robomimic finding that slower, more corrective operators yield worse policies:

- Rakita 2020 (mimicry control, 7 conditions): base ~90 ms measured; added onset latency to 250/500/750 ms degraded accuracy, time, and overshoot on all three tasks; no participant finished the block task at 500 or 750 ms. Equivalent robot slowness did not degrade accuracy. Users adapt to slowness with move-and-wait, not to onset latency.
- Mobile-robot delay study (2025, 10 participants, 0–500 ms): first significant loss between 200 and 300 ms (speed p=0.01, path deviation p=0.011); plateau by 400 ms.
- RoboTurk: 20 ms vs 120 ms one-way delay, pose-controlled phone interface in sim: no significant completion-time difference (KS p≥0.598). California→China servers: mean completion +24 s (assembly) and +28 s (picking).
- Jitter: no quantitative study found. Mechanism per Belkhale: jitter injects action variance at the same state, i.e. action divergence, and per RINSE it adds high-frequency energy that SAL/LDLJ penalise. ACT's 5 Hz result bounds the cost of low command rate.
- UMI: policies trained on zero-latency data need explicit latency matching at deployment; the collection pipeline must log actual per-stream latencies so they can be compensated.

Working thresholds for our curve: ≤120 ms one-way is benign for pose-level control; 200–300 ms is where degradation begins; ≥500 ms breaks fine tasks without predictive aids.

## 3. Implication for our design

Log everything needed to (a) compute the success-vs-latency curve, (b) score each episode with the smoothness/stall metrics above, and (c) reproduce the link timing for deployment latency matching. Keep LeRobot's synthetic `timestamp` and put wall-clock in `complementary_info.*`.

### 3.1 Minimal recorder schema (LeRobot v3, `fps` = control rate, state-only by default)

| Column | dtype, shape | Meaning |
|---|---|---|
| `observation.state` | float32 [7] | measured joints (6) + gripper, sat side, at obs time |
| `observation.environment_state` | float32 [7] | object pose (sim privileged), optional |
| `action` | float32 [7] | operator joint setpoints + gripper for this step |
| `next.done`, `next.success` | bool [1] | episode end, task success |
| `complementary_info.t_cmd_ground` | float64 [1] | wall-clock when operator issued this action |
| `complementary_info.t_cmd_sat` | float64 [1] | sat sim-clock when applied (or NaN if dropped) |
| `complementary_info.t_obs_sat` | float64 [1] | sat sim-clock of observation |
| `complementary_info.t_obs_ground` | float64 [1] | wall-clock when ground received it |
| `complementary_info.cmd_seq`, `.obs_seq` | int64 [1] | sequence numbers for loss accounting |
| `complementary_info.rtt_ms` | float32 [1] | measured round trip at this step |
| `complementary_info.link_state` | int64 [1] | 0 ok, 1 hold, 2 retract, 3 outage |
| `complementary_info.intervention` | bool [1] | safety logic or synthetic operator override active |
| `observation.images.<cam>` | video [3,H,W] | optional, off by default (video is a bandwidth budget in the testbed) |

### 3.2 Per-episode record (sidecar `meta/quality.jsonl`; loader ignores unknown files [unverified])

`episode_index, task, operator_id, link_profile, success, t_start_wall, t_end_wall, reset_s, steps, rtt_ms_mean/p95/max, jitter_ms_std, loss_frac, outage_s, n_interventions, n_hold_events, n_safety_stops, unsafe_motion (bool), sal, ldlj, path_ratio, stall_frac, gripper_chatter_hz, overshoot_count`.

Derived acceptance numbers: success rate; `demos_per_hour = successful / Σ(episode + reset wall time)`; SAL and LDLJ distributions versus the zero-latency baseline; zero `unsafe_motion` on outage. Runnable check: write 2 episodes, reload with pyarrow, assert `timestamp == frame_index/fps` within 1e-4 and `dataset_to_index − dataset_from_index == length`.

## Sources

- https://huggingface.co/docs/lerobot/en/lerobot-dataset-v3
- https://huggingface.co/blog/lerobot-datasets-v3
- https://huggingface.co/docs/lerobot/en/porting_datasets_v3
- https://raw.githubusercontent.com/huggingface/lerobot/main/src/lerobot/datasets/lerobot_dataset.py
- https://raw.githubusercontent.com/huggingface/lerobot/v0.3.3/src/lerobot/datasets/lerobot_dataset.py
- https://raw.githubusercontent.com/huggingface/lerobot/main/src/lerobot/datasets/utils.py
- https://raw.githubusercontent.com/huggingface/lerobot/main/src/lerobot/datasets/video_utils.py
- https://raw.githubusercontent.com/huggingface/lerobot/main/src/lerobot/configs/video.py
- https://raw.githubusercontent.com/huggingface/lerobot/main/src/lerobot/scripts/lerobot_record.py
- https://huggingface.co/docs/lerobot/en/il_robots
- https://huggingface.co/docs/lerobot/en/hilserl
- https://huggingface.co/docs/lerobot/en/hil_data_collection
- https://huggingface.co/datasets/lerobot/example_hil_serl_dataset (meta/info.json, meta/episodes, data, tasks parquet)
- https://docs.phospho.ai/learn/lerobot-dataset
- https://pypi.org/project/lero-core/
- https://docs.trossenrobotics.com/aloha_docs/2.0/operation/data_collection.html
- https://github.com/huggingface/lerobot/issues/769
- https://arxiv.org/html/2304.13705 (ALOHA / ACT)
- https://arxiv.org/html/2401.02117 (Mobile ALOHA)
- https://arxiv.org/html/2403.12945v2 (DROID)
- https://arxiv.org/html/2503.14734v1 (GR00T N1)
- https://arxiv.org/pdf/2303.04137 (Diffusion Policy)
- https://arxiv.org/html/2402.10329 (UMI)
- https://arxiv.org/pdf/2108.03298 (robomimic, "What Matters")
- https://robomimic.github.io/study/
- https://robomimic.github.io/docs/datasets/robomimic_v0.1.html
- https://arxiv.org/abs/2306.02437 (Belkhale, Data Quality in IL)
- https://arxiv.org/html/2604.23000v1 (RINSE)
- https://arxiv.org/html/2605.26349 (DQAF)
- https://arxiv.org/abs/2502.08623 (DemInf)
- https://arxiv.org/pdf/1811.02790 (RoboTurk)
- https://arxiv.org/pdf/2112.05251 (MoMaRT)
- https://graphics.cs.wisc.edu/Papers/2020/RMG20/rmg-hri2020.pdf (Rakita 2020)
- https://arxiv.org/html/2508.18074v1 (communication delay, mobile robot teleop)
- https://arxiv.org/pdf/2605.19138 (COBALT; numbers not extractable, not used)
- https://www.trossenrobotics.com/post/teleoperation-robot-learning-high-quality-demonstration-data
- https://claru.ai/training-data/teleoperation
- https://dexset.ai/blogs/teleoperation-data-collection-robot-learning-complete-2026/
