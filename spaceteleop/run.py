"""Runner: ground <-> link <-> sat over real UDP sockets on 127.0.0.1.

    uv run python -m spaceteleop.run --profile leo_relay --task capture --episodes 8
    uv run python -m spaceteleop.run --profile sweep:500 --task peg --episodes 8
    uv run python -m spaceteleop.run --profile leo_relay --arms 4 --episodes 2

Clock choice: REALTIME. The sim is stepped up to wall-clock elapsed inside the satellite
controller, and the link emulator delays packets in wall clock too, so injected latency,
control lag and sim time are one time base and need no reconciliation. A logical clock
would let episodes run faster than realtime, but only if every socket, thread sleep and
operator reaction were driven from it as well -- more machinery than this program needs.
Cost: an episode takes its own wall-clock duration. Keep --max-s small in tests.

Processes are threads in one interpreter. `--arms N` runs N independent ground/link/sat
triplets concurrently, each on its own ephemeral ports with its own MjData over the shared
read-only MjModel, which is the 4-operator scaling case of the charter. Ports are always
ephemeral, so several runs in separate processes never collide and no --port flag is
needed. Bandwidth is reported as bytes on the wire per direction per second, per arm and
summed, straight from the link emulator's own counters.
"""
import argparse
import socket
import threading
import time

import mujoco

from . import sim
from .ground.loop import run_episode as ground_episode
from .ground.operators import SyntheticOperator
from .link.emulator import Link
from .link.profiles import PROFILES, get, rtt_ms
from .metrics import aggregate, episode_metrics, table
from .record import load_episode, load_sat, write_episode
from .sat.controller import MAX_FRAME, RESET_MAX, run_episode as sat_episode
from .strategies import STRATEGIES, get as get_strategy
from .strategies.baseline import Baseline

TASKS = {
    "capture": "SYNTHESIS 3 task 2: grasp a box drifting at 2-5 cm/s, hold it in the target",
    "peg": "SYNTHESIS 3 task 5: insert a 60 mm peg into a fixture hole, 6 mm clearance",
    "capture_chain": "H20: capture, then RE-RELEASE to seed the next demo (targets A<->B), "
                     "tethered box; --reset free chains, --reset teleop charges a "
                     "teleoperated return-to-spawn",
}


def _sock():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    s.setblocking(False)
    return s


def episode(m, d, profile, seed, args, strategy_cls=None, op=None, st=None):
    """One full episode over real sockets. Returns (rows, ep_summary).

    `op` and `st` are the H20 chaining seam: pass the previous episode's operator and sim
    state and the scene is not reset, so the next demonstration starts from where the last
    one let go. Both default to None = the canonical per-episode behaviour."""
    task = getattr(args, "task", "capture")
    mode = getattr(args, "reset", "free")
    grace = RESET_MAX if task == "capture_chain" else 0.0   # the reset is teleoperated too
    strategy_cls = strategy_cls or get_strategy(getattr(args, "strategy", "baseline"))
    gnd, sat = _sock(), _sock()
    link = Link(get(profile), sat.getsockname(), gnd.getsockname(), seed=seed).start()
    out = {}
    th = threading.Thread(target=lambda: out.update(sat_episode(
        m, d, sat, ("127.0.0.1", link.down_port), seed,
        strategy_cls(cmd_hz=args.cmd_hz), task=task,
        max_s=args.max_s, tel_hz=args.tel_hz, frame_bytes=args.frame_bytes, st=st,
        reset_mode=mode)), daemon=True)
    th.start()
    op = op or SyntheticOperator(m, seed=seed, task=task, tau_h=args.tau_h, reset_mode=mode)
    # the ground copy gets the operator itself (H14 scales the operator's speed, not the
    # wire) and the model (H11 ground ablation needs it for FK)
    gs = strategy_cls(operator=op, cmd_hz=args.cmd_hz, tel_hz=args.tel_hz, tau_h=op.tau_h, m=m)
    t_launch = time.monotonic()
    rows, gstats = ground_episode(gnd, ("127.0.0.1", link.up_port), op, gs,
                                  cmd_hz=args.cmd_hz, tau_h=op.tau_h,
                                  max_s=args.max_s + grace)
    th.join(5.0 + grace)
    stats = link.stats()
    link.stop()
    gnd.close()
    sat.close()
    ev = dict(out.get("events", {}))
    for k, v in getattr(gs, "ev", {}).items():   # a ground-side strategy counts on its own side
        if k.endswith(("_frac", "_peak")):
            ev[k] = max(ev.get(k, 0), v)
    out["events"] = ev
    innov = getattr(gs, "innov", None)
    return rows, dict(gstats, **out, link=stats,
                      t_first_cmd=t_launch + (rows[0]["timestamp"] if rows else 0.0),
                      **({"twin_innov_m": sum(innov) / len(innov)} if innov else {}))


