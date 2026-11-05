"""tools/scorecard.py takes every number from targets.yaml, scores only within
each target's condition labels, and fills in nothing a run did not save.

These tests read the working copy of reference/targets.yaml, so they check the
scorecard against the targets file being committed, whatever the tag points to.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from tools.scorecard import dominant_height, evaluate_targets, t13_years
from treegen.reference import eriksson_1997_height

ROOT = Path(__file__).resolve().parent.parent


def _targets():
    with open(ROOT / "reference" / "targets.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _plot_run(path="mock", mode=None, lai=3.74, stems=1404, year=60, trees=None, trees_py=None, extra=None):
    plot = {"area_m2": 555.6, "side_m": 23.6, "trees": trees or [],
            "stats": [{"year": year, "trees": 78, "stems_per_ha": stems, "died_total": 22, "lai": lai}]}
    if mode is not None:
        plot["mode"] = mode
    plot.update(extra or {})
    return {"path": path, "is_plot": True, "is_tree": False, "is_seedling": False, "plot_data": plot,
            "tree_stats": None, "seedling_data": None, "trees_py": trees_py or {}}


def _tree_run(mode="stand", per_year=None, extra=None):
    stats = {"mode": mode, "per_year": per_year or []}
    stats.update(extra or {})
    return {"path": "mock_tree", "is_plot": False, "is_tree": True, "is_seedling": False, "plot_data": None,
            "tree_stats": stats, "seedling_data": None, "trees_py": {}}


def _seedling_run(h, extra=None):
    data = {"h": h, "rs": {}}
    data.update(extra or {})
    return {"path": "mock_seedling", "is_plot": False, "is_tree": False, "is_seedling": True, "plot_data": None,
            "tree_stats": None, "seedling_data": data, "trees_py": {}}


def _row(results, name, age=None):
    key = f"{name} (age {age})" if age is not None else name
    return next(r for r in results if r["target"] == key)


def test_no_value_filled_in_for_unsaved_light():
    """The subcanopy light comes only from the run's output, whatever the path."""
    results, _ = evaluate_targets(_targets(), [_plot_run(path="out/bench/p38_nat", mode="natural")], ages=[50])
    r = _row(results, "stand_canopy.subcanopy_light_transmittance", 50)
    assert r["status"] == "NOT APPLICABLE"
    assert r["model_value"] == "N/A"


def test_ranges_come_from_targets_yaml():
    targets = copy.deepcopy(_targets())
    run = _plot_run(mode="natural")
    results, _ = evaluate_targets(targets, [run], ages=[60])
    assert _row(results, "stand_canopy.lai_baltic_chronosequence", 60)["status"] == "PASS"
    targets["stand_canopy"]["lai_baltic_chronosequence"]["target_range"] = [4.0, 4.5]
    results, _ = evaluate_targets(targets, [run], ages=[60])
    assert _row(results, "stand_canopy.lai_baltic_chronosequence", 60)["status"] == "FAIL"


def test_run_mode_and_age_conditions():
    targets = _targets()
    results, _ = evaluate_targets(targets, [_plot_run(mode="managed")], ages=[60])
    assert _row(results, "stand_canopy.lai_baltic_chronosequence", 60)["status"] == "NOT APPLICABLE"
    results, _ = evaluate_targets(targets, [_plot_run(mode="natural", year=30)], ages=[30])
    assert _row(results, "stand_canopy.lai_hagemeier", 30)["status"] == "NOT APPLICABLE"


def test_scenario_label():
    """A stand-tree run is managed and not a plot: the dense natural-stand crown
    ratio does not apply, the managed-stand recommendation does."""
    run = _tree_run(per_year=[{"year": 15, "crown_ratio": 0.6, "height_m": 9.0}])
    results, _ = evaluate_targets(_targets(), [run], ages=[15])
    assert _row(results, "stand_canopy.live_crown_ratio.dense_unmanaged_stand", 15)["status"] == "NOT APPLICABLE"
    assert _row(results, "stand_canopy.live_crown_ratio.silvicultural_recommendation", 15)["status"] == "INFO"


