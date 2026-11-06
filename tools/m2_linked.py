"""M2: the figures behind Q21, Q22 and Q23 that no other tool saves.  Reads saved outputs; changes nothing.

    python tools/m2_linked.py > out/bench/ensemble/m2_linked.txt

Implied k is how fast light fades through leaves, worked back from the model's own output:
k = -ln(light) / LAI, from the ensemble's means.  So light L needs LAI = -ln(L) / k.  Paired differences are
means over seeds, +- the standard error of the difference, as in tools/paired.py.  Every folder holds 20
trees (or 5 plots) on the node.
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

from scorecard import ensemble_folders, evaluate_ensemble, load_approved_targets, load_run_data  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
HT, LAI, LIGHT, WIDTH = "height_m", "lai", "subcanopy_diffuse_light_pct", "crown_width_m"


def trees(label: str) -> dict:
    out = {}
    for d in sorted((E / label).glob("*_stand")):
        out[int(d.name.split("_")[0])] = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
    return out


def plots(label: str) -> dict:
    out = {}
    for d in sorted((E / label).glob("plot_*")):
        out[int(d.name.split("_")[1])] = json.loads((d / "plot.json").read_text(encoding="utf-8"))["stats"]
    return out


def at(rows: list, age: int, field: str):
    return next(r for r in rows if r["year"] == age).get(field)


def mean_at(sets: dict, age: int, field: str) -> float:
    return statistics.mean(at(v, age, field) for v in sets.values())


def paired(a: dict, b: dict, age: int, field: str) -> str:
    seeds = sorted(set(a) & set(b))
    d = [at(b[s], age, field) - at(a[s], age, field) for s in seeds]
    return f"{statistics.mean(d):+.3f} +- {statistics.stdev(d) / math.sqrt(len(d)):.3f}"


def per_seed_k(sets: dict, age: int) -> str:
    """Across seeds: each seed's own k, and how closely -ln(light) follows LAI (Pearson r)."""
    lai = [at(v, age, LAI) for v in sets.values()]
    fade = [-math.log(at(v, age, LIGHT) / 100.0) for v in sets.values()]
    ks = [f / x for f, x in zip(fade, lai)]
    r = statistics.correlation(lai, fade) if len(lai) > 2 else float("nan")
    return f"{statistics.mean(ks):.3f} +- {statistics.stdev(ks):.3f} | {r:+.2f}"


