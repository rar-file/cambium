"""Old age, wind and snow (treegen/damage.py): the functions against the papers' own numbers, and off by
default.  Trees here are grown a few years at most; no plot is run."""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from treegen import damage
from treegen.damage import TreeState, Weather
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import load_environment, load_species, option_values

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))


@pytest.fixture()
def sp():
    s, _ = load_species("betula_pendula")
    s.damage.enabled = s.damage.wind.enabled = s.damage.snow.enabled = s.damage.old_age.enabled = True
    return s


def mean_tree(sp, **k) -> TreeState:
    """The mean tree of Kitenberga's Table 2: 57 years, 1,128 stems/ha, 27.5 m2/ha (so 17.6 cm), H/D 1."""
    f = sp.damage.dbh_over_bark_factor
    d = dict(age=57, height_m=17.6, dbh_cm=17.6 / f, stems_per_ha=1128.0, basal_area_m2_ha=27.5, crown_base_m=8.0, crown_width_m=4.0)
    d.update(k)
    return TreeState(**d)


# -- off by default ------------------------------------------------------------
def test_everything_is_off_by_default_and_off_leaves_the_golden_hash_alone():
    from golden import strip_metadata

    s, _ = load_species("betula_pendula")
    opts = {k: v for k, v in option_values(s).items() if k.startswith("damage.")}
    assert opts and all(v is False for v in opts.values())
    assert "damage.enabled" in opts
    # the hash leaves out options that are off
    assert not [k for k in strip_metadata({"options": opts})["options"]]
    assert damage.assess_year(mean_tree(s), Weather(True, 0.0, 40.0), s, np.random.default_rng(1)) is None


def test_off_means_a_model_and_a_plot_are_not_touched():
    s, _ = load_species("betula_pendula")
    m = SimpleNamespace(sp=s, stats=[{}], seed=1)
    assert damage.tree_year(m, 1) is None and not hasattr(m, "damage_log") and not hasattr(m, "_damage_rng")
    p = SimpleNamespace(species=s, seed=1)
    assert damage.plot_year(p, []) == [] and not hasattr(p, "_damage_rng")


# -- old age -------------------------------------------------------------------
def test_old_age_gives_elfvings_worked_example_for_pine():
    """Elfving 2010 p. 68: pine, A 300, SIS 20: AMAX 449.58, p 0.11999 and 0.13481, 5 years 0.01684."""
    oa = SimpleNamespace(amax_b0=5.1650, amax_b1=-0.04526, amax_b2=0.2007, amax_n=10000, site_index_sis_m=20.0,
                         ageing_a=10.0, ageing_b=12.0, years_to_breast_height=0.0)
    assert damage.max_age_years(oa) == pytest.approx(449.58, abs=0.01)
    p300, p305 = damage.share_dead_of_age(300, oa), damage.share_dead_of_age(305, oa)
    assert p300 == pytest.approx(0.11999, abs=1e-4) and p305 == pytest.approx(0.13481, abs=1e-4)
    assert (p305 - p300) / (1 - p300) == pytest.approx(0.01684, abs=1e-4)
    survive = 1.0
    for a in range(300, 305):
        survive *= 1.0 - damage.old_age_hazard(a, oa)
    assert 1.0 - survive == pytest.approx(0.01684, abs=1e-4)


def test_birch_max_age_is_about_300_years_at_sis_24_and_rarely_kills_before_100(sp):
    oa = copy.copy(sp.damage.old_age)
    oa.site_index_sis_m = 24.0
    assert damage.max_age_years(oa) == pytest.approx(300.0, abs=2.0)
    assert damage.old_age_hazard(60, sp.damage.old_age) < 1e-4
    assert damage.share_dead_of_age(100, sp.damage.old_age) < 0.01
    assert 0.3 < damage.share_dead_of_age(240, sp.damage.old_age) < 0.7   # 240 rings: the oldest birch sampled


