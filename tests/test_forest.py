"""Forest settings: self-thinning and vigour mortality, the natural start, spreading seed, and
the stand's measures.  With every setting off, a plot has none of them."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

import cli
from treegen import checkpoint
from treegen.plot import Plot
from treegen.regeneration import SpreadRegeneration
from treegen.thinning import Mortality, Neighbourhood, gap_fraction, over_bark_cm, top_height_m

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import bark  # noqa: E402
import stand_table  # noqa: E402


def species(*items):
    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, list(items))
    return sp


def make_plot(sp, seed=1, mode="natural", lean=False, n_final=1):
    env_p, _ = cli.load_environment("sweden_open_field")
    return Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), n_final, seed, mode, lean=lean)


def mortality(lx=50.0, ly=50.0, **values):
    sp = species()
    for k, v in values.items():
        setattr(sp.mortality, k, v)
    return Mortality(sp.mortality, lx, ly, -lx / 2, -ly / 2)


def test_every_setting_is_off_by_default_and_a_plot_then_has_none_of_it():
    sp = species()
    assert sp.mortality.enabled is False and sp.plot.natural_start.enabled is False
    assert sp.regeneration.spread.enabled is False and sp.plot.stand_measures is False
    plot = make_plot(sp)
    assert plot.mort is None and plot.measures is False and not hasattr(plot, "Lx")
    plot.step()
    assert "basal_area_ob_m2_ha" not in plot.stats[-1] and "relative_density" not in plot.stats[-1]
    plot.enable_regeneration()
    assert not isinstance(plot.regen, SpreadRegeneration)


def test_over_bark_matches_the_comparison_tool():
    sp = species()
    d = np.array([0.0, 0.5, 3.0, 10.0, 25.0, 40.0])
    assert over_bark_cm(d, sp.mortality.bark_double_mm) == pytest.approx(np.maximum(bark.dbh_over_bark(d), 0.0))


def test_neighbourhood_keeps_what_it_blurs_and_reads_a_uniform_stand_as_its_density():
    hood = Neighbourhood(40.0, 20.0, -20.0, -10.0, 1.0, 5.0)
    xs, ys = np.meshgrid(np.arange(40) + 0.5 - 20.0, np.arange(20) + 0.5 - 10.0, indexing="ij")
    xy = np.stack([xs.ravel(), ys.ravel()], 1)
    i, j = hood.cells(xy)
    assert hood.blur(i, j, np.ones(len(xy))) == pytest.approx(np.ones(len(xy)))   # one per m2


def test_the_line_rests_on_two_unmanaged_studies_and_the_rate_on_their_losses():
    """Given Table 3's own stems and basal area, the rate comes within 20 % of Table 3's count at 17, and the
    other unmanaged study and Hagemeier's stands sit where the species file says."""
    m = mortality()
    b = float(m.p.self_thinning_slope)
    N = np.array([11633, 11533, 10200, 9500, 8300, 7670, 6567, 4233, 3133, 2733], float)
    G = np.array([11.3, 13.2, 15.2, 16.6, 18.7, 20.1, 21.3, 20.7, 20.5, 20.9])
    dg = 100 * np.sqrt(G * 4 / np.pi / N)
    rd = N * (dg / 25) ** b / float(m.p.sdi_max)
    assert rd.max() == pytest.approx(1.0, abs=2e-3)
    assert 11633 * math.exp(-m.thinning_rate(rd[:-1]).sum()) == pytest.approx(2733, rel=0.2)

    def relative(n, g):
        return n * (100 * math.sqrt(g * 4 / math.pi / n) / 25) ** b / float(m.p.sdi_max)
    assert 0.95 < relative(4720, 22.0204) < 1.0 and 0.95 < relative(2800, 25.7693) < 1.0     # Martinik et al. 2018
    assert 0.70 < relative(880, 25.2) < 0.77 and 0.70 < relative(420, 28.5) < 0.77           # Hagemeier & Leuschner 2019b


