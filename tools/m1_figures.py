"""Every worked figure in reports/milestone_M1.md and reports/rebaseline_M1.md that isn't a scorecard row,
from saved outputs, with unrounded bands.  Output: out/bench/m1/figures.txt.

    python tools/m1_figures.py > out/bench/m1/figures.txt
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from scorecard import (ensemble_folders, eriksson_1997_height, evaluate_targets, load_approved_targets, load_run_data, naslund_top_height,
                       plot_live_records, t13_years)  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
AGES = (20, 30, 40, 50, 60)
G_C_PER_UNIT = 0.305
DERIVED_UNITS = 1080.3


def runs_of(folder):
    return [load_run_data(str(d)) for d in ensemble_folders(folder)]


def margins(title, runs, ref):
    targets = load_approved_targets(ref)
    print(f"\n## {title}, height rows, targets at {ref}: over the band top, unrounded\n")
    print("| Age | Mean | SD | SE | Band top | Over | Over / SE | Share inside | Band check of the mean (inside is not a pass) |")
    print("|---|---|---|---|---|---|---|---|---|")
    per = [evaluate_targets(targets, [r], ages=list(AGES))[0] for r in runs]
    for age in AGES:
        name = f"tree_allometry.site_index_curves (age {age})"
        vals = []
        for rows in per:
            for r in rows:
                if r["target"] == name and r.get("value") is not None:
                    vals.append((r["value"], r["band"]))
        if not vals:
            print(f"| {age} | not scored at this ref |||||||")
            continue
        v = [x[0] for x in vals]
        lo, hi = vals[0][1]
        m, s = statistics.fmean(v), statistics.stdev(v)
        se = s / len(v) ** 0.5
        share = sum(lo <= x <= hi for x in v) / len(v)
        print(f"| {age} | {m:.3f} | {s:.3f} | {se:.3f} | {hi:.4f} | {m - hi:+.4f} | {(m - hi) / se:+.2f} | {100 * share:.0f} % | {'inside' if lo <= m <= hi else 'FAIL'} |")


def plots_heights(runs):
    print("\n## Plots: top height on the curve, those trees' mean height, all live trees' mean height, tallest (m)\n")
    print("| Age | Curve | Those trees | All live trees | Tallest tree |")
    print("|---|---|---|---|---|")
    for age in AGES:
        cur, sim, allm, tall = [], [], [], []
        for r in runs:
            recs = plot_live_records(r, age)
            h, _, s = naslund_top_height(recs, float(r["plot_data"]["area_m2"]))
            cur.append(h)
            sim.append(s)
            hs = [float(x["height_m"]) for x in recs if x.get("height_m")]
            allm.append(statistics.fmean(hs))
            tall.append(max(hs))
        print(f"| {age} | {statistics.fmean(cur):.2f} | {statistics.fmean(sim):.2f} | {statistics.fmean(allm):.2f} | {statistics.fmean(tall):.2f} |")


def light_k(title, rows_by_age):
    print(f"\n## {title}: Beer-Lambert from the saved LAI and diffuse light\n")
    print("| Age | Mean LAI | Mean light % | k fitted through the origin | LAI needed for 19.8 % at that k | Light at LAI 3.6 at that k, % |")
    print("|---|---|---|---|---|---|")
    for age, pairs in rows_by_age.items():
        x = [p[0] for p in pairs]
        od = [-math.log(p[1] / 100.0) for p in pairs]
        k = sum(a * b for a, b in zip(x, od)) / sum(a * a for a in x)
        print(f"| {age} | {statistics.fmean(x):.3f} | {statistics.fmean(p[1] for p in pairs):.2f} | {k:.4f} | {-math.log(0.198) / k:.2f} | {100 * math.exp(-k * 3.6):.1f} |")
    print(f"\nAt k = 0.37: 19.8 % needs LAI {-math.log(0.198) / 0.37:.2f}; LAI 3.6 gives {100 * math.exp(-0.37 * 3.6):.2f} %; LAI 4.6 gives {100 * math.exp(-0.37 * 4.6):.2f} %.")


def band_options():
    targets = load_approved_targets("master")
    item = targets["tree_allometry"]["site_index_curves"]
    p = dict(item["parameters"], t_ref=item["reference_age_years"])
    print("\n## The height band, by the years to breast height (m)\n")
    print(f"parameters as in targets.yaml: {p}")
    rows = []
    for si in (20.0, 26.0):
        rows.append((si, t13_years(item, si), 150.0 / si))
    print("\n| Site index | T13 used | 150 / SI | Fixed before |\n|---|---|---|---|")
    for si, t, alt in rows:
        print(f"| {si:g} | {t:.2f} | {alt:.2f} | 4 |")
    print("\n| Total age | T13 = 4: low-high | Used: low-high | Width change | If T13 = 150/SI: low-high |\n|---|---|---|---|---|")
    for age in AGES:
        def band(t13):
            return tuple(eriksson_1997_height(si, age - t(si), p["asi"], p["beta"], p["b2"], p["t_ref"]) for si, t in zip((20.0, 26.0), t13))
        before = band((lambda s: 4.0, lambda s: 4.0))
        used = band((lambda s: t13_years(item, s), lambda s: t13_years(item, s)))
        alt = band((lambda s: 150.0 / s, lambda s: 150.0 / s))
        print(f"| {age} | {before[0]:.2f}-{before[1]:.2f} | {used[0]:.2f}-{used[1]:.2f} | {(used[1] - used[0]) - (before[1] - before[0]):+.2f} | {alt[0]:.2f}-{alt[1]:.2f} |")


def top15():
    print("\n## The top 15 at 20 seeds: paired change at 50 and 60, option x 1.25 against baseline, % +- SE (height, LAI)\n")
    d = ROOT / "out" / "bench" / "node" / "screen20"
    import csv
    ranks = list(csv.DictReader(open(d / "ranking.csv", encoding="utf-8")))
    base = {s: json.loads((d / f"baseline__s{s}.json").read_text()) for s in range(1, 21)}
    print("| Rank | Value | Height at 50 | Height at 60 | LAI at 50 | LAI at 60 |\n|---|---|---|---|---|---|")
    for r in ranks:
        cells = []
        for metric in ("height_m", "lai"):
            for age in ("50", "60"):
                diffs = []
                for s in range(1, 21):
                    o = json.loads((d / f"{r['path']}__x1.25__s{s}.json").read_text())
                    diffs.append(100.0 * (o[age][metric] / base[s][age][metric] - 1.0))
                cells.append(f"{statistics.fmean(diffs):+.1f} +- {statistics.stdev(diffs) / 20 ** 0.5:.1f}")
        print(f"| {r['rank']} | `{r['path']}` | " + " | ".join(cells) + " |")


def carbon_on_plots(runs, label):
    print(f"\n## {label}: carbon on plots, by tree (from each tree's own stats)\n")
    print("| Age | Fixed per m2 of leaf, all trees together, g C | Ratio to 329 | Mean of trees, g C | Ratio to 329 | CUE, unweighted mean of trees |")
    print("|---|---|---|---|---|---|")
    for age in (10, 20, 30, 40, 50, 60):
        tot_f, tot_l, per, cue = 0.0, 0.0, [], []
        for r in runs:
            for t in plot_live_records(r, age):
                c = t.get("carbon") or {}
                f, la = c.get("fixed"), t.get("leaf_area_m2")
                if f and la:
                    tot_f += f
                    tot_l += la
                    per.append(f / la)
                if c.get("cue") is not None:
                    cue.append(c["cue"])
        if not per:
            continue
        a = tot_f / tot_l * G_C_PER_UNIT
        b = statistics.fmean(per) * G_C_PER_UNIT
        print(f"| {age} | {a:.0f} | {a / 329.0:.2f} | {b:.0f} | {b / 329.0:.2f} | {statistics.fmean(cue):.2f} |")


def alpha_origin():
    folder = ROOT / "out" / "bench" / "c48m5_nat"
    if not folder.exists():
        print("\n## Alpha's origin: c48m5_nat isn't here")
        return
    r = load_run_data(str(folder))
    print("\n## Alpha's origin: c48m5_nat, the likely run (inferred from its name and time; its manifest doesn't record alpha), years 16-20\n")
    print(f"Derived figure: {DERIVED_UNITS:.0f} units per m2 of leaf.\n")
    print("| Year | All trees together, units per m2 of leaf | Ratio | Mean of trees | Ratio |\n|---|---|---|---|---|")
    for y in range(16, 21):
        tot_f, tot_l, per = 0.0, 0.0, []
        for t in plot_live_records(r, y):
            c = t.get("carbon") or {}
            f, la = c.get("fixed"), t.get("leaf_area_m2")
            if f and la:
                tot_f += f
                tot_l += la
                per.append(f / la)
        if per:
            print(f"| {y} | {tot_f / tot_l:.0f} | {tot_f / tot_l / DERIVED_UNITS:.2f} | {statistics.fmean(per):.0f} | {statistics.fmean(per) / DERIVED_UNITS:.2f} |")


def triangles():
    print("\n## Example tree: triangles per internode\n")
    d = E / "example_5"
    info = json.loads((d / "example.json").read_text(encoding="utf-8"))
    py = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
    for age, a in info["ages"].items():
        print(f"age {age}: {a['crown']['triangles']} triangles, {py[int(age)]['living_internodes']} living internodes, {a['crown']['triangles'] / py[int(age)]['living_internodes']:.2f}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    trees = runs_of(E / "base_trees")
    plots = runs_of(E / "base_plots")
    print("# Worked figures for M1, from saved outputs (tools/m1_figures.py)")
    for ref in ("master", "targets-approved"):
        margins("Stand trees, 20 seeds", trees, ref)
    margins("Plots, 5 seeds, on the curve", plots, "master")
    plots_heights(plots)
    light_k("Stand trees, 20 seeds", {a: [(r["tree_stats"]["per_year"][a]["lai"], r["tree_stats"]["per_year"][a]["subcanopy_diffuse_light_pct"]) for r in trees] for a in (50, 60)})
    light_k("Plots, 5 seeds", {a: [(next(s for s in r["plot_data"]["stats"] if s["year"] == a)["lai"], next(s for s in r["plot_data"]["stats"] if s["year"] == a)["subcanopy_diffuse_light_pct"]) for r in plots] for a in (50, 60)})
    band_options()
    top15()
    carbon_on_plots(plots, "Plots, 5 seeds")
    alpha_origin()
    triangles()


if __name__ == "__main__":
    main()