# -- wind ----------------------------------------------------------------------
@pytest.mark.parametrize("age, read", [(11, 0.3), (100, 1.4), (150, 3.4), (216, 10.4)])
def test_wind_reads_kitenbergas_fig_2(sp, age, read):
    sp.damage.wind.population_offset = 0.0
    assert 100 * damage.wind_damage_probability(mean_tree(sp, age=age), sp.damage) == pytest.approx(read, rel=0.15)


@pytest.mark.parametrize("hd, read", [(0.5, 0.3), (1.0, 0.68), (1.5, 1.6), (1.93, 3.3)])
def test_wind_reads_kitenbergas_fig_1(sp, hd, read):
    sp.damage.wind.population_offset = 0.0
    p = damage.wind_damage_probability(mean_tree(sp, height_m=17.6 * hd), sp.damage)
    assert 100 * p == pytest.approx(read, rel=0.2)


def test_wind_population_offset_brings_the_mean_tree_to_the_observed_damage(sp):
    # her soil mix (Table 2) and 5 % of trees with prior damage, on top of the mean tree
    x = -5.03 + 0.09 * 0.75 + 0.21 * 0.32 + 0.18 * 0.94 + 0.05 * 1.46 + sp.damage.wind.population_offset
    assert 2.9 <= 100 * math.exp(x) / (1 + math.exp(x)) <= 3.4


def test_wind_prior_damage_and_limits(sp):
    dp = sp.damage
    a = damage.wind_damage_probability(mean_tree(sp), dp)
    b = damage.wind_damage_probability(mean_tree(sp, prior_damage=True), dp)
    assert (b / (1 - b)) / (a / (1 - a)) == pytest.approx(4.32, rel=0.01)    # her odds ratio
    # kept inside her data's range, and nothing below 14 cm
    assert damage.wind_damage_probability(mean_tree(sp, age=1000), dp) == damage.wind_damage_probability(mean_tree(sp, age=216), dp)
    assert damage.wind_damage_probability(mean_tree(sp, dbh_cm=5.0), dp) == 0.0
    assert damage.wind_damage_probability(mean_tree(sp, dbh_cm=None), dp) == 0.0


