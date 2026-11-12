"""Death by standing (treegen/death_by_standing.py, mortality.rule birch_2002): Hynynen et al. 2002's survival model
(Eq. 47, Table 32) for each tree's yearly hazard, under the silver birch self-thinning line (Eq. 50, Table 34; Eqs. 52, 61).
Off by default: mortality.rule is crowding, today's rule.

No test here grows a tree.  The numbers are worked by hand from the report's own coefficients, the arithmetic written out
beside each one: Table 32 "Deciduous, SC1-8" a0 3.014, a1 0.1015, a2 -9.313, a3 0.4073; Table 34 silver birch b0 14.1979,
b1 -2.2178; Eq. 3 d_s = 2.0 + 1.25 d.
"""
from __future__ import annotations

import copy
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest

from treegen import checkpoint, damage, death_by_standing as dbs, logs
from treegen.params import load_species
from treegen.plot import Plot
from treegen.thinning import Mortality, over_bark_cm

A = (3.014, 0.1015, -9.313, 0.4073)


@pytest.fixture(scope="module")
def birch():
    sp, _ = load_species("betula_pendula")
    return sp


def cfg(birch, **sets):
    p = copy.deepcopy(birch.mortality.birch_2002)
    for k, v in sets.items():
        setattr(p, k, v)
    return p


def line(birch):
    return birch.plot.height_status.birch_2002


def p5(d, rdfl):
    return float(dbs.p5_from_logit(dbs.eq47_logit(2.0 + 1.25 * d, rdfl, *A)))


# -- the switch -----------------------------------------------------------------------------------------------------------
def test_the_switch_is_off_by_default_and_its_values_are_the_reports(birch):
    m = birch.mortality
    assert m.rule == "crowding" and m.rule in dbs.RULES and dbs.RULES[0] == "crowding"
    p = m.birch_2002
    assert (p.a0, p.a1, p.a2, p.a3) == A                                              # Table 32 p. 51, Deciduous SC1-8
    assert p.period_years == 5.0 and p.over_line == "evenly" and p.line_tangent_below_cm == 12.0   # pp. 50, 58, 56-57
    assert p.line_every_years == 1 and p.line_cut_limit is None
    assert p.start_age_years == 12.0 and p.start_top_height_m is None
    assert (p.data_age_years, p.data_top_height_m, p.data_stems_per_ha) == ([17.0, 50.0], [12.3, 22.4], [370.0, 3051.0])   # p. 24
    # the line and the stump diameter are the height rule's own values: one copy for both rules
    b = line(birch)
    assert (b.self_thinning_b0, b.self_thinning_b1, b.stump_a_cm, b.stump_b) == (14.1979, -2.2178, 2.0, 1.25)


# -- Eq. 47, by hand ------------------------------------------------------------------------------------------------------
def test_eq47_against_trees_worked_by_hand():
    # small, alone: d 3 cm, d_s 2.0 + 3.75 = 5.75; x = 3.014 + 0.1015 x 5.75 = 3.014 + 0.583625 = 3.597625; exp(x) = 36.511417;
    # p5 = 1 / 37.511417 = 0.026659
    assert dbs.eq47_logit(5.75, 0.0, *A) == pytest.approx(3.597625, abs=1e-9)
    assert p5(3.0, 0.0) == pytest.approx(0.026659, abs=1e-6)
    # small, under larger trees: RDFL 0.8: x = 3.597625 - 9.313 x 0.8 + 0.4073 x 5.75 x 0.8 = 3.597625 - 7.4504 + 1.87358 = -1.979195;
    # exp(x) = 0.138180; p5 = 1 / 1.138180 = 0.878595
    assert dbs.eq47_logit(5.75, 0.8, *A) == pytest.approx(-1.979195, abs=1e-9)
    assert p5(3.0, 0.8) == pytest.approx(0.878595, abs=1e-6)
    # middling: d 10 cm, d_s 14.5, RDFL 0.4: x = 3.014 + 1.47175 - 3.7252 + 2.36234 = 3.12289; exp(x) = 22.711922; p5 = 0.042173
    assert p5(10.0, 0.4) == pytest.approx(0.042173, abs=1e-6)
    # large, past 16.7 cm, a dominant: d 20 cm, d_s 27.0, RDFL 0: x = 3.014 + 2.7405 = 5.7545; exp(x) = 315.607704; p5 = 0.003158
    assert p5(20.0, 0.0) == pytest.approx(0.003158, abs=1e-6)
    # the same tree with larger trees around, RDFL 0.5: x = 5.7545 - 4.6565 + 0.4073 x 27 x 0.5 (5.49855) = 6.59655;
    # exp(x) = 732.563481; p5 = 0.001363: LOWER than with none above it (the sign change)
    assert p5(20.0, 0.5) == pytest.approx(0.001363, abs=1e-6)
    # large: d 30 cm, d_s 39.5, RDFL 0.2: x = 3.014 + 4.00925 - 1.8626 + 3.21767 = 8.37832; p5 = 1 / 4352.691939 = 0.000230
    assert p5(30.0, 0.2) == pytest.approx(0.000230, abs=1e-6)


