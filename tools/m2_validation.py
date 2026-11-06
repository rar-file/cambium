"""M2's validation, kept out of every fit: the carbon split against Aosaar 2016, and basal area against Repola
2008 Table 1's range.  Reads saved outputs; changes nothing.

    python tools/m2_validation.py --trees now=base_trees both=m2_cc --plots now=base_plots both=m2_plots_cc

Aosaar et al. 2016, Silva Fennica 50(4), one fertile stand, one 0.03 ha plot, roots partly assumed.  Table 4, p. 8,
age 10, production in Mg/ha/yr: leaves 2.81; stemwood 6.45, stembark 0.56, twigs 0.72, branches 0.16; stump 0.61,
coarse roots 0.82, fine roots 0.89; trees total 13.02.  Shares by my arithmetic: leaves 21.6 %, above-ground wood
60.6 %, below ground 17.8 %.  Table 3, p. 7, age 10: 10,200 stems/ha, basal area 15.2 m2/ha.

The model's split, by dry mass, for one tree in a year, or summed over a plot's living trees.  NPP is cue x
fixed, in the model's carbon units; a unit builds wood_volume_per_carbon of wood at the wood's density.  Leaves
are `leaf_dm_g`, which holds the year's early and late leaves (treegen/growth.py:899, :1670).  Below ground is
what the root budget has left after fine-root upkeep.  Above-ground wood is the remainder, so it also takes any
error in the other two.  This accounting is mine, for a look.  Trees flip year to year, so "8-12" gives the
mean over those ages as well as age 10.

Repola 2008, Silva Fennica 42(4), Table 1, p. 607: 24 stands aged 11-97 at stump height, birch 28-100 % of basal
area, four of them thinning experiments, three on peat.  G 2.7-32.3 m2/ha, mean 19.2.  A range check only, and
not an approved target.  Field basal area is over bark and the model's diameters are wood only, so diameters go
through tools/bark.py's over-bark conversion (Hansen et al. 2023).  Wood-only figures are shown beside them.  On
stand trees, N follows the tree's spacing on a triangular grid, N = 2 x 10000 / (sqrt(3) s^2).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bark import dbh_over_bark  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
AOSAAR = {"leaves": 2.81 / 13.02, "wood": (6.45 + 0.56 + 0.72 + 0.16) / 13.02, "below": (0.61 + 0.82 + 0.89) / 13.02}
AGES = (10, 20, 30, 50, 60)
WINDOW = (8, 9, 10, 11, 12)
G_LOW, G_HIGH, G_MEAN = 2.7, 32.3, 19.2


def parts_of(c: dict, g_per_unit: float, g_resp: float) -> tuple | None:
    """(leaves, below, npp) in carbon units, or None if the tree fixed nothing."""
    fixed, cue = c.get("fixed") or 0.0, c.get("cue") or 0.0
    if fixed <= 0.0 or cue <= 0.0:
        return None
    below = max(fixed - (c.get("shoot") or 0.0) - (c.get("fine_root_maint") or 0.0), 0.0) / g_resp
    return (c.get("leaf_dm_g") or 0.0) / g_per_unit, below, fixed * cue


def shares(parts: list) -> dict | None:
    parts = [p for p in parts if p]
    npp = sum(p[2] for p in parts)
    if not parts or npp <= 0.0:
        return None
    leaves, below = sum(p[0] for p in parts), sum(p[1] for p in parts)
    return {"leaves": 100.0 * leaves / npp, "below": 100.0 * below / npp, "wood": 100.0 * (1.0 - (leaves + below) / npp)}


def stems_per_ha(spacing_m: float) -> float:
    return 2.0 * 10000.0 / (math.sqrt(3.0) * spacing_m * spacing_m)


def tree_years(folder: Path) -> list:
    return [json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"] for d in sorted(folder.glob("*_stand"))]


def row_at(years: list, age: int) -> dict | None:
    return next((r for r in years if r["year"] == age), None)


def plot_living(folder: Path) -> list:
    """One entry per plot: (area_ha, stats by plot year, trees as (germination, removed, per_year))."""
    out = []
    for d in sorted(folder.glob("plot_*")):
        doc = json.loads((d / "plot.json").read_text(encoding="utf-8"))
        trees = []
        for t in doc["trees"]:
            f = d / f"tree_{t['id']:03d}" / "stats.json"
            if f.exists():
                trees.append((t["germination"], t.get("removed"), json.loads(f.read_text(encoding="utf-8"))["per_year"]))
        out.append((doc["area_m2"] / 10000.0, {r["year"]: r for r in doc["stats"]}, trees))
    return out


def plot_at(area_ha: float, trees: list, age: int) -> list:
    """The records of the trees alive in plot year `age`."""
    out = []
    for germ, removed, years in trees:
        if removed is not None and removed <= age:
            continue
        rec = row_at(years, age - germ)
        if rec and (rec.get("dbh_cm") or 0.0) > 0.0:
            out.append(rec)
    return out


def mean_sd(values: list, digits: int = 1) -> str:
    if not values:
        return "none"
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{statistics.mean(values):.{digits}f} +- {sd:.{digits}f}"


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--trees", nargs="*", default=[], help="name=folder")
    ap.add_argument("--plots", nargs="*", default=[], help="name=folder")
    a = ap.parse_args(argv)

    from treegen.params import load_species

    sp, _ = load_species("betula_pendula")
    g_per_unit = float(sp.pipe_model.wood_volume_per_carbon) * float(sp.resource.leaf_costs.wood_basic_density_kg_m3) * 1000.0
    g_resp = 1.0 + float(getattr(sp.resource, "growth_respiration_coefficient", 0.0))

    print(f"Aosaar 2016, age 10, share of NPP: leaves {100 * AOSAAR['leaves']:.1f} %, above-ground wood {100 * AOSAAR['wood']:.1f} %, below ground {100 * AOSAAR['below']:.1f} %; basal area 15.2 m2/ha, 10,200 stems/ha (Table 3).")
    print(f"Repola 2008 Table 1, a range check: G {G_LOW}-{G_HIGH} m2/ha, mean {G_MEAN}.\n")
    print("| Setting | Age | Runs | Leaves (%) | Above-ground wood (%) | Below ground (%) | Basal area, over bark (m2/ha) | Wood only (m2/ha) | Stems/ha | Over bark inside Repola's range? |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for s in a.trees:
        name, folder = s.split("=", 1)
        years = tree_years(E / folder)
        for age in ("8-12",) + AGES:
            ages = WINDOW if age == "8-12" else (age,)
            by_seed = []
            for y in years:
                got = [shares([parts_of(row_at(y, x).get("carbon") or {}, g_per_unit, g_resp)]) for x in ages]
                got = [g for g in got if g]
                if got:
                    by_seed.append({k: statistics.mean(g[k] for g in got) for k in ("leaves", "wood", "below")})
            cells = " | ".join(mean_sd([p[k] for p in by_seed]) for k in ("leaves", "wood", "below"))
            if age == "8-12":
                print(f"| {name} | 8-12, mean | {len(years)} | {cells} | | | | |")
                continue
            rows = [row_at(y, age) for y in years]
            ns = [stems_per_ha(r["stand_spacing_m"]) for r in rows]
            ob = [stems_per_ha(r["stand_spacing_m"]) * math.pi * float(dbh_over_bark(r["dbh_cm"])) ** 2 / 40000.0 for r in rows]
            ub = [stems_per_ha(r["stand_spacing_m"]) * math.pi * r["dbh_cm"] ** 2 / 40000.0 for r in rows]
            inside = "yes" if G_LOW <= statistics.mean(ob) <= G_HIGH else "no"
            print(f"| {name} | {age} | {len(rows)} | {cells} | {mean_sd(ob)} | {mean_sd(ub)} | {statistics.mean(ns):.0f} | {inside} |")
    for s in a.plots:
        name, folder = s.split("=", 1)
        plots = plot_living(E / folder)
        for age in ("8-12",) + AGES:
            ages = WINDOW if age == "8-12" else (age,)
            by_plot = []
            for area, _, trees in plots:
                got = [shares([parts_of(r.get("carbon") or {}, g_per_unit, g_resp) for r in plot_at(area, trees, x)]) for x in ages]
                got = [g for g in got if g]
                if got:
                    by_plot.append({k: statistics.mean(g[k] for g in got) for k in ("leaves", "wood", "below")})
            cells = " | ".join(mean_sd([p[k] for p in by_plot]) for k in ("leaves", "wood", "below"))
            if age == "8-12":
                print(f"| {name}, plots | 8-12, mean | {len(plots)} | {cells} | | | | |")
                continue
            ob, ub, ns, check = [], [], [], []
            for area, stats, trees in plots:
                recs = plot_at(area, trees, age)
                ob.append(sum(math.pi * float(dbh_over_bark(r["dbh_cm"])) ** 2 / 40000.0 for r in recs) / area)
                ub.append(sum(math.pi * r["dbh_cm"] ** 2 / 40000.0 for r in recs) / area)
                ns.append(len(recs) / area)
                check.append(stats[age]["stems_per_ha"])
            if abs(statistics.mean(ns) - statistics.mean(check)) > 0.02 * statistics.mean(check):
                print(f"| {name}, plots | {age} | STEMS DIFFER: {statistics.mean(ns):.0f} from trees, {statistics.mean(check):.0f} from the plot |")
            inside = "yes" if G_LOW <= statistics.mean(ob) <= G_HIGH else "no"
            print(f"| {name}, plots | {age} | {len(plots)} | {cells} | {mean_sd(ob)} | {mean_sd(ub)} | {statistics.mean(ns):.0f} | {inside} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
