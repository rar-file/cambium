"""Records for the reports (species block ``log``; both switches off by default).

Nothing here changes what a tree or a plot grows.  Each function only reads the model, or works on numbers the model had
already worked out when it was called.  tests/test_logging.py grows trees and plots with every log on and off and compares
them; tools/golden.py leaves ``log.*`` settings out of its hashes, as it does ``speed.*``, so a run with the logs on can
be compared with one without.

* ``log.rings``: a tree keeps how each year's rings split, as they were laid: stem and branches, and for each the sapwood
  that replaces what stopped conducting, the sapwood more foliage asks for, and the wind's extra; and each limb's own
  share (``model._ring_log``, written by note_rings below; tools/tree_table.py saves it).
* ``log.stand``: a plot keeps a row a year (``plot.stand_log``): the stem volume of the trees that went, top height on the
  approved definition, the leaf area the year's light was worked out from, and how many leaders light, water or carbon
  held back; and each tree that went, as it stood in its last year (``plot.tree_log``).  tools/forest.py saves both.

Kept without a switch, because each is one number a tree-year that the model has in hand: ``model._must_log`` (what the
year had to pay before any side shoot, the pool it had, and the share of those rings it paid),
``model.sapwood_short_years`` (how many years the pool didn't cover them) and ``model._lit_leaf_m2`` (the leaf area the
tree's buds carried when the year's light was worked out).
"""
from __future__ import annotations

import math

import numpy as np

# tools/bark.py's birch values, for a plot whose species has no mortality block (as tools/tree_list.py)
BARK = (-0.48552367, 0.04957885, 0.84676248)
RING_PARTS = ("replaced", "more_leaf", "wind")


def on(species, name: str) -> bool:
    """Is this log on?  (Species files and models from before the logs existed: no.)"""
    return bool(getattr(getattr(species, "log", None), name, False))


def wood_volumes(model) -> tuple:
    """(stem, branches): wood volume now, m3.  Every living internode is a cylinder, pi r^2 L; the stem is the leader chain
    from the base to its tip, the branches everything else alive.  Wood only: the model has no bark.  The definitions
    and the sums of tools/tree_table.py's snapshot and of tools/m3_wood.py."""
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    volume = np.where(alive, math.pi * T.radius[:n] ** 2 * T.length[:n], 0.0)
    stem_nodes = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
    stem = float(volume[stem_nodes].sum())
    return stem, float(volume.sum()) - stem


def leaf_areas(model) -> dict:
    """The tree's leaf area now, two ways (m2).  sized: each leaf at its own size, which is what the model reports as
    leaf_area_m2 and what shades: T.leaves holds leaves x expansion x (the leaf's size over the reference size), see
    GrowthModel._leaves_at_nodes and light_sources.  counted: the same leaves each at the reference size
    (light.leaf_area_m2) and unshrunk, so the two differ by the sun-and-shade rule and the expansion alone."""
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    held = np.where(alive, T.leaves[:n], 0.0).astype(float)
    factor = T.leaf_scale[:n] * model._size_rel(np.arange(n))
    count = np.divide(held, factor, out=np.zeros(n), where=factor > 0.0)
    a_ref = float(model.light.leaf_area)
    return {"leaf_area_counted_m2": float(count.sum()) * a_ref, "leaf_area_sized_m2": float(held.sum()) * a_ref}


def grew_this_year(model) -> bool:
    """Did the year's carbon solve run for this tree?  (Not for a tree with no living bud left.)"""
    must = getattr(model, "_must_log", None)
    return bool(must) and must.get("year") == model.year


