"""The second round of hang arms (report section 9): four arms between radius 0.006 and 0.003, each with both shoot
lengths, hanging share at today's value; the first round's names and settings are unchanged."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import hang_arms  # noqa: E402


def test_the_second_round_is_two_radii_by_two_shoot_lengths_at_todays_share():
    arms = hang_arms.arms_second()
    assert sorted(arms) == ["r004_h35_t40", "r004_h35_t50", "r004p5_h35_t40", "r004p5_h35_t50"]
    assert arms["r004p5_h35_t40"] == ["mechanics.pendulous_radius=0.0045", "crown_frame.hanging_share=0.35", "crown_frame.twig_shoot_max_m=0.4"]
    assert not set(arms) & set(hang_arms.arms())
    assert set(hang_arms.SECOND_CONTROLS) <= set(hang_arms.arms())


def test_the_first_rounds_names_are_unchanged():
    assert hang_arms.arm_name(0.012, 0.35, 0.5) == "r012_h35_t50"
    assert hang_arms.arm_name(0.006, 0.3, 0.4) == "r006_h30_t40"
    assert hang_arms.arm_name(0.003, 0.35, 0.4) == "r003_h35_t40"
    assert hang_arms.arms_of("first") == hang_arms.arms()


def test_paired_differences_are_seed_by_seed():
    a = {1: 0.50, 2: 0.52, 3: 0.49, 4: 0.51, 5: 0.53}
    b = {1: 0.40, 2: 0.43, 3: 0.38, 4: 0.42, 5: 0.42, 6: 0.99}       # seed 6 has no partner and is left out
    m, se, n, pos = hang_arms.paired(a, b)
    assert n == 5 and pos == 5 and abs(m - 0.10) < 1e-9 and 0 < se < 0.01