def k_row(name: str, sets: dict) -> list:
    out = []
    for age in (50, 60):
        lai, q = mean_at(sets, age, LAI), mean_at(sets, age, LIGHT)
        k = -math.log(q / 100.0) / lai
        out.append(f"| {name} | {age} | {len(sets)} | {lai:.3f} | {q:.2f} | {k:.3f} | {q - 100.0 * math.exp(-0.37 * lai):+.2f} | {-math.log(0.198) / k:.2f} |")
    return out


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base, off, both = trees("base_trees"), trees("m2_nowood"), trees("m2_cc")
    p_base, p_off, p_both, p_shade = plots("base_plots"), plots("m2_plots_nowood"), plots("m2_plots_cc"), plots("m2_plots_shade15_a4.8")
    print("## Implied k, node\n")
    print("| Set | Age | Seeds | LAI | Light (%) | k implied | Light minus exp(-0.37 LAI) (points) | LAI that 19.8 % light would need at this k |")
    print("|---|---|---|---|---|---|---|---|")
    for name, s in (("Trees, wood on", base), ("Trees, wood off", off), ("Trees, both", both), ("Plots, wood on", p_base), ("Plots, wood off", p_off), ("Plots, both", p_both), ("Plots, wood on, death lines 0.15 (test value)", p_shade)):
        print("\n".join(k_row(name, s)))
    print("\nAt k 0.37, 19.8 % light needs LAI " + f"{-math.log(0.198) / 0.37:.2f}.")

    print("\n## Implied k by age, node, trees\n")
    print("| Set | 20 | 30 | 50 | 60 |\n|---|---|---|---|---|")
    for name, s in (("Wood on", base), ("Wood off", off), ("Both", both)):
        cells = []
        for age in (20, 30, 50, 60):
            lai, q = mean_at(s, age, LAI), mean_at(s, age, LIGHT)
            cells.append(f"{-math.log(q / 100.0) / lai:.3f}")
        print(f"| {name} | " + " | ".join(cells) + " |")

    print("\n## Plots' heights against a stand tree, both corrections\n")
    print("| Alpha | Age | Top height on the curve (m) | Thickest 100/ha, mean (m) | All plot trees, mean (m) | Stand tree (m) | All plot trees minus stand tree (m) |\n|---|---|---|---|---|---|---|")
    targets = load_approved_targets("targets-approved")
    for alpha, plot_label, tree_label in (("3.0", "m2_plots_cc_a3.0", "m2_cc_a3.0"), ("3.5", "m2_plots_cc_a3.5", "m2_cc_a3.5"), ("4.8", "m2_plots_cc", "m2_cc")):
        runs = [load_run_data(str(x)) for x in ensemble_folders(E / plot_label)]
        rows = {r["target"]: r for r in evaluate_ensemble(targets, runs, [50, 60])}
        stand = trees(tree_label)
        for age in (50, 60):
            tops, means = [], []
            for folder in sorted((E / plot_label).glob("plot_*")):
                doc = json.loads((folder / "plot.json").read_text(encoding="utf-8"))
                area_ha = doc["area_m2"] / 10000.0
                alive = []
                for t in doc["trees"]:
                    f = folder / f"tree_{t['id']:03d}" / "stats.json"
                    removed = t.get("removed")
                    if not f.exists() or (removed is not None and removed <= age):
                        continue
                    rec = next((r for r in json.loads(f.read_text(encoding="utf-8"))["per_year"] if r["year"] == age - t["germination"]), None)
                    if rec and (rec.get("dbh_cm") or 0.0) > 0.0:
                        alive.append(rec)
                alive.sort(key=lambda r: r["dbh_cm"], reverse=True)
                n = max(1, round(100.0 * area_ha))
                tops.append(statistics.mean(r["height_m"] for r in alive[:n]))
                means.append(statistics.mean(r["height_m"] for r in alive))
            s = mean_at(stand, age, HT)
            print(f"| {alpha} | {age} | {rows[f'tree_allometry.site_index_curves (age {age})']['mean']:.2f} | {statistics.mean(tops):.2f} | {statistics.mean(means):.2f} | {s:.2f} | {statistics.mean(means) - s:+.2f} |")

    print("\n## Across seeds: does each seed's light follow its own LAI?\n")
    print("| Set | Age | Seeds | Each seed's k, mean +- SD | r between LAI and -ln(light) |\n|---|---|---|---|---|")
    for name, s in (("Trees, wood on", base), ("Trees, wood off", off), ("Trees, both", both), ("Plots, wood on", p_base), ("Plots, wood off", p_off), ("Plots, both", p_both)):
        for age in (50, 60):
            print(f"| {name} | {age} | {len(s)} | {per_seed_k(s, age)} |")

    print("\n## Paired change in k-related rows, wood off against wood on\n")
    print("| Set | Age | LAI | Light (points) |\n|---|---|---|---|")
    for name, a, b in (("Trees", base, off), ("Plots", p_base, p_off)):
        for age in (50, 60):
            print(f"| {name} | {age} | {paired(a, b, age, LAI)} | {paired(a, b, age, LIGHT)} |")
    print("\nPer plot, light at 50 and 60, wood off minus wood on: " + "; ".join(f"plot {s}: {at(p_off[s], 50, LIGHT) - at(p_base[s], 50, LIGHT):+.2f}, {at(p_off[s], 60, LIGHT) - at(p_base[s], 60, LIGHT):+.2f}" for s in sorted(p_base)))

    print("\n## Two draws of the default and of each proposed correction (seeds 1-20, then 21-40), each paired with the default on its own seeds\n")
    fresh_base = trees("m2_base_fresh")
    print("| Change | Row | Age | Seeds 1-20 | Seeds 21-40 | All 40 |\n|---|---|---|---|---|---|")
    for name, first, fresh in (("Wood off", off, trees("m2_nowood_fresh")), ("Leaf charge", trees("m2_charge"), trees("m2_charge_fresh")), ("Both", both, trees("m2_cc_fresh"))):
        all_base, all_opt = {**base, **fresh_base}, {**first, **fresh}
        for label, field in (("Height", HT), ("LAI", LAI), ("Light", LIGHT)):
            for age in (50, 60):
                print(f"| {name} | {label} | {age} | {paired(base, first, age, field)} | {paired(fresh_base, fresh, age, field)} | {paired(all_base, all_opt, age, field)} |")
    print("\nThe default's own two draws, seeds 21-40 minus seeds 1-20, unpaired: " + "; ".join(f"{label} at {age}: {mean_at(fresh_base, age, field) - mean_at(base, age, field):+.3f}" for label, field in (("height", HT), ("LAI", LAI), ("light", LIGHT)) for age in (50, 60)) + ".")

    y50, a44 = trees("m2_cc_young0.50"), trees("m2_cc_a4.4")
    print("\n## Young apical 0.50 and alpha 4.4, each against both corrections (Q22)\n")
    print("| Age | Height: young 0.50 | Height: alpha 4.4 | LAI: young 0.50 | LAI: alpha 4.4 | Crown width: young 0.50 |\n|---|---|---|---|---|---|")
    for age in (20, 30, 40, 50, 60):
        print(f"| {age} | {paired(both, y50, age, HT)} | {paired(both, a44, age, HT)} | {paired(both, y50, age, LAI)} | {paired(both, a44, age, LAI)} | {paired(both, y50, age, WIDTH)} |")
    dom54 = trees("m2_cc_y50_dom54")
    print(f"\nApical dominance 0.54 alone, against young 0.50 with dominance 0.62, height at 60: {paired(y50, dom54, 60, HT)}.")
    shares = [100.0 * sum(at(v, 50, LAI) >= 3.60 for v in s.values()) / len(s) for s in (off, y50)]
    print(f"Seeds with LAI at 50 of 3.60 or more: wood off {shares[0]:.0f} %, young 0.50 {shares[1]:.0f} %.")

    charge = trees("m2_charge")
    print("\n## The leaf charge, with wood on and with wood off (Q23)\n")
    print("| Age | Height, wood on | Height, wood off | LAI, wood on | LAI, wood off |\n|---|---|---|---|---|")
    for age in (10, 20, 30, 40, 50, 60):
        print(f"| {age} | {paired(base, charge, age, HT)} | {paired(off, both, age, HT)} | {paired(base, charge, age, LAI)} | {paired(off, both, age, LAI)} |")

    off_f, both_f = trees("m2_nowood_fresh"), trees("m2_cc_fresh")
    all_off, all_both = {**off, **off_f}, {**both, **both_f}
    print("\nWith wood off, all 40 seeds: " + "; ".join(f"age {age}: height {paired(all_off, all_both, age, HT)}, LAI {paired(all_off, all_both, age, LAI)}" for age in (50, 60)) + ".")

    twin = trees("m2_diag_nowoodshade")
    print("\n## Two wood-off runs, same setting, same seeds, different commits (`f45928e`, `3f3d687`)\n")
    print("| Age | Height | LAI |\n|---|---|---|")
    for age in (30, 50, 60):
        print(f"| {age} | {paired(twin, off, age, HT)} | {paired(twin, off, age, LAI)} |")
    print("\n`tools/ensembles_identical.py m2_diag_nowoodshade m2_nowood` compares them field by field: `m2_twin_nowood.txt`.")

    ahead = trees("m2_cc_y50_ahead")
    print(f"\n## Young 0.50 with rings ahead (Q18)\n\nSeed 6 at 60: height {at(ahead[6], 60, HT):.2f} m, LAI {at(ahead[6], 60, LAI):.2f}, light {at(ahead[6], 60, LIGHT):.1f} %.")
    print(f"Height SD at 60: {statistics.stdev(at(v, 60, HT) for v in ahead.values()):.2f} m, against {statistics.stdev(at(v, 60, HT) for v in y50.values()):.2f} m without rings ahead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