def tree_record(model) -> dict:
    """One tree as it stands, for a list of a plot's trees (tools/tree_list.py): wood volumes, leaf area two ways and
    as the year's light had it, what held its leader this year, and the years it couldn't pay its sapwood.

    leader_light: relative light at the leader's bud, the field layer's shade taken out.  light_factor, water_factor,
    carbon_factor: what each left of the curve's step this year (1: not held back), as the tree's yearly row has them
    (GrowthModel._height_limit_log).  All four are None in a year the tree had no leader to limit."""
    stem, branch = wood_volumes(model)
    out = {"stem_m3": stem, "branch_m3": branch, **leaf_areas(model), "leaf_area_lit_m2": getattr(model, "_lit_leaf_m2", None),
           "leader_light": None, "light_factor": None, "water_factor": None, "carbon_factor": None,
           "sapwood_short_years": int(getattr(model, "sapwood_short_years", 0))}
    if grew_this_year(model) and getattr(model, "_hd", None) is not None and model.stats:
        row = model.stats[-1].get("height_limit") or {}
        out.update(leader_light=row.get("light_q"), light_factor=row.get("light"), water_factor=row.get("water"), carbon_factor=row.get("carbon"))
    return out


def naslund_top_height(d_cm, h_m, area_m2: float) -> tuple:
    """Top height on the approved definition, as tools/scorecard.py's naslund_top_height works it out (the same sums in
    the same order; tests/test_logging.py holds the two together).  Elfving 2010 p. 58: "the height according to the
    height curve at the mean diameter of the 100 by diameter largest trees per hectare".  The curve is Naslund's,
    h = 1.3 + d^2 / (a + b d)^2, fitted to the living trees as a straight line of d / sqrt(h - 1.3) on d; the last tree
    counts with its fractional share.  Returns (height on the curve, trees counted, those trees' mean height); nan with
    fewer than three trees past breast height."""
    rows = [(float(d), float(h)) for d, h in zip(d_cm, h_m) if d and h]
    n = 100.0 * area_m2 / 1e4
    usable = [(d, h) for d, h in rows if h > 1.3]
    if len(usable) < 3:
        return float("nan"), 0.0, float("nan")
    d_all, h_all = np.array([x[0] for x in usable]), np.array([x[1] for x in usable])
    b, a = np.polyfit(d_all, d_all / np.sqrt(h_all - 1.3), 1)
    w_sum = d_sum = h_sum = 0.0
    for d, h in sorted(rows, key=lambda x: x[0], reverse=True):
        w = min(1.0, n - w_sum)
        if w <= 0.0:
            break
        w_sum += w
        d_sum += w * d
        h_sum += w * h
    mean_d = d_sum / w_sum
    return 1.3 + mean_d * mean_d / (a + b * mean_d) ** 2, w_sum, h_sum / w_sum


def fitted_top_height(d_cm, h_m, area_m2: float) -> tuple:
    """naslund_top_height for a yearly log: None, not nan, where there is no height to give, and None too where numpy says
    the curve is poorly fitted (a stand just past breast height, its few diameters too alike).  The trees counted and their
    mean height are given either way."""
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        top, counted, simple = naslund_top_height(d_cm, h_m, area_m2)
    poor = any("Polyfit" in str(w.message) for w in caught)
    return (None if poor or top != top else float(top)), float(counted), (None if simple != simple else float(simple))


def limb_starts(model, n: int, alive: np.ndarray) -> np.ndarray:
    """First nodes of the living limbs among the first n nodes: side axes on the stem or on a leader that replaced it
    (tools/tree_table.py's first-order branches, and stats.limbs_on_leader)."""
    T = model.tree
    on_lead = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    return np.nonzero(alive & T.is_lateral[:n] & ~on_lead & on_lead[np.maximum(T.parent[:n], 0)])[0]


