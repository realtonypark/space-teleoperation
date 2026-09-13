"""experiments/matrix.py + aggregate.py: cell counts, resume, and the two statistics."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
import aggregate                                                        # noqa: E402
import matrix                                                           # noqa: E402

ARMS6 = ["b", "t", "d", "g", "p", "pg"]          # B T D G P Pg, selection.md section 3


@pytest.mark.parametrize("block,n", [("A", 66), ("B", 66), ("C", 12), ("E", 30), ("S", 24)])
def test_tier1_counts(block, n):
    """selection.md section 3 Tier 1 + the audit-T02 dropout block S (2 tasks x 6 arms x
    2 profiles): 66 + 66 + 12 + 30 + 24 = 198 cells at 6 arms."""
    cs = matrix.cells(1, [block], ARMS6, 30, ablations=["pg"], baseline="b")
    assert len(cs) == n
    assert len({c.name for c in cs}) == n


def test_dropout_block_forces_an_outage_in_every_episode():
    """T02: block S is the only place hold/retract is ever exercised."""
    cs = matrix.cells(1, ["S"], ARMS6, 30, ablations=["pg"], baseline="b")
    assert {c.profile for c in cs} == {"leo_relay_drop1", "leo_relay_drop12"}
    assert {c.task for c in cs} == {"capture", "peg"}
    assert {c.tau_h for c in cs} == {0.17}
    # the 12 s outage eats over half a 20 s episode, so that profile gets 30 s
    assert {c.max_s for c in cs if c.profile.endswith("drop12")} == {30.0}
    assert {c.max_s for c in cs if c.task == "capture" and c.profile.endswith("drop1")} \
        == {20.0}


def test_tier1_total_and_scaling():
    assert len(matrix.cells(1, None, ARMS6, 30, ablations=["pg"], baseline="b")) == 198
    # counts follow the strategy list, they are not baked in
    assert len(matrix.cells(1, ["A"], ["b"], 30)) == 11
    assert len(matrix.cells(1, ["A"], ARMS6[:3], 30)) == 33
    assert len(matrix.cells(1, ["E"], ARMS6, 30, ablations=[], baseline="b")) == 36


def test_max_s_rule():
    """20 s, 30 s for peg and for every cell at RTT >= 500 ms (geo_relay is 600)."""
    assert matrix.max_s("capture", "zero") == 20.0
    assert matrix.max_s("capture", "sweep:400") == 20.0
    assert matrix.max_s("capture", "sweep:500") == 30.0
    assert matrix.max_s("capture", "geo_relay") == 30.0
    assert matrix.max_s("peg", "zero") == 30.0


def test_paired_seeds_across_arms():
    cs = matrix.cells(1, ["A"], ARMS6, 30, profiles=["leo_relay"])
    assert {c.seeds for c in cs} == {30}          # same base seed + same count = same seeds


def test_resume_skips_existing(tmp_path):
    c = matrix.cells(1, ["A"], ["b"], 2, profiles=["zero"])[0]
    assert not matrix.done(c, str(tmp_path))
    d = tmp_path / c.name
    d.mkdir()
    (d / "summary.json").write_text(json.dumps({"error": None, "episodes": [1]}))
    assert matrix.done(c, str(tmp_path))
    (d / "summary.json").write_text(json.dumps({"error": "exit 1"}))
    assert not matrix.done(c, str(tmp_path))      # a crashed cell is retried


def test_parse_stdout():
    txt = ("arm 0 ep 0 seed 0 success=True 9.2s rtt_p50=12ms hold=0.00s unsafe=1 cage=1 "
           "stalls=0 max_dt=0.01s frames=403\n"
           "arm 0 ep 1 seed 1 success=False 20.1s rtt_p50=10ms hold=0.50s unsafe=0 cage=0 "
           "stalls=2 max_dt=1.30s frames=346\n"
           "\nsuccess_rate     0.50\ndemos_per_hour   391.3\nsal              -4.54\n"
           "unsafe_events    1  (move_in_hold=0, vel_over=0, keepout=1)\n"
           "cage             1\nstalls           2\nmax_dt_s         1.300\n"
           "diagnostics      hold=0, ramp_clip=1768, cage=1\n")
    eps, agg = matrix.parse_stdout(txt)
    assert [e["seed"] for e in eps] == [0, 1]
    assert [e["success"] for e in eps] == [True, False]
    assert eps[1]["duration_s"] == 20.1
    assert agg["demos_per_hour"] == 391.3 and agg["sal"] == -4.54
    # cage is NOT in `unsafe` any more (T07) but is still readable per cell and per episode
    assert agg["unsafe"] == 1 and agg["events"]["keepout"] == 1
    assert agg["cage"] == 1 and agg["events"]["cage"] == 1
    assert [e["cage"] for e in eps] == [1, 0]
    # T06: a cell that stalled under load is flagged, per episode and in the aggregate
    assert [e["stalls"] for e in eps] == [0, 2] and eps[1]["max_dt_s"] == 1.30
    assert agg["stalls"] == 2 and agg["max_dt_s"] == 1.3
    assert agg["events"]["ramp_clip"] == 1768


def test_wilson():
    lo, hi = aggregate.wilson(5, 10)              # textbook 95 % Wilson
    assert (round(lo, 4), round(hi, 4)) == (0.2366, 0.7634)
    lo, hi = aggregate.wilson(0, 10)
    assert lo == 0.0 and round(hi, 4) == 0.2775
    assert aggregate.wilson(0, 0) == (0.0, 1.0)


def test_mcnemar():
    assert aggregate.mcnemar_p(0, 0) == 1.0
    assert aggregate.mcnemar_p(1, 1) == 1.0
    assert aggregate.mcnemar_p(10, 0) == pytest.approx(2 * 0.5 ** 10)
    assert aggregate.mcnemar_p(8, 2) == pytest.approx(0.109375)   # binom 10, k<=2, x2


def _sat(d, ep, n=512, stall=False, step=0.02):
    """Synthetic applied-setpoint sidecar: 780 Hz, one 0.5 s gap when `stall`."""
    import numpy as np
    dt = np.full(n - 1, 0.00128)
    if stall:
        dt[n // 2] = 0.5
    t = np.concatenate([[0.0], np.cumsum(dt)])
    q = np.zeros((n, 7), np.float32)
    q[:, 0] = np.sin(np.linspace(0, 3.0, n)) * step
    (d / "data").mkdir(exist_ok=True)
    np.savez_compressed(d / "data" / f"episode_{ep:06d}_sat.npz", t_ns=(t * 1e9).astype(
        "int64"), t_applied_ns=(t * 1e9).astype("int64"), cmd_seq=np.arange(n),
        hold=np.zeros(n, bool), setpoint=q, assist=np.zeros(n, bool),
        taut=np.zeros(n, bool))


def _cell(tmp, strategy, profile, succ, dur, task="capture", rtt=0.0, events=None,
          stalls=None, sats=0, new_schema=False, agg=None, block="A"):
    """One synthetic cell. `stalls` = per-episode stall counts (new schema only);
    `sats` = how many episodes also get a sidecar; the first `stalls` of them stall."""
    d = tmp / f"{block}_{task}_{strategy}_{profile.replace(':', '')}_tau0.17"
    d.mkdir()
    ev = {"move_in_hold": 0, "vel_over": 0, "keepout": 0, "cage": 0}
    ev.update(events or {})
    eps = []
    for i, (s, x) in enumerate(zip(succ, dur)):
        e = dict(arm=0, ep=i, seed=i, success=bool(s), duration_s=x, rtt_p50=rtt,
                 hold_s=0.0, unsafe=0, frames=100)
        if new_schema:
            e |= dict(stalls=(stalls or [0] * len(succ))[i], max_dt_s=0.002,
                      duration_s=x, duration_active_s=x)
        eps.append(e)
    for i in range(sats):
        _sat(d, i, stall=bool((stalls or [0] * len(succ))[i]))
    a = {"demos_per_hour": 0.0, "unsafe": sum(ev.values()), "events": ev,
         "sal": -6.3, "ldlj": -19.4, "stall_frac": 0.5}
    a.update(agg or {})
    (d / "summary.json").write_text(json.dumps(dict(
        block=block, task=task, strategy=strategy, profile=profile, tau_h=0.17,
        name=d.name, rtt_ms=rtt, error=None, aggregate=a, episodes=eps)))
    return d


def test_aggregate_end_to_end(tmp_path):
    """Baseline 4/10, arm 9/10 on the same seeds: 5 discordant one way, 0 the other.
    Durations are the raw wall clock, so aggregate subtracts the 1 s linger (T09)."""
    base = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
    arm = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", base, [10.0] * 10)
    _cell(raw, "twin", "zero", arm, [8.0] * 10)
    aggregate.main(["--raw", str(raw), "--out", str(out)])
    res = json.loads((out / "results.json").read_text())
    p = {r["arm"]: r for r in res["paired"]}["twin"]
    assert (p["b_only"], p["c_only"]) == (0, 5)
    assert p["mcnemar_p"] == pytest.approx(2 * 0.5 ** 5)
    assert p["diff"] == pytest.approx(0.5)
    assert p["dph_ratio"] == pytest.approx(9.0 / 7.0)       # linger removed from both
    assert p["dph_ci"][0] <= p["dph_ratio"] <= p["dph_ci"][1]
    assert isinstance(p["dropped_resamples"], int)          # T20
    md = (out / "results.md").read_text()
    assert "0.40 [0.17,0.69] 4/10" in md and "0.90 [0.60,0.98] 9/10" in md
    assert "1.0 s was subtracted" in md                     # T09 footnote
    pm = (out / "paired.md").read_text()
    assert "Paired comparisons" in pm and "Zero-cell control" in pm


def test_linger_flags_respected(tmp_path):
    """duration_active_s (or a linger_excluded flag) is used verbatim, no subtraction."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 4, [8.0] * 4, new_schema=True)
    cs = aggregate.main(["--raw", str(raw), "--out", str(out)])
    assert cs[0]["demos_per_hour"] == pytest.approx(3600.0 / 8.0)
    assert not cs[0]["linger_adjusted"]
    assert "no linger correction applied" in (out / "results.md").read_text()


