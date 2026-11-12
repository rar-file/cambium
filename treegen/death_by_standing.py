"""Death by standing: a forest tree's yearly chance of dying from its size and the trees larger than it, under the stand's
self-thinning line (species ``mortality.rule``; ``crowding``, today's rule, by default).

Build note: reports/design/2026-11-12_death_by_standing_build.md.  Design: reports/design/2026-11-12_stand_structure.md
(part M) and its challenge.

With ``mortality.rule: birch_2002``, in a natural plot with ``mortality.enabled``, these replace the crowding, suppressed
and background hazards of treegen/thinning.py once the rule has started.  Old age (thinning.Mortality.old_age_rate, zero
while damage.old_age is on), snow, wind and the carbon rule stay as they are.  Before the start, today's hazards act and
are drawn as today, from the same random stream.

Hynynen, Ojansuu, Hokka, Siipilehto, Salminen & Haapala 2002, Metla Research Papers 835:

* Eq. 47, Table 32 (pp. 50-51), "Deciduous, SC1-8": the chance that a tree dies of within-stand competition in the coming
  five years,

      p5 = 1 / (1 + exp(a0 + a1 d_s + a2 RDFL + a3 d_s RDFL)),   a0 3.014, a1 0.1015, a2 -9.313, a3 0.4073

  d_s the tree's stump diameter (cm; Eq. 3 p. 22: d_s = 2.0 + 1.25 DBH), RDFL the relative density factor of the trees
  larger than it (Eqs. 20-23, pp. 30-31).  The crowding term is (a2 + a3 d_s) RDFL: it raises the chance of dying only
  while d_s < -a2 / a3 = 22.87 cm (DBH 16.69 cm).  For a thicker tree, more larger neighbours make it LESS likely to
  die.  That is the printed equation; it is kept as printed, and the records count the trees past that size.
  Data (p. 24): five experiments, permanent plots in planted or naturally regenerated stands of silver and pubescent
  birch on fertile mineral soils, thinning experiments with untreated control plots; one 5-year period a stand; 7,427
  trees, 476 dead; plot mean age 17-50 years, dominant height 12.3-22.4 m, 370-3,051 stems/ha.  No diameter range is
  printed.

* The yearly hazard (DERIVED): a five-year chance p5 is a constant hazard h = -ln(1 - p5) / 5 a year.  Computed as
  softplus(-x) / 5, x the bracket above, which is the same number without rounding loss.

* The self-thinning line, Eq. 50 and Table 34 p. 53, silver birch: ln N = b0 + b1 ln D_gs, b0 14.1979, b1 -2.2178 (stems
  a hectare); D_gs = 2.0 + 1.25 D_g (Eq. 52 p. 55), D_g the mean DBH weighted by basal area (sum d^3 / sum d^2).  Under
  D_gs 12 cm the line is its tangent at 12 cm (pp. 56-57).  The report checks the stand against it at the end of each
  five-year step, on the stem numbers after Eq. 47's deaths (steps 1-4, p. 55), and where stems are over it multiplies
  every tree's stem number by N_max / N (Eqs. 57 and 61, pp. 57-58: evenly).  It also limits a step's cut to 1.5 times
  the line's own fall over the step (p. 57), for inventory plots whose stem numbers are imprecise.  The line's own data
  (Tables 8 and 11, pp. 21 and 23): untreated control plots, silver birch 10 stands, 17 plots, D_g 7.4-25.5 cm,
  572-6,484 stems/ha.  The model's young stand first meets the line at about 12-15 years, at D_g about 3 cm and about
  13,000 stems/ha: outside those data, on the tangent.

  Here, by default, the check is made every year, after the year's growth (line_every_years: 5 gives the report's
  spacing).  N is the expected number of trees with a DBH that live through this year under Eq. 47 (and old age), and
  D_g is weighted by the same chances, so the check stands where the report's does: at the end of the step, after
  Eq. 47.  If N is over the line, the year's deaths are raised until the expected survivors are on it, one of two ways
  (``over_line``):

  - ``evenly``, the report's own rule (Eq. 61): every counted tree's chance of living the year is multiplied by
    N_max / N, which is one added hazard, ln(N / N_max), the same for every tree;
  - ``by_odds``, the design's own choice, an estimate with no source: every counted tree's five-year odds of dying
    (p5 / (1 - p5)) are multiplied by one factor k, which is Eq. 47 with a0 lowered by ln k for every tree that year.

  Both aim at the line read at the D_g before the raise.  Evenly raises every tree alike, so D_g does not move and the
  expected survivors land exactly on the line.  By odds takes mostly small trees, so D_g rises and the line read after
  the deaths is a little lower: it leaves the stand a little over that line, about 0-2 % on the control's stands made
  10 % over it (the independent check's arithmetic; 11 % on a made-up stand of two sizes).  This is stated, not
  iterated away; the next year's check starts from the stand as it is.

  ``line_cut_limit`` (off, null; the report's is 1.5) keeps the expected survivors at no fewer than this year's counted
  trees less that many times the line's own fall since the last check.  That is a reading of the report's limit, which
  measures a step's whole fall from the stems at the step's start; with line_every_years 5 the two differ.

Shared with the height rule (treegen/height_status.py): the stump diameter (Eq. 3), the growing space and RDFL
(Eqs. 21-23), the self-thinning line (Eq. 50) and D_g, as functions, and their values, read from
``plot.height_status.birch_2002`` (stump_a_cm, stump_b, self_thinning_b0, self_thinning_b1), so the two rules can never
read two lines.  RDFL here is not held at the height data's rdfl_max: the survival data's range of RDF is not printed.

Choices (the build note gives the reasons):

* DBH over bark, cm, to 0.01 cm, and height to 0.001 m, as a tree list holds them, on the stand as it stands when the
  year's deaths are drawn (after its growth, its damage and the carbon rule).  Every tree of the plot stands for
  10^4 / area stems a hectare; RDF and RDFL are read over the whole plot.
* A tree with no DBH (under 1.3 m): d = 0, so d_s = 2.0 cm by Eq. 3, and every tree with a DBH is larger than it (its
  RDFL is the stand's RDF).  It is not counted in the line's stems and its hazard is never raised by the line, since the
  report's inventories count trees past breast height.  This is harsh: under a stand at RDF 0.8 such a tree dies at about
  51 % a year, so with regeneration on the rule would kill almost every seedling, gap or not (SUSPECTED until a run
  with regeneration is made; the build note's limits).
* The start: once the stand is start_age_years old (12, the design's choice and the height rule's own start) and, if
  set, its top height (approved definition, as the height rule reads it) has reached start_top_height_m.  Then it stays
  on.  Before 17 years, past 50, outside 12.3-22.4 m of top height or 370-3,051 stems/ha (the data's limits, p. 24) the
  rule is extrapolated: each plot-year's record says which limits it is outside.
* The random stream: the plot's own mortality stream (treegen/plot.py, mort_rng, seeded [seed, 5381]), the one today's
  rule draws from.  Each year, one uniform for each living tree in the plot's order: it dies if the uniform is under
  1 - exp(-total hazard); then, for each tree that dies, one more uniform picks its cause in proportion to its hazards
  (as thinning.Mortality.draw).  A run repeats exactly.
"""
from __future__ import annotations

