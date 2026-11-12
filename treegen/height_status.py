"""A forest tree's height step by its standing among its neighbours (species block ``plot.height_status``; off by default).

Design and build note: reports/design/2026-11-11_earned_height_build.md (plan step E).

With the switch on, a plot tree's yearly height step is the site curve's step at its own age, times its light and water
factors (unchanged), times its status, set here by its plot once a year before the trees grow.  The tree's drawn vigour
(plot.vigour_sd) then no longer multiplies its height: it stays in its carbon only.  A tree outside a plot never has a
status, so it is unchanged.

Two published rules, chosen by ``plot.height_status.rule``.  Both predict a tree's five-year height growth as the
dominants' five-year growth times a modifier of the tree's diameter over the dominants' diameter:

* ``pine_1995``: Hynynen 1995, Silva Fennica 29(3): 225-246, eq. 5 and Table 6, p. 235.  Scots pine, so on birch it is
  BORROWED, never sourced.

      i_h5 = IH_dom * (d / D_dom) ** (a1 * IH_dom + a2 * (d / D_dom) ** a3)

  D_dom is the mean DBH of the 100 thickest stems a hectare; IH_dom the dominants' height growth over the next five
  years, here the curve's forward five-year step at the stand's age, curve(A + 5) - curve(A).  d / D_dom is held inside
  ratio_min to ratio_max and IH_dom inside ih_min_m to ih_max_m (the data's range, read off the paper's Fig. 5 by eye).
  A tree with no DBH takes ratio_min.

* ``birch_2002``: Hynynen, Ojansuu, Hokka, Siipilehto, Salminen & Haapala 2002, Metla Research Papers 835, Eq. 33 p. 40
  and Table 24 p. 41.  Birch: silver and downy pooled, mineral soils, Finland.

      i_h5 = IH_dom * (d / D_dom) ** ((a1 + a2 * PLANT) * RDFL)

  D_dom is the mean DBH of the trees thicker than D_g, the stand's mean diameter weighted by basal area (Symbols, p. 9:
  sum d^3 / sum d^2).  PLANT is 1 for a planted stand and 0 for a self-sown one.  RDFL is the relative density factor of
  the trees larger than this one (Eqs. 20-23, pp. 30-31): the sum, over every tree with a larger DBH, of its smallest
  growing space, 1 / N, N being the stem number a hectare on the self-thinning line at that tree's stump diameter
  (silver birch, Eq. 50 and Table 34 p. 53: ln N = b0 + b1 ln d_s; stump diameter d_s = 2.0 + 1.25 d, Eq. 3 p. 22, cm).
  Each tree of the plot stands for 10^4 / area stems a hectare.  The report uses the site-independent line for birch
  (p. 54: no site-dependent birch line was presented).  DBH is held inside dbh_min_cm to dbh_max_cm for the ratio, and
  RDFL under rdfl_max (Table 5 p. 18, the data's range); a tree with no DBH takes dbh_min_cm.  RDFL is read on the real
  diameters: a tree with no DBH is larger than none.

Both rules read DBH over bark (cm, as a tree list holds it, to 0.01 cm) and height to 0.001 m.

The dominants keep the curve's step.  Each tree's modifier is divided by the mean modifier of the dominants, so their
mean status is 1 (plot.height_status.scale_over):

* ``top_height``: the 100 thickest stems a hectare (the thickest, and the tallest among equals), the trees whose mean
  diameter the approved top height reads its curve at (tools/scorecard.py naslund_top_height).  For pine_1995 these are
  also the rule's own dominants.
* ``rule``: the rule's own dominants: pine_1995 the same 100 thickest; birch_2002 every tree thicker than D_g.

The rule starts once the plot's top height on the approved definition is start_top_height_m (null: once any tree has a
DBH) and, where start_age_years is set, the stand is that old; then it stays on.  Before, every status is 1.  The top
height read is the one the plot would log at the end of last year; while the curve can't be fitted, the mean height of
the 100 thickest stands in for it.

steer_top_height (the plan's arm B): every status is then multiplied by one plot-wide factor,
(curve(A + 1) - H) / (curve(A + 1) - curve(A)), H the approved top height now, held in 0 to height_driver.catch_up.
In that arm top height follows the curve by design and is not a test.
"""
from __future__ import annotations

import numpy as np

from . import logs