def test_the_rate_starts_at_the_onset_and_is_capped():
    m = mortality()
    r = m.thinning_rate(np.array([0.3, 0.6, 1.0, 10.0]))
    assert r[0] == 0.0 and r[1] == 0.0
    assert r[2] == pytest.approx(float(m.p.rate_at_max))
    assert r[3] == pytest.approx(float(m.p.rate_cap))


def test_weak_trees_go_first_and_the_neighbourhood_keeps_its_rate():
    m = mortality()
    rng = np.random.default_rng(1)
    n = 400
    xy = rng.uniform(-25, 25, (n, 2))
    d = np.full(n, 12.0)
    rings = np.where(np.arange(n) % 2 == 0, 2.0, 0.1)
    hz = m.hazards(xy, d, rings, np.full(n, 30.0), 30.0)
    weak, strong = hz["self-thinned"][1::2], hz["self-thinned"][::2]
    assert weak.mean() > 5.0 * strong.mean()
    # shared out, not added to: the stand's rate is the rate for its density
    assert hz["self-thinned"].mean() == pytest.approx(m.thinning_rate(hz["rd"]).mean(), rel=0.1)


def test_a_thicket_thins_and_an_open_tree_does_not():
    m = mortality(lx=100.0, ly=100.0)
    rng = np.random.default_rng(2)
    thicket = rng.uniform(-30, -20, (60, 2))
    alone = np.array([[30.0, 30.0]])
    xy = np.concatenate([thicket, alone])
    d = np.full(len(xy), 15.0)
    hz = m.hazards(xy, d, np.full(len(xy), 1.0), np.full(len(xy), 30.0), 30.0)
    assert hz["rd"][:-1].mean() > 0.8 and hz["rd"][-1] < 0.1
    assert hz["self-thinned"][:-1].mean() > 0.02 and hz["self-thinned"][-1] == 0.0


def test_a_tree_laying_no_wood_is_suppressed_wherever_it_stands():
    m = mortality()
    hz = m.hazards(np.array([[0.0, 0.0], [20.0, 20.0]]), np.array([10.0, 10.0]), np.array([0.0, 3.0]), np.array([30.0, 30.0]), 30.0)
    assert hz["suppressed"][0] == pytest.approx(float(m.p.vigour.suppressed_hazard))
    assert hz["suppressed"][1] < 0.01
    # no stem yet, no ring to read: the carbon rule's business
    hz = m.hazards(np.array([[0.0, 0.0]]), np.array([0.0]), np.array([0.0]), np.array([3.0]), 3.0)
    assert hz["suppressed"][0] == 0.0


def test_background_and_old_age_follow_their_sources():
    m = mortality()
    # Elfving 2010 p. 64, deciduous, south, D 20, A 60: 0.46 - 0.4 + 0.276 = 0.336 % of volume, less 25 %
    assert m.background_rate(20.0, 60.0) == pytest.approx(0.336 * 0.75 / 100)
    assert m.background_rate(1.0, 5.0) == m.background_rate(7.0, 30.0)   # the closest limit, outside the range
    amax = float(m.p.old_age.max_age_years)
    assert m.old_age_rate(np.array([amax]))[0] == pytest.approx(1.0 / (1.0 + math.exp(-2.0)))
    assert m.old_age_rate(np.array([60.0]))[0] < 0.001


def test_ring_width_reads_the_window():
    m = mortality()
    assert m.ring_mm([10.0, 10.2, 10.4, 10.6, 10.8, 11.0]) == pytest.approx(1.0)   # 1 cm in 5 years: 1 mm a year each side
    assert m.ring_mm([0.0]) == 0.0
    assert m.ring_mm([0.0, 0.4]) == pytest.approx(2.0)   # just past breast height