def test_options_required_label():
    targets = _targets()
    h = {"2": 0.2, "5": 1.5}
    results, _ = evaluate_targets(targets, [_seedling_run(h)])
    assert _row(results, "juvenile_establishment.natural_clearcut_heights", 2)["status"] == "NOT APPLICABLE"
    run = _seedling_run(h, extra={"options": {"field_layer_competition.enabled": True}})
    results, _ = evaluate_targets(targets, [run])
    assert _row(results, "juvenile_establishment.natural_clearcut_heights", 2)["status"] == "PASS"
    assert _row(results, "juvenile_establishment.natural_clearcut_heights", 5)["status"] == "PASS"


def test_crown_ratio_uses_stand_year_and_live_trees():
    """A tree's per_year 'year' counts from its germination; removed trees are left out."""
    trees = [{"id": 0, "germination": 2, "removed": None},
             {"id": 1, "germination": 0, "removed": 10}]
    trees_py = {0: [{"year": y, "crown_ratio": 0.40 if y == 13 else 0.90} for y in range(20)],
                1: [{"year": y, "crown_ratio": 0.10} for y in range(11)]}
    run = _plot_run(mode="natural", year=15, trees=trees, trees_py=trees_py)
    results, _ = evaluate_targets(_targets(), [run], ages=[15])
    r = _row(results, "stand_canopy.live_crown_ratio.dense_unmanaged_stand", 15)
    assert r["model_value"] == "0.40"
    assert r["status"] == "PASS"


def test_info_targets_are_never_pass_or_fail():
    run = _plot_run(mode="natural", stems=880, year=45)
    results, _ = evaluate_targets(_targets(), [run], ages=[45])
    assert _row(results, "stand_canopy.stand_density", 45)["status"] == "INFO"
    tree = _tree_run(mode="open", per_year=[{"year": 60, "dbh_cm": 30.0, "crown_width_m": 7.0, "height_m": 25.0}])
    results, _ = evaluate_targets(_targets(), [tree], ages=[60])
    assert _row(results, "tree_allometry.crown_width_open_grown", 60)["status"] == "INFO"


def test_conditioned_target_without_evaluator_is_listed():
    targets = copy.deepcopy(_targets())
    targets["tree_allometry"]["new_target"] = {"source": "x", "value": 1.0, "conditions": {"text": "y"}}
    results, _ = evaluate_targets(targets, [_plot_run(mode="natural")], ages=[60])
    assert _row(results, "tree_allometry.new_target")["status"] == "NOT SCORED"


def test_dominant_height_thickest_or_tallest():
    """100 trees per ha on 250 m2 is 2.5 trees: the first two in full, the third at half weight."""
    recs = [{"dbh_cm": 30, "height_m": 20.0}, {"dbh_cm": 25, "height_m": 24.0},
            {"dbh_cm": 20, "height_m": 22.0}, {"dbh_cm": 10, "height_m": 10.0}]
    h, n = dominant_height(recs, 250.0, "dbh_cm")
    assert n == pytest.approx(2.5)
    assert h == pytest.approx((20.0 + 24.0 + 0.5 * 22.0) / 2.5)
    h, _ = dominant_height(recs, 250.0, "height_m")
    assert h == pytest.approx((24.0 + 22.0 + 0.5 * 20.0) / 2.5)


