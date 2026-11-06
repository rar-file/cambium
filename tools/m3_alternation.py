"""M3a: how strong is the every-other-year pattern, across seeds?  Reads saved stand-tree outputs.

For each ensemble and age window: the lag-1 autocorrelation of yearly height growth (negative means
a big year tends to follow a small one), the share of seed-years with under 2 cm of height growth,
and the ratio of a year's growth to the next's.  The measures are this tool's own, for a diagnosis;
no source gives a number for them, so they aren't targets.

    python tools/m3_alternation.py base_trees m2_alpha_4.0 m2_diag_maxshoot
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "out" / "bench" / "ensemble"
WINDOWS = ((5, 19), (20, 39), (40, 60))


def lag1(x: list) -> float:
    m = statistics.fmean(x)
    top = sum((a - m) * (b - m) for a, b in zip(x, x[1:]))
    bottom = sum((a - m) ** 2 for a in x)
    return top / bottom if bottom > 0 else 0.0


def increments(folder: Path) -> dict:
    out = {}
    for d in folder.glob("*_stand"):
        py = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
        h = {r["year"]: r["height_m"] for r in py}
        out[int(d.name.split("_")[0])] = {y: h[y] - h[y - 1] for y in h if y - 1 in h}
    return out


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folders", nargs="+")
    a = ap.parse_args(argv)
    print("| Ensemble | Ages | Height growth lag-1 autocorrelation, mean +- SE | Seed-years under 2 cm of growth | Largest yearly growth, median seed (m) |")
    print("|---|---|---|---|---|")
    for name in a.folders:
        if not (E / name).exists():
            print(f"| `{name}` | not there yet | | | |")
            continue
        inc = increments(E / name)
        for lo, hi in WINDOWS:
            rs, small, total, top = [], 0, 0, []
            for s, by_year in inc.items():
                x = [by_year[y] for y in range(lo, hi + 1) if y in by_year]
                rs.append(lag1(x))
                small += sum(v < 0.02 for v in x)
                total += len(x)
                top.append(max(x))
            se = statistics.stdev(rs) / len(rs) ** 0.5
            print(f"| `{name}` | {lo}-{hi} | {statistics.fmean(rs):+.2f} +- {se:.2f} | {100 * small / total:.0f} % | {statistics.median(top):.2f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