def test_old_schema_smoothness_from_sidecar(tmp_path):
    """T05: no stalls field, no sidecar-derived smoothness in the summary -> compute it."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 3, [8.0] * 3, sats=3)
    cs = aggregate.main(["--raw", str(raw), "--out", str(out)])
    c = cs[0]
    assert c["smooth_src"] == "sat"
    assert c["sal"] != -6.3 and c["ldlj"] != -19.4       # not the summary's obs numbers
    assert c["stall_frac"] == pytest.approx(c["stall_frac"])
    assert all(e["stalls"] == 0 for e in c["episodes"])  # derived from the sidecar dt
    assert "[sat]" in (out / "results.md").read_text()


def test_new_schema_keeps_summary_smoothness(tmp_path):
    """A summary that declares sidecar-derived smoothness is used as is."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 3, [8.0] * 3, new_schema=True,
          agg={"smoothness_source": "sat", "sal": -4.2})
    cs = aggregate.main(["--raw", str(raw), "--out", str(out)])
    assert cs[0]["smooth_src"] == "sat" and cs[0]["sal"] == -4.2


def test_missing_fields_never_crash(tmp_path):
    """Minimal old summary: no events, no sidecar, no stalls -> loads, stalls unknown."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    d = raw / "A_capture_baseline_zero_tau0.17"
    d.mkdir()
    (d / "summary.json").write_text(json.dumps(dict(
        block="A", task="capture", strategy="baseline", profile="zero", tau_h=0.17,
        name=d.name, rtt_ms=0.0, aggregate={},
        episodes=[dict(seed=0, success=True, duration_s=9.0)])))
    cs = aggregate.main(["--raw", str(raw), "--out", str(out)])
    assert cs[0]["n"] == 1 and cs[0]["link_unsafe"] == 0 and cs[0]["cage"] == 0
    assert cs[0]["episodes"][0]["stalls"] is None
    assert "| ? |" in (out / "results.md").read_text()


def test_stall_flag_and_exclude(tmp_path):
    """T06: >= 3 stalled episodes flags the cell; --exclude-stalled drops those seeds
    from BOTH arms so the pairing survives."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    st = [1, 1, 1, 0, 0, 0]
    _cell(raw, "baseline", "zero", [1] * 6, [9.0] * 6, new_schema=True)
    _cell(raw, "gain", "zero", [0, 0, 0, 1, 1, 1], [9.0] * 6, new_schema=True, stalls=st)
    cs = {c["strategy"]: c for c in aggregate.main(["--raw", str(raw), "--out", str(out)])}
    assert cs["gain"]["n_stalled"] == 3 and cs["gain"]["contaminated"]
    assert not cs["baseline"]["contaminated"]
    md = (out / "results.md").read_text()
    assert "⚠" in md and "Contaminated cells" in md and "3/6" in md
    cs = {c["strategy"]: c for c in
          aggregate.main(["--raw", str(raw), "--out", str(out), "--exclude-stalled"])}
    assert cs["gain"]["n"] == 3 and cs["baseline"]["n"] == 3      # paired drop
    assert cs["baseline"]["seeds_used"] == [3, 4, 5]
    assert cs["gain"]["k"] == 3 and cs["baseline"]["k"] == 3
    assert "excluded" in (out / "results.md").read_text()


