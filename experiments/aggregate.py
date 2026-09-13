"""Aggregate the matrix: docs/experiments/raw/*/summary.json -> results.md/.json, paired.md.

    uv run python experiments/aggregate.py [--raw RAW] [--out OUT]
        [--exclude-stalled] [--legacy-deadreckon-lead]

results.md   per task: rows = arm, columns = profile in RTT order, one table per metric
             family (success + Wilson CI, demos/hour, RTT, link_unsafe, cage, smoothness,
             plus a table for every extra per-hypothesis counter that appears in the
             run's event dict -- knock-aways, assist fraction, tether-taut, whatever).
             Then the contaminated cells, block S (dropout), the knee per arm and the
             SYNTHESIS section 6 acceptance readout.
results.json the same numbers plus the per-seed success and duration vectors, so any
             paired test can be recomputed without re-running the matrix.
paired.md    every (task, profile) where the baseline arm and another arm both ran:
             paired success difference, discordant counts, McNemar exact p (stdlib), and
             the demos/hour ratio with a paired bootstrap 95 % CI; plus the zero-cell
             control (audit_strategies F3).
curves.json  per (task, arm), the success-and-throughput-vs-RTT curve over zero + sweep,
             ready for the report page to plot.

Audit fixes carried here (docs/experiments/audit_testbed.md, audit_strategies.md):
T05 smoothness is recomputed from the satellite applied-setpoint sidecar when the summary
    does not already carry sidecar-derived numbers; T13 SAL uses padlevel 4.
T06 stalled episodes are counted per cell and flagged; --exclude-stalled drops them
    (paired: the seed goes from every arm of that task/profile/tau group).
T07 link_unsafe (move_in_hold + vel_over + keepout) and cage are separate columns; the
    section 6 gate is on link_unsafe, cage is reported as operator/task-caused.
T09/F2 the 1.0 s satellite linger is subtracted from every duration unless the summary
    says it was already excluded.
T10 direct_gs throughput is also reported per 9.2-minute pass.
T20 every bootstrap CI reports how many resamples were dropped (all-failure resamples).
F1  --legacy-deadreckon-lead relabels the deadreckon arm with its true 90 ms lead.
F3  the paired section carries the zero-cell control for every non-baseline arm.

The parser is tolerant of both the old and the new summary schema: `stalls`, `max_dt_s`,
`cage` as its own counter, `duration_active_s` / `linger_excluded` and `code_version` are
all optional, and a missing field reads as None instead of raising.
"""
import argparse
import glob
import json
import math
import os
import sys
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from spaceteleop.metrics import STALL, ldlj                            # noqa: E402

LINK_SAFE = ("move_in_hold", "vel_over", "keepout")     # link-caused, the section 6 gate
SAFE = LINK_SAFE + ("cage",)                            # cage is operator/task-caused (T07)
DIAG = SAFE + ("hold", "ramp_clip", "pos_clamp", "retract", "jams", "stale")
NAMED = ("zero", "direct_gs", "leo_relay", "geo_relay")     # section 6 acceptance set
PRIMARY_TAU = 0.17
Z = 1.959963984540054                                       # 95 %
STALL_DT_S = 0.2            # T06: a satellite cycle longer than this is a CPU stall
CONTAM_EPS = 3              # T06: cells with this many stalled episodes are flagged
LINGER_S = 1.0              # T09/F2: satellite linger inside duration_s
PASS_MIN = 9.2              # T10: direct_gs pass length, minutes
N_BOOT = 2000
DR_LABEL = "deadreckon (L=60 ms; lead 90 ms in Tier 1 code)"


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


def boot_ratio(a, b, n_boot=N_BOOT, seed=0):
    """Paired bootstrap 95 % CI of demos/hour(a) / demos/hour(b). a, b = (succ, dur).

    Returns (point, lo, hi, dropped): `dropped` is the T20 count of resamples thrown away
    because one arm had no success in them (the CI is narrowed by exactly those)."""
    n = len(a[0])
    if n == 0:
        return (float("nan"),) * 3 + (n_boot,)
    idx = np.random.default_rng(seed).integers(0, n, (n_boot, n))
    r = _dph(a[0], a[1], idx) / _dph(b[0], b[1], idx)
    r = r[np.isfinite(r)]
    point = _dph(a[0], a[1], np.arange(n)) / _dph(b[0], b[1], np.arange(n))
    if not len(r):
        return (float(point), float("nan"), float("nan"), n_boot)
    return (float(point), float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5)),
            n_boot - len(r))