def test_the_crowding_term_changes_sign_past_dbh_16_7_cm(birch):
    # (a2 + a3 d_s) RDFL is negative while d_s < 9.313 / 0.4073 = 22.865210 cm, DBH (22.865210 - 2.0) / 1.25 = 16.692168 cm
    assert dbs.flip_dbh_cm(birch.mortality.birch_2002, line(birch)) == pytest.approx(16.692168, abs=1e-6)
    assert p5(12.0, 0.4) > p5(12.0, 0.0)          # under it: more larger trees, more likely to die
    assert p5(20.0, 0.5) < p5(20.0, 0.0)          # past it: less likely (worked above: 0.001363 against 0.003158)
    assert p5(16.692168, 0.9) == pytest.approx(p5(16.692168, 0.0), rel=1e-6)   # at it: RDFL has no effect


# -- the yearly hazard ------------------------------------------------------------------------------------------------------
def test_the_yearly_hazard_from_the_five_year_chance():
    # d 3 cm, RDFL 0.8: p5 0.878595; h = -ln(1 - 0.878595) / 5 = -ln(0.121405) / 5 = 2.108623 / 5 = 0.421725 a year;
    # a year's chance 1 - exp(-0.421725) = 0.344086
    x = dbs.eq47_logit(5.75, 0.8, *A)
    h = float(dbs.yearly_hazard(x, 5.0))
    assert h == pytest.approx(0.421725, abs=1e-6)
    assert 1.0 - math.exp(-h) == pytest.approx(0.344086, abs=1e-6)
    # five years of it give the five-year chance back, and both ways of writing it agree
    assert 1.0 - math.exp(-5.0 * h) == pytest.approx(0.878595, abs=1e-6)
    xs = np.array([-8.0, -2.0, 0.0, 3.6, 8.4, 20.0])
    assert np.allclose(dbs.yearly_hazard(xs, 5.0), dbs.hazard_from_p5(dbs.p5_from_logit(xs), 5.0), rtol=1e-8, atol=0.0)
    assert np.all(np.isfinite(dbs.yearly_hazard(np.array([-800.0, 800.0]), 5.0)))     # no overflow at the ends
    # d 20 cm, RDFL 0: p5 0.003158; h = 0.000633 a year
    assert float(dbs.yearly_hazard(dbs.eq47_logit(27.0, 0.0, *A), 5.0)) == pytest.approx(0.000633, abs=1e-6)


