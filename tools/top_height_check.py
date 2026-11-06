"""Once, as a cross-check (the maintainer, 2026-11-06): the plots' top height two ways.

Elfving 2010 p. 58: "Top height is defined as the height according to the height curve at
the mean diameter of the 100 by diameter largest trees per hectare."  The report names no
curve.  This fits a Naslund curve to each plot at each age, h = 1.3 + d^2 / (a + b d)^2, as a
straight line of d / sqrt(h - 1.3) on d, and reads it at those trees' mean diameter, against
those trees' mean height.  It came out over the maintainer's 0.3 m limit, so the scorecard now uses the
curve too (DECISIONS.md row 44); this tool shows the difference.

    python tools/top_height_check.py out/bench/ensemble/base_plots
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AGES = (20, 30, 40, 50, 60)


def naslund_fit(d: np.ndarray, h: np.ndarray) -> tuple:
    """(a, b) of h = 1.3 + d^2 / (a + b d)^2, from trees taller than breast height."""
    ok = (d > 0) & (h > 1.3)
    b, a = np.polyfit(d[ok], d[ok] / np.sqrt(h[ok] - 1.3), 1)
    return float(a), float(b)


def naslund_height(d: float, a: float, b: float) -> float:
    return 1.3 + d * d / (a + b * d) ** 2


def thickest(d: np.ndarray, h: np.ndarray, need: float) -> tuple:
    """Mean diameter and mean height of the thickest `need` trees; the last one counts with
    its fractional share, as tools/scorecard.py does."""
    order = np.argsort(-d)
    w_sum = d_sum = h_sum = 0.0
    for i in order:
        w = min(1.0, need - w_sum)
        if w <= 0.0:
            break
        w_sum += w
        d_sum += w * d[i]
        h_sum += w * h[i]
    return d_sum / w_sum, h_sum / w_sum, w_sum


def live_trees(folder: Path, age: int) -> tuple:
    plot = json.loads((folder / "plot.json").read_text(encoding="utf-8"))
    ds, hs = [], []
    for t in plot["trees"]:
        if t.get("removed") is not None and t["removed"] <= age:
            continue
        f = folder / f"tree_{t['id']:03d}" / "stats.json"
        if not f.exists():
            continue
        y = age - int(t.get("germination", 0) or 0)
        r = next((r for r in json.loads(f.read_text(encoding="utf-8"))["per_year"] if r["year"] == y), None)
        if r and r.get("dbh_cm") and r.get("height_m"):
            ds.append(r["dbh_cm"])
            hs.append(r["height_m"])
    return np.array(ds, float), np.array(hs, float), float(plot["area_m2"])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(sys.argv[1])
    print("| Plot | Age | Live trees | Trees counted (100/ha) | Mean height (m) | Naslund at their mean diameter (m) | Difference (m) |")
    print("|---|---|---|---|---|---|---|")
    worst = 0.0
    all_diffs = []
    for folder in sorted(d for d in root.iterdir() if (d / "plot.json").exists()):
        for age in AGES:
            d, h, area = live_trees(folder, age)
            if len(d) < 5:
                continue
            md, mh, counted = thickest(d, h, 100.0 * area / 1e4)
            a, b = naslund_fit(d, h)
            curve = naslund_height(md, a, b)
            diff = curve - mh
            all_diffs.append(diff)
            worst = max(worst, abs(diff))
            print(f"| {folder.name} | {age} | {len(d)} | {counted:.2f} | {mh:.2f} | {curve:.2f} | {diff:+.2f} |")
    if all_diffs:
        print(f"\nLargest difference {worst:.2f} m; mean {np.mean(all_diffs):+.2f} m; mean of the absolute differences {np.mean(np.abs(all_diffs)):.2f} m.")
        print("Under 0.3 m: keep the simple version." if worst < 0.3 else "0.3 m or more somewhere: not simply equivalent; see the table.")


if __name__ == "__main__":
    main()