def note_rings(model, year: int, ring, need, keep, sap, length, unit: float, levels, alive, share: float = 1.0) -> None:
    """log.rings: how this year's rings split, in carbon units (the pool's), kept as model._ring_log.  Reads only.

    ring: the ring laid on each node (m2), as GrowthModel._growth_factor hands it back.  need: the sapwood the foliage
    beyond each node asks for (Huber value x leaf area beyond, new shoots' leaves included; m2).  keep: last year's
    sapwood less what stopped conducting.  sap: last year's sapwood.  length: internode lengths, 0 at dead nodes.
    unit: m3 of wood a unit of carbon builds.  share: in a year the pool didn't cover the year's must-haves, the
    share of their rings it paid; the split is of what was laid.

    Per node the ring is three parts, which add up to it:
    * more_leaf: sapwood for foliage beyond what last year's sapwood carried, max(need - sap, 0);
    * replaced: the rest of the sapwood rule's ring, max(need - keep, 0), which makes up for sapwood that stopped
      conducting (pipe_model.sapwood_senescence_per_year, and branch_sapwood_senescence on side axes);
    * wind: whatever was laid beyond that: the wind's extra, and for a tree with no neighbours the surplus put on
      the stem.
    The stem is the leader chain, as tools/tree_table.py's stem wood; branch is every other living node.  The limb_
    arrays give each living limb its subtree's three parts; limb_node is the limb's first node as numbered when the
    rings were worked out, with its birth year and its height on the stem beside it."""
    T = model.tree
    n0 = len(alive)
    ring = np.asarray(ring, float)
    sapwood = np.minimum(np.maximum(need - keep, 0.0) * share, ring)
    more = np.minimum(np.maximum(need - sap, 0.0) * share, sapwood)
    parts = np.stack([sapwood - more, more, ring - sapwood], 1) * (np.asarray(length, float) / unit)[:, None]
    stem = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
    on_stem = np.zeros(n0, bool)
    on_stem[stem[stem < n0]] = True
    first = limb_starts(model, n0, alive)
    by_limb = T.basipetal(levels, parts)[first]
    model._ring_log = {"year": int(year),
                       "stem": {k: float(v) for k, v in zip(RING_PARTS, parts[on_stem].sum(0))},
                       "branch": {k: float(v) for k, v in zip(RING_PARTS, parts[alive & ~on_stem].sum(0))},
                       "limb_node": first, "limb_birth": T.birth[first].astype(np.int64), "limb_z": T.pos[T.parent[first], 2].copy(),
                       **{f"limb_{k}": by_limb[:, i].copy() for i, k in enumerate(RING_PARTS)}}


STAND_LOG_WHAT = {
    "year": "plot year; the row is the plot at the end of that year",
    "trees": "living trees at the end of the year",
    "top_height_approved_m": "top height on the approved definition (treegen/logs.py naslund_top_height, as tools/scorecard.py): a Naslund curve fitted to the "
                             "living trees, read at the mean diameter of the 100 thickest a hectare; diameters over bark to 0.01 cm and heights to 0.001 m, "
                             "as a tree list holds them; null with fewer than three trees past 1.3 m, or while their diameters are too alike for the curve "
                             "to be fitted (numpy's warning)",
    "top_height_trees": "how many trees that mean diameter is of (the last with its fractional share)",
    "top_height_mean_m": "those trees' mean height, the plot's own top height",
    "dead_trees": "trees that went this year, whatever the cause (thinned ones too)",
    "dead_stem_m3": "their stem wood volume as they stood in their last year, m3 on the plot: the leader chain's living internodes, pi r^2 L, wood only, no bark, no stump taken off",
    "dead_stem_m3_ha": "the same a hectare",
    "dead_stem_m3_by_cause": "the same on the plot, by cause",
    "lai": "leaf area index as the plot reports it: the trees' leaf area at the end of the year, each leaf at its own size",
    "lai_lit": "the leaf area index this year's light was worked out from: the buds' leaf weights at the start of the season x the reference leaf area, "
               "each leaf at its own size too, before the year's new shoots",
    "trees_grew": "trees whose carbon solve ran this year (a tree with no living bud has none)",
    "leaders": "of those, trees with a leader under the height limit",
    "light_slowed": "leaders whose light factor was under 1 (light at the leader under height_driver.light_full)",
    "water_slowed": "leaders whose water factor was under 1",
    "carbon_cut": "leaders whose own shoot cost more than the tree's whole pool, and was cut",
    "short_of_sapwood": "trees whose pool didn't cover the year's must-haves (the leader's shoot, the frame's limbs and the foliage's sapwood), so their rings were cut by share",
}
