"""Ensemble tools: the paired rule, the multi-seed ranking and the example tree. No growth runs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from ensemble import median_seed  # noqa: E402
from paired import band_distance, band_move, compare, paired_difference  # noqa: E402
from sensitivity_screen import rank_paired, result_name  # noqa: E402


def test_an_effect_counts_only_above_two_standard_errors():
    r = paired_difference([1.0, 2.0, 3.0, 4.0], [1.5, 2.5, 3.5, 4.51])
    assert r["counts"] and r["n"] == 4 and r["mean"] == pytest.approx(0.5025)
    # same mean, but the differences scatter widely: within the noise
    r = paired_difference([1.0, 2.0, 3.0, 4.0], [3.0, 0.0, 5.0, 2.0 + 2.0 * 0.0])
    assert not r["counts"]
    assert paired_difference([1.0], [2.0]) is None
    with pytest.raises(ValueError):
        paired_difference([1.0, 2.0], [1.0])


def test_compare_pairs_only_seeds_in_both_and_by_seed():
    base = {1: {60: {"height_m": 10.0}}, 2: {60: {"height_m": 20.0}}, 3: {60: {"height_m": 99.0}}}
    option = {2: {60: {"height_m": 21.0}}, 1: {60: {"height_m": 11.0}}, 4: {60: {"height_m": 99.0}}}
    rows = compare(base, option, ages=(60,), metrics=("height_m",))
    assert rows[0]["n"] == 2
    assert rows[0]["mean"] == pytest.approx(1.0)
    assert rows[0]["base_mean"] == pytest.approx(15.0)


def test_example_tree_is_the_seed_closest_to_the_median():
    rows = {1: {"height_m": 20.0, "dbh_cm": 20.0, "lai": 2.0, "crown_ratio": 0.5},
            2: {"height_m": 25.0, "dbh_cm": 25.0, "lai": 3.0, "crown_ratio": 0.6},
            3: {"height_m": 30.0, "dbh_cm": 30.0, "lai": 4.0, "crown_ratio": 0.7}}
    assert median_seed(rows) == 2


def _write(folder, path, factor, seed, height):
    res = {str(a): {"height_m": height, "dbh_cm": 10.0, "leaf_area_m2": 10.0, "fixed": 10.0} for a in (30, 50, 60)}
    (folder / result_name(path, factor, seed)).write_text(json.dumps(res))


def test_multi_seed_ranking_puts_a_real_effect_first_and_flags_noise(tmp_path):
    jitter = [0.1, -0.1, 0.2, -0.2, 0.0]
    for i, s in enumerate(range(1, 6)):
        _write(tmp_path, None, 1.0, s, 100.0)
        _write(tmp_path, "real.effect", 1.25, s, 110.0 + jitter[i])
        _write(tmp_path, "just.noise", 1.25, s, 100.0 + jitter[i] * 5)
    rank_paired(tmp_path, 5)
    rows = (tmp_path / "ranking.csv").read_text().splitlines()
    assert rows[1].split(",")[1] == "real.effect" and rows[1].split(",")[6] == "no"
    assert rows[2].split(",")[1] == "just.noise" and rows[2].split(",")[6] == "yes"


def test_band_distance():
    assert band_distance(5.0, 4.0, 6.0) == 0.0
    assert band_distance(7.5, 4.0, 6.0) == 1.5
    assert band_distance(3.0, 4.0, 6.0) == 1.0


def test_band_move_says_closer_further_or_no_change():
    too_tall = [27.0, 27.1, 26.9, 27.0]
    # a clear move towards a band that ends at 26.7, and the same move away from it
    assert band_move(too_tall, [26.8, 26.9, 26.7, 26.8], 20.7, 26.7)["moved"] == "closer"
    assert band_move(too_tall, [27.2, 27.3, 27.1, 27.2], 20.7, 26.7)["moved"] == "further"
    # the same size of change, but all of it inside the band, changes no distance
    inside = [23.0, 23.1, 22.9, 23.0]
    assert band_move(inside, [23.2, 23.3, 23.1, 23.2], 20.7, 26.7)["moved"] == "no change"
    # a noisy difference doesn't count, whichever way its mean went
    noisy = band_move(too_tall, [28.0, 26.0, 28.5, 26.0], 20.7, 26.7)
    assert not noisy["counts"] and noisy["moved"] == "no change"