import math

import numpy as np

from . import height_status as hs

RULES = ("crowding", "birch_2002")
OVER_LINE = ("evenly", "by_odds")
CAUSES = ("competition", "self-thinning line", "old age")

# What a plot-year's record holds (log.stand; tools/forest.py writes it into stand_log.json as death_rule_what)
RECORD_WHAT = {
    "rule": "mortality.rule; this record exists only with it birch_2002",
    "started": "whether the rule acts this year; before it starts, today's hazards act (treegen/thinning.py)",
    "over_line": "mortality.birch_2002.over_line: how deaths are raised over the line, evenly (Eq. 61) or by_odds (the design's estimate). Both aim at "
                 "the line at the D_g before the raise; evenly lands on it, by_odds leaves the stand a little over the line read after the deaths "
                 "(about 0-2 % on the control's stands)",
    "stand_age": "plot year: the stand's age at the end of this season, when the year's deaths are drawn",
    "top_height_m": "top height the start and the data limits read: the approved definition, or the 100 thickest's mean height while the curve can't be fitted",
    "stems_ha": "living trees with a DBH a hectare, before this year's deaths by this rule",
    "trees_no_dbh": "living trees with no DBH, not counted in stems_ha",
    "rdf": "the stand's relative density factor, sum of growing spaces (Eqs. 21-22) a hectare, over the trees with a DBH",
    "dg_cm": "D_g over bark, the mean DBH weighted by basal area, each tree weighted by its chance of living the year under Eq. 47 (and old age)",
    "dgs_cm": "D_gs = 2.0 + 1.25 D_g (Eq. 52)",
    "line_stems_ha": "stems a hectare on the silver birch self-thinning line at D_gs (Eq. 50; its tangent at 12 cm below 12 cm). The line's own data "
                     "(Table 11 p. 23): D_g 7.4-25.5 cm, 572-6,484 stems a hectare; outside them the line is extrapolated",
    "line_share": "stems_ha over line_stems_ha, before this year's deaths",
    "expected_survivors_ha": "trees with a DBH expected to live the year under Eq. 47 (and old age) alone, a hectare",
    "line_check": "whether the line is checked this year (every line_every_years from the start)",
    "line_target_ha": "the stems a hectare the line allows this year: the line, or more under line_cut_limit",
    "line_binds": "whether expected survivors were over line_target_ha, so the line raised deaths",
    "line_added_hazard": "evenly: the hazard a year added to every counted tree, ln(N / N_max); 0 when the line didn't bind",
    "line_ln_k": "by_odds: ln of the factor on every counted tree's five-year odds of dying; 0 when the line didn't bind",
    "line_added_deaths_expected": "deaths the line added, expected: the sum over trees of the raise in each one's chance of dying this year",
    "deaths": "trees that died of this rule this year, by drawn cause",
    "flip_dbh_cm": "DBH over which Eq. 47's crowding term (a2 + a3 d_s) RDFL turns negative, -a2 / a3 as a stump diameter, through Eq. 3",
    "past_flip_share": "share of the trees with a DBH that are thicker than flip_dbh_cm",
    "outside_data": "the survival data's limits (Hynynen et al. 2002 p. 24) the stand is outside this year: age (17-50), top_height (12.3-22.4 m), stems (370-3,051 a hectare)",
    "trees": "started years only, one entry per living tree before this year's deaths, in the plot's order: id; d_cm, the DBH read (0: none); rdfl; "
             "p5, Eq. 47's five-year chance; hazard, the rule's total hazard a year (competition + line + old age); line, the hazard a year the line "
             "added (0: none); raised, 1 where the line raised it",
}