def test_storm_years_keep_the_periods_damage(sp):
    """Whatever the storms' spacing, a tree's chance per period stays the model's."""
    state = mean_tree(sp)
    rng = np.random.default_rng(7)
    sp.damage.snow.enabled = False
    hits, trees = 0, 200_000
    years = 5
    for _ in range(trees // 1000):
        for _year in range(years):
            w = damage.draw_weather(rng, sp.damage)
            if w.storm:
                hits += int((rng.random(1000) < damage.storm_hit_probability(state, sp.damage)).sum())
    assert hits / trees == pytest.approx(damage.wind_damage_probability(state, sp.damage), rel=0.25)


def test_weather_doesnt_depend_on_which_parts_are_on(sp):
    a = [damage.draw_weather(r, sp.damage) for r in [np.random.default_rng(3)] * 20]
    sp.damage.snow.enabled = False
    b = [damage.draw_weather(r, sp.damage) for r in [np.random.default_rng(3)] * 20]
    assert [w.storm for w in a] == [w.storm for w in b] and [w.wind_from_deg for w in a] == [w.wind_from_deg for w in b]


# -- how a tree fails ----------------------------------------------------------
def test_the_trees_wind_takes_uproot_about_a_third_of_the_time(sp):
    """Kitenberga p. 6: 31 % and 35 % uprooted.  The trees wind took on plots with paid roots: root moment 1.12 x the stem's."""
    tree = mean_tree(sp)
    stem = damage.stem_breaking_moment_knm(tree.dbh_cm, sp.damage.failure.mor_green_mpa)
    tree.anchorage = {"critical_turning_moment": {"by_wind_dir_knm": {"0": 1.12 * stem}}}
    assert 0.31 <= damage.uproot_probability(tree, 0.0, sp) <= 0.35


def test_slender_trees_snap_and_stout_or_shallow_rooted_ones_uproot(sp):
    """Zubizarreta-Gerendiain et al. 2012 pp. 187, 193: uprooted Scots pines have the lower H/D (too few
    birches to compare); shallow soils uproot."""
    slender = damage.uproot_probability(mean_tree(sp, height_m=25.0), 0.0, sp)
    stout = damage.uproot_probability(mean_tree(sp, height_m=12.0), 0.0, sp)
    assert slender < stout
    deep = mean_tree(sp, anchorage={"critical_turning_moment": {"by_wind_dir_knm": {"0": 40.0, "180": 10.0}}})
    assert damage.uproot_probability(deep, 180.0, sp) > damage.uproot_probability(deep, 0.0, sp)


def test_breaking_moment_goes_with_the_cube_of_diameter():
    """Nykanen p. 195; a 30 cm stem at 44 MPa."""
    assert damage.stem_breaking_moment_knm(30.0, 44.0) == pytest.approx(math.pi / 32 * 0.3 ** 3 * 44e3)
    assert damage.stem_breaking_moment_knm(40.0, 44.0) / damage.stem_breaking_moment_knm(20.0, 44.0) == pytest.approx(8.0)


def test_uprooting_moment_falls_back_to_krisans_regression_without_roots(sp):
    """Krisans' two site means (0.67 m3, 46.9 kN m; 1.43 m3, 154.3 kN m) straddle the regression."""
    a = damage.uprooting_moment_knm(TreeState(87, 29.1, 25.5), 0.0, sp)
    b = damage.uprooting_moment_knm(TreeState(87, 32.8, 35.0), 0.0, sp)
    assert a == pytest.approx(101 * 0.67, rel=0.02) and b == pytest.approx(101 * 1.43, rel=0.02)
    assert 46.9 < a and b < 154.3


def test_snap_heights_follow_her_table_3_and_fig_4(sp):
    rng = np.random.default_rng(1)
    plain = np.array([damage.snap_height_m(mean_tree(sp, height_m=20.0, dbh_cm=20.0 / sp.damage.dbh_over_bark_factor), sp.damage, rng) for _ in range(4000)]) / 20.0
    hurt = np.array([damage.snap_height_m(mean_tree(sp, height_m=20.0, dbh_cm=20.0 / sp.damage.dbh_over_bark_factor, prior_damage=True), sp.damage, rng) for _ in range(4000)]) / 20.0
    assert plain.mean() == pytest.approx(0.435, abs=0.02)      # 0.532 - 0.097
    assert hurt.mean() == pytest.approx(0.345, abs=0.02)
    assert (plain < 0.4).mean() == pytest.approx(0.54, abs=0.08)
    # 61 % against her 73 %: her Table 3 puts the damaged trees' mean at 0.345, her Fig. 4 at about 0.31
    assert (hurt < 0.4).mean() == pytest.approx(0.73, abs=0.13)
    assert (hurt < 0.4).mean() > (plain < 0.4).mean()


def test_a_stem_broken_below_the_crown_or_left_with_too_few_leaves_dies(sp):
    """Nykanen p. 195 for the crown; TUNED for the leaves.  Leaves evenly from 8 m to 17.6 m: half are above 12.8 m."""
    wind = Weather(True, 90.0, 0.0)
    fates = {}
    for seed in range(600):
        s = mean_tree(sp, crown_base_m=8.0, prior_damage=True, age=216)
        e = damage._failure(s, wind, sp, np.random.default_rng(seed), "wind")
        if e.snap_height_m is not None:
            fates[e.fatal] = fates.get(e.fatal, []) + [e.snap_height_m]
        else:
            assert e.fatal and e.plate
    assert max(fates[True]) < 12.8 <= min(fates[False])
    # the tree's own leaves, when known, decide instead
    e = damage._failure(mean_tree(sp, crown_base_m=1.0, anchorage={"critical_turning_moment": {"by_wind_dir_knm": {"0": 1e6}}}),
                        wind, sp, np.random.default_rng(3), "wind", share_above=lambda z: 0.9)
    assert e.snap_height_m is not None and e.fatal
    e = damage._failure(mean_tree(sp, crown_base_m=1.0, anchorage={"critical_turning_moment": {"by_wind_dir_knm": {"0": 1e6}}}),
                        wind, sp, np.random.default_rng(3), "wind", share_above=lambda z: 0.1)
    assert e.snap_height_m is not None and not e.fatal


# -- snow ----------------------------------------------------------------------
def test_a_birch_at_taper_1_120_stands_60_kg(sp):
    """Nykanen Fig. 2, from Peltola et al. 1997."""
    tree = TreeState(40, 12.0, 10.0 / sp.damage.dbh_over_bark_factor, crown_base_m=6.0, crown_width_m=2.0, crown_wood_kg=30.0)
    assert damage.snow_overload_probability(tree, 60.0, sp) < 0.1


def test_risk_falls_with_taper_and_crown_depth(sp):
    """Nykanen Fig. 3: three trees of 15 m, 15 / 20 / 30 cm, crowns 30 / 50 / 95 %."""
    ratios = [damage.snow_loading(TreeState(40, 15.0, d, crown_base_m=15.0 * (1.0 - c), crown_width_m=2.5, crown_wood_kg=30.0), 60.0, sp)[0]
              for d, c in ((15, 0.3), (20, 0.5), (30, 0.95))]
    assert ratios[0] > ratios[1] > ratios[2]


def test_an_off_centre_crown_is_at_more_risk(sp):
    """Nykanen p. 201: asymmetric crowns."""
    a = TreeState(40, 15.0, 15.0, crown_base_m=8.0, crown_width_m=3.0, crown_offset_m=0.0)
    b = TreeState(40, 15.0, 15.0, crown_base_m=8.0, crown_width_m=3.0, crown_offset_m=1.5)
    assert damage.snow_loading(b, 40.0, sp)[0] > damage.snow_loading(a, 40.0, sp)[0]


def test_a_thin_stem_that_cant_carry_it_is_overloaded_and_a_stand_tree_isnt(sp):
    thin = TreeState(40, 21.4, 7.5, crown_base_m=12.0, crown_width_m=2.0, crown_wood_kg=5.0)
    assert damage.snow_loading(thin, 60.0, sp)[1] < 1.0
    assert damage.snow_overload_probability(thin, 60.0, sp) == 1.0
    stand = TreeState(60, 26.0, 29.0, crown_base_m=7.0, crown_width_m=3.5, crown_wood_kg=120.0)
    assert damage.snow_overload_probability(stand, 60.0, sp) < 0.01


def test_an_overloaded_stem_bends_and_few_break(sp):
    """Donis 2024: 93.7 % of damaged trees were bent, so even a stand all overloaded loses few to the snow."""
    snow = Weather(False, 0.0, 60.0)
    sp.damage.old_age.enabled = False
    thin = TreeState(9, 12.0, 3.0, crown_base_m=3.0, crown_width_m=4.0, crown_wood_kg=2.0)
    assert damage.snow_overload_probability(thin, 60.0, sp) == 1.0
    rng = np.random.default_rng(1)
    causes = [damage.assess_year(thin, snow, sp, rng).cause for _ in range(4000)]
    assert causes.count("snow bend") / 4000 == pytest.approx(0.937, abs=0.015)
    assert set(causes) <= {"snow bend", "snow snap", "snow uproot"}


def test_no_tree_holds_more_snow_than_falls_on_its_share_of_the_ground(sp):
    wide = TreeState(30, 16.0, 8.0, crown_base_m=4.0, crown_width_m=4.0, crown_wood_kg=5.0)
    packed = TreeState(30, 16.0, 8.0, crown_base_m=4.0, crown_width_m=4.0, crown_wood_kg=5.0, stems_per_ha=4000.0)      # 2.5 m2 each against 12.6
    roomy = TreeState(30, 16.0, 8.0, crown_base_m=4.0, crown_width_m=4.0, crown_wood_kg=5.0, stems_per_ha=100.0)
    assert damage.snow_loading(packed, 60.0, sp)[1] > damage.snow_loading(wide, 60.0, sp)[1]
    assert damage.snow_loading(roomy, 60.0, sp)[1] == damage.snow_loading(wide, 60.0, sp)[1]


# -- pit and mound -------------------------------------------------------------
def _plate(sp, az=0.0):
    s = TreeState(80, 25.0, 30.0, anchorage={"plate_radius_m": 0.9, "plate_depth_m": 0.55, "plate_soil_mass_kg": 1000.0}, x_m=2.0, y_m=-3.0)
    return damage.root_plate(s, az, sp)


def test_the_mound_holds_the_soil_the_pit_lost(sp):
    p = _plate(sp, 30.0)
    g = np.linspace(-8.0, 8.0, 801)
    xx, yy = np.meshgrid(g + p["x_m"], g + p["y_m"], indexing="ij")
    relief = damage.ground_relief(np.stack([xx.ravel(), yy.ravel()], 1), [p], [0], 20.0)
    cell = (g[1] - g[0]) ** 2
    assert relief[relief < 0].sum() * cell == pytest.approx(-p["pit_volume_m3"], rel=0.02)
    assert relief[relief > 0].sum() * cell == pytest.approx(p["pit_volume_m3"], rel=0.02)
    assert relief.sum() * cell == pytest.approx(0.0, abs=0.02)
    assert relief.min() == pytest.approx(-0.55, abs=0.01)


def test_the_tree_falls_downwind_and_the_mound_lies_past_the_hinge(sp):
    # the wind comes from the west (180): tree, hinge and mound go east (0)
    s = mean_tree(sp, prior_damage=True, anchorage={"plate_radius_m": 1.0, "plate_depth_m": 0.5, "critical_turning_moment": {"by_wind_dir_knm": {"180": 0.01}}})
    e = damage._failure(s, Weather(True, 180.0, 0.0), sp, np.random.default_rng(1), "wind")
    assert e.cause == "wind uproot" and e.fall_azimuth_deg == 0.0
    assert e.plate["hinge_x_m"] == pytest.approx(1.0) and e.plate["hinge_y_m"] == pytest.approx(0.0, abs=1e-6)
    assert e.plate["mound_x_m"] == pytest.approx(2.0)


def test_the_relief_fades(sp):
    p = _plate(sp)
    pit = np.array([[p["x_m"], p["y_m"]]])
    assert damage.ground_relief(pit, [p], [20], 20.0)[0] == pytest.approx(0.5 * damage.ground_relief(pit, [p], [0], 20.0)[0])


def test_uprooting_bares_the_seedbed_on_pit_and_mound(sp):
    p = _plate(sp, 0.0)
    L, nc = 20.0, 20
    c = (np.arange(nc) + 0.5) * L / nc - 0.5 * L
    cx, cy = np.meshgrid(c, c, indexing="ij")
    regen = SimpleNamespace(cx=cx, cy=cy, L=L, cs=L / nc, mineral=np.zeros((nc, nc)))
    damage.expose_mineral_soil(regen, p)
    d_pit, d_mound = np.hypot(cx - p["x_m"], cy - p["y_m"]), np.hypot(cx - p["mound_x_m"], cy - p["mound_y_m"])
    assert (regen.mineral[d_pit < 0.5] == 1.0).all() and (regen.mineral[d_mound < 0.5] == 1.0).all()
    assert regen.mineral[np.minimum(d_pit, d_mound) > 3.0].max() == 0.0
    damage.expose_mineral_soil(None, p)    # a plot without regeneration


def test_a_tree_without_root_numbers_still_gets_a_plate(sp):
    p = damage.root_plate(TreeState(60, 25.0, 30.0), 0.0, sp)
    assert p["plate_radius_m"] == pytest.approx(2.2 * 0.3) and p["plate_depth_m"] == 0.85


def test_events_can_be_saved_as_json(sp):
    import json

    json.dumps(damage.Event("wind uproot", True, None, 12.34567, _plate(sp)).as_dict())
    assert damage.Event("old age", True).as_dict() == {"cause": "old age", "fatal": True}


# -- on real trees -------------------------------------------------------------
def _grown(sp, years=12, seed=1, stand=True):
    env_p, _ = load_environment("sweden_open_field")
    m = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p))
    m.run(years)
    return m


