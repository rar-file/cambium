"""A plot-year as a plain list of trees, in JSON: what a stand template could be made from.

    python tools/forest.py run --seed 1 --area 1000 --years 60 --tree-lists 20,30,40,50,60 --out out/forest/a
        # writes out/forest/a/trees_020.json and so on, as the run passes those years
    python tools/tree_list.py out/some_plot --out trees.json
        # from a tools/plot.py folder with a checkpoint: the year that checkpoint holds

Each tree: position in metres from the plot's centre (the plot repeats at its edges, so a list tiles),
species, age, height, DBH over bark (null below 1.3 m), crown base, crown width, alive or dead.  A dead
tree is given as it was in its last year, with the year it died and why; the model has no standing
dead, so dead_years only says how long back to list them.  No decay or fall is implied.

Since 2026-11-11 each tree also has the plot year its first season followed, its drawn vigour, its stem
and branch wood and stem volume, its leaf area counted two more ways, the light at its leader and what
held its leader this year, and the years it couldn't pay its sapwood (treegen/logs.py tree_record).  A
living tree has them always.  A dead one has the first two always and the rest only from a run with
log.stand on, which keeps each tree as it went.

From a plot with plot.height_status on (treegen/height_status.py), each tree also has the status that
multiplied its height step this year and how the rule worked it out, and the list's header the rule's
plot-year (height_status_year).  A list from a plot without the switch has none of these.

From a plot with log.stem_tops on (treegen/logs.py, 2026-11-12), each tree also has stem_top_m beside height_m: the
top of its stem, where height_m is its highest living point, which can be a limb's.  Both are as the tree's last
yearly row measured them.  A list from a plot without the log has no such column.
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from treegen import logs  # noqa: E402
from treegen.thinning import over_bark_cm  # noqa: E402

BARK = (-0.48552367, 0.04957885, 0.84676248)     # tools/bark.py; for plots whose species has no mortality block
DENSITY = 530.0                                  # kg of dry wood a m3, the stem's basic density, as tools/tree_table.py and tools/m3_wood.py have it


def _row(id_: int, x: float, y: float, species: str, last: dict, bark, info: dict | None = None, record: dict | None = None) -> dict:
    wood = last.get("dbh_cm")
    info = info or {}
    return {"id": id_, "x_m": round(x, 3), "y_m": round(y, 3), "species": species, "age_years": int(last["age_years"]),
            "height_m": round(float(last["height_m"]), 3),
            # log.stem_tops, only from a plot with it on: the stem's own top beside the height, which is the highest living point
            **({"stem_top_m": None if last["stem_top_m"] is None else round(float(last["stem_top_m"]), 3)} if "stem_top_m" in last else {}),
            "dbh_cm": None if wood is None else round(float(over_bark_cm(wood, bark)), 2),
            "crown_base_m": None if last.get("crown_base_height_m") is None else round(float(last["crown_base_height_m"]), 3),
            "crown_width_m": round(float(last.get("crown_width_m") or 0.0), 3),
            **{k: (None if last.get(k) is None else round(float(last[k]), 4)) for k in EXTRA},
            "germination_year": info.get("germination"), "vigour": info.get("vigour"), **_more(record)}


# For checks on young trees (2026-11-09): leaf area and leaf dry mass, the stem's wood diameter at 5 cm (a stand-in for a stem-base
# diameter), the lowest live branch, and the carbon fixed and turned down this year (sink_limited).  Null where a row doesn't carry them.
EXTRA = ("leaf_area_m2", "leaf_dm_g", "d0_wood_cm", "lowest_live_branch_m", "carbon_fixed", "carbon_sink_limited")

# From a tree's record (treegen/logs.py tree_record), 2026-11-11.  Wood is wood only, no bark, at DENSITY; the stem is the leader chain and
# the branches every other living internode, as tools/tree_table.py's snapshot.  leaf_area_sized_m2 counts each leaf at its own size,
# as leaf_area_m2 does (the two differ only where a top broke after the year's row was written); leaf_area_counted_m2 counts the same
# leaves each at the reference leaf area; leaf_area_lit_m2 is what the tree's buds carried when the year's light was worked out, before
# its new shoots.  leader_light is the relative light at the leader's bud; light_factor, water_factor and carbon_factor are what each
# left of the curve's step this year (1: not held back).  sapwood_short_years: years, so far, in which the tree's pool didn't cover
# the year's must-haves, so its rings were cut by share.
MORE = ("stem_kg", "branch_kg", "stem_m3", "leaf_area_counted_m2", "leaf_area_sized_m2", "leaf_area_lit_m2", "leader_light", "light_factor",
        "water_factor", "carbon_factor", "sapwood_short_years")


def _six(v):
    """A number to six figures; None and whole counts as they are."""
    return v if v is None or isinstance(v, int) else float(f"{float(v):.6g}")


# plot.height_status, only from a plot with it on (treegen/height_status.py): the status that multiplied the tree's height step
# this year, the rule's modifier before the dominants' mean divided it, d over the dominants' diameter as the rule held it, and
# (rule birch_2002) the relative density factor of the larger trees.  Columns a list without the switch doesn't have at all.
STATUS = ("height_status", "height_modifier", "height_ratio", "height_rdfl")


def _more(record: dict | None) -> dict:
    """A record's columns; null for a row with no record."""
    if record is None:
        return {k: None for k in MORE}
    got = {**record, "stem_kg": record["stem_m3"] * DENSITY, "branch_kg": record["branch_m3"] * DENSITY}
    out = {k: _six(got.get(k)) for k in MORE}
    if "height_status" in record:
        out.update({k: _six(record.get(k)) for k in STATUS})
    return out


