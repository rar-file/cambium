"""The third round of hang arms (report section 11): two radii just softer than 0.0045, and the existing two-end-bud
switch (crown_frame.twig_end_buds 2, option J) at 0.0045 and 0.0047; today's share and shoot length throughout.  The
earlier rounds' names and settings are unchanged."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import hang_arms  # noqa: E402


def test_the_third_round_is_two_radii_and_the_two_end_bud_switch_at_two_radii():
    arms = hang_arms.arms_third()
    assert sorted(arms) == ["r004p5_h35_t50_j2", "r004p7_h35_t50", "r004p7_h35_t50_j2", "r004p9_h35_t50"]
    assert arms["r004p9_h35_t50"] == ["mechanics.pendulous_radius=0.0049", "crown_frame.hanging_share=0.35", "crown_frame.twig_shoot_max_m=0.5"]
    assert arms["r004p5_h35_t50_j2"] == ["mechanics.pendulous_radius=0.0045", "crown_frame.hanging_share=0.35", "crown_frame.twig_shoot_max_m=0.5",
                                         "crown_frame.twig_end_buds=2"]
    assert arms["r004p7_h35_t50_j2"][:3] == arms["r004p7_h35_t50"]
    assert hang_arms.arms_of("third") == arms


def test_no_name_is_reused_and_the_controls_were_grown_before():
    third, earlier = set(hang_arms.arms_third()), set(hang_arms.arms()) | set(hang_arms.arms_second())
    assert not third & earlier
    assert set(hang_arms.THIRD_CONTROLS) <= earlier
    assert hang_arms.arms_of("first") == hang_arms.arms() and hang_arms.arms_of("second") == hang_arms.arms_second()