RULES = ("pine_1995", "birch_2002")
SCALES = ("top_height", "rule")


# -- the two published modifiers -------------------------------------------------------------------------------------
def pine_1995_modifier(ratio, ih_m, a1: float, a2: float, a3: float):
    """Hynynen 1995 eq. 5 (p. 235): the tree's five-year height growth over the dominants', at d / D_dom = ratio and the
    dominants' five-year growth ih_m (m).  No limits here."""
    r = np.asarray(ratio, float)
    return r ** (a1 * float(ih_m) + a2 * r ** a3)


def birch_2002_modifier(ratio, rdfl, a1: float, a2: float, planted: bool):
    """Hynynen et al. 2002 Eq. 33 (p. 40): the tree's five-year height growth over the dominants', at d / D_dom = ratio
    and the relative density factor of the larger trees rdfl.  No limits here."""
    r = np.asarray(ratio, float)
    return r ** ((a1 + a2 * (1.0 if planted else 0.0)) * np.asarray(rdfl, float))


# -- what the birch rule reads ---------------------------------------------------------------------------------------
def stump_cm(d_cm, a: float, b: float):
    """Hynynen et al. 2002 Eq. 3 (p. 22, from Laasasenaho 1975): diameter at stump height from DBH, cm."""
    return a + b * np.asarray(d_cm, float)


def self_thinning_stems(ds_cm, b0: float, b1: float):
    """Hynynen et al. 2002 Eq. 50, Table 34 (p. 53): stems a hectare on the self-thinning line at stump diameter ds_cm."""
    return np.exp(b0 + b1 * np.log(np.asarray(ds_cm, float)))


def growing_space(d_cm, p) -> np.ndarray:
    """Eq. 21 (p. 31): each tree's smallest growing space, a share of a hectare, 1 / N at its own stump diameter.  0 for a
    tree with no DBH, which no inventory counts."""
    d = np.asarray(d_cm, float)
    out = np.zeros(len(d))
    on = d > 0.0
    out[on] = 1.0 / self_thinning_stems(stump_cm(d[on], float(p.stump_a_cm), float(p.stump_b)), float(p.self_thinning_b0), float(p.self_thinning_b1))
    return out


def rdfl(d_cm, stems_per_tree_ha: float, p) -> np.ndarray:
    """Eq. 23 (p. 31): for each tree, the summed growing space of the trees with a larger DBH, each tree standing for
    stems_per_tree_ha stems a hectare.  Trees of equal DBH don't count each other."""
    d = np.asarray(d_cm, float)
    if not len(d):
        return np.zeros(0)
    space = growing_space(d, p) * float(stems_per_tree_ha)
    order = np.argsort(d, kind="stable")
    ds = d[order]
    above = np.concatenate([np.cumsum(space[order][::-1])[::-1], [0.0]])
    return above[np.searchsorted(ds, d, side="right")]


def basal_area_mean_cm(d_cm) -> float:
    """D_g: the mean diameter weighted by basal area, sum d^3 / sum d^2, over the trees with a DBH; 0 if none."""
    d = np.asarray(d_cm, float)
    d = d[d > 0.0]
    return float(np.sum(d ** 3) / np.sum(d ** 2)) if len(d) else 0.0


def birch_dominants(d_cm) -> np.ndarray:
    """Hynynen et al. 2002's dominant trees (Symbols p. 9, and p. 26): those thicker than D_g.  If none is (every DBH
    alike), the trees at D_g."""
    d = np.asarray(d_cm, float)
    dg = basal_area_mean_cm(d)
    if dg <= 0.0:
        return np.zeros(0, np.int64)
    big = np.nonzero(d > dg)[0]
    return big if len(big) else np.nonzero(d >= dg * (1.0 - 1e-12))[0]


def thickest(d_cm, h_m, area_m2: float) -> np.ndarray:
    """The 100 thickest stems a hectare (at least one), the tallest first among equals, as the plot picks its dominants
    for plot.height_follows_dominants."""
    n = max(1, int(round(100.0 * area_m2 / 1e4)))
    return np.lexsort((-np.asarray(h_m, float), -np.asarray(d_cm, float)))[:n]