def test_state_from_a_grown_tree(sp):
    m = _grown(sp)
    s = damage.state_from_model(m)
    assert s.age == 12 and s.height_m == m.stats[-1]["height_m"] and s.dbh_cm == m.stats[-1]["dbh_cm"]
    assert s.stems_per_ha > 0 and s.basal_area_m2_ha > 0 and s.crown_wood_kg > 0
    assert 0.0 <= s.crown_offset_m < s.height_m
    a = damage.anchorage_of(m)
    assert a["plate_radius_m"] > 0 and a["critical_turning_moment"]["mean_knm"] > 0


def test_a_broken_top_comes_off_and_the_tree_grows_on(sp):
    m = _grown(sp)
    h0 = m.stats[-1]["height_m"]
    n_alive = int((m.tree.death[: m.tree.n] < 0).sum())
    assert damage.apply_top_break(m, 0.6 * h0, m.year + 1)
    assert int((m.tree.death[: m.tree.n] < 0).sum()) < n_alive
    alive = m.tree.death[: m.tree.n] < 0
    trunk = m.tree.trunk_chain(m.leader_axes)
    assert m.tree.pos[trunk, 2].max() < h0
    assert m.tree.pos[: m.tree.n][alive, 2].max() < h0
    m.run(3)
    assert m.year == 15 and m.stats[-1]["dbh_cm"] > 0
    assert len(m.leader_axes) >= 1