# -- the printed equations ---------------------------------------------------------------------------------------------
def eq47_logit(ds_cm, rdfl, a0: float, a1: float, a2: float, a3: float):
    """The bracket of Eq. 47 (p. 50): x = a0 + a1 d_s + a2 RDFL + a3 d_s RDFL, so p5 = 1 / (1 + exp(x))."""
    ds = np.asarray(ds_cm, float)
    r = np.asarray(rdfl, float)
    return a0 + a1 * ds + a2 * r + a3 * ds * r


def p5_from_logit(x):
    """Eq. 47's chance of dying in five years, 1 / (1 + exp(x)) = exp(-softplus(x)), without overflow."""
    return np.exp(-np.logaddexp(0.0, np.asarray(x, float)))


def yearly_hazard(x, period_years: float):
    """The constant yearly hazard of a five-year chance p5 = 1 / (1 + exp(x)): -ln(1 - p5) / period = softplus(-x) / period."""
    return np.logaddexp(0.0, -np.asarray(x, float)) / float(period_years)


def hazard_from_p5(p5, period_years: float):
    """The same from p5 itself: -ln(1 - p5) / period."""
    return -np.log1p(-np.asarray(p5, float)) / float(period_years)


def flip_dbh_cm(p, line) -> float:
    """The DBH (cm) past which Eq. 47's crowding term (a2 + a3 d_s) RDFL is negative: d_s = -a2 / a3, through Eq. 3."""
    a2, a3 = float(p.a2), float(p.a3)
    if a3 == 0.0:
        return math.inf
    return (-a2 / a3 - float(line.stump_a_cm)) / float(line.stump_b)


def line_stems_ha(dgs_cm: float, line, tangent_below_cm) -> float:
    """Stems a hectare on the self-thinning line at D_gs (Eq. 50, Table 34 p. 53); under tangent_below_cm (12 cm, p. 57) the
    line's tangent there: N(D_t) (1 + b1 (D - D_t) / D_t).  None: the curve all the way."""
    b0, b1 = float(line.self_thinning_b0), float(line.self_thinning_b1)
    if tangent_below_cm is not None and dgs_cm < float(tangent_below_cm):
        dt = float(tangent_below_cm)
        nt = float(hs.self_thinning_stems(dt, b0, b1))
        return nt * (1.0 + b1 * (dgs_cm - dt) / dt)
    return float(hs.self_thinning_stems(dgs_cm, b0, b1))


