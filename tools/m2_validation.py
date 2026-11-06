"""M2's validation, kept out of every fit: the carbon split against Aosaar 2016 Table 4, and basal area
against Repola 2008 Table 1's range.  Reads saved outputs; changes nothing.

    python tools/m2_validation.py --trees now=base_trees both=m2_cc --plots now=base_plots both=m2_plots_cc

Aosaar et al. 2016, Silva Fennica 50(4), Table 4, p. 8: one fertile stand, age 10, 10,200 stems/ha, roots
partly assumed.  Production in Mg/ha/yr: leaves 2.81; stemwood 6.45, stembark 0.56, twigs 0.72, branches
0.16; stump 0.61, coarse roots 0.82, fine roots 0.89; trees total 13.02.  As shares: leaves 21.6 %,
above-ground wood 60.6 %, below ground 17.8 %.

The model's split, by dry mass, for one tree in a year.  NPP is cue x fixed, in the model's carbon units; a
unit builds wood_volume_per_carbon of wood at the wood's density.  Leaves are `leaf_dm_g`, the dry mass of
the leaves on last year's buds; the late leaves of this year's new shoots aren't in it, so leaves read a
little low.  Below ground is what the root budget has left after fine-root upkeep.  Above-ground wood is
the remainder, so it also takes any error in the other two.  This accounting is mine, for a look.

Repola 2008, Silva Fennica 42(4), Table 1: 24 stands aged 11-97, some thinned, some mixed, G 2.7-32.3
m2/ha, mean 19.2.  A range check only.  On plots, G = N pi (mean^2 + sd^2) / 40000, from the plot's stems
per hectare and the mean and spread of its diameters.  On stand trees, G = N pi d^2 / 40000, with N from
the tree's spacing s, on a triangular grid: N = 2 x 10000 / (sqrt(3) s^2).
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

E = ROOT / "out" / "bench" / "ensemble"
AOSAAR = {"leaves": 2.81 / 13.02, "wood": (6.45 + 0.56 + 0.72 + 0.16) / 13.02, "below": (0.61 + 0.82 + 0.89) / 13.02}
AGES = (10, 20, 30, 50, 60)
G_LOW, G_HIGH, G_MEAN = 2.7, 32.3, 19.2


def tree_years(folder: Path) -> list:
    return [json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"] for d in sorted(folder.glob("*_stand"))]


def split_of(row: dict, g_per_unit: float, g_resp: float) -> dict | None:
    c = row.get("carbon") or {}
    fixed, cue = c.get("fixed") or 0.0, c.get("cue") or 0.0
    if fixed <= 0.0 or cue <= 0.0:
        return None
    npp = fixed * cue
    leaf_units = (c.get("leaf_dm_g") or 0.0) / g_per_unit
    below = max(fixed - (c.get("shoot") or 0.0) - (c.get("fine_root_maint") or 0.0), 0.0) / g_resp
    return {"leaves": leaf_units / npp, "below": below / npp, "wood": 1.0 - (leaf_units + below) / npp}


def stems_per_ha(spacing_m: float) -> float:
    return 2.0 * 10000.0 / (math.sqrt(3.0) * spacing_m * spacing_m)


def stand_g(row: dict) -> float | None:
    d, s = row.get("dbh_cm"), row.get("stand_spacing_m")
    if not d or not s:
        return None
    return stems_per_ha(s) * math.pi * d * d / 40000.0


def plot_rows(folder: Path) -> list:
    out = []
    for d in sorted(folder.glob("plot_*")):
        out.append(json.loads((d / "plot.json").read_text(encoding="utf-8"))["stats"])
    return out


def plot_g(row: dict) -> float:
    m, s, n = row["dbh_mean_cm"], row.get("dbh_sd_cm") or 0.0, row["stems_per_ha"]
    return n * math.pi * (m * m + s * s) / 40000.0


def mean_sd(values: list) -> str:
    return f"{statistics.mean(values):.1f} +- {statistics.stdev(values) if len(values) > 1 else 0.0:.1f}"


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

    print(f"Aosaar 2016 Table 4, age 10, share of NPP: leaves {100 * AOSAAR['leaves']:.1f} %, above-ground wood {100 * AOSAAR['wood']:.1f} %, below ground {100 * AOSAAR['below']:.1f} %. One fertile stand at 10,200 stems/ha; the model's is one tree.\n")
    print("| Setting | Age | Seeds | Leaves (%) | Above-ground wood (%) | Below ground (%) | Basal area (m2/ha) | Stems/ha |")
    print("|---|---|---|---|---|---|---|---|")
    for s in a.trees:
        name, folder = s.split("=", 1)
        years = tree_years(E / folder)
        for age in AGES:
            rows = [next(r for r in y if r["year"] == age) for y in years]
            parts = [p for p in (split_of(r, g_per_unit, g_resp) for r in rows) if p]
            gs = [g for g in (stand_g(r) for r in rows) if g is not None]
            ns = [stems_per_ha(r["stand_spacing_m"]) for r in rows if r.get("stand_spacing_m")]
            print(f"| {name} | {age} | {len(rows)} | " + " | ".join(mean_sd([100 * p[k] for p in parts]) for k in ("leaves", "wood", "below")) + f" | {mean_sd(gs) if gs else 'none'} | {statistics.mean(ns) if ns else 0:.0f} |")
    print(f"\nRepola 2008 Table 1, a range check: G {G_LOW}-{G_HIGH} m2/ha, mean {G_MEAN}.\n")
    print("| Plots | Age | Plots run | Basal area (m2/ha) | Stems/ha | Mean diameter (cm) | Inside the range? |")
    print("|---|---|---|---|---|---|---|")
    for s in a.plots:
        name, folder = s.split("=", 1)
        plots = plot_rows(E / folder)
        for age in AGES:
            rows = [next((r for r in p if r["year"] == age), None) for p in plots]
            rows = [r for r in rows if r]
            gs = [plot_g(r) for r in rows]
            mean = statistics.mean(gs)
            print(f"| {name} | {age} | {len(rows)} | {mean_sd(gs)} | {statistics.mean(r['stems_per_ha'] for r in rows):.0f} | {statistics.mean(r['dbh_mean_cm'] for r in rows):.1f} | {'yes' if G_LOW <= mean <= G_HIGH else 'no'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