def run_arm(m, args, arm, sink):
    d = mujoco.MjData(m)
    eps, n, bw, resets = [], 0, [], []
    chain = args.task == "capture_chain"
    op, st, t_success = None, None, None
    for k in range(args.episodes):
        seed = args.seed + 1000 * arm + k
        if op is None or not chain:
            op = SyntheticOperator(m, seed=seed, task=args.task, tau_h=args.tau_h,
                                   reset_mode=args.reset)
        t0 = time.monotonic()
        rows, s = episode(m, d, args.profile, seed, args, op=op, st=st)
        if t_success is not None:
            # R, per the H20 trap: success -> the next episode's FIRST command, over the
            # real link, through the real operator. Never a sim.reset teleport.
            resets.append(s["t_first_cmd"] - t_success)
        if chain:
            st, t_success = s["st"], s["success_wall"]
            op.restart(s["released"])
        if len(rows) < 4:
            if not eps:
                raise RuntimeError(f"arm {arm} episode {k} produced {len(rows)} commands: "
                                   f"the satellite or the link never came up")
            # A whole episode inside a blackout (e.g. a GEO handover phased onto link
            # start) is a failed demonstration, not a harness fault: log it and go on.
            em = dict(eps[-1], success=False, duration_s=float(args.max_s), frames=0,
                      rtt_p50=float("nan"), rtt_p95=float("nan"), rtt_max=float("nan"),
                      cmd_loss=1.0, hold_frames=0, hold_s=0.0, stalls=0, max_dt_s=0.0,
                      cage=0, no_link=True, events={k2: 0 for k2 in eps[-1]["events"]})
            eps.append(em)
            bw.append(s["link"])
            print(f"arm {arm} ep {k} seed {seed} success=False NO_LINK {args.max_s:.1f}s")
            continue
        out = args.out if args.arms == 1 else f"{args.out}/arm{arm}"
        path = write_episode(out, k, rows, task=args.task, index0=n, satlog=s["satlog"])
        n += len(rows)
        # T09: the episode ends at the success/done instant (or the cap). `done_wall` is the
        # satellite's own stamp for it; what follows is the 1 s linger, the thread join and
        # the npz write, none of which a data campaign would pay for twice.
        dur = (s["done_wall"] - t0) if s.get("done_wall") else time.monotonic() - t0
        em = episode_metrics(load_episode(path), s.get("success"), dur,
                             s["cmds_sent"], s.get("cmds_rx", 0), events=s.get("events"),
                             sat=load_sat(path), vmax=Baseline.vmax)
        eps.append(em)
        bw.append(s["link"])
        print(f"arm {arm} ep {k} seed {seed} success={em['success']} "
              f"{em['duration_s']:.1f}s rtt_p50={em['rtt_p50']:.0f}ms "
              f"hold={em['hold_s']:.2f}s unsafe={em['unsafe']} cage={em['cage']} "
              f"stalls={em['stalls']} max_dt={em['max_dt_s']:.2f}s frames={em['frames']}"
              + (f" reset={s['reset_s']:.1f}s" if chain else "")
              + (f" innov={s['twin_innov_m'] * 1000:.1f}mm" if "twin_innov_m" in s else ""))
    sink[arm] = (eps, bw, resets)


def main(argv=None):
    p = argparse.ArgumentParser(prog="spaceteleop.run")
    p.add_argument("--profile", default="zero",
                   help=f"{' | '.join(sorted(PROFILES))} | sweep:<rtt_ms>")
    p.add_argument("--task", default="capture", choices=sorted(TASKS))
    p.add_argument("--reset", default="free", choices=("free", "teleop"),
                   help="capture_chain: free = the release seeds the next demo (chained); "
                        "teleop = carry the box back to the spawn zone first, charged")
    p.add_argument("--strategy", default="baseline", choices=sorted(STRATEGIES))
    p.add_argument("--list-tasks", action="store_true", help="print the task set and exit")
    p.add_argument("--arms", type=int, default=1, help="independent concurrent triplets")
    p.add_argument("--episodes", type=int, default=3, help="episodes PER ARM")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="docs/experiments/raw/run")
    p.add_argument("--max-s", type=float, default=20.0)
    p.add_argument("--cmd-hz", type=float, default=50.0)
    p.add_argument("--tel-hz", type=float, default=30.0)
    p.add_argument("--tau-h", type=float, default=0.17,
                   help="human visuomotor correction delay, s (SYNTHESIS 8: 170 ms)")
    p.add_argument("--frame-bytes", type=int, default=0,
                   help=f"pad telemetry to model a video budget (max {MAX_FRAME})")
    args = p.parse_args(argv)
    if args.list_tasks:
        print("\n".join(f"{k:<9} {v}" for k, v in sorted(TASKS.items())))
        return None

    m, _ = sim.build(args.task)
    sink = {}
    ths = [threading.Thread(target=run_arm, args=(m, args, a, sink))
           for a in range(args.arms)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    if len(sink) != args.arms:
        raise RuntimeError(f"only {len(sink)}/{args.arms} arms finished")

    eps = [e for a in range(args.arms) for e in sink[a][0]]
    bw = [b for a in range(args.arms) for b in sink[a][1]]
    rs = [r for a in range(args.arms) for r in sink[a][2]]
    up = sum(b["up_bps"] for b in bw) / max(1, len(bw)) * args.arms
    down = sum(b["down_bps"] for b in bw) / max(1, len(bw)) * args.arms
    print()
    if args.arms > 1:
        for a in range(args.arms):
            g = aggregate(sink[a][0])
            print(f"arm {a}: success_rate {g['success_rate']:.2f}  "
                  f"demos_per_hour {g['demos_per_hour']:.1f}  unsafe {g['unsafe']}  "
                  f"rtt_p50 {g['rtt_p50']:.0f} ms")
        print()
    agg = aggregate(eps)
    agg["reset_R_s"] = sum(rs) / len(rs) if rs else float("nan")
    print(table(args.profile, agg, extra=[
        ("task", args.task), ("strategy", args.strategy), ("arms", args.arms),
        ("reset_mode", args.reset),
        ("R_s", f"{agg['reset_R_s']:.2f} (n={len(rs)})"),
        ("wire_up_Bps", f"{up:,.0f}"), ("wire_down_Bps", f"{down:,.0f}"),
        ("nominal_rtt_ms", f"{rtt_ms(args.profile):.0f}"), ("written", args.out)]))
    return agg


if __name__ == "__main__":
    main()
