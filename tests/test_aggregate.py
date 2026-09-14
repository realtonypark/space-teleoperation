"""Regression checks for the second-wave statistical audit."""
import numpy as np
import pytest

from experiments import aggregate as a


def cell(strategy="baseline", profile="zero", block="A", success=(1, 1), stalls=(0, 0)):
    c = dict(task="capture", strategy=strategy, profile=profile, block=block,
             tau_h=0.17, rtt_ms=0, linger_excluded=True,
             aggregate={"events": dict.fromkeys(a.LINK_SAFE, 0)},
             episodes=[dict(seed=i, success=bool(s), duration_s=10., stalls=st)
                       for i, (s, st) in enumerate(zip(success, stalls))])
    a._vectors(c)
    return c


def test_complete_acceptance_and_known_safety_required():
    cs = [cell(profile=p) for p in a.NAMED]
    key = ("baseline", .17, "A")
    assert a.acceptance(cs, [key])[key]["passes"]
    for c in cs:
        c['aggregate']['events']['cage'] = 0
    assert a.acceptance(cs, [key])[key]['strict_safety_status'] == 'ZERO_OBSERVED'
    cs[0]['cage'] = 1
    assert a.acceptance(cs, [key])[key]['strict_safety_status'] == 'FAIL'
    assert a.acceptance(cs[:3], [key])[key]["status"] == "INCOMPLETE"
    cs[-1]["aggregate"]["events"] = {}
    assert not a.acceptance(cs, [key])[key]["passes"]


def test_stall_filter_can_remove_every_seed_without_crossing_blocks():
    cs = [cell(stalls=(1, 1)), cell("twin"), cell(block="T2")]
    a.drop_stalled(cs)
    assert [c["n"] for c in cs] == [0, 0, 2]
    assert cs[1]["dropped_seeds"] == [0, 1]
    assert a.paired(cs, "baseline") == []


def test_legacy_top_level_cage_count_cannot_pass_strict_safety():
    cs = [cell(profile=p) for p in a.NAMED]
    for c in cs:
        c["aggregate"]["cage"] = 1
        a._vectors(c)
    result = a.acceptance(cs, [("baseline", .17, "A")])[("baseline", .17, "A")]
    assert result["cage_named"] == 4 and result["strict_safety_status"] == "FAIL"


def test_pairing_uses_same_block():
    rows = a.paired([cell(success=(0, 0)), cell(block="T2"),
                     cell("twin", block="T2")], "baseline")
    assert len(rows) == 1 and rows[0]["diff"] == 0
    assert rows[0]["block"] == "T2"


def test_gross_throughput_retains_failures_and_zero_baselines():
    yes, no, dur = np.ones(8, bool), np.zeros(8, bool), np.full(8, 10.)
    assert a.boot_gross_diff((yes, dur), (no, dur)) == (360., 360., 360.)
    half = np.array([1, 1, 1, 1, 0, 0, 0, 0], bool)
    assert a.boot_ratio((half, dur), (yes, dur))[0] == 1
    assert a.boot_gross_diff((half, dur), (yes, dur))[0] == -180
    assert a.holm([.03, .001, .04]) == pytest.approx([.06, .003, .06])


def test_knee_reports_sampled_bracket_and_skips_zero_success_reference():
    cs = [cell(success=(0, 0)), cell(profile="sweep:100"),
          cell(profile="sweep:250", success=(0, 0))]
    cs[1]["rtt_ms"], cs[2]["rtt_ms"] = 100, 250
    key = ("baseline", .17, "A")
    assert a.knee(cs, [key]) == {}
    cs[0] = cell()
    knee = a.knee(cs, [key])[key]
    assert knee["knee_ms"] == pytest.approx(130)
    assert knee["bracket_ms"] == [100, 250]
    cs[-1] = cell(profile="sweep:250")
    cs[-1]["rtt_ms"] = 250
    assert a.knee(cs, [key])[key]["status"] == "not_observed"


def test_outputs_are_strict_json_with_nulls_and_real_zeros(tmp_path):
    import json
    from docs.experiments.second_wave import analyze

    raw, out = tmp_path / 'raw', tmp_path / 'out'
    for strategy in ('baseline', 'twin'):
        for profile in ('zero', 'leo_relay', 'sweep:400'):
            c = cell(strategy, profile, success=(0, 0))
            c['name'] = f'{strategy}_{profile}'
            c['aggregate'].update(sal=float('nan'), rtt_p50_ms=float('inf'))
            path = raw / c['name']
            path.mkdir(parents=True)
            (path / 'summary.json').write_text(json.dumps(c))
    a.main(['--raw', str(raw), '--out', str(out)])

    def reject_constant(value):
        raise AssertionError(f'Non-JSON constant: {value}')

    results = json.loads((out / 'results.json').read_text(), parse_constant=reject_constant)
    curves = json.loads((out / 'curves.json').read_text(), parse_constant=reject_constant)
    assert results['cells'][0]['aggregate']['sal'] is None
    assert results['cells'][0]['aggregate']['rtt_p50_ms'] is None
    assert results['paired'][0]['dph_ratio'] is None
    assert results['paired'][0]['dph_ci'] == [None, None]
    assert results['paired'][0]['gross_dph_diff'] == 0
    assert results['acceptance'][0]['success_frac'] is None
    assert curves['curves'][0]['points'][0]['success'] == 0
    assert '- [-, -]' in (out / 'paired.md').read_text()
    assert 'nan' not in (out / 'results.md').read_text()
    assert a._f(None) == a._f(float('inf')) == a._f(float('nan')) == '-'
    assert a.json_safe((0, float('-inf'))) == [0, None]

    # Fresh-result processing reconstructs vectors; JSON nulls remain valid input.
    cs = analyze.select(results['cells'], 0)
    assert analyze.joint_rows(cs)[0]['conditional_rr_ci'] == [None, None]
    assert analyze.acceptance_rows(cs)[0]['gross_dph_frac'] is None
    zero = next(c for c in cs if c['strategy'] == 'baseline' and c['profile'] == 'zero')
    for e in zero['episodes']:
        e['seed'] += 10
    a._vectors(zero)
    assert analyze.joint_rows(cs) == []