def test_a_break_that_misses_the_stem_does_nothing(sp):
    m = _grown(sp, 6)
    assert damage.apply_top_break(m, 1000.0, m.year + 1) is False
    assert damage.apply_top_break(m, 0.0, m.year + 1) is False


def test_on_its_own_a_tree_logs_a_fatal_blow_and_carries_on(sp):
    sp.damage.old_age.enabled = sp.damage.snow.enabled = False
    sp.damage.wind.storm_return_years = 1
    sp.damage.wind.min_dbh_cm = 0.0
    sp.damage.wind.population_offset = 8.0     # every storm hits
    m = _grown(sp, 8)
    for _ in range(4):
        damage.tree_year(m, m.year + 1)
        m.step()
    assert m.year == 12 and m.damage_log
    assert all(e["cause"] in ("wind snap", "wind uproot") for e in m.damage_log)


def test_the_same_seed_gives_the_same_blows(sp):
    sp.damage.wind.storm_return_years = 1
    sp.damage.wind.population_offset = 3.0
    sp.damage.wind.min_dbh_cm = 0.0

    def run():
        m = _grown(sp, 6)
        for _ in range(3):
            damage.tree_year(m, m.year + 1)
            m.step()
        return m.damage_log

    assert run() == run()


class FakePlot:
    """As much of treegen.plot.Plot as damage.plot_year uses, on a few real trees."""

    def __init__(self, sp, trees):
        self.species, self.trees, self.seed, self.year, self.area = sp, trees, 1, trees[0].year, 200.0
        self.alive = list(range(len(trees)))
        self.info = [{"id": k, "x": 2.0 * k, "y": 0.0} for k in self.alive]
        self.regen = None
        self.finished = []
        for m in trees:
            m._plot_spacing = 5.0

    def _finish(self, k, cause):
        self.alive.remove(k)
        self.info[k]["removed"] = self.year
        self.info[k]["cause"] = cause
        self.finished.append((k, cause))
        self.trees[k] = None