def _base_wood_cm(model, at_m: float = 0.05):
    T = model.tree
    trunk = T.trunk_chain(model.leader_axes)
    z, r = T.pos[trunk, 2], T.radius[trunk]
    if len(trunk) < 2 or z.max() < at_m:
        return None
    j = max(int((z >= at_m).argmax()), 1)
    f = (at_m - z[j - 1]) / max(z[j] - z[j - 1], 1e-9)
    return 200.0 * float(r[j - 1] + f * (r[j] - r[j - 1]))


def last_year_of(model) -> dict:
    """What a list needs from a living tree's last yearly row."""
    s = model.stats[-1]
    c = s.get("carbon") or {}
    out = {"age_years": model.year, "height_m": s["height_m"], "dbh_cm": s.get("dbh_cm"),
           "crown_base_height_m": s.get("crown_base_height_m"), "crown_width_m": s.get("crown_width_m"),
           "leaf_area_m2": s.get("leaf_area_m2"), "leaf_dm_g": c.get("leaf_dm_g"), "d0_wood_cm": _base_wood_cm(model),
           "lowest_live_branch_m": s.get("lowest_live_branch_m"), "carbon_fixed": c.get("fixed"), "carbon_sink_limited": c.get("sink_limited")}
    if logs.on(model.sp, "stem_tops"):
        out["stem_top_m"] = model.stem_top_measured()
    return out


def tree_list(plot, dead_years: int = 10, run: dict | None = None) -> dict:
    """The plot as it stands at the end of plot.year, and what died in the dead_years before it."""
    species = plot.species.species.scientific_name
    bark = getattr(getattr(plot.species, "mortality", None), "bark_double_mm", BARK)
    sides = plot._sides()
    went = getattr(plot, "tree_log", None) or {}      # log.stand: each tree that went, as it stood
    status = {}
    if getattr(plot, "_status_cfg", None) is not None:
        status = {"height_status": "plot.height_status (treegen/height_status.py), rule " + str(plot._status_cfg.rule) + ": height_status multiplied the "
                                   "tree's height step this year in place of its drawn vigour; height_modifier is the rule's modifier before the dominants' "
                                   "mean divided it, height_ratio d over the dominants' diameter as the rule held it, height_rdfl the relative density "
                                   "factor of the larger trees (rule birch_2002); all from the stand at the end of the year before",
                  "height_status_year": dict(getattr(plot, "_status_row", None) or {})}
    stem = logs.on(plot.species, "stem_tops")
    gone = getattr(plot, "stem_tops_gone", None) or {}      # log.stem_tops: the stem top of each tree that went, as its last yearly row measured it
    stem_note = {"stem_top": "stem_top_m (log.stem_tops): the top of the tree's stem, the last node of the leader chain, which is what the height curve limits; "
                             "height_m is the tree's highest living point, which can be a limb's second top or fork above the stem; both as the tree's "
                             "last yearly row measured them"} if stem else {}
    trees = []
    for k in plot.alive:
        i = plot.info[k]
        trees.append(dict(_row(k, i["x"], i["y"], species, last_year_of(plot.trees[k]), bark, i, logs.tree_record(plot.trees[k])), alive=True))
    for i in plot.info:
        removed = i.get("removed")
        if removed is None or removed <= plot.year - dead_years or "last" not in i:
            continue
        last = dict(i["last"], stem_top_m=gone.get(i["id"])) if stem else i["last"]
        trees.append(dict(_row(i["id"], i["x"], i["y"], species, last, bark, i, went.get(i["id"])), alive=False, died_year=removed, cause=i.get("cause")))
    return {"plot_year": plot.year, "years_since_stand_began": plot.year, "side_x_m": sides[0], "side_y_m": sides[1], "area_m2": plot.area,
            "repeats_at_edges": True, "origin": "centre of the plot", "dbh": "over bark at 1.3 m, tools/bark.py; null below 1.3 m",
            "crown_width": "mean of the widths along x and y",
            "wood": f"stem_kg and branch_kg: dry wood at {DENSITY:g} kg/m3, no bark; stem_m3: the stem's wood volume; the stem is the leader chain, the branches every other living internode",
            "leaf_area": "leaf_area_m2 and leaf_area_sized_m2: each leaf at its own size; leaf_area_counted_m2: each at the reference leaf area; "
                         "leaf_area_lit_m2: what the buds carried when the year's light was worked out",
            "leader": "leader_light: relative light at the leader's bud; light_factor, water_factor, carbon_factor: what each left of the curve's step this year; "
                      "sapwood_short_years: years the pool didn't cover the year's must-haves",
            "germination": "germination_year: the plot year after which the tree's first season came, so its age is the plot year less this; "
                           "vigour: its drawn factor on carbon gain (plot.vigour_sd), to 4 places",
            **status, **stem_note, "seed": plot.seed, "mode": plot.mode, "run": run or {},
            "trees_alive": len(plot.alive), "trees": trees}


def write(plot, path, dead_years: int = 10, run: dict | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree_list(plot, dead_years, run), indent=0), encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", help="a plot folder with a checkpoint.pkl (tools/plot.py); read only")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dead-years", type=int, default=10)
    a = ap.parse_args()
    # not Plot.resume: that tidies the folder for a run that carries on
    with open(Path(a.folder) / "checkpoint.pkl", "rb") as f:
        plot = pickle.load(f)
    print(write(plot, a.out, a.dead_years))


if __name__ == "__main__":
    main()
