"""Aggregate the matrix: docs/experiments/raw/*/summary.json -> results.md/.json, paired.md.

    uv run python experiments/aggregate.py [--raw docs/experiments/raw] [--out docs/experiments]

results.md   per task: rows = arm, columns = profile in RTT order, one table per metric
             family (success + Wilson CI, demos/hour, RTT, unsafe by type, smoothness,
             plus a table for every extra per-hypothesis counter that appears in the
             run's event dict -- knock-aways, assist fraction, tether-taut, whatever).
             Then the knee per arm and the SYNTHESIS section 6 acceptance readout.
results.json the same numbers plus the per-seed success and duration vectors, so any
             paired test can be recomputed without re-running the matrix.
paired.md    every (task, profile) where the baseline arm and another arm both ran:
             paired success difference, discordant counts, McNemar exact p (stdlib), and
             the demos/hour ratio with a paired bootstrap 95 % CI.
"""
import argparse
import glob
import json
import math
import os
import warnings

import numpy as np

SAFE = ("move_in_hold", "vel_over", "keepout", "cage")
DIAG = SAFE + ("hold", "ramp_clip", "pos_clamp", "retract", "jams", "stale")
NAMED = ("zero", "direct_gs", "leo_relay", "geo_relay")     # section 6 acceptance set
PRIMARY_TAU = 0.17
Z = 1.959963984540054                                       # 95 %