# -- one plot-year -----------------------------------------------------------------------------------------------------
def top_heights(d_cm, h_m, area_m2: float) -> tuple:
    """(approved, read): top height on the approved definition (treegen/logs.py fitted_top_height), None where the curve
    can't be fitted; and the height the start reads, which is that, else the 100 thickest's mean height, else 0."""
    top, _, simple = logs.fitted_top_height(list(d_cm), list(h_m), area_m2)
    return top, (top if top is not None else (simple if simple is not None else 0.0))


def plot_year(cfg, d_cm, h_m, area_m2: float, stand_age: float, curve, catch_up: float, started: bool) -> dict:
    """Each living tree's status for this year's height step.

    cfg: plot.height_status.  d_cm: DBH over bark, 0 for a tree with none; h_m: height; both for every living tree, as
    it stood at the end of last year.  stand_age: the plot's years so far (the season about to grow ends at stand_age + 1).
    curve: total age -> the curve's height (GrowthModel._curve_height).  started: whether the rule had started already.
    Returns {"status", "modifier", "ratio", "rdfl"} (arrays, the last three None before the start), "started", and "row",
    the plot-year's record."""
    rule = str(cfg.rule)
    if rule not in RULES:
        raise ValueError(f"plot.height_status.rule must be one of {RULES}, not {rule!r}")
    scale_over = str(getattr(cfg, "scale_over", "top_height"))
    if scale_over not in SCALES:
        raise ValueError(f"plot.height_status.scale_over must be one of {SCALES}, not {scale_over!r}")
    p = getattr(cfg, rule)
    d = np.asarray(d_cm, float)
    h = np.asarray(h_m, float)
    n = len(d)
    top_fit, top_h = top_heights(d, h, area_m2)
    row = {"rule": rule, "started": False, "top_height_m": round(float(top_h), 4),
           "top_height_approved_m": None if top_fit is None else round(float(top_fit), 4)}
    if not started:
        start_h = getattr(p, "start_top_height_m", None)
        start_age = getattr(p, "start_age_years", None)
        ready = bool(np.any(d > 0.0)) if start_h is None else top_h >= float(start_h)
        started = ready and (start_age is None or stand_age >= float(start_age))
    if not started or not np.any(d > 0.0):
        return {"status": np.ones(n), "modifier": None, "ratio": None, "rdfl": None, "started": bool(started), "row": row}
    top = thickest(d, h, area_m2)
    load = None
    if rule == "pine_1995":
        own = top
        dd = d[top][d[top] > 0.0]
        ddom = float(np.mean(dd))
        ih = float(np.clip(curve(stand_age + 5.0) - curve(stand_age), float(p.ih_min_m), float(p.ih_max_m)))
        ratio = np.clip(np.where(d > 0.0, d / ddom, float(p.ratio_min)), float(p.ratio_min), float(p.ratio_max))
        mod = pine_1995_modifier(ratio, ih, float(p.a1), float(p.a2), float(p.a3))
        row.update(dominant_dbh_cm=round(ddom, 4), ih_m=round(ih, 4))
    else:
        own = birch_dominants(d)
        ddom = float(np.mean(d[own]))
        per_tree = 1e4 / float(area_m2)
        load = np.minimum(rdfl(d, per_tree, p), float(p.rdfl_max))
        held = np.clip(np.where(d > 0.0, d, float(p.dbh_min_cm)), float(p.dbh_min_cm), float(p.dbh_max_cm))
        ratio = held / ddom
        mod = birch_2002_modifier(ratio, load, float(p.a1), float(p.a2), bool(p.planted))
        row.update(dominant_dbh_cm=round(ddom, 4), dg_cm=round(basal_area_mean_cm(d), 4),
                   rdf=round(float(np.sum(growing_space(d, p)) * per_tree), 4), rule_dominants=int(len(own)))
    dominants = top if scale_over == "top_height" else own
    mean_dom = float(np.mean(mod[dominants]))
    status = mod / mean_dom
    row.update(started=True, scale_over=scale_over, dominants=int(len(dominants)), dominants_mean_modifier=round(mean_dom, 6))
    if bool(getattr(cfg, "steer_top_height", False)):
        f = 1.0
        if top_fit is not None:
            step = curve(stand_age + 1.0) - curve(stand_age)
            f = float(np.clip((curve(stand_age + 1.0) - top_fit) / step, 0.0, float(catch_up))) if step > 0.0 else 1.0
        status = status * f
        row["steer_factor"] = round(f, 6)
    return {"status": status, "modifier": mod, "ratio": ratio, "rdfl": load, "started": True, "row": row}

