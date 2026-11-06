"""The adoption gate's numbers, on made-up ensembles."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gate import compare, decide  # noqa: E402

BAND = (20.7, 26.7)


def ensemble(values, name="height (age 60)", band=BAND, status="FAIL"):
    return {f"{i + 1}_stand": {name: (v, band, status)} for i, v in enumerate(values)}


def test_an_option_that_moves_towards_the_band_passes():
    rows, seeds = compare(ensemble([27.0, 27.1, 26.9, 27.0]), ensemble([26.8, 26.9, 26.7, 26.8]))
    assert len(seeds) == 4 and rows[0]["moved"] == "closer"
    assert decide(rows, "option")["ok"]


def test_an_option_that_changes_nothing_fails_but_a_correction_passes():
    rows, _ = compare(ensemble([27.0, 27.1, 26.9, 27.0]), ensemble([27.0, 27.1, 26.9, 27.0]))
    assert rows[0]["moved"] == "no change"
    assert not decide(rows, "option")["ok"]
    assert decide(rows, "correction")["ok"]


def test_significantly_worse_stops_an_option_and_flags_a_correction():
    rows, _ = compare(ensemble([27.0, 27.1, 26.9, 27.0]), ensemble([27.2, 27.3, 27.1, 27.2]))
    assert rows[0]["moved"] == "further"
    assert not decide(rows, "option")["ok"]
    correction = decide(rows, "correction")
    assert correction["ok"] and "QUESTIONS.md" in correction["note"]


def test_pass_to_fail_stops_both():
    rows, _ = compare(ensemble([26.5, 26.6, 26.4, 26.5]), ensemble([26.9, 27.0, 26.8, 26.9]))
    assert rows[0]["base_verdict"] == "PASS" and rows[0]["option_verdict"] == "FAIL"
    assert not decide(rows, "option")["ok"]
    assert not decide(rows, "correction")["ok"]


def test_info_rows_and_unpaired_seeds_are_left_out():
    info = ensemble([1.0, 2.0, 3.0], name="crown ratio (age 60)", status="INFO")
    rows, _ = compare(info, info)
    assert rows == []
    base, option = ensemble([27.0, 27.1, 26.9]), ensemble([26.8, 26.9, 26.7, 26.5])
    rows, seeds = compare(base, option)
    assert len(seeds) == 3 and rows[0]["n"] == 3
