"""Reanalyse archived vectors; run from the repository root with uv run python <this file>."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments import aggregate as a

OUT = Path(__file__).resolve().parent
B = 10000


def exact_bound(k, n, alpha, lower):
    """One-sided Clopper-Pearson bound by inversion of a binomial tail."""
    if lower and k == 0:
        return 0.
    if not lower and k == n:
        return 1.
    lo, hi = 0., 1.
    for _ in range(60):
        p = (lo + hi) / 2
        cdf = sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j)
                  for j in range(k if lower else k + 1))
        if cdf > (1 - alpha if lower else alpha):
            lo = p
        else:
            hi = p
    return (lo + hi) / 2


def vectors(c, seeds):
    by = {e['seed']: e for e in c['episodes']}
    return (np.array([by[s]['success'] for s in seeds], bool),
            np.array([c['durations'][c['seeds_used'].index(s)] for s in seeds]))


def select(cs, minimum_seed):
    cs = copy.deepcopy(cs)
    for c in cs:
        c['episodes'] = [e for e in c['episodes'] if e['seed'] >= minimum_seed]
        a._vectors(c)
    a.drop_stalled(cs)
    return cs


def joint_rows(cs):
    """Same seed resample across zero/profile and both arms; not independent ratios."""
    out = []
    for arm in ('twin', 'gain'):
        for profile in ('sweep:400', 'geo_relay'):
            wanted = [(s, p) for p in ('zero', profile) for s in ('baseline', arm)]
            cells = [next((c for c in cs if c['task'] == 'capture' and
                           (c['strategy'], c['profile']) == key), None) for key in wanted]
            if any(c is None for c in cells):
                continue
            seeds = sorted(set.intersection(*(set(c['seeds_used']) for c in cells)))
            if not seeds:
                continue
            vs = [vectors(c, seeds) for c in cells]
            idx = np.random.default_rng(19).integers(0, len(seeds), (B, len(seeds)))
            def calc(i):
                bz, az, bp, ap = vs
                did = (ap[0][i].mean(axis=-1) - bp[0][i].mean(axis=-1)
                       - az[0][i].mean(axis=-1) + bz[0][i].mean(axis=-1))
                rr = (a._dph(*ap, i) / a._dph(*bp, i)) / (a._dph(*az, i) / a._dph(*bz, i))
                return did, rr
            did, rr = calc(idx)
            point = calc(np.arange(len(seeds)))
            finite = rr[np.isfinite(rr)]
            out.append(dict(arm=arm, profile=profile, n=len(seeds), success_did=float(point[0]),
                            success_did_ci=np.percentile(did, [2.5, 97.5]).tolist(),
                            conditional_dph_ratio_of_ratios=float(point[1]),
                            conditional_rr_ci=(np.percentile(finite, [2.5, 97.5]).tolist()
                                               if len(finite) else [None, None]),
                            conditional_rr_dropped=B-len(finite)))
    return out


def acceptance_rows(cs):
    out = []
    for task in sorted({c['task'] for c in cs}):
        tc = [c for c in cs if c['task'] == task]
        keys, _ = a.arms(tc)
        for key, result in a.acceptance(tc, keys).items():
            z, l = [next(c for c in tc if (c['strategy'], c['tau_h'], c['block']) == key
                         and c['profile'] == p) for p in ('zero', 'leo_relay')]
            seeds = sorted(set(z['seeds_used']) & set(l['seeds_used']))
            if not seeds:
                continue
            zv, lv = vectors(z, seeds), vectors(l, seeds)
            # Two 97.5% one-sided exact marginal bounds -> >=95% joint lower bound.
            sf_lo = exact_bound(l['k'], l['n'], .025, True) / exact_bound(z['k'], z['n'], .025, False)
            idx = np.random.default_rng(23).integers(0, len(seeds), (B, len(seeds)))
            gross = lambda v, i: 3600 * v[0][i].sum(axis=-1) / v[1][i].sum(axis=-1)
            margin = gross(lv, idx) - .8 * gross(zv, idx)
            df = a.boot_ratio(lv, zv, n_boot=B)
            out.append(dict(task=task, strategy=key[0], block=key[2], **result,
                            n_zero=z['n'], n_leo=l['n'], success_frac_lower95_exact=sf_lo,
                            conditional_dph_ratio_ci=list(df[1:3]),
                            gross_dph_frac=(l['demos_per_hour_gross']/z['demos_per_hour_gross']
                                            if z['demos_per_hour_gross'] else None),
                            gross_margin_ci=np.percentile(margin, [2.5, 97.5]).tolist()))
    return out


def knee_rows(cs):
    out = []
    for task, block in [('capture', 'A'), ('peg', 'B')]:
        tc = [c for c in cs if c['task'] == task and c['block'] == block]
        by_arm = {}
        # Same resampled seed indices for every profile and strategy in a task.
        seeds = sorted(set.intersection(*(set(c['seeds_used']) for c in tc)))
        idx = np.random.default_rng(29).integers(0, len(seeds), (B, len(seeds)))
        for arm in sorted({c['strategy'] for c in tc}):
            z = next(c for c in tc if c['strategy'] == arm and c['profile'] == 'zero')
            sw = sorted([c for c in tc if c['strategy'] == arm and c['profile'].startswith('sweep:')],
                        key=lambda c: c['rtt_ms'])
            thr = .8 * vectors(z, seeds)[0][idx].mean(axis=-1)
            rates = [vectors(c, seeds)[0][idx].mean(axis=-1) for c in sw]
            knees = np.full(B, np.inf)
            knees[rates[0] < thr] = sw[0]['rtt_ms']
            for j in range(1, len(sw)):
                hit = np.isinf(knees) & (rates[j] < thr) & (rates[j-1] >= thr)
                knees[hit] = (sw[j-1]['rtt_ms'] + (rates[j-1][hit]-thr[hit]) /
                              (rates[j-1][hit]-rates[j][hit]) * (sw[j]['rtt_ms']-sw[j-1]['rtt_ms']))
            knees[thr == 0] = np.nan
            by_arm[arm] = knees
            valid = knees[~np.isnan(knees)]
            quant = np.quantile(valid, [.025, .975], method='inverted_cdf')
            point = a.knee(tc, [(arm, .17, block)])[(arm, .17, block)]
            out.append(dict(task=task, arm=arm, paired_n=len(seeds), **point,
                            bootstrap_knee_interval_ms=quant.tolist(),
                            not_crossed_fraction=float(np.isinf(knees).mean()),
                            undefined_fraction=float(np.isnan(knees).mean())))
        for row in [r for r in out if r['task'] == task and r['arm'] != 'baseline']:
            ka, kb = by_arm[row['arm']], by_arm['baseline']
            valid = np.isfinite(ka) & np.isfinite(kb)
            row['shift_both_crossed_fraction'] = float(valid.mean())
            row['shift_ci_conditional_ms'] = (np.percentile(ka[valid]-kb[valid], [2.5, 97.5]).tolist()
                                                if valid.any() else None)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-results', type=Path, help='Corrected-run aggregate results.json')
    args = parser.parse_args()
    assert abs(exact_bound(0, 30, .05, False) - (1 - .05 ** (1/30))) < 1e-12
    assert abs(exact_bound(30, 30, .05, True) - .05 ** (1/30)) < 1e-12
    inputs = [ROOT / f'docs/experiments/{tier}/results.json' for tier in ('tier1', 'tier2')]
    t1, t2 = [json.loads(p.read_text())['cells'] for p in inputs]
    full, fresh = select(t2, 0), select(t2, 30)
    recovered = copy.deepcopy(t2)
    evidence = OUT / 'no_link_records.json'
    restored = json.loads(evidence.read_text())
    inputs.append(evidence)
    for record in restored:
        c = next(c for c in recovered if c['name'] == record['cell'])
        if record['seed'] not in c['seeds_used']:
            c['episodes'].append(dict(ep=record['seed'], seed=record['seed'], success=False,
                                      duration_s=record['duration_s'], stalls=None))
            a._vectors(c)
    result = dict(inputs={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  bootstrap_resamples=dict(paired=a.N_BOOT, diagnostics=B), tier2_all=a.paired(full, 'baseline'),
                  tier2_fresh=a.paired(fresh, 'baseline'),
                  restored_no_link=restored,
                  tier2_recovered_all=a.paired(select(recovered, 0), 'baseline'),
                  tier2_recovered_fresh=a.paired(select(recovered, 30), 'baseline'),
                  zero_adjustment_all=joint_rows(full), zero_adjustment_fresh=joint_rows(fresh),
                  acceptance_tier1=acceptance_rows(t1), acceptance_tier2=acceptance_rows(t2),
                  knee_tier1=knee_rows(t1))
    if args.fresh_results:
        new = json.loads(args.fresh_results.read_text())['cells']
        result['corrected_run'] = dict(
            source=str(args.fresh_results), sha256=hashlib.sha256(args.fresh_results.read_bytes()).hexdigest(),
            comparisons=a.paired(select(new, 0), 'baseline'),
            acceptance=acceptance_rows(new), zero_adjustment=joint_rows(select(new, 0)))
    # Infinity is a censored knee, not JSON numeric data.
    def clean(v):
        if isinstance(v, float) and not math.isfinite(v):
            return 'beyond_sweep' if math.isinf(v) else None
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, list):
            return [clean(x) for x in v]
        return v
    (OUT / 'statistics.json').write_text(json.dumps(clean(result), indent=2, allow_nan=False) + '\n')
    print(f'{len(full)} Tier-2 cells; {sum(c["n"] for c in fresh)} held-out historical episodes -> {OUT / "statistics.json"}')


if __name__ == '__main__':
    main()