def wilson(k, n, z=Z):
    """95 % Wilson score interval for k successes in n."""
    if n == 0:
        return (0.0, 1.0)
    c = (k + z * z / 2) / (n + z * z)
    h = z / (n + z * z) * math.sqrt(k * (n - k) / n + z * z / 4)
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_p(b, c):
    """Two-sided exact McNemar: binomial(b+c, 0.5) tail. b, c = discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * 0.5 ** n
    return min(1.0, 2 * tail)


def _dph(succ, dur, idx):
    """demos/hour = 3600 / mean wall of the SUCCESSFUL episodes (metrics.aggregate)."""
    d = np.where(succ[idx], dur[idx], np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")                      # all-failure resamples -> nan
        return 3600.0 / np.nanmean(d, axis=-1)


def boot_ratio(a, b, n_boot=2000, seed=0):
    """Paired bootstrap 95 % CI of demos/hour(a) / demos/hour(b). a, b = (succ, dur)."""
    n = len(a[0])
    if n == 0:
        return (float("nan"),) * 3
    idx = np.random.default_rng(seed).integers(0, n, (n_boot, n))
    r = _dph(a[0], a[1], idx) / _dph(b[0], b[1], idx)
    r = r[np.isfinite(r)]
    point = _dph(a[0], a[1], np.arange(n)) / _dph(b[0], b[1], np.arange(n))
    if not len(r):
        return (float(point), float("nan"), float("nan"))
    return (float(point), float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5)))


def load(raw):
    """Every clean summary.json under `raw`, enriched with the per-seed vectors."""
    out = []
    for p in sorted(glob.glob(f"{raw}/*/summary.json")):
        with open(p) as f:
            s = json.load(f)
        if s.get("error") or not s.get("episodes"):
            continue
        eps = sorted(s["episodes"], key=lambda e: e["seed"])
        s["seeds_used"] = [e["seed"] for e in eps]
        s["success"] = [int(e["success"]) for e in eps]
        s["durations"] = [e["duration_s"] for e in eps]
        s["n"], s["k"] = len(eps), sum(s["success"])
        s["wilson"] = wilson(s["k"], s["n"])
        out.append(s)
    return out


def arms(cs):
    """Distinct (strategy, tau, block) row keys and their display labels."""
    keys = sorted({(c["strategy"], c["tau_h"], c["block"]) for c in cs})
    dup = {(s, t) for s, t, _ in keys if sum(1 for a in keys if a[:2] == (s, t)) > 1}
    lab = {}
    for s, t, b in keys:
        lab[(s, t, b)] = s + ("" if t == PRIMARY_TAU else f" tau{t}") + \
            (f" [{b}]" if (s, t) in dup else "")
    return keys, lab


def _table(cs, profiles, keys, lab, fmt):
    """rows = arm, cols = profile (already in RTT order), cell = fmt(summary) or '-'."""
    by = {(c["strategy"], c["tau_h"], c["block"], c["profile"]): c for c in cs}
    head = "| arm | " + " | ".join(profiles) + " |"
    rule = "|---" * (len(profiles) + 1) + "|"
    rows = []
    for k in keys:
        cells = [fmt(by[k + (p,)]) if k + (p,) in by else "-" for p in profiles]
        rows.append(f"| {lab[k]} | " + " | ".join(cells) + " |")
    return "\n".join([head, rule] + rows)


def _g(c, key, d=float("nan")):
    return c["aggregate"].get(key, d)


def _arm(k):
    return k[0] + ("" if k[1] == PRIMARY_TAU else f" tau{k[1]}")


def _nonzero(c):
    ev = {k: int(_g(c, "events", {}).get(k, 0)) for k in SAFE}
    hit = [f"{k}={v}" for k, v in ev.items() if v]
    return f" ({', '.join(hit)})" if hit else ""


def _f(v, p=2):
    return f"{v:.{p}f}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)


def extras(cs):
    """Per-hypothesis counters that appear in the event dicts (knock-away, assist, ...)."""
    ks = set()
    for c in cs:
        ks |= {k for k in _g(c, "events", {}) if k not in DIAG}
    return sorted(ks)


def knee(cs, keys):
    """First sweep RTT where success < 0.8 x that arm's own zero cell, interpolated."""
    out = {}
    for k in keys:
        rows = [c for c in cs if (c["strategy"], c["tau_h"], c["block"]) == k]
        zero = next((c for c in rows if c["profile"] == "zero"), None)
        sw = sorted([c for c in rows if c["profile"].startswith("sweep:")],
                    key=lambda c: c["rtt_ms"])
        if zero is None or len(sw) < 2:
            continue
        thr = 0.8 * zero["k"] / max(1, zero["n"])
        pts = [(c["rtt_ms"], c["k"] / max(1, c["n"])) for c in sw]
        hit = None
        for (r0, s0), (r1, s1) in zip(pts, pts[1:]):
            if s1 < thr <= s0:
                hit = r0 + (s0 - thr) / (s0 - s1) * (r1 - r0)
                break
            if s0 < thr:                       # already below at the first sweep point
                hit = r0
                break
        out[k] = dict(threshold=thr, zero_success=zero["k"] / max(1, zero["n"]),
                      knee_ms=hit, points=pts)
    return out


def acceptance(cs, keys):
    """SYNTHESIS section 6: leo_relay as a fraction of the same arm's zero cell."""
    out = {}
    for k in keys:
        rows = {c["profile"]: c for c in cs
                if (c["strategy"], c["tau_h"], c["block"]) == k}
        z, l = rows.get("zero"), rows.get("leo_relay")
        if not z or not l:
            continue
        sz, sl = z["k"] / max(1, z["n"]), l["k"] / max(1, l["n"])
        dz, dl = _g(z, "demos_per_hour", 0.0), _g(l, "demos_per_hour", 0.0)
        out[k] = dict(success_frac=sl / sz if sz else float("nan"),
                      dph_frac=dl / dz if dz else float("nan"),
                      success_zero=sz, success_leo=sl, dph_zero=dz, dph_leo=dl,
                      unsafe_named=sum(int(_g(rows[p], "unsafe", 0)) for p in NAMED
                                       if p in rows),
                      profiles_present=[p for p in NAMED if p in rows])
    return out


