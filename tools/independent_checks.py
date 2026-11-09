"""Reported rows beside the scorecard: checks that sit outside the approved targets (review 2026-11-09, top 5, item 2).

    python tools/independent_checks.py out/bench/ensemble/node_f5_trees out/bench/ensemble/node_f5_plots
    python tools/scorecard.py --ensemble out/bench/ensemble/node_f5_plots --independent      # the same rows, after the scorecard's

Nothing here is PASS or FAIL, and nothing here is an approved target: each row shows the model's ensemble mean beside
a published figure, and says whether any model value was ever set against that figure ("kind").  A row with no
published figure in the repository says so; a target for it has to be proposed to the maintainer and approved first.

Reference figures and where they come from (none is in the approved targets as a scored band):
* Repola 2008, Silva Fennica 42(4):605, Eqs. 7 and 9, as coded in tools/m3_wood.py: stem wood and living branches
  from the tree's own over-bark diameter and height.  Model wood has no bark; Repola's branches include it.
* Hagemeier & Leuschner 2019, Forests 10(3):265, Table 3, as quoted in reference/targets.yaml (stand_density.measures):
  site 1, 45 yr: dbh 19 +- 6 cm, height 20 +- 3 m; site 2, 67 yr: 25 +- 3 cm, 25 +- 3 m.  Basal area 25.2 and
  28.5 m2/ha as quoted in reports/birch_v1_final.md; those printed figures don't add up (QUESTIONS.md Q32).
* Hagemeier & Leuschner 2019b, Forests 10(10):925: median light 14.8 %, as in reference/targets.yaml.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bark import dbh_over_bark  # noqa: E402
from m3_wood import repola  # noqa: E402

AGES = (30, 45, 50, 60)
LIGHT_MEDIAN_PCT = 14.8
HAGEMEIER = {45: {"dbh": (19.0, 6.0), "height": (20.0, 3.0), "basal_area": 25.2},
             67: {"dbh": (25.0, 3.0), "height": (25.0, 3.0), "basal_area": 28.5}}

INDEPENDENT = "independent"
TUNED = "tuned against"
PARTLY = "partly"


def _mean(xs: list) -> str:
    xs = [float(x) for x in xs]
    if not xs:
        return "not saved"
    return f"{statistics.fmean(xs):.3g} ({min(xs):.3g}-{max(xs):.3g}), n {len(xs)}"


def _row(what, age, model, reference, kind, note) -> dict:
    return {"what": what, "age": age, "model": model, "reference": reference, "kind": kind, "note": note}


def tree_rows(folder: Path, ages=AGES) -> list:
    """Stand trees grown by tools/tree_table.py: wood against Repola at the tree's own size, and stem volume a hectare."""
    runs = []
    for d in sorted(Path(folder).glob("*_stand")):
        if (d / "tree.json").exists() and (d / "stats.json").exists():
            snaps = {s["age"]: s for s in json.loads((d / "tree.json").read_text(encoding="utf-8"))["snapshots"]}
            years = {r["year"]: r for r in json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]}
            runs.append((snaps, years))
    rows = []
    for age in ages:
        stem, branch, vol = [], [], []
        for snaps, years in runs:
            s, y = snaps.get(age), years.get(age)
            if s is None or y is None or not y.get("dbh_cm"):
                continue
            r_stem, r_branch = repola(float(dbh_over_bark(float(y["dbh_cm"]))), float(y["height_m"]))
            stem.append(s["stem_kg"] / r_stem)
            branch.append(s["branch_kg"] / r_branch)
            if y.get("lai") and y.get("leaf_area_m2"):
                vol.append(s["stem_m3"] * float(y["lai"]) * 1e4 / float(y["leaf_area_m2"]))
        if not stem:
            continue
        rows.append(_row("stem wood over Repola's at its own DBH and height (ratio)", age, _mean(stem), "1.0", INDEPENDENT,
                         "no value was set against it; ring_share_max's comment notes stem wood ran 12-20 % over without it"))
        rows.append(_row("branch wood over Repola's living branches (ratio)", age, _mean(branch), "1.0; Repola's include bark, the model's don't", INDEPENDENT,
                         "no value was set against it"))
        rows.append(_row("stem volume, wood only (m3/ha), stand tree x its stems/ha", age, _mean(vol), "none in the repository", INDEPENDENT,
                         "needs a yield table read at its source: proposed, not approved"))
    return rows


