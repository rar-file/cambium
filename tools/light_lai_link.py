"""Does a tree's light under the canopy just follow its leaf area?  (the maintainer, 2026-11-06)

The paper behind the light target gives an extinction coefficient of 0.37, so Beer-Lambert
says light = 100 * exp(-0.37 * LAI): LAI 3.2 gives about 30 %, and 19.8 % needs about 4.4.
If the model's diffuse light follows its LAI this way across the seeds of an ensemble, the
two failures are one failure, and should be reported as linked.

    python tools/light_lai_link.py out/bench/ensemble/base_trees --ages 20,30,40,50,60
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path


def read_seeds(folder: Path) -> dict:
    out = {}
    for f in sorted(folder.glob("*_stand/stats.json")):
        out[int(f.parent.name.split("_")[0])] = json.loads(f.read_text(encoding="utf-8"))["per_year"]
    return out


def fit_through_origin(xs: list, ys: list) -> float:
    """Slope of y = k x, the one number Beer-Lambert allows."""
    return sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)


def correlation(xs: list, ys: list) -> float:
    return statistics.correlation(xs, ys) if len(set(xs)) > 1 and len(set(ys)) > 1 else float("nan")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder")
    ap.add_argument("--ages", default="20,30,40,50,60")
    ap.add_argument("--k", type=float, default=0.37)
    ap.add_argument("--light-key", default="subcanopy_diffuse_light_pct")
    a = ap.parse_args(argv)
    seeds = read_seeds(Path(a.folder))
    print(f"{len(seeds)} seeds; light = {a.light_key}; Beer-Lambert k = {a.k}\n")
    print("| Age | Mean LAI | Mean light % | Light from LAI at k % | Mean gap, points | Largest gap | Correlation of -ln(light) with LAI | Fitted k |")
    print("|---|---|---|---|---|---|---|---|")
    pooled_x, pooled_y = [], []
    for age in [int(x) for x in a.ages.split(",")]:
        lai = [rows[age]["lai"] for rows in seeds.values()]
        light = [rows[age][a.light_key] for rows in seeds.values()]
        pred = [100.0 * math.exp(-a.k * x) for x in lai]
        gap = [m - p for m, p in zip(light, pred)]
        od = [-math.log(m / 100.0) for m in light]
        pooled_x += lai
        pooled_y += od
        print(f"| {age} | {statistics.fmean(lai):.2f} | {statistics.fmean(light):.1f} | {statistics.fmean(pred):.1f} | "
              f"{statistics.fmean(gap):+.2f} | {max(gap, key=abs):+.2f} | {correlation(lai, od):+.3f} | {fit_through_origin(lai, od):.3f} |")
    print(f"\nAll those ages pooled: fitted k {fit_through_origin(pooled_x, pooled_y):.3f}, correlation {correlation(pooled_x, pooled_y):+.3f}, {len(pooled_x)} points.")
    print(f"LAI needed for 19.8 % light at k = {a.k}: {-math.log(0.198) / a.k:.2f}; light at LAI 3.2: {100 * math.exp(-a.k * 3.2):.1f} %.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