# -- the line ---------------------------------------------------------------------------------------------------------------
def test_the_line_and_its_tangent_under_12_cm_by_hand(birch):
    b = line(birch)
    # D_gs 20: ln 20 = 2.995732; 14.1979 - 2.2178 x 2.995732 = 7.554034; exp = 1908.29 stems/ha
    assert dbs.line_stems_ha(20.0, b, 12.0) == pytest.approx(1908.294, abs=0.01)
    # D_gs 12: 14.1979 - 2.2178 x 2.484907 = 8.686904; exp = 5924.63.  Under it the tangent: at 8, 5924.63 x (1 + 2.2178 x 4 / 12)
    # = 5924.63 x 1.739267 = 10304.52 (the curve itself would give 14561.18)
    assert dbs.line_stems_ha(12.0, b, 12.0) == pytest.approx(5924.633, abs=0.01)
    assert dbs.line_stems_ha(8.0, b, 12.0) == pytest.approx(10304.517, abs=0.01)
    assert dbs.line_stems_ha(8.0, b, None) == pytest.approx(14561.183, abs=0.01)
    assert dbs.line_stems_ha(11.999999, b, 12.0) == pytest.approx(dbs.line_stems_ha(12.000001, b, 12.0), rel=1e-6)
    # D_g weighted by basal area: (1000 + 8000) / (100 + 400) = 18.0; with weights 1 and 0.5: (1000 + 4000) / (100 + 200) = 16.6667
    assert dbs.dg_weighted_cm([10.0, 20.0, 0.0], [1.0, 1.0, 1.0]) == pytest.approx(18.0)
    assert dbs.dg_weighted_cm([10.0, 20.0, 0.0], [1.0, 0.5, 1.0]) == pytest.approx(16.666667, abs=1e-6)


def uniform(n=150, d=20.0, h=18.0):
    return np.full(n, d), np.full(n, h)


@pytest.mark.parametrize("over", ["evenly", "by_odds"])
def test_the_cap_on_an_even_stand_over_the_line_by_hand(birch, over):
    # 150 trees of DBH 20 cm on 1000 m2, 1500/ha.  Equal DBHs don't count each other: RDFL 0, so each has x = 5.7545 and
    # h = ln(1 + exp(-5.7545)) / 5 = 0.000633 a year.  D_g 20, D_gs 27: ln 27 = 3.295837; 14.1979 - 2.2178 x 3.295837 = 6.888393;
    # N_max = 980.824/ha, 98.0824 trees here.  Expected survivors 150 exp(-0.000633) = 149.9051.
    # evenly: added hazard ln(149.9051 / 98.0824) = 0.424195; each tree's total h + 0.424195 = 0.424827 = ln(150 / 98.0824).
    # by odds: on an even stand each tree must live with 98.0824 / 150, so its total is the same 0.424827; its five-year chance
    # 1 - (98.0824 / 150)^5 = 0.880464, odds 7.365674 against exp(-5.7545) = 0.0031685: k = 2324.66, ln k = 7.751331.
    d, h = uniform()
    state = {}
    out = dbs.plot_year(cfg(birch, over_line=over), line(birch), d, h, np.zeros(len(d)), 1000.0, 40.0, state)
    row, hz = out["row"], out["hazards"]
    assert out["started"] and row["line_binds"] and row["line_stems_ha"] == pytest.approx(980.824, abs=0.001)
    assert row["stems_ha"] == 1500.0 and row["line_share"] == pytest.approx(1500.0 / 980.824, rel=1e-5)
    total = hz["competition"] + hz["self-thinning line"] + hz["old age"]
    assert np.allclose(total, 0.424827, atol=1e-6)
    assert float(np.sum(np.exp(-total))) == pytest.approx(98.0824, abs=1e-3)       # expected survivors on the line
    if over == "evenly":
        assert row["line_added_hazard"] == pytest.approx(0.424195, abs=1e-6) and row["line_ln_k"] == 0.0
    else:
        assert row["line_ln_k"] == pytest.approx(7.751331, abs=1e-5) and row["line_added_hazard"] == 0.0
    # the line added 149.9051 - 98.0824 = 51.8227 deaths, expected
    assert row["line_added_deaths_expected"] == pytest.approx(51.8227, abs=1e-3)
    assert out["trees"]["raised"] == [1] * 150


def mixed():
    """60 trees of 25 cm and 90 of 8 cm on 1000 m2: well over the line."""
    d = np.array([25.0] * 60 + [8.0] * 90)
    h = np.where(d > 10.0, 20.0, 12.0)
    return d, h


