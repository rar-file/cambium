"""M2: the alpha sweep on stand trees, with the paired comparisons PROTOCOL.md section 4 asks for.
Exploring only.  Reads saved outputs; the 6.0 row is the 20-seed screen's alpha x 1.25.

    python tools/m2_alpha_report.py > out/bench/ensemble/m2_alpha_report.txt
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

from paired import paired_difference  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
SCREEN = ROOT / "out" / "bench" / "node" / "screen20"
SEEDS = range(1, 21)
BAND_TOP = {50: 25.1239, 60: 26.7328}
FOLDERS = {"2.7": "m2_alpha_2.7", "3.5": "m2_alpha_3.5", "4.0": "m2_alpha_4.0", "4.4": "m2_alpha_4.4", "4.6": "m2_alpha_4.6", "4.8": "base_trees",
           "5.0": "m2_alpha_5.0", "5.2": "m2_alpha_5.2", "5.8": "m2_alpha_5.8", "6.8": "m2_alpha_6.8"}


def load():
    out = {}
    for a, folder in FOLDERS.items():
        rows = {}
        for s in SEEDS:
            f = E / folder / f"{s}_stand" / "stats.json"
            if not f.exists():
                break
            py = json.loads(f.read_text(encoding="utf-8"))["per_year"]
            rows[s] = {age: {"h": py[age]["height_m"], "lai": py[age]["lai"], "light": py[age]["subcanopy_diffuse_light_pct"], "la": py[age]["leaf_area_m2"]} for age in (30, 50, 60)}
        if len(rows) == 20:
            out[a] = rows
    rows = {}
    for s in SEEDS:
        d = json.loads((SCREEN / f"resource.alpha__x1.25__s{s}.json").read_text())
        rows[s] = {age: {"h": d[str(age)]["height_m"], "lai": d[str(age)]["lai"], "light": d[str(age)]["diffuse_light_pct"], "la": d[str(age)]["leaf_area_m2"]} for age in (30, 50, 60)}
    out["6.0"] = rows
    return dict(sorted(out.items(), key=lambda x: float(x[0])))


def values(rows, age, key):
    return [rows[s][age][key] for s in SEEDS]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = load()
    print("# Alpha on stand trees: 20 seeds each, node. Exploring only. 6.0 is the screen's alpha x 1.25, at code 68782d9; 4.8 is the baseline, at 68782d9; the rest at f45928e.\n")
    print("| Alpha | Height at 50, 60 (m) | Over band top at 50, 60 (m) | LAI at 50 +- SE | LAI at 60 +- SE | SEs under 3.6 at 50, 60 | Median LAI at 60 | Seeds at 3.6 or more at 60 | Light at 50, 60 (%) | k at 60 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for a, rows in data.items():
        h = {age: statistics.fmean(values(rows, age, "h")) for age in (50, 60)}
        l50, l60 = values(rows, 50, "lai"), values(rows, 60, "lai")
        se50, se60 = statistics.stdev(l50) / 20 ** 0.5, statistics.stdev(l60) / 20 ** 0.5
        m50, m60 = statistics.fmean(l50), statistics.fmean(l60)
        light = {age: statistics.fmean(values(rows, age, "light")) for age in (50, 60)}
        k = sum(x * -math.log(y / 100.0) for x, y in zip(l60, values(rows, 60, "light"))) / sum(x * x for x in l60)
        print(f"| {a} | {h[50]:.2f}, {h[60]:.2f} | {h[50] - BAND_TOP[50]:+.2f}, {h[60] - BAND_TOP[60]:+.2f} | {m50:.3f} +- {se50:.3f} | {m60:.3f} +- {se60:.3f} | "
              f"{(3.6 - m50) / se50:+.1f}, {(3.6 - m60) / se60:+.1f} | {statistics.median(l60):.2f} | {sum(x >= 3.6 for x in l60)} | {light[50]:.1f}, {light[60]:.1f} | {k:.3f} |")
    print("\n**LAI between neighbouring settings, paired on seed (difference +- SE, ratio; counts above 2):**\n")
    print("| Step | At 50 | At 60 |\n|---|---|---|")
    keys = list(data)
    for x, y in list(zip(keys, keys[1:])) + [("5.2", "6.8")]:
        cells = []
        for age in (50, 60):
            r = paired_difference(values(data[x], age, "lai"), values(data[y], age, "lai"))
            cells.append(f"{r['mean']:+.3f} +- {r['se']:.3f} ({r['ratio']:.1f})")
        print(f"| {x} to {y} | {cells[0]} | {cells[1]} |")
    print("\n**Age 30, per tree, because LAI there depends on the stem density, which depends on height:**\n")
    print("| Alpha | Height (m) | Leaf area of the tree (m2) | LAI |\n|---|---|---|---|")
    for a, rows in data.items():
        print(f"| {a} | {statistics.fmean(values(rows, 30, 'h')):.2f} | {statistics.fmean(values(rows, 30, 'la')):.1f} | {statistics.fmean(values(rows, 30, 'lai')):.2f} |")


if __name__ == "__main__":
    main()
