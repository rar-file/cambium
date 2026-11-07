"""Reads a plot profile from tools/speed_profile.py: shares, cost per tree-year by tree size, and memory.

    python tools/speed_plot_read.py out/bench/ensemble/node_speed_prof1/node_speed_plot_default.json
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for name in sys.argv[1:]:
        d = json.loads(Path(name).read_text(encoding="utf-8"))
        rows = {int(k): v for k, v in d["rows"].items()}
        total = sum(d["totals"].values())
        print(f"\n## {Path(name).stem}: {d['seconds']:.0f} s, {d['years']} years, area {d.get('area_m2', 0):.0f} m2")
        ages = [a for a in (10, 20, 30, 40, 50, 60) if a in rows]
        print("\n| Component | Seconds | Share | " + " | ".join(f"Year {a}" for a in ages) + " |")
        print("|---|---|---|" + "---|" * len(ages))
        for c in sorted(d["totals"], key=lambda k: -d["totals"][k]):
            print(f"| {c} | {d['totals'][c]:.1f} | {100 * d['totals'][c] / total:.1f} % | " + " | ".join(f"{rows[a]['by'].get(c, 0.0):.2f}" for a in ages) + " |")
        print("| **Wall** |  |  | " + " | ".join(f"{rows[a]['wall']:.1f}" for a in ages) + " |")
        for key in ("trees", "nodes", "alive", "rss_mb"):
            print(f"| {key} |  |  | " + " | ".join(f"{rows[a][key]:.0f}" for a in ages) + " |")
        tree_years = sum(r["stepped"] for r in rows.values())
        steps = sum(r["tree_steps_s"] for r in rows.values())
        print(f"\nTree-years {tree_years}; {d['seconds'] / tree_years:.3f} s per tree-year all in; {steps / tree_years:.3f} s in the trees' own steps; "
              f"{(d['seconds'] - steps) / tree_years:.3f} s shared (light, soil, the plot's own).")
        lo = 0
        print("\n| Live nodes in the tree | Tree-years | Seconds per tree-year | Per 1,000 live nodes |")
        print("|---|---|---|---|")
        per = d["per_tree"]
        for hi in (500, 2000, 5000, 10000, 20000, 40000, 10 ** 9):
            hit = [p for p in per if lo <= p[2] < hi]
            if hit:
                s = statistics.fmean(p[3] for p in hit)
                nodes = statistics.fmean(p[2] for p in hit)
                print(f"| {lo}-{hi if hi < 10 ** 9 else 'up'} | {len(hit)} | {s:.3f} | {1000 * s / max(nodes, 1):.3f} |")
            lo = hi
        by_age = {}
        for p in per:
            by_age.setdefault(p[0], []).append(p[3])
        print("\nPer tree-year by plot age: " + ", ".join(f"{a}: {statistics.fmean(by_age[a]):.3f} s" for a in ages if a in by_age))
        for age, m in d["memory"].items():
            if int(age) in (20, 40, 60):
                n = rows[int(age)]["trees"]
                print(f"\nMemory, year {age}, {n} trees: {m['model_mb']} MB in attributes, {m['model_mb'] / max(n, 1):.1f} a tree; " + ", ".join(f"{t['what'].replace('plot.trees[*].', '')} {t['mb']}" for t in m["top"][:9]))


if __name__ == "__main__":
    main()
