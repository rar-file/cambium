"""The adoption gate's numbers, on made-up ensembles."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gate import Refused, check_like_for_like, compare, decide  # noqa: E402
from paired import band_move  # noqa: E402

BAND = (20.7, 26.7)
NAME = "height (age 60)"


def ensemble(values, name=NAME, band=BAND):
    return [{name: (v, band)} for v in values]


def rows_for(base, option, base_verdict="FAIL", option_verdict="FAIL"):
    return compare(ensemble(base), ensemble(option), {NAME: base_verdict}, {NAME: option_verdict})


def test_an_option_that_moves_towards_the_band_passes():
    rows, unscored = rows_for([27.0, 27.1, 26.9, 27.0], [26.8, 26.9, 26.7, 26.8])
    assert not unscored and rows[0]["moved"] == "closer"
    assert decide(rows, unscored, "option")["ok"]


def test_an_option_that_changes_nothing_fails_but_a_correction_passes():
    rows, unscored = rows_for([27.0, 27.1, 26.9, 27.0], [27.0, 27.1, 26.9, 27.0])
    assert rows[0]["moved"] == "no change"
    assert not decide(rows, unscored, "option")["ok"]
    assert decide(rows, unscored, "correction")["ok"]


def test_significantly_worse_stops_an_option_with_a_rerun_and_flags_a_correction():
    rows, unscored = rows_for([27.0, 27.1, 26.9, 27.0], [27.2, 27.3, 27.1, 27.2])
    assert rows[0]["moved"] == "further"
    option = decide(rows, unscored, "option")
    assert not option["ok"] and "rerun" in option["note"]
    correction = decide(rows, unscored, "correction")
    assert correction["ok"] and "QUESTIONS.md" in correction["note"]


def test_pass_to_fail_stops_an_option_but_a_correction_stays_and_goes_to_questions():
    rows, unscored = rows_for([26.5, 26.6, 26.4, 26.5], [26.9, 27.0, 26.8, 26.9], "PASS", "FAIL")
    assert not decide(rows, unscored, "option")["ok"]
    correction = decide(rows, unscored, "correction")
    assert correction["ok"] and "don't revert" in correction["note"]


def test_a_target_scored_on_one_side_only_stops_it():
    base = ensemble([27.0, 27.1, 26.9, 27.0])
    option = [{} for _ in base]
    rows, unscored = compare(base, option, {NAME: "PASS"}, {})
    assert rows == [] and len(unscored) == 1
    assert not decide(rows, unscored, "option")["ok"]
    assert not decide(rows, unscored, "correction")["ok"]
    # one seed short counts too
    rows, unscored = compare(base, base[:-1] + [{}], {NAME: "FAIL"}, {NAME: "FAIL"})
    assert len(unscored) == 1


def test_crossing_a_band_counts_only_the_change_in_distance():
    # the whole move is large and clear, but the distance goes from 0.05 to 0: under 2 SE
    base = [26.75 + 0.1 * x for x in (-1, 1, -1, 1, 0)]
    option = [26.0 + 0.1 * x for x in (1, -1, 0, 1, -1)]
    r = band_move(base, option, *BAND)
    assert r["counts"] and r["distance_base"] > 0 and r["distance_option"] == 0
    assert r["distance_base"] - r["distance_option"] < 2 * r["se"]
    assert r["moved"] == "no change"


def _run(computer="node", kernel="neoversen1", commit="abc", plot=False):
    manifest = {"machine": {"computer": computer, "cpu": "c", "numpy_openblas_kernel": kernel, "scipy_openblas_kernel": kernel},
                "git_commit": commit, "uncommitted_sha256": None}
    return {"is_plot": True, "plot_data": {"run_manifest": manifest}} if plot else {"is_plot": False, "tree_stats": {"run_manifest": manifest}}


NAMES = [f"{i}_stand" for i in range(1, 21)]


def test_like_for_like_passes_and_refuses():
    base = [_run() for _ in NAMES]
    assert check_like_for_like(base, [_run() for _ in NAMES], (NAMES, NAMES), "option", None, None)["what"] == "tree"
    with pytest.raises(Refused, match="seeds"):
        check_like_for_like(base[:3], base[:3], (NAMES[:3], NAMES[:3]), "correction", None, None)
    with pytest.raises(Refused, match="different seeds"):
        check_like_for_like(base, base, (NAMES, [n + "x" for n in NAMES]), "option", None, None)
    with pytest.raises(Refused, match="machine"):
        check_like_for_like(base, [_run(computer="pc", kernel="Haswell") for _ in NAMES], (NAMES, NAMES), "correction", None, None)
    with pytest.raises(Refused, match="code"):
        check_like_for_like(base, [_run(commit="def") for _ in NAMES], (NAMES, NAMES), "option", None, None)
    # a correction changes the code, by its nature
    assert check_like_for_like(base, [_run(commit="def") for _ in NAMES], (NAMES, NAMES), "correction", None, None)
    # the node's early runs have no commit: refused until it's stated
    nulls = [_run(commit=None) for _ in NAMES]
    with pytest.raises(Refused, match="no commit"):
        check_like_for_like(nulls, base, (NAMES, NAMES), "option", None, None)
    assert check_like_for_like(nulls, base, (NAMES, NAMES), "option", "abc", None)
