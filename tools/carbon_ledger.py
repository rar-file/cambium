"""The share of a year's fixed carbon that no sink took (review 2026-11-09, top 5, item 4).  Reporting only.

    python tools/carbon_ledger.py out/bench/ensemble/node_f5_trees out/bench/ensemble/node_f5_plots

growth.py takes what the pool couldn't spend off the year's "fixed" and saves it as carbon.sink_limited
(_growth_factor), so the carbon the leaves could have fixed is fixed + sink_limited, and the share turned down is
sink_limited over that.  Stand trees: from stats.json, every year.  Plots: from the tree lists (tools/tree_list.py),
at the list years only; a plot's share is the sum over its living trees.  The roots' unspent "rest" isn't saved in
either, so it isn't in these figures.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

AGES = (30, 50, 60)


def share(fixed: float, idle: float) -> float | None:
    return idle / (fixed + idle) if fixed + idle > 0.0 else None


def trees(folder: Path) -> dict:
    out = {a: [] for a in AGES}
    for d in sorted(folder.glob("*_stand")):
        if not (d / "stats.json").exists():
            continue
        rows = {r["year"]: r for r in json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]}
        for a in AGES:
            c = (rows.get(a) or {}).get("carbon") or {}
            s = share(float(c.get("fixed", 0.0)), float(c.get("sink_limited", 0.0)))
            if s is not None:
                out[a].append(s)
    return out


def plots(folder: Path) -> tuple:
    whole, per_tree = {a: [] for a in AGES}, {a: [] for a in AGES}
    for d in sorted(folder.glob("plot_*")):
        for a in AGES:
            f = d / f"trees_{a:03d}.json"
            if not f.exists():
                continue
            rows = [t for t in json.loads(f.read_text(encoding="utf-8"))["trees"] if t["alive"] and t.get("carbon_fixed") is not None]
            fixed = sum(float(t["carbon_fixed"]) for t in rows)
            idle = sum(float(t.get("carbon_sink_limited") or 0.0) for t in rows)
            s = share(fixed, idle)
            if s is not None:
                whole[a].append(s)
            per_tree[a] += [x for x in (share(float(t["carbon_fixed"]), float(t.get("carbon_sink_limited") or 0.0)) for t in rows) if x is not None]
    return whole, per_tree


def line(name: str, by_age: dict) -> str:
    cells = []
    for a in AGES:
        xs = by_age[a]
        cells.append(f"{100 * statistics.fmean(xs):.1f} % ({100 * min(xs):.1f}-{100 * max(xs):.1f}), n {len(xs)}" if xs else "not saved")
    return f"| {name} | " + " | ".join(cells) + " |"


def main() -> int:
    print("| Share of fixed carbon no sink took | " + " | ".join(f"Age {a}" for a in AGES) + " |")
    print("|---|" + ":---:|" * len(AGES))
    for arg in sys.argv[1:]:
        folder = Path(arg)
        t = trees(folder)
        if any(t.values()):
            print(line(f"{folder.name}: stand trees, each tree", t))
        whole, per_tree = plots(folder)
        if any(whole.values()):
            print(line(f"{folder.name}: plots, each plot as a whole", whole))
            print(line(f"{folder.name}: plots, each living tree", per_tree))
    return 0


if __name__ == "__main__":
    sys.exit(main())
