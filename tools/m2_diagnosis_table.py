"""M2: what moves the leaf-area ceiling?  Each diagnosis run against its baseline, paired on seed.
Exploring only; nothing here is adopted.  Reads saved outputs.

    python tools/m2_diagnosis_table.py base_trees m2_shade15_a4.8 m2_diag_apical ...
    python tools/m2_diagnosis_table.py m2_alpha_4.0 m2_shade15_a4.0

The first folder is the baseline.  A difference counts only above 2 standard errors of the paired
difference (PROTOCOL.md section 4).  With this many cells, a lone pass is a reason to look further.
"""
from __future__ import annotations

import argparse
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from paired import load, paired_difference  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
ROWS = (
    ("height_m", "Height (m)", (5, 10, 20, 30, 50, 60)),
    ("leaf_area_m2", "Tree's leaf area (m2)", (30, 50, 60)),
    ("lai", "LAI", (30, 50, 60)),
    ("subcanopy_diffuse_light_pct", "Light (%)", (30, 50, 60)),
    ("living_spurs", "Living spurs", (50, 60)),
    ("living_internodes", "Living internodes", (50, 60)),
    ("crown_width_m", "Crown width (m)", (50, 60)),
)


def cell(base, option, seeds, metric, age):
    # a value can be missing (no light reading under a canopy shorter than the sampling heights)
    seeds = [s for s in seeds if base[s][age][metric] is not None and option[s][age][metric] is not None]
    a = [base[s][age][metric] for s in seeds]
    b = [option[s][age][metric] for s in seeds]
    r = paired_difference(a, b)
    if r is None:
        return float("nan"), float("nan"), "too few seeds"
    flag = "**" if r["ratio"] > 2 else ""
    return statistics.fmean(a), statistics.fmean(b), f"{flag}{r['mean']:+.3g} +- {r['se']:.2g}{flag}"


def implied_k(rows, seeds, age):
    seeds = [s for s in seeds if rows[s][age]["subcanopy_diffuse_light_pct"] is not None]
    lai = [rows[s][age]["lai"] for s in seeds]
    light = [rows[s][age]["subcanopy_diffuse_light_pct"] for s in seeds]
    if not seeds:
        return float("nan")
    return sum(x * -math.log(y / 100.0) for x, y in zip(lai, light)) / sum(x * x for x in lai)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("base")
    ap.add_argument("options", nargs="+")
    a = ap.parse_args(argv)
    base = load(E / a.base)
    options = {name: load(E / name) for name in a.options if (E / name).exists()}
    missing = [n for n in a.options if n not in options]
    if missing:
        print(f"Not there yet: {', '.join(missing)}\n")
    print(f"**Against `{a.base}`, paired on seed; bold counts over 2 SE. Mean of the baseline, then each option's mean and difference.**\n")
    print("| Row | Age | Baseline | " + " | ".join(f"`{n}`" for n in options) + " |")
    print("|---|---|---|" + "---|" * len(options))
    for metric, title, ages in ROWS:
        for age in ages:
            cells = []
            base_mean = None
            for name, rows in options.items():
                seeds = sorted(set(base) & set(rows))
                base_mean, mean, text = cell(base, rows, seeds, metric, age)
                cells.append(f"{mean:.3g}: {text}")
            print(f"| {title} | {age} | {base_mean:.3g} | " + " | ".join(cells) + " |")
    print(f"| Implied k | 60 | {implied_k(base, sorted(base), 60):.3f} | " + " | ".join(f"{implied_k(r, sorted(r), 60):.3f}" for r in options.values()) + " |")
    print(f"\nSeeds: baseline {len(base)}; " + "; ".join(f"{n} {len(r)}" for n, r in options.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