def test_old_cell_stalls_from_sidecar(tmp_path):
    """T06 on an old cell: no `stalls` field, so the 0.2 s sidecar gap is the detector."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 4, [9.0] * 4, sats=4, stalls=[1, 1, 1, 0])
    cs = aggregate.main(["--raw", str(raw), "--out", str(out)])
    assert [e["stalls"] for e in cs[0]["episodes"]] == [1, 1, 1, 0]
    assert cs[0]["n_stalled"] == 3 and cs[0]["contaminated"]
    assert cs[0]["max_dt_s"] == pytest.approx(0.5, rel=1e-3)
    assert "⚠" in (out / "results.md").read_text()


def test_cage_and_link_unsafe_split(tmp_path):
    """T07: cage is its own column and does not gate; link_unsafe does."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    for p in ("zero", "leo_relay"):
        _cell(raw, "baseline", p, [1] * 10, [9.0] * 10, events={"cage": 12})
        _cell(raw, "twin", p, [1] * 10, [9.0] * 10,
              events={"cage": 3, "move_in_hold": 1})
    cs = {(c["strategy"], c["profile"]): c
          for c in aggregate.main(["--raw", str(raw), "--out", str(out)])}
    assert cs[("baseline", "zero")]["link_unsafe"] == 0
    assert cs[("baseline", "zero")]["cage"] == 12
    assert cs[("twin", "zero")]["link_unsafe"] == 1
    acc = {r["strategy"]: r for r in
           json.loads((out / "results.json").read_text())["acceptance"]}
    assert acc["baseline"]["link_unsafe_named"] == 0 and acc["baseline"]["cage_named"] == 24
    assert acc["baseline"]["passes"] is True        # cage alone does not fail the gate
    assert acc["twin"]["link_unsafe_named"] == 2 and acc["twin"]["passes"] is False
    md = (out / "results.md").read_text()
    assert "link_unsafe = move_in_hold + vel_over + keepout" in md
    assert "operator/task-caused" in md