def test_top_height_and_gap_fraction():
    assert top_height_m(np.array([1.0, 5.0, 3.0]), np.array([1.0, 9.0, 7.0]), 100.0) == 9.0
    assert top_height_m(np.array([1.0, 5.0, 3.0]), np.array([1.0, 9.0, 7.0]), 200.0) == pytest.approx(8.0)
    assert gap_fraction(None, -5, -5, 10, 10, 2.0, 2.0) == 1.0
    low = np.array([[0.0, 0.0, 1.0]])
    assert gap_fraction(low, -5, -5, 10, 10, 2.0, 2.0) == 1.0     # below the height a gap is read at
    high = np.array([[0.1, 0.1, 5.0], [-4.9, -4.9, 5.0]])
    assert gap_fraction(high, -5, -5, 10, 10, 2.0, 2.0) == pytest.approx(23 / 25)


def test_natural_start_density_and_rectangle_and_patch():
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=5000", "plot.natural_start.area_m2=100")
    p = make_plot(sp)
    assert len(p.trees) == 50 and p.area == pytest.approx(100.0)
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=2000", "plot.natural_start.side_x_m=60",
                 "plot.natural_start.side_y_m=10", "plot.natural_start.patch_x_m=10")
    p = make_plot(sp)
    assert len(p.trees) == 20 and p.area == pytest.approx(600.0)
    xs = np.array([i["x"] for i in p.info])
    assert xs.min() >= -30.0 and xs.max() <= -20.0
    lx, ly = p._sides()
    assert lx == pytest.approx(60.0, abs=0.2) and ly == pytest.approx(10.0, abs=0.2)
    assert p.cell[2] != p.cell[3]


def test_lean_plot_grows_the_same_trees():
    def grow(lean):
        sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=8000", "plot.natural_start.area_m2=20",
                     "mortality.enabled=true", "plot.stand_measures=true")
        plot = make_plot(sp, lean=lean)
        for _ in range(5):
            plot.step()
        return plot
    full, lean = grow(False), grow(True)
    assert len(full.stats) == 5 and full.stats == lean.stats
    assert [i.get("cause") for i in full.info] == [i.get("cause") for i in lean.info]
    a, b = lean.trees[lean.alive[0]], lean.trees[lean.alive[-1]]
    assert a.light is b.light and a.sp is not b.sp and a.sp.light is b.sp.light


def test_stand_measures_in_a_plot():
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=6000", "plot.natural_start.area_m2=25",
                 "mortality.enabled=true", "plot.stand_measures=true")
    plot = make_plot(sp, lean=True)
    for _ in range(4):
        plot.step()
    s = plot.stats[-1]
    d = np.array([plot._dbh(k) * 100 for k in plot.alive])
    ob = over_bark_cm(d, sp.mortality.bark_double_mm)
    assert s["basal_area_ob_m2_ha"] == pytest.approx(float((np.pi / 4 * (ob / 100) ** 2).sum()) / plot.area * 1e4, abs=0.01)
    assert 0.0 <= s["gap_fraction"] <= 1.0 and s["relative_density"] >= 0.0
    assert s["top_height_m"] >= s["height_mean_m"] - 0.01 and s["new_trees"] == 0


def _spread(lx=400.0, ly=10.0, **values):
    sp = species("regeneration.spread.enabled=true")
    for k, v in values.items():
        setattr(sp.regeneration.spread, k, v)
    env_p, _ = cli.load_environment("sweden_open_field")
    return SpreadRegeneration(sp.regeneration, sp.bud_fate.short_shoot_survival_light, cli.make_soil(env_p), lx, ly, 1)