def test_in_a_plot_the_dead_go_through_finish_and_what_happened_is_saved(sp):
    import json

    sp.damage.old_age.enabled = sp.damage.snow.enabled = False
    sp.damage.wind.storm_return_years = 1
    sp.damage.wind.min_dbh_cm = 0.0
    sp.damage.wind.population_offset = 9.0
    p = FakePlot(sp, [_grown(copy.deepcopy(sp), 8, seed) for seed in (1, 2, 3, 4)])
    for _ in range(3):
        p.year += 1
        damage.plot_year(p, list(p.alive))
    assert p.finished
    for k, cause in p.finished:
        assert cause in ("wind snap", "wind uproot") and p.info[k]["damage"][-1]["fatal"]
    for rec in (r for i in p.info for r in i.get("damage", [])):
        if rec["cause"] == "wind uproot":
            assert rec["plate"]["pit_depth_m"] > 0 and rec["plate"]["mound_height_m"] > 0
    survivors = [k for k in p.alive if p.info[k].get("damage")]
    assert all(p.info[k]["prior_damage"] for k in survivors)
    json.dumps(p.info)


def test_the_log_holds_every_year_and_every_event_with_the_tree_s_size(sp):
    import json

    sp.damage.old_age.enabled = sp.damage.snow.enabled = False
    sp.damage.wind.storm_return_years = 1
    sp.damage.wind.min_dbh_cm = 0.0
    sp.damage.wind.population_offset = 9.0
    p = FakePlot(sp, [_grown(copy.deepcopy(sp), 8, seed) for seed in (1, 2, 3)])
    p.year += 1
    damage.plot_year(p, list(p.alive))
    log = p.damage_log
    assert [y["year"] for y in log["years"]] == [p.year]
    row = log["years"][0]
    assert row["storm"] and row["trees"] == 3 and row["wind_at_risk"] == 3 and row["events"] == len(log["events"]) > 0
    assert row["wind_expected"] > 0.0 and row["fatal"] == sum(e["fatal"] for e in log["events"])
    for e in log["events"]:
        assert e["cause"].startswith("wind") and e["year"] == p.year and e["dbh_cm"] > 0 and e["height_m"] > 0 and e["hd_over_bark"] > 0
        assert e["uprooted"] == ("plate" in e) and e["root_moment_knm"] > 0 and e["stem_moment_knm"] > 0
        assert e["took"]["leaf_share"] > 0.0
    json.dumps(log)
    # and it's saved only when there's something in it, so an off run's output doesn't change
    from pathlib import Path as P
    root = P(__file__).resolve().parent.parent
    assert 'if getattr(plot, "damage_log", None):' in (root / "tools" / "forest.py").read_text(encoding="utf-8")


