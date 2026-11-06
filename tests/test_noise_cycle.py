"""The diagnosis of the see-saw and the Naslund cross-check, on made-up series."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from noise_cycle import best_lag, fast_share, first_alternating_year, first_year_above, smooth  # noqa: E402
from top_height_check import naslund_fit, naslund_height, thickest  # noqa: E402


def test_finds_the_start_of_a_strong_see_saw():
    steady = np.full(10, 10.0)
    saw = 10.0 + 8.0 * np.array([1, -1] * 10, float)
    assert first_alternating_year(np.concatenate([steady, saw])) == 9
    assert first_alternating_year(np.full(40, 10.0)) is None
    # swings too small to count
    assert first_alternating_year(10.0 + 0.1 * np.array([1, -1] * 20, float)) is None


def test_first_year_above_a_threshold():
    a, b = np.full(10, 100.0), np.full(10, 100.0)
    a[6:] = 102.0
    assert first_year_above(a, b, 1.0) == 6
    assert first_year_above(a, b, 5.0) is None


def test_a_cycle_out_of_step_is_all_fast_and_a_drift_is_mostly_slow():
    y = np.arange(40.0)
    saw = np.array([1.0, -1.0] * 20)
    assert fast_share(saw - (-saw)) > 0.9     # same swing, opposite step
    assert fast_share(0.5 * y) < 0.1          # a slow drift apart
    assert np.allclose(smooth(np.full(9, 3.0)), 3.0)


def test_a_shifted_cycle_is_found_at_its_lag():
    rng = np.random.default_rng(1)
    x = rng.normal(size=80) + np.array([3.0, -3.0, 1.0, -1.0] * 20)
    a = x[3:]
    b = x[:-3]
    c0, k, ck = best_lag(b, a)
    assert abs(k) == 3 and ck > 0.9 and ck > c0


def test_naslund_recovers_its_own_curve():
    d = np.linspace(5.0, 40.0, 30)
    h = 1.3 + d ** 2 / (1.5 + 0.2 * d) ** 2
    a, b = naslund_fit(d, h)
    assert a == pytest.approx(1.5) and b == pytest.approx(0.2)
    assert naslund_height(20.0, a, b) == pytest.approx(1.3 + 400.0 / (1.5 + 4.0) ** 2)


def test_thickest_counts_the_last_tree_by_its_share():
    d, h = np.array([30.0, 20.0, 10.0]), np.array([25.0, 20.0, 15.0])
    md, mh, n = thickest(d, h, 1.5)
    assert n == pytest.approx(1.5)
    assert md == pytest.approx((30.0 + 0.5 * 20.0) / 1.5)
    assert mh == pytest.approx((25.0 + 0.5 * 20.0) / 1.5)
