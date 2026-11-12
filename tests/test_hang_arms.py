"""The hang arms tool: the factorial is the one the report names, the rule does what the report says, and a grown
tree keeps the stand tree's light beside its hang measures."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import hang_arms  # noqa: E402


def test_the_factorial_is_three_radii_by_two_shares_by_two_shoot_lengths_and_holds_todays_values():
    arms = hang_arms.arms()
    assert len(arms) == 12 and len(set(arms)) == 12
    assert hang_arms.baseline_name() in arms
    today = arms[hang_arms.baseline_name()]
    assert today == ["mechanics.pendulous_radius=0.012", "crown_frame.hanging_share=0.35", "crown_frame.twig_shoot_max_m=0.5"]
    for sets in arms.values():
        assert [s.split("=")[0] for s in sets] == ["mechanics.pendulous_radius", "crown_frame.hanging_share", "crown_frame.twig_shoot_max_m"]


def test_todays_arm_matches_the_species_file():
    from treegen.params import load_species

    sp, _ = load_species("betula_pendula")
    assert (sp.mechanics.pendulous_radius, sp.crown_frame.hanging_share, sp.crown_frame.twig_shoot_max_m) == hang_arms.TODAY


def test_the_rule_counts_a_move_toward_the_photo_only_past_twice_its_standard_error():
    base = {1: 0.60, 2: 0.62, 3: 0.61, 4: 0.63, 5: 0.59}
    clear = {s: v - 0.10 + 0.002 * s for s, v in base.items()}        # 0.09-0.098 lower, seed by seed
    noise = {1: 0.58, 2: 0.64, 3: 0.60, 4: 0.62, 5: 0.60}             # mean 0.608 against 0.610
    c = hang_arms.toward(base, clear, 0.30)
    assert c["moved"] and c["better"] and not c["passed"] and not c["worse"]
    n = hang_arms.toward(base, noise, 0.30)
    assert not n["moved"] and not n["better"]


def test_passing_the_photo_by_more_than_noise_is_not_better():
    base = {1: 0.60, 2: 0.62, 3: 0.61, 4: 0.63, 5: 0.59}
    under = {s: 0.15 + 0.001 * s for s in base}                       # far below a photo reading 0.30
    v = hang_arms.toward(base, under, 0.30)
    assert v["moved"] and v["passed"] and not v["better"]


def test_a_measure_below_its_photo_moves_toward_it_by_rising():
    base = {1: 0.38, 2: 0.39, 3: 0.40, 4: 0.38, 5: 0.39}               # crown width under the photo's 0.50
    wider = {s: v + 0.05 for s, v in base.items()}
    assert hang_arms.toward(base, wider, 0.50)["better"]
    assert hang_arms.toward(wider, base, 0.50)["worse"]


def test_the_guards_read_stand_leaf_area_and_light_at_50_and_60():
    def tree(lai, light):
        return {"ages": {str(a): {"stats": {"lai": lai, "subcanopy_diffuse_light_pct": light}} for a in (50, 60)}}

    good = {s: tree(4.4, 15.0) for s in range(1, 6)}
    dim = {s: tree(4.4, 21.0) for s in range(1, 6)}
    thin = {s: tree(3.4, 15.0) for s in range(1, 6)}
    assert all(g["holds"] for g in hang_arms.guards(good).values())
    assert not any(g["holds"] for g in hang_arms.guards(dim).values())
    assert not any(g["holds"] for g in hang_arms.guards(thin).values())


def test_a_grown_stand_tree_keeps_its_light_and_its_settings(tmp_path):
    sets = hang_arms.arms()["r003_h30_t40"]
    assert hang_arms.one(1, sets, tmp_path, 8, True, (8,), False) == 0
    r = json.loads((tmp_path / "hang.json").read_text(encoding="utf-8"))
    assert r["scenario"] == sets
    stats = r["ages"]["8"]["stats"]
    assert stats["subcanopy_diffuse_light_pct"] is not None and 0.0 < stats["subcanopy_diffuse_light_pct"] <= 100.0
    assert "H1_hanging_share_of_branch_length" in r["ages"]["8"]["geometry"]
