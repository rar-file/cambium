"""The stand by age, as a forester reads it, against the sources: stems/ha, basal area over bark,
mean and top height, gap fraction, new trees a year.

    python tools/stand_table.py out/bench/forest/thin1                 # a folder of plot_N folders
    python tools/stand_table.py out/bench/forest/thin1/plot_1          # one plot
    python tools/stand_table.py out/bench/ensemble/base_plots --ages 8,17,20,30,40,50,60

Plots from tools/forest.py carry these measures.  Older plots from tools/plot.py don't, so
this works them out from the trees' stats.json (no gap fraction there).

Each row is the mean across plots, with the lowest and highest plot in brackets.  One plot
isn't a verdict: the count of plots is in the heading.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import bark  # noqa: E402

AGES = (20, 30, 40, 50, 60)
SOURCES = [
    "Sources (over bark; none of these is a target in reference/targets.yaml's sense unless named there):",
    "- Aosaar et al. 2016 Table 3 (one 0.03 ha plot, unmanaged, fertile): 11,633 stems/ha and 11.3 m2/ha at age 8; 2,733 and 20.9 at 17.",
    "- Hagemeier & Leuschner 2019 Table 3: 880 stems/ha at 45 (mean DBH 19 cm), 420 at 67 (25 cm); basal area worked out from those: 27.4, 20.9.",
    "- Repola 2008 Table 1: 24 Finnish stands aged 11-97, 2.7-32.3 m2/ha, mean 19.2.",
    "- Soderberg 1986 in Elfving 2010 App. 11, broadleaves, SI 26 (guide only; it under-predicts young birch): limit 20, 26, 30, 33 m2/ha at 30, 40, 50, 60.",
]


def from_trees(folder: Path, age: int, doc: dict) -> dict | None:
    """Stems, basal area and heights at a plot age, from each tree's stats.json (older plots)."""
    d, h = [], []
    area = doc["area_m2"]
    for tree in doc["trees"]:
        removed = tree.get("removed")
        if tree["germination"] >= age or (removed is not None and removed <= age):
            continue
        f = folder / f"tree_{tree['id']:03d}" / "stats.json"
        if not f.exists():
            continue
        rows = json.loads(f.read_text(encoding="utf-8"))["per_year"]
        row = next((r for r in rows if r["year"] == age - tree["germination"]), None)
        if row is None:
            continue
        d.append(row.get("dbh_cm") or 0.0)
        h.append(row["height_m"])
    if not d:
        return None
    ob = bark.dbh_over_bark(np.array(d))
    h = np.array(h)
    n_top = max(1, round(100 * area / 1e4))
    top = float(h[np.argsort(-ob, kind="stable")[:n_top]].mean())
    return {"stems_per_ha": len(d) / area * 1e4, "basal_area_ob_m2_ha": float((np.pi / 4 * (ob / 100) ** 2).sum()) / area * 1e4,
            "dg_ob_cm": 100 * float(np.sqrt(np.mean((ob / 100) ** 2))), "height_mean_m": float(h.mean()), "top_height_m": top}


def read_plot(folder: Path, ages) -> dict:
    """Plot age -> its row, for the ages asked."""
    doc = json.loads((folder / "plot.json").read_text(encoding="utf-8"))
    by_year = {s["year"]: s for s in doc["stats"]}
    out = {}
    for age in ages:
        s = by_year.get(age)
        if s is None:
            continue
        if "basal_area_ob_m2_ha" in s:
            row = dict(s)
        else:
            row = from_trees(folder, age, doc)
            if row is None:
                continue
        # new trees a year over the five years up to this age
        if "new_trees" in s:
            row["new_trees_a_year"] = float(np.mean([by_year[y].get("new_trees", 0) for y in range(age - 4, age + 1) if y in by_year]))
        out[age] = row
    return {"rows": out, "peak_mb": doc.get("peak_mb"), "runtime_s": doc.get("runtime_s"), "area_m2": doc.get("area_m2"), "doc": doc}


def plot_folders(folder: Path) -> list:
    if (folder / "plot.json").exists():
        return [folder]
    return sorted((p for p in folder.iterdir() if (p / "plot.json").exists()), key=lambda p: p.name)


def stat(values) -> str:
    """Mean, and the lowest and highest plot when there are several."""
    v = [x for x in values if x is not None]
    if not v:
        return "n/a"
    mean = float(np.mean(v))
    f = (lambda x: f"{x:,.0f}") if abs(mean) >= 100 else (lambda x: f"{x:.1f}") if abs(mean) >= 1 else (lambda x: f"{x:.2f}")
    return f(mean) if len(v) == 1 else f"{f(mean)} ({f(min(v))}-{f(max(v))})"


def table(folder: Path, ages) -> str:
    plots = [read_plot(p, ages) for p in plot_folders(folder)]
    lines = [f"**{folder.name}: {len(plots)} plot(s), of {plots[0]['area_m2']:.0f} m2.**" if plots else f"{folder}: no plots", ""]
    head = ["Age", "Stems/ha, all", "Stems/ha past 1.3 m", "Basal area over bark (m2/ha)", "Dg over bark (cm)", "Mean height (m)", "Top height (m)", "Gap fraction",
            "New trees a year"]
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    keys = ["stems_per_ha", "stems_bh_per_ha", "basal_area_ob_m2_ha", "dg_ob_cm", "height_mean_m", "top_height_m", "gap_fraction", "new_trees_a_year"]
    for age in ages:
        rows = [p["rows"][age] for p in plots if age in p["rows"]]
        if rows:
            lines.append(f"| {age} | " + " | ".join(stat([r.get(k) for r in rows]) for k in keys) + " |")
    path = size_density(plots)
    if path:
        lines += ["", path]
    peaks = [p["peak_mb"] for p in plots if p.get("peak_mb")]
    times = [p["runtime_s"] for p in plots if p.get("runtime_s")]
    if peaks:
        lines += ["", f"Worst peak memory {max(peaks) / 1024:.1f} GB, longest run {max(times) / 60:.0f} min."]
    return "\n".join(lines)