def boot_diff(a, b, n_boot=N_BOOT, seed=1):
    """Paired bootstrap 95 % CI of mean(a) - mean(b) for two success vectors."""
    n = len(a)
    if n == 0:
        return (float("nan"),) * 3
    idx = np.random.default_rng(seed).integers(0, n, (n_boot, n))
    d = a[idx].mean(axis=-1) - b[idx].mean(axis=-1)
    return (float(a.mean() - b.mean()), float(np.percentile(d, 2.5)),
            float(np.percentile(d, 97.5)))


def _sal4(v, dt, fc=10.0, amp_th=0.05):
    """Spectral arc length, padlevel 4 (T13: metrics.sal pads 2, SPARC reference is 4)."""
    v = np.asarray(v, float)
    if len(v) < 8 or not np.any(v):
        return float("nan")
    n = int(2 ** (np.ceil(np.log2(len(v))) + 4))
    mag = np.abs(np.fft.rfft(v, n))
    mag /= mag.max()
    f = np.fft.rfftfreq(n, dt)
    k = f <= fc
    mag, f = mag[k], f[k]
    inx = np.where(mag >= amp_th)[0]
    if len(inx) < 2:
        return float("nan")
    mag, f = mag[inx[0]:inx[-1] + 1], f[inx[0]:inx[-1] + 1]
    df = np.diff(f) / (f[-1] - f[0] or 1.0)
    return float(-np.sum(np.sqrt(df ** 2 + np.diff(mag) ** 2)))


def sat_stats(path):
    """T05: SAL / LDLJ / stall_frac plus the T06 stall counters from one `*_sat.npz`.

    The applied-setpoint stream is the satellite's own ~780 Hz log, so it has none of the
    30-to-50 Hz sample-and-hold artefact that `observation.state` carries."""
    try:
        with np.load(path) as z:
            t = z["t_ns"].astype(np.float64) / 1e9
            sp = np.asarray(z["setpoint"], float)[:, :6]
    except (OSError, ValueError, KeyError):
        return None
    if len(t) < 9:
        return None
    dt = np.diff(t)
    period = float(np.median(dt))
    v = np.linalg.norm(np.diff(sp, axis=0), axis=1) / np.maximum(dt, 1e-9)
    return dict(stalls=int((dt > STALL_DT_S).sum()), max_dt_s=float(dt.max()),
                sal=_sal4(v, period), ldlj=ldlj(v, period),
                stall_frac=float(np.mean(v < STALL)))


def _mean(xs):
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return float(np.mean(xs)) if xs else None


def _has_sat_smoothness(s):
    """True if the summary already carries sidecar-derived smoothness (new schema)."""
    agg = s.get("aggregate") or {}
    return "sal_sat" in agg or agg.get("smoothness_source") in ("sat", "setpoint")


def _enrich(s):
    """Fill per-episode stalls / max_dt_s / smoothness from the sidecars where needed."""
    eps = s["episodes"]
    need_sm = not _has_sat_smoothness(s)
    sm = []
    for e in eps:
        p = f"{s['dir']}/data/episode_{int(e.get('ep', e['seed'])):06d}_sat.npz"
        st = None
        if os.path.exists(p) and (need_sm or e.get("stalls") is None):
            st = sat_stats(p)
        if e.get("stalls") is None:
            e["stalls"] = st["stalls"] if st else None
        if e.get("max_dt_s") is None:
            e["max_dt_s"] = st["max_dt_s"] if st else None
        if st and need_sm:
            sm.append(st)
    agg = s.get("aggregate") or {}
    if sm:
        s["sal"], s["ldlj"] = _mean([x["sal"] for x in sm]), _mean([x["ldlj"] for x in sm])
        s["stall_frac"] = _mean([x["stall_frac"] for x in sm])
        s["smooth_src"] = "sat"
    else:
        s["sal"] = agg.get("sal_sat", agg.get("sal"))
        s["ldlj"] = agg.get("ldlj_sat", agg.get("ldlj"))
        s["stall_frac"] = agg.get("stall_frac_sat", agg.get("stall_frac"))
        s["smooth_src"] = "sat" if _has_sat_smoothness(s) else "obs"