def test_a_year_with_no_storm_or_snow_needs_no_look_at_the_tree(sp):
    """Trees are to grow live in a game: damage shouldn't walk every stem every year."""
    sp.damage.wind.enabled = sp.damage.snow.enabled = False
    p = FakePlot(sp, [_grown(copy.deepcopy(sp), 6, 1)])
    called = []
    real = damage.state_from_model
    damage.state_from_model = lambda *a, **k: called.append(1) or real(*a, **k)
    try:
        p.year += 1
        damage.plot_year(p, list(p.alive))
    finally:
        damage.state_from_model = real
    assert not called


def _exposure_plot(sp, n=400, side=31.6, dbh=20.0):
    rng = np.random.default_rng(5)
    trees = [SimpleNamespace(stats=[{"dbh_cm": dbh}]) for _ in range(n)]
    info = [{"x": float(rng.uniform(-side / 2, side / 2)), "y": float(rng.uniform(-side / 2, side / 2))} for _ in range(n)]
    return SimpleNamespace(trees=trees, info=info, area=side * side)


def test_a_storm_falls_in_patches_and_takes_what_it_would_have_taken(sp):
    p = _exposure_plot(sp)
    trees = list(range(len(p.trees)))
    for seed in range(5):
        out = damage.storm_exposure(p, trees, np.random.default_rng(seed), sp.damage, 1.098)
        centres = out.pop("centres")
        assert len(centres) == 1
        values = np.array([out[k] for k in trees])
        assert values.mean() == pytest.approx(1.0)                    # the stand's damage is unchanged
        high = values > 1.0
        assert sp.damage.wind.gap_damage_share == pytest.approx(values[high].sum() / values.sum())    # most of it in the patch
        assert values[high].min() > 5.0 * values[~high].max()
        # the patch is where it says, across the plot's repeat
        lx = math.sqrt(p.area)
        for k in np.nonzero(high)[0]:
            dx, dy = abs(p.info[k]["x"] - centres[0][0]), abs(p.info[k]["y"] - centres[0][1])
            assert math.hypot(min(dx, lx - dx), min(dy, lx - dy)) <= sp.damage.wind.gap_radius_m