# Aosaar et al. 2016 Table 3, unmanaged stand: quadratic mean DBH (worked out from N and G), age, stems/ha, basal area
AOSAAR = [(3.52, 8, 11633, 11.3), (4.36, 10, 10200, 15.2), (5.36, 12, 8300, 18.7), (6.43, 14, 6567, 21.3), (7.89, 15, 4233, 20.7), (9.87, 17, 2733, 20.9)]


def size_density(plots) -> str:
    """Stems and basal area at the same stem size as Aosaar's stand.  This doesn't depend on how fast
    the trees get there, so it's the check on thinning while height growth is still changing."""
    if not plots or "doc" not in plots[0]:
        return ""
    rows = []
    for dg, age, n, g in AOSAAR:
        ns, gs, ys = [], [], []
        for p in plots:
            stats = [s for s in p["doc"]["stats"] if s.get("dg_ob_cm")]
            # the first year the stand has reached this size
            hit = next((s for s in stats if s["dg_ob_cm"] >= dg), None)
            if hit is not None:
                ns.append(hit["stems_per_ha"])
                gs.append(hit["basal_area_ob_m2_ha"])
                ys.append(hit["year"])
        if ns:
            rows.append(f"| {dg:.1f} | {age}, {n:,}, {g} | {float(np.mean(ys)):.0f}, {stat(ns)}, {stat(gs)} |")
    if not rows:
        return ""
    return "\n".join(["| Dg over bark (cm) | Aosaar: age, stems/ha, m2/ha | This run: age, stems/ha, m2/ha |", "|---|---|---|", *rows])


def fronts(s: dict, side_y_m: float, min_stems_ha: float = 400.0, slice_m: float = 10.0) -> dict:
    """How far a forest has come along its ground this year, from one year's row (metres from the
    seed-source end):  'first' is the furthest tree 2 m tall or more, 'forest' is the end of the
    unbroken run of slices with at least min_stems_ha of such trees, 'seedling' the furthest of any size."""
    area = slice_m * side_y_m / 1e4
    stems = s["stems_along_x"]
    tall = [n / area for n in stems]
    first = max((slice_m * (i + 1) for i, n in enumerate(stems) if n > 0), default=0.0)
    seedling = max((slice_m * (i + 1) for i, n in enumerate(s.get("seedlings_along_x", [])) if n > 0), default=0.0)
    forest = 0.0
    for i, density in enumerate(tall):
        if density < min_stems_ha:
            break
        forest = slice_m * (i + 1)
    return {"first": first, "forest": forest, "seedling": seedling}


def spread_table(folder: Path, every: int = 5, min_stems_ha: float = 400.0) -> str:
    """How far and how fast a forest advances, by year, across a run's plots."""
    docs = [json.loads((p / "plot.json").read_text(encoding="utf-8")) for p in plot_folders(folder)]
    docs = [d for d in docs if any("stems_along_x" in s for s in d["stats"])]
    if not docs:
        return f"{folder}: no ground with a seed source at one end"
    lines = [f"**{folder.name}: {len(docs)} plot(s), {docs[0]['side_m']:.0f} x {docs[0]['side_y_m']:.0f} m.** "
             f"Distances are from the source end; a tree counts from 2 m tall; forest = at least {min_stems_ha:.0f} stems/ha unbroken.", "",
             "| Year | Furthest tree (m) | Forest edge (m) | Furthest seedling (m) | Stems/ha, whole ground | New trees that year |", "|---|---|---|---|---|---|"]
    years = sorted({s["year"] for d in docs for s in d["stats"] if "stems_along_x" in s})
    series = []
    for d in docs:
        series.append({s["year"]: dict(fronts(s, d["side_y_m"], min_stems_ha), stems=s["stems_per_ha"], new=s.get("new_trees", 0))
                       for s in d["stats"] if "stems_along_x" in s})
    for y in years:
        if y % every and y != years[-1]:
            continue
        rows = [s[y] for s in series if y in s]
        lines.append(f"| {y} | {stat([r['first'] for r in rows])} | {stat([r['forest'] for r in rows])} | {stat([r['seedling'] for r in rows])} | "
                     f"{stat([r['stems'] for r in rows])} | {stat([r['new'] for r in rows])} |")
    # speed: a straight line through each plot's edge, while it's still moving and short of the far end
    for key, name in (("first", "furthest tree"), ("forest", "forest edge")):
        speeds = []
        for s in series:
            ys = np.array([y for y in sorted(s) if s[y][key] > 0], float)
            xs = np.array([s[int(y)][key] for y in ys], float)
            if len(ys) < 5:
                continue
            ok = xs < 0.9 * docs[0]["side_m"]
            if ok.sum() >= 5 and np.ptp(xs[ok]) > 0:
                speeds.append(float(np.polyfit(ys[ok], xs[ok], 1)[0]))
        if speeds:
            lines.append(f"\nSpeed of the {name}, fitted while inside the ground: {stat(speeds)} m a year.")
    return "\n".join(lines)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--ages", default=",".join(str(a) for a in AGES))
    ap.add_argument("--spread", action="store_true", help="how far and how fast a forest advances")
    a = ap.parse_args()
    ages = [int(x) for x in a.ages.split(",")]
    for f in a.folders:
        print(table(Path(f), ages))
        print()
        if a.spread:
            print(spread_table(Path(f)))
            print()
    print("\n".join(SOURCES))


if __name__ == "__main__":
    main()
