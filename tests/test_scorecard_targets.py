"""tools/scorecard.py takes every number from the approved targets.yaml, scores
only within each target's conditions, and fills in nothing a run did not save."""
from __future__ import annotations

import copy

from tools.scorecard import evaluate_targets, load_approved_targets


def _plot_run(path="mock", mode=None, lai=3.74, stems=1404, year=60, trees=None, trees_py=None, extra=None):
    plot = {"area_m2": 555.6, "side_m": 23.6, "trees": trees or [],
            "stats": [{"year": year, "trees": 78, "stems_per_ha": stems, "died_total": 22, "lai": lai}]}
    if mode is not None:
        plot["mode"] = mode
    plot.update(extra or {})
    return {"path": path, "is_plot": True, "is_tree": False, "is_seedling": False, "plot_data": plot,
            "tree_stats": None, "seedling_data": None, "trees_py": trees_py or {}}


def _row(results, name, age=None):
    key = f"{name} (age {age})" if age is not None else name
    return next(r for r in results if r["target"] == key)


def test_no_value_filled_in_for_unsaved_light():
    """The subcanopy light comes only from the run's output, whatever the path."""
    results, _ = evaluate_targets(load_approved_targets(), [_plot_run(path="out/bench/p38_nat", mode="natural")], ages=[50])
    r = _row(results, "stand_canopy.subcanopy_light_transmittance", 50)
    assert r["status"] == "NOT APPLICABLE"
    assert r["model_value"] == "N/A"


def test_ranges_come_from_targets_yaml():
    targets = copy.deepcopy(load_approved_targets())
    run = _plot_run(mode="natural")
    results, _ = evaluate_targets(targets, [run], ages=[60])
    assert _row(results, "stand_canopy.lai_baltic_chronosequence", 60)["status"] == "PASS"
    targets["stand_canopy"]["lai_baltic_chronosequence"]["target_range"] = [4.0, 4.5]
    results, _ = evaluate_targets(targets, [run], ages=[60])
    assert _row(results, "stand_canopy.lai_baltic_chronosequence", 60)["status"] == "FAIL"


def test_run_mode_and_age_conditions():
    targets = load_approved_targets()
    results, _ = evaluate_targets(targets, [_plot_run(mode="managed")], ages=[60])
    assert _row(results, "stand_canopy.lai_baltic_chronosequence", 60)["status"] == "NOT APPLICABLE"
    results, _ = evaluate_targets(targets, [_plot_run(mode="natural", year=30)], ages=[30])
    assert _row(results, "stand_canopy.lai_hagemeier", 30)["status"] == "NOT APPLICABLE"


def test_crown_ratio_uses_stand_year_and_live_trees():
    """A tree's per_year 'year' counts from its germination; removed trees are left out."""
    trees = [{"id": 0, "germination": 2, "removed": None},
             {"id": 1, "germination": 0, "removed": 10}]
    trees_py = {0: [{"year": y, "crown_ratio": 0.40 if y == 13 else 0.90} for y in range(20)],
                1: [{"year": y, "crown_ratio": 0.10} for y in range(11)]}
    run = _plot_run(mode="natural", year=15, trees=trees, trees_py=trees_py)
    results, _ = evaluate_targets(load_approved_targets(), [run], ages=[15])
    r = _row(results, "stand_canopy.live_crown_ratio.dense_unmanaged_stand", 15)
    assert r["model_value"] == "0.40"
    assert r["status"] == "PASS"


def test_single_value_without_range_is_not_pass_or_fail():
    run = _plot_run(mode="natural", stems=880, year=45)
    results, _ = evaluate_targets(load_approved_targets(), [run], ages=[45])
    assert _row(results, "stand_canopy.stand_density", 45)["status"] == "NO RANGE"


def test_conditioned_target_without_evaluator_is_listed():
    targets = copy.deepcopy(load_approved_targets())
    targets["tree_allometry"]["new_target"] = {"source": "x", "value": 1.0, "conditions": {"note": "y"}}
    results, _ = evaluate_targets(targets, [_plot_run(mode="natural")], ages=[60])
    assert _row(results, "tree_allometry.new_target")["status"] == "NOT SCORED"