def dg_weighted_cm(d_cm, weights) -> float:
    """D_g, sum w d^3 / sum w d^2, over the trees with a DBH; 0 if none (weights all 1: height_status.basal_area_mean_cm)."""
    d = np.asarray(d_cm, float)
    w = np.asarray(weights, float)
    on = d > 0.0
    den = float(np.sum(w[on] * d[on] ** 2))
    return float(np.sum(w[on] * d[on] ** 3)) / den if den > 0.0 else 0.0


# -- the line's raise ----------------------------------------------------------------------------------------------------
def raise_evenly(survival, counted, target: float) -> float:
    """Eq. 61: the hazard a year that, added to every counted tree, brings their expected survivors from sum(survival) to
    target.  0 if they are not over it."""
    s = float(np.sum(np.asarray(survival, float)[np.asarray(counted, bool)]))
    return math.log(s / target) if target > 0.0 and s > target else 0.0


def raise_by_odds(x, other, counted, target: float, period_years: float) -> float:
    """ln k: the one factor on every counted tree's five-year odds of dying (Eq. 47's x lowered by ln k) that brings their
    expected survivors to target, by bisection; 0 if they are not over it.  other: the tree's other hazards a year."""
    c = np.asarray(counted, bool)
    xc = np.asarray(x, float)[c]
    oc = np.asarray(other, float)[c]

    def survivors(lnk: float) -> float:
        return float(np.sum(np.exp(-(yearly_hazard(xc - lnk, period_years) + oc))))

    if target <= 0.0 or not len(xc) or survivors(0.0) <= target:
        return 0.0
    lo, hi = 0.0, 1.0
    while survivors(hi) > target:
        lo, hi = hi, 2.0 * hi
        if hi > 1e6:
            break
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if survivors(mid) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-12 * max(1.0, hi):
            break
    return hi


# -- one plot-year -------------------------------------------------------------------------------------------------------
def outside_data(p, stand_age: float, top_height_m: float, stems_ha: float) -> list:
    """Which of the survival data's limits (p. 24) the stand is outside: age, top_height, stems."""
    out = []
    for name, value, lim in (("age", stand_age, p.data_age_years), ("top_height", top_height_m, p.data_top_height_m),
                             ("stems", stems_ha, p.data_stems_per_ha)):
        if value < float(lim[0]) or value > float(lim[1]):
            out.append(name)
    return out


def _six(v) -> float:
    return float(f"{float(v):.6g}")