def test_exposure_scales_the_hit_and_a_small_stand_has_no_patch_to_speak_of(sp):
    a = mean_tree(sp)
    b = mean_tree(sp, storm_exposure=3.0)
    assert damage.storm_hit_probability(b, sp.damage) == pytest.approx(3.0 * damage.storm_hit_probability(a, sp.damage))
    assert damage.storm_hit_probability(mean_tree(sp, storm_exposure=1000.0), sp.damage) == 1.0
    p = _exposure_plot(sp, n=1)
    out = damage.storm_exposure(p, [0], np.random.default_rng(1), sp.damage, 1.098)
    assert set(out) == {"centres"}     # all in or all out: everything at the mean


def test_a_bent_stem_isnt_prior_damage_but_a_broken_one_is(sp):
    sp.damage.old_age.enabled = sp.damage.wind.enabled = False
    sp.damage.snow.return_years = 1
    sp.damage.snow.load_range_kg_m2 = [60.0, 60.0]
    sp.damage.snow.crown_catch_fraction = 1.0
    p = FakePlot(sp, [_grown(copy.deepcopy(sp), 7, seed) for seed in (1, 2, 3)])
    p.year += 1
    damage.plot_year(p, list(p.alive))
    causes = [rec["cause"] for i in p.info for rec in i.get("damage", [])]
    assert "snow bend" in causes
    for i in p.info:
        for rec in i.get("damage", []):
            if rec["cause"] == "snow bend":
                assert not i.get("prior_damage")


def test_the_snow_reads_the_real_stem_when_it_has_one(sp):
    even = mean_tree(sp, crown_wood_kg=20.0)
    z = np.linspace(0.0, even.height_m, 40)
    p = (1.0 / sp.damage.stem_form_factor - 1.0) / 2.0
    thick = 1.5 * 0.5 * even.dbh_cm / 100.0 * (np.maximum(even.height_m - z, 0.0) / (even.height_m - 1.3)) ** p   # the same taper, 1.5 x as thick
    real = mean_tree(sp, crown_wood_kg=20.0, stem_z=z, stem_r=thick)
    assert damage.snow_loading(real, 60.0, sp)[1] > 1.5 * damage.snow_loading(even, 60.0, sp)[1]


def test_a_grown_tree_s_state_holds_its_stem(sp):
    m = _grown(sp, 12)
    s = damage.state_from_model(m)
    assert (np.diff(s.stem_z) >= 0.0).all() and s.stem_z[-1] <= s.height_m + 1e-3
    assert s.stem_r[0] >= s.stem_r[-1]
    share = damage.top_break_share(m, 0.5 * s.height_m)
    assert 0.0 < share <= 1.0
    took = damage.apply_top_break(m, 0.5 * s.height_m, m.year + 1)
    assert took["leaf_share"] == pytest.approx(share, abs=1e-3) and took["height_left_m"] < s.height_m


def test_a_tree_in_a_plot_is_left_to_the_plot(sp):
    m = _grown(sp, 4)
    m.__dict__.pop("damage_log", None)   # growing it alone, as _grown does, runs the tree's own yearly call
    m._plot_spacing = 5.0
    assert damage.tree_year(m, m.year + 1) is None and not hasattr(m, "damage_log")


def test_the_rates_tool_reads_the_log(sp, tmp_path, capsys):
    import json

    from tools import damage_rates

    sp.damage.old_age.enabled = sp.damage.snow.enabled = False
    sp.damage.wind.storm_return_years = 1
    sp.damage.wind.min_dbh_cm = 0.0
    sp.damage.wind.population_offset = 9.0
    p = FakePlot(sp, [_grown(copy.deepcopy(sp), 8, seed) for seed in (1, 2, 3)])
    p.year += 1
    damage.plot_year(p, list(p.alive))
    folder = tmp_path / "plot_1"
    folder.mkdir()
    (folder / "plot.json").write_text(json.dumps({"damage_log": p.damage_log}))
    assert damage_rates.main([str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "1 plots" in out and "wind" in out and "Per 5 years" in out
