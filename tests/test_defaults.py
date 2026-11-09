"""The shipped defaults, end to end (review 2026-11-09, findings 6 and 8).

Other tests set what they need; these set nothing unless they say so.  The bounds on the 60-year tree are sanity
bounds, wide on purpose: they catch a default tree going badly wrong, they aren't targets.
"""
from __future__ import annotations

import math

import cli
from treegen import checkpoint
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import load_environment, load_species
from treegen.plot import Plot
from treegen.reference import eriksson_1997_height


def grow(years: int, sets=(), seed: int = 3):
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, list(sets))
    env, _ = load_environment("sweden_open_field")
    model = GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)
    for _ in range(years):
        model.step()
    return model


def site_index_band(sp, age: float) -> tuple:
    """The height band SI low to SI high at this total age, as tools/scorecard.py works it: T13 = 150 / SIS."""
    ref, hd = sp.reference.height, sp.height_driver
    out = []
    for si in (float(ref.site_index_low), float(ref.site_index_high)):
        t13 = float(hd.t13_numerator) / si
        for _ in range(200):
            t13 = float(hd.t13_numerator) / eriksson_1997_height(si, float(hd.sis_total_age_years) - t13, ref.asi, ref.beta, ref.b2)
        out.append(eriksson_1997_height(si, age - t13, ref.asi, ref.beta, ref.b2))
    return tuple(out)


def test_a_default_stand_tree_is_a_sane_birch_at_50_and_60():
    model = grow(60)
    rows = {s["year"]: s for s in model.stats}
    for age in (50, 60):
        s = rows[age]
        lo, hi = site_index_band(model.sp, age)
        assert lo <= s["height_m"] <= hi, (age, s["height_m"], lo, hi)
        assert 10.0 <= s["dbh_cm"] <= 45.0, (age, s["dbh_cm"])
        assert 2.0 <= s["lai"] <= 7.0, (age, s["lai"])
        assert 0.2 <= s["crown_ratio"] <= 0.9, (age, s["crown_ratio"])
        assert 1.5 <= s["crown_width_m"] <= 12.0, (age, s["crown_width_m"])
        assert s["carbon"]["fixed"] > 0.0
    # it kept growing: taller and thicker at 60 than at 50, and never shrinking in girth
    assert rows[60]["height_m"] > rows[50]["height_m"] and rows[60]["dbh_cm"] > rows[50]["dbh_cm"]
    dbh = [s["dbh_cm"] for s in model.stats if s["dbh_cm"] is not None]
    assert all(b >= a - 1e-9 for a, b in zip(dbh, dbh[1:]))
    n = model.tree.n
    assert all(math.isfinite(float(x)) for x in model.tree.radius[:n])


def test_crown_fix_c_is_the_default_and_young_limbs_reach_further_with_it():
    """DECISIONS 107: chase 1.0 and limb_shoot_floor_m 0.5, on the shipped values, against the values before it
    (0.5 and 0.2) on the same seed.  The fix's point is that young limbs grow fast enough for the crown to close."""
    sp, _ = load_species("betula_pendula")
    assert float(sp.crown_frame.chase) == 1.0 and float(sp.crown_frame.limb_shoot_floor_m) == 0.5
    now = grow(15)
    before = grow(15, ["crown_frame.chase=0.5", "crown_frame.limb_shoot_floor_m=0.2"])
    a, b = now.stats[-1], before.stats[-1]
    assert abs(a["height_m"] - b["height_m"]) < 0.3      # height stays on the curve
    assert a["crown_width_m"] > b["crown_width_m"], (a["crown_width_m"], b["crown_width_m"])
    assert a["leaf_area_m2"] > b["leaf_area_m2"], (a["leaf_area_m2"], b["leaf_area_m2"])


def _plot(*items):
    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, list(items))
    env_p, _ = cli.load_environment("sweden_open_field")
    return Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), 1, 1, "natural")


def test_plot_spacing_counts_every_tree_by_default_and_only_the_canopy_with_the_switch():
    """plot.spacing_min_height_share: null by default, so every living tree counts, as before.  Set, only trees at
    least that share of the canopy top's height count."""
    sp, _ = cli.load_species("betula_pendula")
    assert sp.plot.spacing_min_height_share is None
    base = _plot()
    for _ in range(5):
        base.step()
    k = base.alive[0]
    assert base.trees[k]._plot_spacing == math.sqrt(base.area / len(base.alive))
    tall = _plot("plot.spacing_min_height_share=0.99")
    for _ in range(5):
        tall.step()
    # the count is taken from the heights at the start of the last year: rebuild it from the year before's rows
    h = [tall.trees[j].stats[-2]["height_m"] for j in tall.alive if len(tall.trees[j].stats) >= 2]
    n = sum(1 for x in h if x >= 0.99 * max(h))
    assert 1 <= n < len(tall.alive)
    assert tall.trees[tall.alive[0]]._plot_spacing == math.sqrt(tall.area / n)