def test_the_cap_evenly_and_by_odds_on_a_mixed_stand(birch):
    d, h = mixed()
    got = {}
    for over in ("evenly", "by_odds"):
        out = dbs.plot_year(cfg(birch, over_line=over), line(birch), d, h, np.zeros(len(d)), 1000.0, 40.0, {})
        hz, row = out["hazards"], out["row"]
        total = hz["competition"] + hz["self-thinning line"]
        assert row["line_binds"]
        # both bring the expected survivors to the line's stems, in trees on the plot (the record holds it to 0.001/ha)
        assert float(np.sum(np.exp(-total))) == pytest.approx(row["line_stems_ha"] / 10.0, abs=1e-4)
        got[over] = hz["self-thinning line"]
    even, odds = got["evenly"], got["by_odds"]
    assert np.allclose(even, even[0]) and even[0] > 0.0                    # the same added hazard for every tree
    assert odds[-1] > odds[0] > 0.0                                         # by odds: the small trees are raised more
    # by odds, the large trees die less than evenly, the small more
    assert odds[0] < even[0] < odds[-1]


def test_under_the_line_eq47_acts_alone(birch):
    d = np.array([25.0] * 20 + [8.0] * 20)                                  # 400/ha, far under the line
    out = dbs.plot_year(cfg(birch), line(birch), d, np.full(40, 15.0), np.zeros(40), 1000.0, 40.0, {})
    assert out["started"] and not out["row"]["line_binds"]
    assert np.all(out["hazards"]["self-thinning line"] == 0.0) and out["trees"]["raised"] == [0] * 40
    assert out["row"]["line_added_deaths_expected"] == 0.0


def test_the_cut_limit_and_the_years_between_checks(birch):
    d, h = uniform()
    # line_cut_limit 1.5: stems 1500/ha now, the line 980.824 now and 1100 at the last check: the most the line may take
    # brings stems to 1500 - 1.5 x (1100 - 980.824) = 1321.236/ha
    out = dbs.plot_year(cfg(birch, line_cut_limit=1.5), line(birch), d, h, np.zeros(150), 1000.0, 40.0,
                        {"started": True, "start_year": 12.0, "line_prev": 1100.0})
    assert out["row"]["line_target_ha"] == pytest.approx(1321.236, abs=1e-3)
    total = out["hazards"]["competition"] + out["hazards"]["self-thinning line"]
    assert float(np.sum(np.exp(-total))) == pytest.approx(132.1236, abs=1e-3)
    # every 5 years from the start at 12: checked at 17, not at 13
    five = cfg(birch, line_every_years=5)
    st = {"started": True, "start_year": 12.0, "line_prev": None}
    assert not dbs.plot_year(five, line(birch), d, h, np.zeros(150), 1000.0, 13.0, st)["row"]["line_check"]
    assert dbs.plot_year(five, line(birch), d, h, np.zeros(150), 1000.0, 17.0, st)["row"]["line_binds"]


# -- the start --------------------------------------------------------------------------------------------------------------
def test_the_start_gate(birch):
    d, h = mixed()
    st = {}
    before = dbs.plot_year(cfg(birch), line(birch), d, h, np.zeros(150), 1000.0, 11.0, st)
    assert not before["started"] and before["hazards"] is None and before["trees"] is None
    assert before["row"]["line_stems_ha"] > 0.0 and st["line_prev"] == pytest.approx(before["row"]["line_stems_ha"], abs=1e-3)   # read, not acted on
    assert dbs.plot_year(cfg(birch), line(birch), d, h, np.zeros(150), 1000.0, 12.0, st)["started"] and st["start_year"] == 12.0
    # once started it stays on
    assert dbs.plot_year(cfg(birch, start_age_years=99.0), line(birch), d, h, np.zeros(150), 1000.0, 13.0, st)["started"]
    # the data's top height as a condition: a stand of 12-20 m tops reaches 12.3 m, one of 5 m doesn't
    tall = cfg(birch, start_top_height_m=12.3)
    assert dbs.plot_year(tall, line(birch), d, h, np.zeros(150), 1000.0, 20.0, {})["started"]
    assert not dbs.plot_year(tall, line(birch), d, np.full(150, 5.0), np.zeros(150), 1000.0, 20.0, {})["started"]
    # outside the survival data: at 11 years only its age is (1,500/ha and a 20 m top are inside 370-3,051 and 12.3-22.4 m)
    row = before["row"]
    assert row["outside_data"] == ["age"] and row["stems_ha"] == 1500.0