def test_direct_gs_per_pass(tmp_path):
    """T10: direct_gs also reads demos per 9.2-minute pass."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "direct_gs", [1] * 4, [10.0] * 4, rtt=30.0)   # 9 s active
    cs = aggregate.main(["--raw", str(raw), "--out", str(out)])
    assert cs[0]["demos_per_hour"] == pytest.approx(400.0)
    assert cs[0]["demos_per_pass"] == pytest.approx(400.0 * 9.2 / 60)
    assert "61.3/pass" in (out / "results.md").read_text()


def test_dropped_resamples_reported(tmp_path):
    """T20: an arm that almost never succeeds produces all-failure resamples."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 10, [9.0] * 10)
    _cell(raw, "twin", "zero", [1] + [0] * 9, [9.0] * 10)
    aggregate.main(["--raw", str(raw), "--out", str(out)])
    p = json.loads((out / "results.json").read_text())["paired"][0]
    assert p["dropped_resamples"] > 0
    assert f"| {p['dropped_resamples']} |" in (out / "paired.md").read_text()


def test_block_s_readout(tmp_path):
    """Block S: the dropout profiles get their own hold/retract/link_unsafe table."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "leo_relay_drop1", [1] * 4, [9.0] * 4, block="S", rtt=48.0,
          events={"hold": 7, "retract": 2, "move_in_hold": 0})
    _cell(raw, "twin", "leo_relay_drop12", [0, 1, 1, 1], [9.0] * 4, block="S", rtt=48.0,
          events={"hold": 19, "retract": 5, "vel_over": 1})
    aggregate.main(["--raw", str(raw), "--out", str(out)])
    md = (out / "results.md").read_text()
    assert "Block S: forced dropout" in md
    assert "| capture | baseline | leo_relay_drop1 | 7 | 2 | 0 | 0 | 1.00 4/4 |" in md
    assert "| capture | twin | leo_relay_drop12 | 19 | 5 | 1 | 0 | 0.75 3/4 |" in md


def test_curves_json(tmp_path):
    """curves.json: one entry per (task, arm), points over zero + sweep in RTT order."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 10, [9.0] * 10)
    _cell(raw, "baseline", "leo_relay", [1] * 10, [9.0] * 10, rtt=48.0)   # not a curve pt
    for r, k in ((250, 8), (500, 4)):
        _cell(raw, "baseline", f"sweep:{r}", [1] * k + [0] * (10 - k), [9.0] * 10,
              rtt=float(r))
    aggregate.main(["--raw", str(raw), "--out", str(out)])
    cv = json.loads((out / "curves.json").read_text())["curves"]
    assert len(cv) == 1 and cv[0]["task"] == "capture" and cv[0]["arm"] == "baseline"
    pts = cv[0]["points"]
    assert [p["rtt_nominal_ms"] for p in pts] == [0.0, 250.0, 500.0]
    assert set(pts[0]) == {"rtt_nominal_ms", "profile", "success", "ci_lo", "ci_hi",
                           "demos_per_hour", "n"}
    assert pts[0]["profile"] == "zero"
    assert pts[1]["success"] == pytest.approx(0.8) and pts[1]["n"] == 10
    assert pts[1]["ci_lo"] < 0.8 < pts[1]["ci_hi"]
    assert pts[2]["demos_per_hour"] == pytest.approx(450.0)   # 9 s - 1 s linger