def test_seed_runs_out_along_x_and_stops_at_the_ends():
    r = _spread(kernel="lognormal")
    x0 = np.array([[-195.0, 0.0]])
    r.count_trees(np.zeros((0, 2)))
    rain = r.seed_rain(x0, np.array([1.0]))
    along = rain.sum(1)
    dist = np.abs(r.cx[:, 0] - x0[0, 0])
    # a line of sources across the repeat: its mean reach along x is under the 2-D mean of 65 m
    mean_x = float((along * dist).sum() / along.sum())
    assert 20.0 < mean_x < 65.0
    # the half thrown behind a source at the end of the ground is lost; none comes round
    assert 0.45 < rain.sum() < 0.6
    assert along[-5:].sum() < 0.001 * along[:50].sum()
    # a source in the middle keeps nearly all of it
    assert 0.98 < r.seed_rain(np.array([[0.0, 0.0]]), np.array([1.0])).sum() <= 1.0


def test_the_mixed_kernel_is_highest_at_the_tree_and_has_a_tail():
    r = _spread(lx=1600.0, ly=10.0, far_share=0.005)
    r.count_trees(np.zeros((0, 2)))
    x0 = np.array([[-795.0, 0.0]])
    rain = r.seed_rain(x0, np.array([1.0]))
    along = rain.sum(1)
    dist = np.abs(r.cx[:, 0] - x0[0, 0])
    assert along.argmax() <= 4                                   # no hole at the tree
    # half thrown behind is lost; of the half thrown ahead, far_share reaches its long kernel
    assert 0.45 < rain.sum() < 0.62
    # the near part is all but gone by 776 m, the far part isn't
    past = along[dist > 776.0].sum() / along.sum()
    assert past > 0.1 * float(r.p.spread.far_share) * math.exp(-776.0 / 370.0)
    # with no far share there's next to nothing there
    r2 = _spread(lx=1600.0, ly=10.0, far_share=0.0)
    r2.count_trees(np.zeros((0, 2)))
    near_only = r2.seed_rain(x0, np.array([1.0])).sum(1)
    assert near_only[dist > 776.0].sum() < 0.01 * along[dist > 776.0].sum()


def test_crop_and_seed_size_limit():
    r = _spread(lx=40.0, ly=40.0, mast_share=1.0)
    assert r.seed_crop() == pytest.approx(float(r.p.spread.mast_factor))
    r = _spread(lx=40.0, ly=40.0, mast_share=0.0)
    assert r.seed_crop() == 1.0
    r = _spread(lx=40.0, ly=40.0)
    crops = [r.seed_crop() for _ in range(3000)]
    assert 0.3 < np.mean(np.array(crops) > 1.0) < 0.37
    assert r.fecundity(0.10, 30) == 0.0                          # 10 cm of wood is under 12 cm over bark
    assert r.fecundity(0.20, 30) == pytest.approx(float(r.p.seeds_ref))
    assert r.fecundity(0.20, 5) == 0.0                           # the age rule still holds


def test_damage_takes_over_old_age():
    sp = species("mortality.enabled=true", "damage.enabled=true", "damage.old_age.enabled=true")
    plot = make_plot(sp)
    assert plot.mort.old_age_elsewhere is True
    n = 5
    hz = plot.mort.hazards(np.zeros((n, 2)), np.full(n, 20.0), np.full(n, 1.0), np.full(n, 200.0), 200.0)
    assert (hz["old age"] == 0.0).all()
    assert make_plot(species("mortality.enabled=true")).mort.old_age_elsewhere is False


def test_a_crowded_tree_throws_seed_shorter_than_an_open_one():
    r = _spread()
    x0 = np.array([[-195.0, 0.0]])
    r.count_trees(np.zeros((0, 2)))
    open_rain = r.seed_rain(x0, np.array([1.0])).sum(1)
    r.count_trees(np.tile(x0, (3, 1)))
    closed_rain = r.seed_rain(x0, np.array([1.0])).sum(1)
    dist = np.abs(r.cx[:, 0] - x0[0, 0])
    assert (closed_rain * dist).sum() / closed_rain.sum() < 0.7 * (open_rain * dist).sum() / open_rain.sum()