def test_the_records_say_where_the_data_end(birch):
    p = cfg(birch)
    assert dbs.outside_data(p, 30.0, 18.0, 1000.0) == []
    assert dbs.outside_data(p, 55.0, 23.1, 474.0) == ["age", "top_height"]
    assert dbs.outside_data(p, 16.0, 11.0, 6474.0) == ["age", "top_height", "stems"]
    d = np.array([25.0] * 60 + [8.0] * 90)
    row = dbs.plot_year(p, line(birch), d, np.full(150, 20.0), np.zeros(150), 1000.0, 40.0, {})["row"]
    assert row["past_flip_share"] == 0.4 and row["flip_dbh_cm"] == pytest.approx(16.6922, abs=1e-4)


# -- a tree with no DBH -----------------------------------------------------------------------------------------------------
def test_a_tree_with_no_dbh(birch):
    # 10 trees of 20 cm and one with none on 100 m2 (100 stems/ha a tree): its d_s is 2.0 (Eq. 3 at d 0) and every tree with a
    # DBH is above it: RDFL = 10 x 100 / 980.824 = 1.019551.  x = 3.014 + 0.203 - 9.313 x 1.019551 + 0.4073 x 2 x 1.019551
    # = -5.447552; p5 = 0.995712; h = -ln(0.004288) / 5 = 1.090370 a year
    d = np.array([20.0] * 10 + [0.0])
    h = np.array([18.0] * 10 + [1.1])
    out = dbs.plot_year(cfg(birch), line(birch), d, h, np.zeros(11), 100.0, 30.0, {})
    assert out["trees"]["rdfl"][-1] == pytest.approx(1.019551, abs=1e-5)       # the record holds six figures
    assert out["hazards"]["competition"][-1] == pytest.approx(1.090370, abs=1e-6)
    # it isn't counted in the line's stems, and the line never raises it: 10 trees, 1000/ha against 980.8, binds
    assert out["row"]["stems_ha"] == 1000.0 and out["row"]["trees_no_dbh"] == 1 and out["row"]["line_binds"]
    assert out["hazards"]["self-thinning line"][-1] == 0.0 and out["hazards"]["self-thinning line"][0] > 0.0


def test_a_choice_that_doesnt_exist_is_refused(birch):
    d, h = mixed()
    with pytest.raises(ValueError):
        dbs.plot_year(cfg(birch, over_line="sideways"), line(birch), d, h, np.zeros(150), 1000.0, 40.0, {})


def test_the_draw_repeats_and_picks_causes_by_hazard():
    hz = {"competition": np.array([0.0, 50.0, 0.0, 0.2]), "self-thinning line": np.array([0.0, 0.0, 50.0, 0.2]),
          "old age": np.zeros(4)}
    a = dbs.draw(hz, np.random.default_rng([3, 5381]))
    assert a == dbs.draw(hz, np.random.default_rng([3, 5381]))
    got = dict(a)
    assert 0 not in got and got[1] == "competition" and got[2] == "self-thinning line"


# -- in the plot, with no tree grown ----------------------------------------------------------------------------------------
class Tree:
    """What Plot._self_thin reads of a tree: its wood DBH, its age and its last height."""

    def __init__(self, d_cm, age, h):
        self.d, self.year, self.stats = d_cm, age, [{"height_m": h}]

    def dbh_m(self):
        return None if self.d <= 0.0 else self.d / 100.0