def paired(cs, baseline):
    """Every (task, profile, tau) where the baseline arm and another arm both ran."""
    out = []
    for c in cs:
        if c["strategy"] == baseline:
            continue
        b = next((x for x in cs if x["strategy"] == baseline and x["task"] == c["task"]
                  and x["profile"] == c["profile"] and x["tau_h"] == c["tau_h"]), None)
        if b is None:
            continue
        seeds = sorted(set(b["seeds_used"]) & set(c["seeds_used"]))
        bi = {s: i for i, s in enumerate(b["seeds_used"])}
        ci = {s: i for i, s in enumerate(c["seeds_used"])}
        bs = np.array([b["success"][bi[s]] for s in seeds], bool)
        as_ = np.array([c["success"][ci[s]] for s in seeds], bool)
        bd = np.array([b["durations"][bi[s]] for s in seeds], float)
        ad = np.array([c["durations"][ci[s]] for s in seeds], float)
        nb, nc = int((bs & ~as_).sum()), int((as_ & ~bs).sum())
        pt, lo, hi = boot_ratio((as_, ad), (bs, bd))
        out.append(dict(task=c["task"], profile=c["profile"], rtt_ms=c["rtt_ms"],
                        tau_h=c["tau_h"], arm=c["strategy"], baseline=baseline,
                        n=len(seeds), base_success=float(bs.mean()) if len(seeds) else 0.0,
                        arm_success=float(as_.mean()) if len(seeds) else 0.0,
                        diff=float(as_.mean() - bs.mean()) if len(seeds) else 0.0,
                        b_only=nb, c_only=nc, mcnemar_p=mcnemar_p(nb, nc),
                        dph_ratio=pt, dph_ci=[lo, hi]))
    return sorted(out, key=lambda r: (r["task"], r["rtt_ms"], r["arm"]))


def results_md(cs, kn, acc, baseline):
    doc = ["# Experiment results", "",
           f"{len(cs)} cells, {sum(c['n'] for c in cs)} episodes. "
           f"Baseline arm: `{baseline}`. Paired tests: `paired.md`.", ""]
    for task in sorted({c["task"] for c in cs}):
        tc = [c for c in cs if c["task"] == task]
        profiles = [p for _, p in sorted({(c["rtt_ms"], c["profile"]) for c in tc})]
        keys, lab = arms(tc)
        doc += [f"## Task `{task}`", ""]
        for title, fmt in [
            ("Success rate (95 % Wilson CI)",
             lambda c: f"{c['k'] / c['n']:.2f} [{c['wilson'][0]:.2f},{c['wilson'][1]:.2f}] "
                       f"{c['k']}/{c['n']}"),
            ("demos/hour (gross in brackets where the run reports it)",
             lambda c: f"{_f(_g(c, 'demos_per_hour'), 1)}" +
                       (f" [{_f(_g(c, 'demos_per_hour_gross'), 1)}]"
                        if "demos_per_hour_gross" in c["aggregate"] else "")),
            ("RTT p50 / p95, ms",
             lambda c: f"{_f(_g(c, 'rtt_p50_ms'), 0)} / {_f(_g(c, 'rtt_p95_ms'), 0)}"),
            ("Unsafe events (total; the section 6 counts that are non-zero)",
             lambda c: f"{int(_g(c, 'unsafe', 0))}" + _nonzero(c)),
            ("SAL / LDLJ / stall_frac",
             lambda c: f"{_f(_g(c, 'sal'))} / {_f(_g(c, 'ldlj'))} / "
                       f"{_f(_g(c, 'stall_frac'))}"),
        ]:
            doc += [f"**{title}**", "", _table(tc, profiles, keys, lab, fmt), ""]
        for k in extras(tc):
            doc += [f"**{k}**", "",
                    _table(tc, profiles, keys, lab,
                           lambda c, k=k: _f(_g(c, "events", {}).get(k, 0))), ""]
    doc += ["## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell", "",
            "| task | arm | zero success | threshold | knee (ms) |", "|---|---|---|---|---|"]
    for (task, k), v in sorted(kn.items()):
        kms = "never (> 1000)" if v["knee_ms"] is None else f"{v['knee_ms']:.0f}"
        doc.append(f"| {task} | {_arm(k)} | {v['zero_success']:.2f} | "
                   f"{v['threshold']:.2f} | {kms} |")
    if not kn:
        doc.append("| (no arm has a `zero` cell and >= 2 sweep points yet) |")
    doc += ["", "## SYNTHESIS section 6 acceptance readout (leo_relay / own zero cell)", "",
            "| task | arm | success frac | demos/h frac | unsafe on "
            + ", ".join(NAMED) + " |", "|---|---|---|---|---|"]
    for (task, k), v in sorted(acc.items()):
        doc.append(f"| {task} | {_arm(k)} | "
                   f"{v['success_frac']:.2f} | {v['dph_frac']:.2f} | "
                   f"{v['unsafe_named']} ({'+'.join(v['profiles_present'])}) |")
    if not acc:
        doc.append("| (no arm has both a `zero` and a `leo_relay` cell yet) |")
    doc += ["", "Acceptance (PROGRAM.md): both fractions >= 0.80 and zero unsafe events.", ""]
    return "\n".join(doc)