def test_seedlings_take_in_the_open_and_not_under_a_closed_canopy():
    r = _spread(lx=40.0, ly=40.0)
    r.count_trees(np.zeros((0, 2)))
    xy = np.array([[-15.0, 0.0]])
    seeds = np.array([1e7])
    free = np.zeros(r.cx.shape, bool)
    closed = np.full(r.cx.shape, 0.22)     # this model's closed canopy, at the ground
    # under a closed canopy's leaf area nothing takes, whatever the light reads
    r.read_canopy(np.stack([r.cx.ravel(), r.cy.ravel(), np.full(r.cx.size, 15.0)], 1), np.full(r.cx.size, 4.0 * r.csx * r.csy))
    assert r.step(xy, seeds, closed, 0.38, free) == []
    r.overhead = None
    assert len(r.step(xy, seeds, np.ones(r.cx.shape), 0.38, free)) > 100
    half = np.where(r.cx < 0.0, 0.10, 1.0)                # half the ground is a gap
    placed = np.array(r.step(xy, seeds, half, 0.38, free))
    assert len(placed) and (placed[:, 0] > -0.1 * r.csx).mean() > 0.99


def test_no_seedling_takes_under_cover_however_bright_the_light_reads():
    r = _spread(lx=40.0, ly=40.0)
    r.count_trees(np.zeros((0, 2)))
    xs, ys = np.meshgrid(np.arange(-20.0, 0.0, 0.5), np.arange(-20.0, 20.0, 0.5), indexing="ij")
    canopy = np.stack([xs.ravel(), ys.ravel(), np.full(xs.size, 15.0)], 1)    # crowns over the half with x < 0
    r.read_canopy(canopy, np.full(xs.size, 4.0 * 0.25))                       # 4 m2 of leaf per m2 of ground
    assert r.overhead[(r.cx > -15.0) & (r.cx < -5.0)].min() > 3.5 and r.overhead[(r.cx > 5.0) & (r.cx < 15.0)].max() < 0.4
    placed = np.array(r.step(np.array([[0.0, 0.0]]), np.array([1e7]), np.ones(r.cx.shape), 0.38, np.zeros(r.cx.shape, bool)))
    assert len(placed) > 50 and (placed[:, 0] < -6.0).sum() <= 0.1 * len(placed)    # what's left is at the far edge, across the repeat
    low = np.stack([xs.ravel(), ys.ravel(), np.full(xs.size, 1.0)], 1)        # young growth under 2 m is no canopy
    r.read_canopy(low, np.full(xs.size, 1.0))
    assert r.overhead.max() == 0.0


def test_a_windthrow_takes_the_trees_in_its_circle_and_bares_soil():
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=4000", "plot.natural_start.area_m2=100",
                 "regeneration.spread.enabled=true", "regeneration.spread.repeat_ends=true", "mortality.enabled=true", "plot.stand_measures=true")
    plot = make_plot(sp, lean=True)
    plot.enable_regeneration()
    plot.step()
    before = len(plot.alive)
    inside = [k for k in plot.alive if math.hypot(plot.info[k]["x"], plot.info[k]["y"]) <= 3.0]
    assert plot.open_gap(0.0, 0.0, 3.0) == len(inside) > 0
    assert len(plot.alive) == before - len(inside)
    assert all(plot.info[k]["cause"] == "windthrow" for k in inside)
    assert plot.regen.mineral.max() == pytest.approx(float(sp.regeneration.spread.windthrow_mineral))
    assert plot.regen.mineral.min() < 0.05


def test_occupied_cells_take_nobody_and_the_memory_limit_holds():
    r = _spread(lx=40.0, ly=40.0, max_recruits_per_year=7)
    r.count_trees(np.zeros((0, 2)))
    out = r.step(np.array([[0.0, 0.0]]), np.array([1e7]), np.ones(r.cx.shape), 0.38, np.zeros(r.cx.shape, bool))
    assert len(out) == 7
    r = _spread(lx=40.0, ly=40.0)
    r.count_trees(np.zeros((0, 2)))
    assert r.step(np.array([[0.0, 0.0]]), np.array([1e7]), np.ones(r.cx.shape), 0.38, np.ones(r.cx.shape, bool)) == []


