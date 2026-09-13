"""experiments/matrix.py + aggregate.py: cell counts, resume, and the two statistics."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
import aggregate                                                        # noqa: E402
import matrix                                                           # noqa: E402

ARMS6 = ["b", "t", "d", "g", "p", "pg"]          # B T D G P Pg, selection.md section 3


@pytest.mark.parametrize("block,n", [("A", 66), ("B", 66), ("C", 12), ("E", 30)])
def test_tier1_counts(block, n):
    """selection.md section 3 Tier 1: 66 + 66 + 12 + 30 = 174 cells at 6 arms."""
    cs = matrix.cells(1, [block], ARMS6, 30, ablations=["pg"], baseline="b")
    assert len(cs) == n
    assert len({c.name for c in cs}) == n


def test_tier1_total_and_scaling():
    assert len(matrix.cells(1, None, ARMS6, 30, ablations=["pg"], baseline="b")) == 174
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
    txt = ("arm 0 ep 0 seed 0 success=True 9.2s rtt_p50=12ms hold=0.00s unsafe=1 frames=403\n"
           "arm 0 ep 1 seed 1 success=False 20.1s rtt_p50=10ms hold=0.50s unsafe=0 frames=346\n"
           "\nsuccess_rate     0.50\ndemos_per_hour   391.3\nsal              -4.54\n"
           "unsafe_events    1  (move_in_hold=0, vel_over=0, keepout=0, cage=1)\n"
           "diagnostics      hold=0, ramp_clip=1768\n")
    eps, agg = matrix.parse_stdout(txt)
    assert [e["seed"] for e in eps] == [0, 1]
    assert [e["success"] for e in eps] == [True, False]
    assert eps[1]["duration_s"] == 20.1
    assert agg["demos_per_hour"] == 391.3 and agg["sal"] == -4.54
    assert agg["unsafe"] == 1 and agg["events"]["cage"] == 1
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


def _cell(tmp, strategy, profile, succ, dur, task="capture", rtt=0.0):
    d = tmp / f"A_{task}_{strategy}_{profile.replace(':', '')}_tau0.17"
    d.mkdir()
    (d / "summary.json").write_text(json.dumps(dict(
        block="A", task=task, strategy=strategy, profile=profile, tau_h=0.17,
        rtt_ms=rtt, error=None, aggregate={"demos_per_hour": 3600.0 / (sum(
            x for x, s in zip(dur, succ) if s) / max(1, sum(succ))), "unsafe": 0,
            "events": {"cage": 0}},
        episodes=[dict(seed=i, success=bool(s), duration_s=x, rtt_p50=rtt, hold_s=0.0,
                       unsafe=0, frames=100) for i, (s, x) in enumerate(zip(succ, dur))])))


def test_aggregate_end_to_end(tmp_path):
    """Baseline 4/10, arm 9/10 on the same seeds: 5 discordant one way, 0 the other."""
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
    assert p["dph_ratio"] == pytest.approx(10.0 / 8.0)
    assert p["dph_ci"][0] <= p["dph_ratio"] <= p["dph_ci"][1]
    md = (out / "results.md").read_text()
    assert "0.40 [0.17,0.69] 4/10" in md and "0.90 [0.60,0.98] 9/10" in md
    assert "Paired comparisons" in (out / "paired.md").read_text()


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