def paired_md(rows, baseline):
    doc = ["# Paired comparisons", "",
           f"Same seeds per cell, so success is a McNemar test on the discordant seeds "
           f"(`b` = `{baseline}` only, `c` = arm only; two-sided exact binomial). "
           f"demos/hour ratio is arm / {baseline} with a paired bootstrap 95 % CI "
           f"(2000 resamples of the seed list).", "",
           "| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | "
           "demos/h ratio [95 % CI] |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ci = f"[{r['dph_ci'][0]:.2f}, {r['dph_ci'][1]:.2f}]"
        doc.append(f"| {r['task']} | {r['profile']} | {r['tau_h']} | {r['arm']} | {r['n']} | "
                   f"{r['base_success']:.2f} | {r['arm_success']:.2f} | {r['diff']:+.2f} | "
                   f"{r['b_only']} | {r['c_only']} | {r['mcnemar_p']:.4f} | "
                   f"{r['dph_ratio']:.2f} {ci} |")
    if not rows:
        doc.append("| (no non-baseline arm has a paired baseline cell yet) |")
    return "\n".join(doc) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(prog="aggregate")
    p.add_argument("--raw", default="docs/experiments/raw")
    p.add_argument("--out", default="docs/experiments")
    p.add_argument("--baseline", default="baseline")
    a = p.parse_args(argv)
    cs = load(a.raw)
    os.makedirs(a.out, exist_ok=True)
    kn, acc = {}, {}
    for task in sorted({c["task"] for c in cs}):
        tc = [c for c in cs if c["task"] == task]
        keys, _ = arms(tc)
        kn |= {(task, k): v for k, v in knee(tc, keys).items()}
        acc |= {(task, k): v for k, v in acceptance(tc, keys).items()}
    pr = paired(cs, a.baseline)
    open(f"{a.out}/results.md", "w").write(results_md(cs, kn, acc, a.baseline) + "\n")
    open(f"{a.out}/paired.md", "w").write(paired_md(pr, a.baseline))
    json.dump({"cells": [{k: v for k, v in c.items() if k != "cmd"} for c in cs],
               "paired": pr,
               "knee": [{"task": t, "strategy": k[0], "tau_h": k[1], "block": k[2], **v}
                        for (t, k), v in sorted(kn.items())],
               "acceptance": [{"task": t, "strategy": k[0], "tau_h": k[1], "block": k[2],
                               **v} for (t, k), v in sorted(acc.items())]},
              open(f"{a.out}/results.json", "w"), indent=1)
    print(f"{len(cs)} cells -> {a.out}/results.md, results.json, paired.md "
          f"({len(pr)} paired comparisons)")
    return cs


if __name__ == "__main__":
    main()
