"""The birch v1 final report's hand-worked numbers, recomputed from saved outputs (final check (c), item 2).

    python tools/v1_workings.py [--ensemble out/bench/ensemble] [--old-plots DIR]

Prints, for reports/birch_v1_workings.txt:
- plot top height on the approved definition (scorecard's own naslund_top_height) from the tree lists;
- the young crown ratio from node_v1_young's tree lists;
- the Baltic LAI band year by year (node_v1_plots);
- the light extinction k = -ln(light / 100) / LAI;
- paired differences between seeds, mean +/- standard error;
- how often the height curve held the leader (height_limit.held_by) in the stand trees.
Reads only; runs no model.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import scorecard as sc  # noqa: E402


def plot_stats(folder: Path) -> dict:
    out = {}
    for p in sorted(folder.glob("plot_*"), key=lambda q: int(q.name.split("_")[1])):
        d = json.loads((p / "plot.json").read_text(encoding="utf-8"))
        out[int(p.name.split("_")[1])] = ({s["year"]: s for s in d["stats"]}, p)
    return out


def tree_list(p: Path, age: int):
    f = p / f"trees_{age:03d}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def paired(a: dict, b: dict) -> str:
    keys = sorted(set(a) & set(b))
    d = [b[k] - a[k] for k in keys]
    if len(d) < 2:
        return "n/a"
    return f"{st.fmean(d):+.3f} +/- {st.stdev(d) / math.sqrt(len(d)):.3f} (n {len(d)})"


def stand_seeds(folder: Path) -> dict:
    out = {}
    for s in sorted(folder.glob("*_stand")) + sorted(folder.glob("*_open")):
        out[int(s.name.split("_")[0])] = {r["year"]: r for r in json.loads((s / "stats.json").read_text(encoding="utf-8"))["per_year"]}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensemble", default=str(ROOT / "out" / "bench" / "ensemble"))
    ap.add_argument("--old-plots", nargs="*", default=[], help="plot folders of the settings before the forest fixes (seeds paired by number)")
    a = ap.parse_args()
    E = Path(a.ensemble)

    plots = plot_stats(E / "node_v1_plots")
    print(f"== node_v1_plots: {len(plots)} plots")
    for age in (30, 50, 60):
        hs = []
        for _, (_, p) in plots.items():
            d = tree_list(p, age)
            recs = [{"dbh_cm": t["dbh_cm"], "height_m": t["height_m"]} for t in d["trees"] if t["alive"] and t["dbh_cm"]]
            hs.append(sc.naslund_top_height(recs, float(d["area_m2"]))[0])
        print(f"top height, approved definition, age {age}: {st.fmean(hs):.2f} m ({min(hs):.2f}-{max(hs):.2f})")
    years = sorted(next(iter(plots.values()))[0])
    inside = []
    for y in range(6, 61):
        if y in years:
            v = st.fmean(s[y]["lai"] for s, _ in plots.values())
            inside.append((y, v, 2.5 <= v <= 4.5))
    n_in = sum(1 for _, _, ok in inside if ok)
    print(f"Baltic band 2.5-4.5 at 6-60: inside in {n_in} of {len(inside)} years: {[y for y, _, ok in inside if ok]}")
    print(f"  under 2.5: {[y for y, v, _ in inside if v < 2.5]}; over 4.5: {[y for y, v, _ in inside if v > 4.5]}; peak {max(v for _, v, _ in inside):.2f}")
    for age in (50, 60):
        ks = [-math.log(s[age]["subcanopy_diffuse_light_pct"] / 100.0) / s[age]["lai"] for s, _ in plots.values()]
        lai = st.fmean(s[age]["lai"] for s, _ in plots.values())
        print(f"k at {age}: {st.fmean(ks):.3f}; LAI {lai:.3f}; LAI for light at the 14.8 % median: {-math.log(0.148) / st.fmean(ks):.2f}; "
              f"light at LAI 4.5: {100 * math.exp(-st.fmean(ks) * 4.5):.1f} %")

    young = E / "node_v1_young"
    if young.exists():
        yp = plot_stats(young)
        print(f"== node_v1_young: {len(yp)} plots")
        for age in (11, 15, 20, 22):
            means, low = [], 0
            for _, (_, p) in yp.items():
                d = tree_list(p, age)
                cr = [(t["height_m"] - t["crown_base_m"]) / t["height_m"] for t in d["trees"]
                      if t["alive"] and t["height_m"] > 0 and t["crown_base_m"] is not None]
                means.append(st.fmean(cr))
                low += sum(1 for c in cr if c <= 0.45)
            print(f"crown ratio at {age}: {st.fmean(means):.3f} ({min(means):.3f}-{max(means):.3f}); trees at 0.45 or under: {low}")

    if a.old_plots:
        old = {}
        for f in a.old_plots:
            old.update(plot_stats(Path(f)))
        for key, name in (("subcanopy_diffuse_light_pct", "light"), ("lai", "LAI")):
            for age in (50, 60):
                pa = {k: s[age][key] for k, (s, _) in old.items() if age in s}
                pb = {k: s[age][key] for k, (s, _) in plots.items()}
                print(f"forest fixes, paired by seed, {name} at {age}: {paired(pa, pb)}")

    for lab_a, lab_b in (("node_v1_trees", "node_v1_treesR"),):
        A, B = stand_seeds(E / lab_a), stand_seeds(E / lab_b)
        print(f"== {lab_b} minus {lab_a}, paired by seed")
        for key in ("subcanopy_diffuse_light_pct", "lai"):
            for age in (50, 60):
                pa = {k: v[age][key] for k, v in A.items()}
                pb = {k: v[age][key] for k, v in B.items()}
                print(f"{key} at {age}: {paired(pa, pb)}")
    B = stand_seeds(E / "node_v1_treesR")
    held = {}
    for v in B.values():
        for r in v.values():
            h = (r.get("height_limit") or {}).get("held_by")
            if h:
                held[h] = held.get(h, 0) + 1
    print(f"== node_v1_treesR: what held the leader, seed-years: {held}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