def plot_rows(folder: Path, ages=AGES) -> list:
    """Forest plots grown by tools/forest.py: basal area, the spread of diameters and heights, light against the median."""
    plots = []
    for d in sorted(Path(folder).glob("plot_*")):
        if (d / "plot.json").exists():
            stats = {s["year"]: s for s in json.loads((d / "plot.json").read_text(encoding="utf-8"))["stats"]}
            plots.append((d, stats))
    rows = []
    for age in ages:
        ref = HAGEMEIER.get(age) or (HAGEMEIER[67] if age == 60 else None)
        at = "" if age in HAGEMEIER or ref is None else " (the 67-year stand, not this age)"
        ba, light, cv, d_mean, h_sd, h_mean = [], [], [], [], [], []
        for d, stats in plots:
            s = stats.get(age)
            if s is None:
                continue
            if s.get("basal_area_ob_m2_ha") is not None:
                ba.append(s["basal_area_ob_m2_ha"])
            if s.get("subcanopy_diffuse_light_pct") is not None:
                light.append(s["subcanopy_diffuse_light_pct"] - LIGHT_MEDIAN_PCT)
            lst = d / f"trees_{age:03d}.json"
            if lst.exists():
                trees = [t for t in json.loads(lst.read_text(encoding="utf-8"))["trees"] if t["alive"] and t.get("dbh_cm")]
                if len(trees) >= 3:
                    ds, hs = [t["dbh_cm"] for t in trees], [t["height_m"] for t in trees]
                    d_mean.append(statistics.fmean(ds))
                    cv.append(statistics.stdev(ds) / statistics.fmean(ds))
                    h_mean.append(statistics.fmean(hs))
                    h_sd.append(statistics.stdev(hs))
        if not (ba or light):
            continue
        rows.append(_row("basal area over bark (m2/ha)", age, _mean(ba), f"{ref['basal_area']}{at}; Q32 open" if ref else "none at this age", TUNED,
                         "stems/ha and Dg were tuned against Hagemeier (wind_speed, sdi_max, rate_at_max), so basal area follows"))
        rows.append(_row("light under the canopy, points from the 14.8 % median", age, _mean(light), "0", TUNED,
                         "shedding thresholds and death lines were set against light"))
        if cv:
            rows.append(_row("mean DBH over bark of stems past 1.3 m (cm)", age, _mean(d_mean), f"{ref['dbh'][0]:g}{at}" if ref else "none at this age", TUNED,
                             "Dg was tuned against"))
            rows.append(_row("spread of DBH: SD over mean", age, _mean(cv), f"{ref['dbh'][1] / ref['dbh'][0]:.2f}{at}" if ref else "none at this age", INDEPENDENT,
                             "no value was set against the spread"))
            rows.append(_row("mean height of stems past 1.3 m (m)", age, _mean(h_mean), f"{ref['height'][0]:g}{at}" if ref else "none at this age", PARTLY,
                             "top height follows the curve by design; the mean of all stems doesn't"))
            rows.append(_row("spread of height: SD (m)", age, _mean(h_sd), f"{ref['height'][1]:g}{at}" if ref else "none at this age", INDEPENDENT,
                             "no value was set against it; a tree's height limit goes with its drawn vigour (plot.vigour_sd)"))
    return rows


def rows_for(folder) -> list:
    folder = Path(folder)
    return tree_rows(folder) + plot_rows(folder)


def table(rows: list, header: str = "") -> str:
    lines = ([header, ""] if header else []) + ["| Check | Age | Model: mean (lowest-highest), runs | Published figure | Kind | Note |", "|---|:---:|:---:|:---:|:---:|---|"]
    lines += [f"| {r['what']} | {r['age']} | {r['model']} | {r['reference']} | **{r['kind']}** | {r['note']} |" for r in rows]
    lines += ["", "Reported rows, never PASS/FAIL: none of these is an approved target. Kind: independent = no model value was set against it."]
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for folder in sys.argv[1:]:
        print(table(rows_for(folder), f"Reported checks, outside the approved targets: {folder}"))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