def _durations(s):
    """T09/F2: active duration per episode, and whether we had to subtract the linger."""
    agg = s.get("aggregate") or {}
    excluded = bool(s.get("linger_excluded") or agg.get("linger_excluded"))
    out, adj = [], False
    for e in s["episodes"]:
        if e.get("duration_active_s") is not None:
            out.append(float(e["duration_active_s"]))
        elif excluded:
            out.append(float(e["duration_s"]))
        else:
            out.append(max(0.1, float(e["duration_s"]) - LINGER_S))
            adj = True
    return out, adj


def _vectors(s):
    """(Re)build the per-seed vectors and the cell-level rates from s['episodes']."""
    eps = sorted(s["episodes"], key=lambda e: e["seed"])
    s["episodes"] = eps
    s["seeds_used"] = [e["seed"] for e in eps]
    s["success"] = [int(e["success"]) for e in eps]
    s["durations"], adj = _durations(s)
    s["linger_adjusted"] = adj
    s["stalled"] = [bool(e.get("stalls") or 0) for e in eps]
    s["n"], s["k"] = len(eps), sum(s["success"])
    s["wilson"] = wilson(s["k"], s["n"])
    ok = [d for d, y in zip(s["durations"], s["success"]) if y]
    tot = sum(s["durations"])
    s["demos_per_hour"] = 3600.0 / float(np.mean(ok)) if ok else 0.0
    s["demos_per_hour_gross"] = 3600.0 * s["k"] / tot if tot else 0.0
    s["demos_per_pass"] = s["demos_per_hour"] * PASS_MIN / 60.0
    ev = s.get("aggregate", {}).get("events", {}) or {}
    s["link_unsafe"] = sum(int(ev.get(k, 0)) for k in LINK_SAFE)
    s["cage"] = int(ev.get("cage", 0))


def load(raw, exclude_stalled=False):
    """Every clean summary.json under `raw`, enriched with the per-seed vectors."""
    out = []
    for p in sorted(glob.glob(f"{raw}/*/summary.json")):
        with open(p) as f:
            s = json.load(f)
        if s.get("error") or not s.get("episodes"):
            continue
        s["dir"] = os.path.dirname(p)
        _enrich(s)
        _vectors(s)
        s["n_stalled"] = sum(s["stalled"])
        s["contaminated"] = s["n_stalled"] >= CONTAM_EPS
        s["max_dt_s"] = max([e["max_dt_s"] for e in s["episodes"]
                             if e.get("max_dt_s") is not None], default=None)
        out.append(s)
    if exclude_stalled:
        drop_stalled(out)
    return out


def drop_stalled(cs):
    """T06: drop stalled episodes; the seed goes from every arm of the same cell group."""
    bad = {}
    for c in cs:
        g = (c["task"], c["profile"], c["tau_h"])
        bad.setdefault(g, set()).update(
            s for s, st in zip(c["seeds_used"], c["stalled"]) if st)
    for c in cs:
        drop = bad[(c["task"], c["profile"], c["tau_h"])]
        keep = [e for e in c["episodes"] if e["seed"] not in drop]
        c["dropped_seeds"] = sorted(drop & set(c["seeds_used"]))
        if keep and len(keep) != len(c["episodes"]):
            c["episodes"] = keep
            _vectors(c)
    return cs


def arms(cs, legacy_dr=False):
    """Distinct (strategy, tau, block) row keys and their display labels."""
    keys = sorted({(c["strategy"], c["tau_h"], c["block"]) for c in cs})
    dup = {(s, t) for s, t, _ in keys if sum(1 for a in keys if a[:2] == (s, t)) > 1}
    lab = {}
    for s, t, b in keys:
        lab[(s, t, b)] = (DR_LABEL if legacy_dr and s == "deadreckon" else s) + \
            ("" if t == PRIMARY_TAU else f" tau{t}") + (f" [{b}]" if (s, t) in dup else "")
    return keys, lab


def _table(cs, profiles, keys, lab, fmt):
    """rows = arm, cols = profile (already in RTT order), cell = fmt(summary) or '-'.

    A cell with >= CONTAM_EPS stalled episodes (T06) is marked in every table."""
    by = {(c["strategy"], c["tau_h"], c["block"], c["profile"]): c for c in cs}
    head = "| arm | " + " | ".join(profiles) + " |"
    rule = "|---" * (len(profiles) + 1) + "|"
    rows = []
    for k in keys:
        cells = []
        for p in profiles:
            c = by.get(k + (p,))
            cells.append("-" if c is None else fmt(c) + (" ⚠" if c["contaminated"] else ""))
        rows.append(f"| {lab[k]} | " + " | ".join(cells) + " |")
    return "\n".join([head, rule] + rows)