def test_a_plot_spreads_recruits_from_its_patch():
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=3000", "plot.natural_start.side_x_m=60",
                 "plot.natural_start.side_y_m=6", "plot.natural_start.patch_x_m=6", "plot.stand_measures=true",
                 "mortality.enabled=true", "regeneration.spread.enabled=true", "regeneration.maturity_years=2",
                 "regeneration.spread.seed_min_dbh_wood_cm=null", "regeneration.spread.max_recruits_per_year=5")
    plot = make_plot(sp, lean=True)
    plot.enable_regeneration()
    for _ in range(4):
        plot.step()
    s = plot.stats[-1]
    assert "stems_along_x" in s and len(s["stems_along_x"]) == 6 and "recruits" in s
    assert any(row["new_trees"] > 0 for row in plot.stats)
    recruits = [i for i in plot.info if i.get("recruit")]
    assert recruits and max(i["x"] for i in recruits) > -24.0     # past the patch


def test_stand_table_reads_a_plot_and_a_folder(tmp_path):
    for n, g in ((1, 20.0), (2, 30.0)):
        d = tmp_path / f"plot_{n}"
        d.mkdir()
        stats = [{"year": y, "stems_per_ha": 800 + n, "basal_area_ob_m2_ha": g, "dg_ob_cm": 20.0, "height_mean_m": 18.0, "top_height_m": 22.0,
                  "gap_fraction": 0.1, "new_trees": 2} for y in range(1, 61)]
        (d / "plot.json").write_text(json.dumps({"area_m2": 1000.0, "stats": stats, "peak_mb": 2048, "runtime_s": 600}))
    text = stand_table.table(tmp_path, [50, 60])
    assert "2 plot(s)" in text and "25.0 (20.0-30.0)" in text and "| 60 |" in text and "| 50 |" in text
    assert "2.0 GB" in text
    assert "1 plot(s)" in stand_table.table(tmp_path / "plot_1", [60])


def test_stems_at_aosaars_stem_size_and_the_forest_edge(tmp_path):
    stats = [{"year": y, "stems_per_ha": 12000 - 1000 * y, "basal_area_ob_m2_ha": 10.0 + y, "dg_ob_cm": 3.0 + y, "height_mean_m": 5.0,
              "top_height_m": 6.0, "gap_fraction": 0.1, "new_trees": 1,
              "stems_along_x": [8, 8, 8, 0, 1, 0], "seedlings_along_x": [0, 0, 0, 3, 0, 2]} for y in range(1, 8)]
    d = tmp_path / "plot_1"
    d.mkdir()
    (d / "plot.json").write_text(json.dumps({"area_m2": 600.0, "side_m": 60.0, "side_y_m": 10.0, "stats": stats, "peak_mb": 100, "runtime_s": 60}))
    text = stand_table.table(d, [5])
    # the first year the stand reaches Dg 3.52 is year 1 (Dg 4.0): 11,000 stems/ha there
    assert "| 3.5 | 8, 11,633, 11.3 | 1, 11,000, 11.0 |" in text
    f = stand_table.fronts(stats[0], 10.0)
    assert f == {"first": 50.0, "forest": 40.0, "seedling": 60.0}     # [8, 8, 8, 0, 1, 0]: three slices read together
    assert stand_table.fronts({"stems_along_x": [8, 8, 8, 0, 0, 0, 1]}, 10.0)["forest"] == 40.0
    assert "Forest edge" in stand_table.spread_table(d)