def plot_year(p, line, d_cm, h_m, other, area_m2: float, stand_age: float, state: dict) -> dict:
    """The rule's year for every living tree, before the year's deaths are drawn.

    p: mortality.birch_2002.  line: plot.height_status.birch_2002 (the stump diameter and the self-thinning line).  d_cm:
    DBH over bark, 0 for a tree with none; h_m: height; other: each tree's other hazards a year this rule keeps (old age).
    stand_age: the plot's year.  state: the plot's own record of the rule, {"started", "start_year", "line_prev"}, changed
    here.  Returns {"started", "hazards" (by cause, arrays; None before the start), "row" (the plot-year's record),
    "trees" (the per-tree record; None before the start)}."""
    over = str(p.over_line)
    if over not in OVER_LINE:
        raise ValueError(f"mortality.birch_2002.over_line must be one of {OVER_LINE}, not {over!r}")
    d = np.asarray(d_cm, float)
    h = np.asarray(h_m, float)
    old = np.asarray(other, float)
    n = len(d)
    per_tree = 1e4 / float(area_m2)
    counted = d > 0.0
    _, top_h = hs.top_heights(d, h, area_m2)
    if not state.get("started"):
        start_h = getattr(p, "start_top_height_m", None)
        start_age = getattr(p, "start_age_years", None)
        if (start_age is None or stand_age >= float(start_age)) and (start_h is None or top_h >= float(start_h)):
            state["started"], state["start_year"] = True, float(stand_age)
    started = bool(state.get("started"))
    # Eq. 47 for every tree: a tree with no DBH has d = 0 (d_s 2.0) and every tree with a DBH above it
    ds = hs.stump_cm(d, float(line.stump_a_cm), float(line.stump_b))
    rdfl = hs.rdfl(d, per_tree, line)
    x = eq47_logit(ds, rdfl, float(p.a0), float(p.a1), float(p.a2), float(p.a3))
    period = float(p.period_years)
    h47 = yearly_hazard(x, period)
    live = np.exp(-(h47 + old))
    stems_ha = float(np.sum(counted)) * per_tree
    dg = dg_weighted_cm(d, live)
    row = {"rule": "birch_2002", "started": started, "over_line": over, "stand_age": float(stand_age), "top_height_m": round(float(top_h), 4),
           "stems_ha": round(stems_ha, 3), "trees_no_dbh": int(n - np.sum(counted)),
           "rdf": round(float(np.sum(hs.growing_space(d, line))) * per_tree, 6), "dg_cm": round(dg, 4)}
    flip = flip_dbh_cm(p, line)
    row["flip_dbh_cm"] = round(flip, 4)
    row["past_flip_share"] = round(float(np.mean(d[counted] > flip)), 4) if np.any(counted) else 0.0
    row["outside_data"] = outside_data(p, float(stand_age), float(top_h), stems_ha)
    line_now = None
    if dg > 0.0:
        dgs = float(line.stump_a_cm) + float(line.stump_b) * dg
        line_now = line_stems_ha(dgs, line, getattr(p, "line_tangent_below_cm", None))
        row.update(dgs_cm=round(dgs, 4), line_stems_ha=round(line_now, 3), line_share=round(stems_ha / line_now, 6))
    survivors_ha = float(np.sum(live[counted])) * per_tree
    row["expected_survivors_ha"] = round(survivors_ha, 3)
    if not started:
        if line_now is not None:
            state["line_prev"] = line_now
        return {"started": False, "hazards": None, "row": row, "trees": None}
    every = int(getattr(p, "line_every_years", 1) or 1)
    check = line_now is not None and int(round(float(stand_age) - float(state["start_year"]))) % every == 0
    added = np.zeros(n)
    row.update(line_check=bool(check), line_binds=False, line_added_hazard=0.0, line_ln_k=0.0, line_added_deaths_expected=0.0)
    if check:
        target_ha = line_now
        limit = getattr(p, "line_cut_limit", None)
        prev = state.get("line_prev")
        if limit is not None and prev is not None:
            target_ha = max(target_ha, stems_ha - float(limit) * max(float(prev) - line_now, 0.0))
        target = target_ha / per_tree
        row["line_target_ha"] = round(target_ha, 3)
        if survivors_ha > target_ha:
            row["line_binds"] = True
            if over == "evenly":
                extra = raise_evenly(live, counted, target)
                added = np.where(counted, extra, 0.0)
                row["line_added_hazard"] = _six(extra)
            else:
                lnk = raise_by_odds(x, old, counted, target, period)
                added = np.where(counted, yearly_hazard(x - lnk, period) - h47, 0.0)
                row["line_ln_k"] = _six(lnk)
            row["line_added_deaths_expected"] = round(float(np.sum(live * (1.0 - np.exp(-added)))), 4)
        state["line_prev"] = line_now
    hazards = {"competition": h47, "self-thinning line": added, "old age": old}
    total = h47 + added + old
    trees = {"d_cm": [round(float(v), 2) for v in d], "rdfl": [_six(v) for v in rdfl], "p5": [_six(v) for v in p5_from_logit(x)],
             "hazard": [_six(v) for v in total], "line": [_six(v) for v in added], "raised": [int(v > 0.0) for v in added]}
    return {"started": True, "hazards": hazards, "row": row, "trees": trees}


def draw(hazards: dict, rng) -> list:
    """Which trees die this year: (position, cause).  One uniform a tree, in order: it dies if the uniform is under
    1 - exp(-total); then one more uniform for each tree that dies picks its cause in proportion to its hazards."""
    h = np.stack([np.asarray(hazards[c], float) for c in CAUSES], 1)
    total = h.sum(1)
    die = np.nonzero(rng.random(len(total)) < 1.0 - np.exp(-total))[0]
    out = []
    for n in die.tolist():
        pick = rng.random() * total[n]
        out.append((n, CAUSES[min(int(np.searchsorted(np.cumsum(h[n]), pick)), len(CAUSES) - 1)]))
    return out