def _g(c, key, d=float("nan")):
    return c["aggregate"].get(key, d)


def _arm(k):
    return k[0] + ("" if k[1] == PRIMARY_TAU else f" tau{k[1]}")


def _f(v, p=2):
    if v is None:
        return "-"
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
    """SYNTHESIS section 6: leo_relay as a fraction of the same arm's zero cell.

    The gate is on link_unsafe over the four named profiles (T07); `cage` is counted and
    reported next to it but does not gate, because it is operator/task-caused."""
    out = {}
    for k in keys:
        rows = {c["profile"]: c for c in cs
                if (c["strategy"], c["tau_h"], c["block"]) == k}
        z, l = rows.get("zero"), rows.get("leo_relay")
        if not z or not l:
            continue
        sz, sl = z["k"] / max(1, z["n"]), l["k"] / max(1, l["n"])
        dz, dl = z["demos_per_hour"], l["demos_per_hour"]
        sf = sl / sz if sz else float("nan")
        df = dl / dz if dz else float("nan")
        lu = sum(rows[p]["link_unsafe"] for p in NAMED if p in rows)
        out[k] = dict(success_frac=sf, dph_frac=df, success_zero=sz, success_leo=sl,
                      dph_zero=dz, dph_leo=dl, link_unsafe_named=lu,
                      cage_named=sum(rows[p]["cage"] for p in NAMED if p in rows),
                      passes=bool(sf >= 0.8 and df >= 0.8 and lu == 0),
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
        pt, lo, hi, dropped = boot_ratio((as_, ad), (bs, bd))
        diff, dlo, dhi = boot_diff(as_, bs)
        out.append(dict(task=c["task"], profile=c["profile"], rtt_ms=c["rtt_ms"],
                        tau_h=c["tau_h"], arm=c["strategy"], baseline=baseline,
                        n=len(seeds), base_success=float(bs.mean()) if len(seeds) else 0.0,
                        arm_success=float(as_.mean()) if len(seeds) else 0.0,
                        diff=diff if len(seeds) else 0.0, diff_ci=[dlo, dhi],
                        b_only=nb, c_only=nc, mcnemar_p=mcnemar_p(nb, nc),
                        dph_ratio=pt, dph_ci=[lo, hi], dropped_resamples=dropped))
    return sorted(out, key=lambda r: (r["task"], r["rtt_ms"], r["arm"]))


def curves(cs, legacy_dr=False):
    """T10/report: (task, arm) -> the success and demos/hour curve over zero + sweep.

    `zero` and `sweep:0` share the nominal x = 0 (they differ in jitter structure, T08),
    so every point carries its profile name as well."""
    out = []
    for task in sorted({c["task"] for c in cs}):
        tc = [c for c in cs if c["task"] == task]
        keys, lab = arms(tc, legacy_dr)
        for k in keys:
            rows = [c for c in tc if (c["strategy"], c["tau_h"], c["block"]) == k
                    and (c["profile"] == "zero" or c["profile"].startswith("sweep:"))]
            if not rows:
                continue
            pts = [dict(rtt_nominal_ms=float(c["rtt_ms"]), profile=c["profile"],
                        success=c["k"] / max(1, c["n"]),
                        ci_lo=c["wilson"][0], ci_hi=c["wilson"][1],
                        demos_per_hour=c["demos_per_hour"], n=c["n"])
                   for c in sorted(rows, key=lambda c: (c["rtt_ms"],
                                                        c["profile"] != "zero"))]
            out.append(dict(task=task, arm=lab[k], strategy=k[0], tau_h=k[1], block=k[2],
                            points=pts))
    return out


def _block_s(cs, legacy_dr=False):
    """Block S readout: the dropout profiles, hold / retract / link_unsafe / success."""
    rows = [c for c in cs if c["profile"].startswith("leo_relay_drop")]
    if not rows:
        return []
    doc = ["## Block S: forced dropout (leo_relay_drop1 / leo_relay_drop12)", "",
           "Hold and retract are the counts the run reports; `link_unsafe` is the section 6 "
           "link-caused sum, which is what the dropout block exists to exercise (T02).", "",
           "| task | arm | profile | hold | retract | link_unsafe | cage | success |",
           "|---|---|---|---|---|---|---|---|"]
    for c in sorted(rows, key=lambda c: (c["task"], c["strategy"], c["profile"])):
        ev = _g(c, "events", {})
        name = DR_LABEL if legacy_dr and c["strategy"] == "deadreckon" else c["strategy"]
        doc.append(f"| {c['task']} | {name} | {c['profile']} | "
                   f"{int(ev.get('hold', 0))} | {int(ev.get('retract', 0))} | "
                   f"{c['link_unsafe']} | {c['cage']} | "
                   f"{c['k'] / max(1, c['n']):.2f} {c['k']}/{c['n']} |")
    return doc + [""]


def results_md(cs, kn, acc, baseline, legacy_dr=False, excluded=False):
    doc = ["# Experiment results", "",
           f"{len(cs)} cells, {sum(c['n'] for c in cs)} episodes. "
           f"Baseline arm: `{baseline}`. Paired tests: `paired.md`. Curves: `curves.json`.",
           ""]
    if excluded:
        doc += ["Stalled episodes are **excluded** (`--exclude-stalled`): a stalled seed is "
                "dropped from every arm of the same task/profile/tau, so the pairing holds.",
                ""]
    for task in sorted({c["task"] for c in cs}):
        tc = [c for c in cs if c["task"] == task]
        profiles = [p for _, p in sorted({(c["rtt_ms"], c["profile"]) for c in tc})]
        keys, lab = arms(tc, legacy_dr)
        doc += [f"## Task `{task}`", ""]
        for title, fmt in [
            ("Success rate (95 % Wilson CI)",
             lambda c: f"{c['k'] / c['n']:.2f} [{c['wilson'][0]:.2f},{c['wilson'][1]:.2f}] "
                       f"{c['k']}/{c['n']}"),
            ("demos/hour (gross in brackets; direct_gs also per 9.2-min pass)",
             lambda c: f"{_f(c['demos_per_hour'], 1)} [{_f(c['demos_per_hour_gross'], 1)}]" +
                       (f" = {_f(c['demos_per_pass'], 1)}/pass"
                        if c["profile"] == "direct_gs" else "")),
            ("RTT p50 / p95, ms",
             lambda c: f"{_f(_g(c, 'rtt_p50_ms'), 0)} / {_f(_g(c, 'rtt_p95_ms'), 0)}"),
            ("link_unsafe = move_in_hold + vel_over + keepout (the section 6 gate)",
             lambda c: f"{c['link_unsafe']}"),
            ("cage contacts (operator/task-caused, reported not gated)",
             lambda c: f"{c['cage']}"),
            ("SAL / LDLJ / stall_frac (source: sat = applied-setpoint sidecar, obs = "
             "observation.state)",
             lambda c: f"{_f(c['sal'])} / {_f(c['ldlj'])} / {_f(c['stall_frac'])} "
                       f"[{c['smooth_src']}]"),
            ("Stalled episodes (satellite cycle > 0.2 s)",
             lambda c: (f"{c['n_stalled']}/{c['n']}"
                        if any(e.get("stalls") is not None for e in c["episodes"])
                        else "?")),
        ]:
            doc += [f"**{title}**", "", _table(tc, profiles, keys, lab, fmt), ""]
        for k in extras(tc):
            doc += [f"**{k}**", "",
                    _table(tc, profiles, keys, lab,
                           lambda c, k=k: _f(_g(c, "events", {}).get(k, 0))), ""]
    bad = [c for c in cs if c["contaminated"]]
    doc += ["## Contaminated cells (T06: >= 3 episodes with a satellite cycle > 0.2 s)", ""]
    if bad:
        doc += ["Those episodes are neither the profile nor the strategy: the buffered "
                "commands drain in one burst and the sim steps 1-2 s against one setpoint. "
                "Marked ⚠ in every table above. Re-run them, or use "
                "`--exclude-stalled`.", "",
                "| cell | stalled / n | max cycle dt, s |", "|---|---|---|"]
        for c in sorted(bad, key=lambda c: -c["n_stalled"]):
            doc.append(f"| {c['name']} | {c['n_stalled']}/{c['n']} | "
                       f"{_f(c['max_dt_s'], 2)} |")
    else:
        doc.append("None.")
    doc += [""] + _block_s(cs, legacy_dr)
    doc += ["## Knee: first sweep RTT with success < 0.8 x that arm's own zero cell", "",
            "| task | arm | zero success | threshold | knee (ms) |", "|---|---|---|---|---|"]
    for (task, k), v in sorted(kn.items()):
        kms = "never (> 1000)" if v["knee_ms"] is None else f"{v['knee_ms']:.0f}"
        doc.append(f"| {task} | {_arm(k)} | {v['zero_success']:.2f} | "
                   f"{v['threshold']:.2f} | {kms} |")
    if not kn:
        doc.append("| (no arm has a `zero` cell and >= 2 sweep points yet) |")
    doc += ["", "## SYNTHESIS section 6 acceptance readout (leo_relay / own zero cell)", "",
            "| task | arm | success frac | demos/h frac | link_unsafe on "
            + ", ".join(NAMED) + " | cage (not gated) | gate |",
            "|---|---|---|---|---|---|---|"]
    for (task, k), v in sorted(acc.items()):
        doc.append(f"| {task} | {_arm(k)} | "
                   f"{v['success_frac']:.2f} | {v['dph_frac']:.2f} | "
                   f"{v['link_unsafe_named']} ({'+'.join(v['profiles_present'])}) | "
                   f"{v['cage_named']} | {'PASS' if v['passes'] else 'FAIL'} |")
    if not acc:
        doc.append("| (no arm has both a `zero` and a `leo_relay` cell yet) |")
    doc += ["", "Acceptance (PROGRAM.md, SYNTHESIS section 6): both fractions >= 0.80 and "
            "zero **link-caused** unsafe events. `cage` is the arm touching the cage while "
            "the operator chases a drifting box; it fires at zero latency on every arm "
            "(audit T07), so it is reported as operator/task-caused and does not gate.", "",
            "### Footnotes", ""]
    if any(c["linger_adjusted"] for c in cs):
        doc.append(f"- Durations: the run's `duration_s` includes the {LINGER_S:.1f} s "
                   "satellite linger (audit T09 / F2). No summary carried "
                   "`duration_active_s` or `linger_excluded`, so **1.0 s was subtracted "
                   "from every episode** before demos/hour; the correction is exact per "
                   "episode (the linger is a constant), not a fit.")
    else:
        doc.append("- Durations: taken from `duration_active_s` / `linger_excluded` as "
                   "reported; no linger correction applied here.")
    doc += ["- Smoothness: `[sat]` cells are recomputed here from the satellite "
            "applied-setpoint sidecar at ~780 Hz (audit T05: `observation.state` is 30 Hz "
            "held at 50 Hz, which puts a floor of ~0.4 under `stall_frac`); SAL uses "
            "padlevel 4 (T13). `[obs]` cells are the run's own numbers.",
            f"- `direct_gs` per-pass throughput = demos/hour x {PASS_MIN}/60 "
            "(SYNTHESIS section 6: window-limited, report per pass).",
            "- ⚠ marks a cell with >= 3 stalled episodes (T06)."]
    if legacy_dr:
        doc.append("- `deadreckon` ran with `L = 60 ms` but the Tier 1 code evaluates the "
                   "fit at `now + interp_s + L`, so its effective lead over the baseline is "
                   "**90 ms** (audit_strategies F1). Score H12 against `L_eff = 90 ms`.")
    return "\n".join(doc)


def paired_md(rows, baseline, legacy_dr=False):
    doc = ["# Paired comparisons", "",
           f"Same seeds per cell, so success is a McNemar test on the discordant seeds "
           f"(`b` = `{baseline}` only, `c` = arm only; two-sided exact binomial). "
           f"demos/hour ratio is arm / {baseline} with a paired bootstrap 95 % CI "
           f"({N_BOOT} resamples of the seed list); `drop` is how many resamples were "
           f"thrown away because one arm had no success in them (audit T20 - the CI is "
           f"narrowed by exactly those).", ""]
    if legacy_dr:
        doc += ["`deadreckon` leads the baseline by 90 ms, not the nominal 60 ms "
                "(audit_strategies F1).", ""]
    doc += ["| task | profile | tau | arm | n | base | arm | diff | b | c | McNemar p | "
            "demos/h ratio [95 % CI] | drop |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ci = f"[{r['dph_ci'][0]:.2f}, {r['dph_ci'][1]:.2f}]"
        doc.append(f"| {r['task']} | {r['profile']} | {r['tau_h']} | {r['arm']} | {r['n']} | "
                   f"{r['base_success']:.2f} | {r['arm_success']:.2f} | {r['diff']:+.2f} | "
                   f"{r['b_only']} | {r['c_only']} | {r['mcnemar_p']:.4f} | "
                   f"{r['dph_ratio']:.2f} {ci} | {r['dropped_resamples']} |")
    if not rows:
        doc.append("| (no non-baseline arm has a paired baseline cell yet) |")
    zero = [r for r in rows if r["profile"] == "zero"]
    doc += ["", "## Zero-cell control (audit_strategies F3)", "",
            "A latency hider must not gain on the zero-latency cell: a gain there is "
            "against the operator model, not against the link (selection.md section 4, H10 "
            "and H14 amendments). Flagged when a CI excludes zero in the positive "
            "direction; read such an arm's profile gains as the ratio of ratios "
            "(arm/baseline at the profile) / (arm/baseline at zero).", "",
            "| task | arm | n | success diff [95 % CI] | demos/h ratio [95 % CI] | drop | "
            "flag |", "|---|---|---|---|---|---|---|"]
    for r in zero:
        gain = r["diff_ci"][0] > 0 or r["dph_ci"][0] > 1.0
        flag = "⚠ gain at zero latency" if gain else "ok"
        doc.append(f"| {r['task']} | {r['arm']} | {r['n']} | "
                   f"{r['diff']:+.2f} [{r['diff_ci'][0]:+.2f}, {r['diff_ci'][1]:+.2f}] | "
                   f"{r['dph_ratio']:.3f} [{r['dph_ci'][0]:.3f}, {r['dph_ci'][1]:.3f}] | "
                   f"{r['dropped_resamples']} | {flag} |")
    if not zero:
        doc.append("| (no arm has a paired `zero` cell yet) |")
    return "\n".join(doc) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(prog="aggregate")
    p.add_argument("--raw", default="docs/experiments/raw")
    p.add_argument("--out", default="docs/experiments")
    p.add_argument("--baseline", default="baseline")
    p.add_argument("--exclude-stalled", action="store_true",
                   help="drop stalled episodes (T06); the seed goes from every paired arm")
    p.add_argument("--legacy-deadreckon-lead", action="store_true",
                   help="cells predate the F1 fix: label deadreckon with its 90 ms lead")
    a = p.parse_args(argv)
    dr = a.legacy_deadreckon_lead
    cs = load(a.raw, a.exclude_stalled)
    os.makedirs(a.out, exist_ok=True)
    kn, acc = {}, {}
    for task in sorted({c["task"] for c in cs}):
        tc = [c for c in cs if c["task"] == task]
        keys, _ = arms(tc, dr)
        kn |= {(task, k): v for k, v in knee(tc, keys).items()}
        acc |= {(task, k): v for k, v in acceptance(tc, keys).items()}
    pr = paired(cs, a.baseline)
    cv = curves(cs, dr)
    open(f"{a.out}/results.md", "w").write(
        results_md(cs, kn, acc, a.baseline, dr, a.exclude_stalled) + "\n")
    open(f"{a.out}/paired.md", "w").write(paired_md(pr, a.baseline, dr))
    json.dump({"curves": cv}, open(f"{a.out}/curves.json", "w"), indent=1)
    json.dump({"cells": [{k: v for k, v in c.items() if k not in ("cmd", "dir")}
                         for c in cs],
               "paired": pr,
               "knee": [{"task": t, "strategy": k[0], "tau_h": k[1], "block": k[2], **v}
                        for (t, k), v in sorted(kn.items())],
               "acceptance": [{"task": t, "strategy": k[0], "tau_h": k[1], "block": k[2],
                               **v} for (t, k), v in sorted(acc.items())]},
              open(f"{a.out}/results.json", "w"), indent=1)
    print(f"{len(cs)} cells -> {a.out}/results.md, results.json, paired.md, curves.json "
          f"({len(pr)} paired comparisons, "
          f"{sum(c['contaminated'] for c in cs)} contaminated cells)")
    return cs


if __name__ == "__main__":
    main()