def test_legacy_deadreckon_label(tmp_path):
    """F1: the flag relabels the arm and adds the footnote; default is the plain name."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 4, [9.0] * 4)
    _cell(raw, "deadreckon", "zero", [1] * 4, [9.0] * 4)
    aggregate.main(["--raw", str(raw), "--out", str(out)])
    assert "lead 90 ms" not in (out / "results.md").read_text()
    aggregate.main(["--raw", str(raw), "--out", str(out), "--legacy-deadreckon-lead"])
    md = (out / "results.md").read_text()
    assert "| deadreckon (L=60 ms; lead 90 ms in Tier 1 code) |" in md
    assert "audit_strategies F1" in md


def test_knee_interpolation(tmp_path):
    """1.0 at 0/100, 0.9 at 250, 0.5 at 400; threshold 0.8 -> 250 + 0.25*150 = 287.5."""
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _cell(raw, "baseline", "zero", [1] * 10, [10.0] * 10)
    for rtt, k in ((0, 10), (100, 10), (250, 9), (400, 5)):
        _cell(raw, "baseline", f"sweep:{rtt}", [1] * k + [0] * (10 - k), [10.0] * 10,
              rtt=float(rtt))
    aggregate.main(["--raw", str(raw), "--out", str(out)])
    knee = json.loads((out / "results.json").read_text())["knee"][0]
    assert knee["threshold"] == pytest.approx(0.8)
    assert knee["knee_ms"] == pytest.approx(287.5)
