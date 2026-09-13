"""Runner: ground <-> link <-> sat over real UDP sockets on 127.0.0.1.

    uv run python -m spaceteleop.run --profile leo_relay --task capture --episodes 3 \
        --seed 0 --out docs/experiments/raw/leo

Clock choice: REALTIME. The sim is stepped up to wall-clock elapsed inside the satellite
controller, and the link emulator delays packets in wall clock too, so injected latency,
control lag and sim time are one time base and need no reconciliation. A logical clock
would let episodes run faster than realtime, but only if every socket, thread sleep and
operator reaction were driven from it as well -- more machinery than this program needs.
Cost: an episode takes its own wall-clock duration. Keep --max-s small in tests.

Processes are threads in one interpreter (sat controller + link drain threads + ground
loop on the main thread). They share nothing but the read-only MjModel and the sockets
are real, so moving any of them to a subprocess is a launcher change, not a rewrite.
"""
import argparse
import socket
import threading
import time

from . import sim
from .ground.loop import run_episode as ground_episode
from .ground.operators import SyntheticOperator
from .link.emulator import Link
from .link.profiles import PROFILES, rtt_ms
from .metrics import aggregate, episode_metrics, table
from .record import load_episode, write_episode
from .sat.controller import MAX_FRAME, run_episode as sat_episode
from .strategies.baseline import Baseline


def _sock():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    s.setblocking(False)
    return s


def episode(m, d, profile, seed, args, strategy_cls=Baseline):
    """One full episode over real sockets. Returns (rows, ep_summary)."""
    gnd, sat = _sock(), _sock()
    link = Link(PROFILES[profile], sat.getsockname(), gnd.getsockname(), seed=seed).start()
    out = {}
    th = threading.Thread(target=lambda: out.update(sat_episode(
        m, d, sat, ("127.0.0.1", link.down_port), seed, strategy_cls(),
        max_s=args.max_s, tel_hz=args.tel_hz, frame_bytes=args.frame_bytes)), daemon=True)
    th.start()
    op = SyntheticOperator(m, seed=seed, tau_h=args.tau_h)
    rows, gstats = ground_episode(gnd, ("127.0.0.1", link.up_port), op, strategy_cls(),
                                  cmd_hz=args.cmd_hz, tau_h=op.tau_h, max_s=args.max_s)
    th.join(5.0)
    link.stop()
    gnd.close()
    sat.close()
    return rows, dict(gstats, **out, link=link.stats())


def main(argv=None):
    p = argparse.ArgumentParser(prog="spaceteleop.run")
    p.add_argument("--profile", default="zero", choices=sorted(PROFILES))
    p.add_argument("--task", default="capture", choices=["capture"])
    p.add_argument("--episodes", type=int, default=3)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="docs/experiments/raw/run")
    p.add_argument("--max-s", type=float, default=30.0)
    p.add_argument("--cmd-hz", type=float, default=50.0)
    p.add_argument("--tel-hz", type=float, default=30.0)
    p.add_argument("--tau-h", type=float, default=0.25)
    p.add_argument("--frame-bytes", type=int, default=0,
                   help=f"pad telemetry to model a video budget (max {MAX_FRAME})")
    args = p.parse_args(argv)

    m, d = sim.build()
    eps, n = [], 0
    for k in range(args.episodes):
        seed = args.seed + k
        t0 = time.monotonic()
        rows, s = episode(m, d, args.profile, seed, args)
        if len(rows) < 4:
            raise RuntimeError(f"episode {k} produced {len(rows)} commands: "
                               f"the satellite or the link never came up ({s})")
        path = write_episode(args.out, k, rows, task=args.task, index0=n)
        n += len(rows)
        em = episode_metrics(load_episode(path), s.get("success"), time.monotonic() - t0,
                             s["cmds_sent"], s.get("cmds_rx", 0))
        eps.append(em)
        print(f"ep {k} seed {seed} success={em['success']} {em['duration_s']:.1f}s "
              f"rtt_p50={em['rtt_p50']:.0f}ms hold={em['hold_s']:.2f}s frames={em['frames']}")
    agg = aggregate(eps)
    print()
    print(table(args.profile, agg))
    print(f"nominal_rtt_ms   {rtt_ms(args.profile):.0f}")
    print(f"written          {args.out}")
    return agg


if __name__ == "__main__":
    main()
