"""Test that tools/scorecard.py runs and evaluates outputs against approved targets."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from tools.scorecard import load_approved_targets, load_run_data, evaluate_targets, print_scorecard

ROOT = Path(__file__).resolve().parent.parent


def test_scorecard_runs():
    targets = load_approved_targets()
    assert "stand_canopy" in targets
    assert "tree_allometry" in targets

    # Test evaluating a mock plot run
    mock_plot = {
        "area_m2": 555.6,
        "side_m": 23.6,
        "trees": [{"id": 0, "germination": 0}],
        "stats": [
            {
                "year": 60,
                "trees": 78,
                "stems_per_ha": 1404,
                "died_total": 22,
                "lai": 3.74,
            }
        ],
    }
    run = {
        "path": "mock",
        "is_plot": True,
        "is_tree": False,
        "is_seedling": False,
        "plot_data": mock_plot,
        "tree_stats": None,
        "seedling_data": None,
        "trees_py": {},
    }

    results, unconditioned = evaluate_targets(targets, [run], target_age=60)
    assert len(results) > 0
    # LAI should pass
    lai_res = next((r for r in results if "lai_baltic_chronosequence" in r["target"]), None)
    assert lai_res is not None
    assert lai_res["status"] == "PASS"

    # Scorecard text format.  The band check above is still PASS; the printed word is the row's kind's
    # (DECISIONS 110 item 4): one run is never a verdict, and only an independent row can print PASS.
    out = print_scorecard(results, unconditioned)
    assert "| Target |" in out
    assert "**IN BAND" in out
    assert "**PASS**" not in out
    assert "Targets without conditions" in out