def bare_plot(sp, year, seed=7, n=400, log=False):
    """A plot made by hand, its trees fixed, with the mortality the plot would make: only what _self_thin and _finish read."""
    sp = copy.deepcopy(sp)
    checkpoint.set_values(sp, ["mortality.enabled=true"] + (["log.stand=true"] if log else []))
    rng = np.random.default_rng(seed)
    plot = Plot.__new__(Plot)
    plot.species, plot.year, plot.area, plot.L = sp, year, 1000.0, math.sqrt(1000.0)
    plot.cell = (-plot.L / 2, -plot.L / 2, 32, 32)
    d = np.round(np.abs(rng.normal(9.0, 4.0, n)), 2)
    d[:3] = 0.0
    plot.trees = [Tree(float(d[k]), year - int(rng.integers(0, 4)), 1.3 + 0.9 * float(d[k])) for k in range(n)]
    plot.info = [{"id": k, "x": float(rng.uniform(-15, 15)), "y": float(rng.uniform(-15, 15))} for k in range(n)]
    plot.alive = list(range(n))
    plot.on_finish, plot.measures = None, False
    plot.mort = Mortality(sp.mortality, plot.L, plot.L, plot.cell[0], plot.cell[1], sp.damage.old_age)
    plot.mort.old_age_elsewhere = damage._is_on(sp) and bool(sp.damage.old_age.enabled)
    plot.mort_rng = np.random.default_rng([seed, 5381])
    plot.rings = {k: [0.0, max(float(d[k]) - 0.4, 0.0)] for k in range(n)}
    if log:
        plot._log_death = lambda k, cause: None      # a tree's record reads a grown tree; this one has none
    return plot


def todays_deaths(plot):
    """Today's rule by hand: the hazards and the draw of treegen/thinning.py, as Plot._self_thin calls them."""
    M = plot.mort
    now = list(plot.alive)
    d = np.array([plot._dbh(k) * 100.0 for k in now])
    rings = np.zeros(len(now))
    for n, k in enumerate(now):
        hist = list(plot.rings[k])
        if d[n] <= 0.0:
            hist = [0.0]
        else:
            hist = (hist + [float(d[n])])[-(int(M.p.vigour.window_years) + 1):]
        rings[n] = M.ring_mm(hist)
    xy = np.array([[plot.info[k]["x"], plot.info[k]["y"]] for k in now])
    age = np.array([plot.trees[k].year for k in now], float)
    hz = M.hazards(xy, d, rings, age, float(plot.year))
    return [(now[n], cause) for n, cause in M.draw(hz, copy.deepcopy(plot.mort_rng))]


def deaths_of(plot):
    before = list(plot.alive)
    plot._self_thin(before)
    return [(k, plot.info[k]["cause"]) for k in before if k not in plot.alive]


def test_switched_off_the_plot_takes_todays_code_path(birch):
    plot = bare_plot(birch, 20)
    assert plot.species.mortality.rule == "crowding"
    want = todays_deaths(plot)
    got = deaths_of(plot)
    assert want and sorted(got) == sorted(want)
    assert {c for _, c in got} <= {"self-thinned", "suppressed", "background", "old age"}


def test_before_its_start_the_rule_kills_as_today_and_after_it_by_eq47(birch):
    sp = copy.deepcopy(birch)
    checkpoint.set_values(sp, ['mortality.rule="birch_2002"'])
    early = bare_plot(sp, 11, log=True)
    want = todays_deaths(early)
    assert sorted(deaths_of(early)) == sorted(want)                         # year 11, before the start at 12: today's
    rec = early.stand_log[-1]["death_rule"]
    assert not rec["started"] and "trees" not in rec and rec["line_stems_ha"] > 0.0
    late = bare_plot(sp, 30, log=True)
    d5 = late.trees[5].d
    got = deaths_of(late)
    assert got and {c for _, c in got} <= set(dbs.CAUSES)
    rec = late.stand_log[-1]["death_rule"]
    assert rec["started"] and sum(rec["deaths"].values()) == len(got)
    assert rec["trees"]["id"] == list(range(400)) and len(rec["trees"]["hazard"]) == 400 and rec["line_binds"]
    assert rec["trees"]["d_cm"][0] == 0.0 and rec["trees"]["d_cm"][5] == round(float(over_bark_cm(d5, late.mort.bark)), 2)
    json.dumps(late.stand_log)
    # with the log off nothing is kept, and the deaths are the same
    quiet = bare_plot(sp, 30, log=False)
    assert deaths_of(quiet) == got and not hasattr(quiet, "stand_log")
    assert set(rec) - {"deaths", "trees"} <= set(dbs.RECORD_WHAT)
    assert logs.on(late.species, "stand") and not logs.on(quiet.species, "stand")