def test_height_band_and_definition():
    targets = copy.deepcopy(_targets())
    si = targets["tree_allometry"]["site_index_curves"]
    p = si["parameters"]
    lo = eriksson_1997_height(20.0, 60.0 - t13_years(si, 20.0), p["asi"], p["beta"], p["b2"])
    hi = eriksson_1997_height(26.0, 60.0 - t13_years(si, 26.0), p["asi"], p["beta"], p["b2"])
    # stand-tree run: the tree's own height against the band at total age 60
    run = _tree_run(per_year=[{"year": 60, "height_m": (lo + hi) / 2}])
    results, _ = evaluate_targets(targets, [run], ages=[60])
    r = _row(results, "tree_allometry.site_index_curves", 60)
    assert r["status"] == "PASS"
    assert f"{lo:.2f}-{hi:.2f} m" in r["target_range"]
    run = _tree_run(per_year=[{"year": 60, "height_m": hi + 0.1}])
    results, _ = evaluate_targets(targets, [run], ages=[60])
    assert _row(results, "tree_allometry.site_index_curves", 60)["status"] == "FAIL"
    # outside the age labels
    results, _ = evaluate_targets(targets, [_tree_run(per_year=[{"year": 15, "height_m": 9.0}])], ages=[15])
    assert _row(results, "tree_allometry.site_index_curves", 15)["status"] == "NOT APPLICABLE"
    # plot run: scored only once the definition is set
    trees = [{"id": k, "germination": 0, "removed": None} for k in range(8)]
    trees_py = {k: [{"year": 60, "height_m": (lo + hi) / 2, "dbh_cm": 20.0 + k}] for k in range(8)}
    plot = _plot_run(mode="natural", trees=trees, trees_py=trees_py)
    si["dominant_height_definition"] = "unconfirmed"
    results, _ = evaluate_targets(targets, [plot], ages=[60])
    assert _row(results, "tree_allometry.site_index_curves", 60)["status"] == "NOT APPLICABLE"
    si["dominant_height_definition"] = "100_thickest_per_ha"
    results, _ = evaluate_targets(targets, [plot], ages=[60])
    assert _row(results, "tree_allometry.site_index_curves", 60)["status"] == "PASS"


def test_time_to_breast_height_rule():
    """T13 = 150 / SIS (Elfving 2010 p. 56), SIS the curve's own top height at
    total age 100; numbers worked out separately from the same curve."""
    item = {"parameters": {"asi": 7, "beta": 394, "b2": 1.387}, "reference_age_years": 50,
            "time_to_breast_height": {"numerator": 150, "sis_total_age_years": 100}}
    for si, t13, sis in ((20.0, 5.98, 25.08), (26.0, 5.01, 29.93)):
        t = t13_years(item, si)
        assert t == pytest.approx(t13, abs=0.01)
        assert eriksson_1997_height(si, 100.0 - t, 7, 394, 1.387) == pytest.approx(sis, abs=0.01)
        assert t * sis == pytest.approx(150.0, abs=0.2)


def test_fixed_time_to_breast_height_still_read():
    """A targets file from before the rule (an older git ref) keeps its number."""
    assert t13_years({"years_to_breast_height": 4}, 20.0) == 4.0


def test_light_is_read_for_each_year_and_only_as_diffuse():
    targets = _targets()
    name = "stand_canopy.subcanopy_light_transmittance"
    # stand tree: each age has its own value
    py = [{"year": 50, "subcanopy_diffuse_light_pct": 15.0, "subcanopy_light_pct": 25.0},
          {"year": 60, "subcanopy_diffuse_light_pct": 30.0, "subcanopy_light_pct": 40.0}]
    results, _ = evaluate_targets(targets, [_tree_run(per_year=py)], ages=[50, 60])
    assert _row(results, name, 50)["status"] == "PASS"
    assert _row(results, name, 50)["model_value"] == "15.0 %"
    assert _row(results, name, 60)["status"] == "FAIL"
    # plot: from the plot's yearly stats
    plot = _plot_run(mode="natural", year=50, extra={})
    plot["plot_data"]["stats"][0]["subcanopy_diffuse_light_pct"] = 12.0
    results, _ = evaluate_targets(targets, [plot], ages=[50])
    assert _row(results, name, 50)["status"] == "PASS"
    # only the sky-and-sun value: shown, never scored
    results, _ = evaluate_targets(targets, [_tree_run(per_year=[{"year": 50, "subcanopy_light_pct": 15.0}])], ages=[50])
    r = _row(results, name, 50)
    assert r["status"] == "NOT APPLICABLE"
    assert r["model_value"] == "N/A"
    assert "15.0 %" in r["notes"]
    # a value at the run level is not read
    results, _ = evaluate_targets(targets, [_tree_run(per_year=[{"year": 50}], extra={"subcanopy_diffuse_light_pct": 15.0})], ages=[50])
    assert _row(results, name, 50)["status"] == "NOT APPLICABLE"