def test_the_fast_spread_estimate_runs_on_the_models_own_rules(tmp_path):
    import argparse
    import spread_estimate
    stats = [{"year": y, "dg_ob_cm": 1.0 * y, "height_mean_m": 1.0 * y} for y in range(1, 41)]
    (tmp_path / "plot.json").write_text(json.dumps({"stats": stats}))
    a = argparse.Namespace(species="betula_pendula", environment="sweden_open_field", set=[], seed=1, length=300.0, width=10.0,
                           curve=str(tmp_path), stems=2000.0, patch=20.0, size_sd=0.2, years=16)
    out = spread_estimate.run(a)
    assert len(out["rows"]) == 16
    assert out["rows"][8]["new_trees"] == 0          # no seed before the maturity age
    assert max(r["new_trees"] for r in out["rows"]) > 0
    assert stand_table.fronts(out["rows"][-1], 10.0)["first"] > 50.0


def test_a_plot_year_as_a_plain_tree_list(tmp_path):
    import tree_list
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=9000", "plot.natural_start.area_m2=20",
                 "mortality.enabled=true", "plot.stand_measures=true")
    plot = make_plot(sp, lean=True)
    for _ in range(5):
        plot.step()
    dead = [i for i in plot.info if i.get("removed") is not None]
    assert dead and plot.alive
    doc = json.loads(tree_list.write(plot, tmp_path / "trees.json").read_text(encoding="utf-8"))
    alive = [t for t in doc["trees"] if t["alive"]]
    gone = [t for t in doc["trees"] if not t["alive"]]
    assert len(alive) == doc["trees_alive"] == len(plot.alive) and len(gone) == len(dead)
    assert doc["plot_year"] == 5 and doc["area_m2"] == pytest.approx(plot.area) and doc["repeats_at_edges"] is True
    for t in doc["trees"]:
        assert set(t) >= {"x_m", "y_m", "species", "age_years", "height_m", "dbh_cm", "crown_base_m", "crown_width_m", "alive"}
        assert t["species"] == sp.species.scientific_name and abs(t["x_m"]) <= doc["side_x_m"] / 2 + 0.01
    k = plot.alive[0]
    row = next(t for t in alive if t["id"] == k)
    d = plot.trees[k].stats[-1]["dbh_cm"]
    assert row["height_m"] == pytest.approx(plot.trees[k].stats[-1]["height_m"], abs=0.001)
    assert row["age_years"] == plot.trees[k].year
    assert (row["dbh_cm"] is None) == (d is None)
    if d is not None:
        assert row["dbh_cm"] == pytest.approx(float(bark.dbh_over_bark(d)), abs=0.01)
    assert all(t["died_year"] <= 5 and t["cause"] for t in gone)
    # how far back the dead are listed
    assert not any(not t["alive"] for t in tree_list.tree_list(plot, dead_years=0)["trees"])


def test_settings_lists_every_change():
    import forest
    args = type("A", (), {"stems": 9000.0, "mortality_off": False, "strip": None, "patch": None, "area": 500.0, "spread": False, "set": ["x=1"]})
    items = forest.settings(args)
    assert "mortality.enabled=true" in items and "plot.natural_start.area_m2=500.0" in items and "x=1" in items
    sp = species(*items[:-1])
    assert sp.mortality.enabled is True and sp.plot.natural_start.stems_per_ha == 9000.0


def test_shade_trial_field_scales_light():
    import shade_trial

    class Open:
        p = type("P", (), {"C": 1.0})
        S, lo, periodic = np.zeros((2, 2, 2)), np.zeros(3), True

        def exposure(self, pos, self_weight, own_shade=None):
            return np.full(len(pos), 0.8)

        def sample(self, pts):
            return np.zeros(len(pts))

    f = shade_trial.ShadedField(Open(), 0.25)
    assert f.exposure(np.zeros((3, 3)), np.zeros(3))[0] == pytest.approx(0.2)
    assert np.exp(-f.sample(np.zeros((1, 3)))[0]) == pytest.approx(0.25)
    assert f.relative_light_at_heights([2.0]) is None and f.diffuse_light_at_heights([2.0]) is None
