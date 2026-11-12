"""A forest tree's height step by its standing among its neighbours (treegen/height_status.py, plot.height_status;
plan 2026-11-11, step E).  Off by default.

The formulas are checked against numbers worked by hand from the papers' own coefficients: Hynynen 1995 Table 6 (Scots
pine, borrowed) and Hynynen et al. 2002 Table 24, Table 34 and Eq. 3 (birch).  The arithmetic is written out beside
each number.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from treegen import checkpoint, height_status as hs, logs
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import load_environment, load_species

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tree_list  # noqa: E402
from test_forest import make_plot, species  # noqa: E402
from test_speed import digest  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    sp, _ = load_species("betula_pendula")
    return sp.plot.height_status


def rule(cfg, name, **sets):
    c = copy.deepcopy(cfg)
    c.rule = name
    for k, v in sets.items():
        if "." in k:
            block, key = k.split(".")
            setattr(getattr(c, block), key, v)
        else:
            setattr(c, k, v)
    return c


def line(a):
    """A straight curve, 0.4 m a year: its forward five-year step is 2.0 m at any age."""
    return 0.4 * a


def stand(seed=1, n=60, mean=20.0, sd=5.0):
    rng = np.random.default_rng(seed)
    d = np.round(np.abs(rng.normal(mean, sd, n)) + 1.0, 2)
    h = np.round(1.3 + 0.8 * d, 3)
    return d, h


# -- the switch -----------------------------------------------------------------------------------------------------
def test_the_switch_is_off_by_default_and_its_values_are_the_papers(cfg):
    assert cfg.enabled is False and cfg.steer_top_height is False and cfg.scale_over == "top_height"
    p, b = cfg.pine_1995, cfg.birch_2002
    assert (p.a1, p.a2, p.a3) == (0.2445, -0.471, 0.8045)                          # Hynynen 1995 Table 6
    assert (b.a1, b.a2, b.planted) == (1.54405, -0.81202, False)                   # Hynynen et al. 2002 Table 24, self-sown
    assert (b.self_thinning_b0, b.self_thinning_b1) == (14.1979, -2.2178)          # Table 34, silver birch
    assert (b.stump_a_cm, b.stump_b) == (2.0, 1.25)                                # Eq. 3
    assert (b.dbh_min_cm, b.dbh_max_cm, b.rdfl_max, b.start_top_height_m, b.start_age_years) == (1.0, 41.4, 1.567, 2.6, 12.0)   # Table 5


# -- the formulas, by hand ------------------------------------------------------------------------------------------
def test_the_pine_rule_against_hand_worked_numbers():
    # d/D_dom 0.6, IH_dom 2.0 m: 0.6^0.8045 = exp(0.8045 x -0.510826) = 0.663020; exponent 0.2445 x 2.0 - 0.4710 x 0.663020
    # = 0.489000 - 0.312282 = 0.176718; 0.6^0.176718 = exp(-0.090273) = 0.913683
    assert hs.pine_1995_modifier(0.6, 2.0, 0.2445, -0.4710, 0.8045) == pytest.approx(0.913683, abs=2e-6)
    # d/D_dom 0.4, IH_dom 1.0 m: 0.4^0.8045 = exp(0.8045 x -0.916291) = 0.478473; exponent 0.2445 - 0.4710 x 0.478473 = 0.019139;
    # 0.4^0.019139 = exp(-0.017537) = 0.982616
    assert hs.pine_1995_modifier(0.4, 1.0, 0.2445, -0.4710, 0.8045) == pytest.approx(0.982616, abs=2e-6)
    # a tree at the dominants' diameter grows the dominants' step, whatever IH
    assert hs.pine_1995_modifier(1.0, 3.3, 0.2445, -0.4710, 0.8045) == 1.0


def test_the_birch_rule_against_hand_worked_numbers():
    # self-sown: exponent 1.54405 x 0.4 = 0.617620; 0.6^0.617620 = exp(0.617620 x -0.510826) = exp(-0.315496) = 0.729427
    assert hs.birch_2002_modifier(0.6, 0.4, 1.54405, -0.81202, False) == pytest.approx(0.729427, abs=2e-6)
    # planted: (1.54405 - 0.81202) x 0.4 = 0.292812; exp(0.292812 x -0.510826) = exp(-0.149576) = 0.861073
    assert hs.birch_2002_modifier(0.6, 0.4, 1.54405, -0.81202, True) == pytest.approx(0.861073, abs=2e-6)
    # the step S table (reports/sources_opened_2026-11-11.md, item 1) to its two places: 0.73 and 0.86 at d/D_dom 0.6, RDFL 0.4
    assert round(float(hs.birch_2002_modifier(0.6, 0.4, 1.54405, -0.81202, False)), 2) == 0.73
    # the largest tree has no larger tree: RDFL 0, so it grows the dominants' step at any size
    assert hs.birch_2002_modifier(1.3, 0.0, 1.54405, -0.81202, False) == 1.0


def test_the_self_thinning_line_and_the_stump_diameter_by_hand(cfg):
    b = cfg.birch_2002
    # DBH 9.5 cm: stump 2.0 + 1.25 x 9.5 = 13.875 cm; ln 13.875 = 2.630089; 14.1979 - 2.2178 x 2.630089 = 8.364889; exp = 4293.6 stems/ha
    assert hs.stump_cm(9.5, b.stump_a_cm, b.stump_b) == 13.875
    assert hs.self_thinning_stems(13.875, b.self_thinning_b0, b.self_thinning_b1) == pytest.approx(4293.6, abs=0.1)
    assert hs.growing_space([9.5, 0.0], b)[0] == pytest.approx(1.0 / 4293.6, rel=3e-5)
    assert hs.growing_space([9.5, 0.0], b)[1] == 0.0          # no DBH: no growing space counted


def test_rdfl_sums_the_larger_trees_only(cfg):
    b = cfg.birch_2002
    # 1000 m2: each tree stands for 10 stems/ha.  N at stump 39.5 cm (DBH 30) = 421.83/ha, at 27.0 cm (DBH 20) = 980.82/ha
    g30, g20 = 10.0 / 421.829, 10.0 / 980.824
    got = hs.rdfl([10.0, 20.0, 30.0], 10.0, b)
    assert got[2] == 0.0
    assert got[1] == pytest.approx(g30, rel=1e-5)                 # 0.0237063
    assert got[0] == pytest.approx(g30 + g20, rel=1e-5)           # 0.0339018
    # equal diameters don't count each other; a tree with no DBH has every tree with one above it
    tie = hs.rdfl([20.0, 20.0, 30.0, 0.0], 10.0, b)
    assert tie[0] == tie[1] == pytest.approx(g30, rel=1e-5)
    assert tie[3] == pytest.approx(2 * g20 + g30, rel=1e-5)


def test_the_dominant_diameters_by_hand():
    # D_g = sum d^3 / sum d^2 = (1000 + 8000 + 27000 + 27000) / (100 + 400 + 900 + 900) = 63000 / 2300 = 27.3913 cm
    d = [10.0, 20.0, 30.0, 30.0]
    assert hs.basal_area_mean_cm(d) == pytest.approx(27.3913, abs=1e-4)
    assert list(hs.birch_dominants(d)) == [2, 3]                   # the trees thicker than D_g; their mean is 30
    assert hs.basal_area_mean_cm([0.0, 0.0]) == 0.0
    # the 100 thickest a hectare: 10 on 1000 m2, the taller first among equals
    dd = np.arange(1.0, 31.0)
    assert sorted(hs.thickest(dd, dd, 1000.0)) == list(range(20, 30))
    assert list(hs.thickest([5.0, 5.0], [3.0, 4.0], 100.0)) == [1]


# -- one plot-year ----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name,scale", [("pine_1995", "top_height"), ("birch_2002", "top_height"), ("birch_2002", "rule")])
def test_the_dominants_mean_status_is_one(cfg, name, scale):
    d, h = stand()
    out = hs.plot_year(rule(cfg, name, scale_over=scale), d, h, 1000.0, 40.0, line, 1.25, True)
    group = hs.thickest(d, h, 1000.0) if scale == "top_height" or name == "pine_1995" else hs.birch_dominants(d)
    assert out["started"] and float(np.mean(out["status"][group])) == pytest.approx(1.0, abs=1e-12)
    assert out["row"]["dominants"] == len(group) and out["row"]["dominants_mean_modifier"] > 0.0
    assert np.allclose(out["status"] * out["row"]["dominants_mean_modifier"], out["modifier"], rtol=1e-5)
    json.dumps(out["row"])


def test_the_pine_rule_holds_its_ratio_and_ih_and_a_tree_without_dbh_takes_the_lowest_ratio(cfg):
    c = rule(cfg, "pine_1995")
    d = np.array([30.0] * 10 + [40.0, 6.0, 0.0])                # the 10 thickest on 1000 m2 are the 40 and nine 30s: D_dom 31
    h = np.array([20.0] * 10 + [21.0, 8.0, 0.5])
    steep = lambda a: 1.0 * a                                     # forward five-year step 5.0 m, held at 3.6
    out = hs.plot_year(c, d, h, 1000.0, 30.0, steep, 1.25, True)
    assert out["row"]["ih_m"] == 3.6 and out["row"]["dominant_dbh_cm"] == pytest.approx(31.0)
    assert out["ratio"][10] == 1.1                                # 40 / 31 = 1.29, held at 1.1
    assert out["ratio"][11] == 0.4 and out["ratio"][12] == 0.4    # 6 / 31 = 0.19, held; no DBH: the lowest ratio, never status 1
    assert out["modifier"][12] == pytest.approx(float(hs.pine_1995_modifier(0.4, 3.6, 0.2445, -0.471, 0.8045)))
    assert out["status"][12] < 0.7
    flat = lambda a: 0.01 * a                                     # 0.05 m in five years, held at 0.6
    assert hs.plot_year(c, d, h, 1000.0, 30.0, flat, 1.25, True)["row"]["ih_m"] == 0.6


def test_the_birch_rule_holds_dbh_and_rdfl_inside_the_reports_range(cfg):
    c = rule(cfg, "birch_2002")
    d = np.array([50.0, 30.0, 20.0, 0.5, 0.0])
    h = np.array([30.0, 25.0, 20.0, 1.4, 1.0])
    out = hs.plot_year(c, d, h, 1000.0, 40.0, line, 1.25, True)
    ddom = out["row"]["dominant_dbh_cm"]
    assert ddom == pytest.approx(50.0)                            # D_g = 160000.125 / 3800.25 = 42.1: only the 50 is thicker
    assert out["ratio"][0] == pytest.approx(41.4 / 50.0)          # DBH held at 41.4
    assert out["ratio"][3] == out["ratio"][4] == pytest.approx(1.0 / 50.0)   # under 1.0 cm and no DBH: 1.0 cm
    assert out["rdfl"][0] == 0.0 and out["rdfl"][4] > out["rdfl"][3] > out["rdfl"][2]  # the 0.5 cm tree is larger than the one with none
    dense = hs.plot_year(c, np.array([30.0] * 30 + [5.0]), np.array([25.0] * 30 + [6.0]), 10.0, 40.0, line, 1.25, True)
    assert dense["rdfl"][-1] == 1.567                             # 30 trees of 30 cm on 10 m2: RDFL 30 x 1000 / 421.8 = 71, held at the data's top


def test_nothing_starts_before_the_sources_data(cfg):
    d, h = stand(mean=6.0, sd=1.5)
    h = np.round(1.3 + 0.6 * d, 3)                                 # top height near 6 m
    pine = rule(cfg, "pine_1995")
    out = hs.plot_year(pine, d, h, 1000.0, 15.0, line, 1.25, False)
    assert not out["started"] and np.all(out["status"] == 1.0) and out["modifier"] is None
    assert 5.0 < out["row"]["top_height_m"] < 10.0
    # once started it stays on, though top height read under its start again
    assert hs.plot_year(pine, d, h, 1000.0, 15.0, line, 1.25, True)["started"]
    # from the first DBH (the information arm A-early)
    early = rule(cfg, "pine_1995", **{"pine_1995.start_top_height_m": None})
    assert hs.plot_year(early, d, h, 1000.0, 15.0, line, 1.25, False)["started"]
    assert not hs.plot_year(early, np.zeros(5), np.ones(5), 1000.0, 3.0, line, 1.25, False)["started"]
    # birch: top height 2.6 m and stand age 12, both from Table 5
    birch = rule(cfg, "birch_2002")
    assert not hs.plot_year(birch, d, h, 1000.0, 11.0, line, 1.25, False)["started"]
    assert hs.plot_year(birch, d, h, 1000.0, 12.0, line, 1.25, False)["started"]
    low = np.round(1.3 + 0.05 * d, 3)                              # top height under 2.6 m
    assert not hs.plot_year(birch, d, low, 1000.0, 20.0, line, 1.25, False)["started"]


def test_arm_b_steers_the_approved_top_height_to_the_curve(cfg):
    d, h = stand()
    top = logs.fitted_top_height(list(d), list(h), 1000.0)[0]
    for name in ("pine_1995", "birch_2002"):
        c = rule(cfg, name, steer_top_height=True)
        plain = hs.plot_year(rule(cfg, name), d, h, 1000.0, 40.0, line, 1.25, True)
        # the curve 0.1 m above top height next year, with a step of 0.4 m: F = 0.1 / 0.4 = 0.25
        near = lambda a, t=top: t + 0.1 + 0.4 * (a - 41.0)
        out = hs.plot_year(c, d, h, 1000.0, 40.0, near, 1.25, True)
        assert out["row"]["steer_factor"] == pytest.approx(0.25, abs=1e-6)
        assert np.allclose(out["status"], 0.25 * plain["status"])
        far = lambda a, t=top: t + 5.0 + 0.4 * (a - 41.0)         # far below the curve: held at catch_up
        assert hs.plot_year(c, d, h, 1000.0, 40.0, far, 1.25, True)["row"]["steer_factor"] == 1.25
        above = lambda a, t=top: t - 1.0 + 0.4 * (a - 41.0)       # above it: no growth, never negative
        assert hs.plot_year(c, d, h, 1000.0, 40.0, above, 1.25, True)["row"]["steer_factor"] == 0.0


def test_a_rule_or_scale_that_doesnt_exist_is_refused(cfg):
    d, h = stand()
    with pytest.raises(ValueError):
        hs.plot_year(rule(cfg, "spruce"), d, h, 1000.0, 40.0, line, 1.25, True)
    with pytest.raises(ValueError):
        hs.plot_year(rule(cfg, "pine_1995", scale_over="tallest"), d, h, 1000.0, 40.0, line, 1.25, True)


# -- in the model -----------------------------------------------------------------------------------------------------
PLOT = ("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=9000", "plot.natural_start.area_m2=20",
        "mortality.enabled=true", "plot.stand_measures=true")


def grow_plot(sp, years):
    plot = make_plot(sp, lean=True)
    for _ in range(years):
        plot.step()
    return plot


@pytest.mark.slow
def test_the_switch_off_changes_nothing_and_a_tree_outside_a_plot_is_unchanged_with_it_on():
    plain = species(*PLOT)
    gone = species(*PLOT)
    del gone.plot.height_status
    a, b = grow_plot(plain, 6), grow_plot(gone, 6)
    assert a.stats == b.stats and a.info == b.info and a.alive == b.alive
    assert {k: digest(a.trees[k]) for k in a.alive} == {k: digest(b.trees[k]) for k in b.alive}
    assert not hasattr(a, "_status_cfg") and all(getattr(a.trees[k], "_height_status", None) is None for k in a.alive)
    assert all("height_status" not in t for t in tree_list.tree_list(a)["trees"])

    def tree(*sets):
        sp, _ = load_species("betula_pendula")
        checkpoint.set_values(sp, list(sets))
        env, _ = load_environment("sweden_open_field")
        m = GrowthModel(sp, make_environment(env), 3, stand=True, soil=make_soil(env), lean=True)
        for _ in range(8):
            m.step()
        return m

    off, on = tree(), tree("plot.height_status.enabled=true", "plot.height_status.pine_1995.start_top_height_m=null")
    assert off.stats == on.stats and digest(off) == digest(on)


@pytest.mark.slow
@pytest.mark.parametrize("sets", [("plot.height_status.rule=\"pine_1995\"", "plot.height_status.pine_1995.start_top_height_m=null"),
                                  ("plot.height_status.rule=\"birch_2002\"", "plot.height_status.birch_2002.start_top_height_m=null",
                                   "plot.height_status.birch_2002.start_age_years=null")])
def test_with_the_switch_on_each_plot_tree_steps_by_its_status_not_its_draw(sets):
    sp = species(*PLOT, "plot.height_status.enabled=true", *sets)
    plot = make_plot(sp, lean=True)
    used = 0
    for _ in range(8):
        plot.step()
        for k in plot.alive:
            m = plot.trees[k]
            hd = getattr(m, "_hd", None)
            if hd is None or not logs.grew_this_year(m):
                continue
            # the step's multiplier is the status the plot set, not the draw over the dominants' draw
            assert hd["vigour"] == m._height_status
            used += 1
    assert used > 0
    rows = [s["height_status"] for s in plot.stats]
    assert any(r["started"] for r in rows) and all(r["rule"] == sp.plot.height_status.rule for r in rows)
    started = [r for r in rows if r["started"]]
    assert all(r["dominants_mean_modifier"] > 0.0 for r in started)
    doc = tree_list.tree_list(plot)
    json.dumps(doc)
    living = [t for t in doc["trees"] if t["alive"]]
    assert living and all(t["height_status"] is not None and t["height_modifier"] is not None for t in living)
    assert doc["height_status_year"] == plot._status_row
    assert all(math.isfinite(t["height_status"]) and t["height_status"] >= 0.0 for t in living)
