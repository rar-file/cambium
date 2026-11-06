"""M2: does moving alpha keep the shape of Eriksson's curves across site index?

For each alpha: the site index the mean height reads as at each age, on the approved equation and
T13 rule.  A tree following one curve reads the same at every age.  Below age 20 no approved band
applies (QUESTIONS.md Q17), so those columns are information, never a verdict.  Exploring only;
reads saved outputs and the approved equation.

    python tools/m2_shape.py > out/bench/ensemble/m2_shape.txt
    python tools/m2_shape.py 0.48=pc_base 1.44=pc_fineroot_1.44         # any ensembles, by name=folder
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from scorecard import load_approved_targets, t13_years  # noqa: E402
from treegen.reference import eriksson_1997_height  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
SWEEP = {"2.7": "m2_alpha_2.7", "3.5": "m2_alpha_3.5", "4.0": "m2_alpha_4.0", "4.4": "m2_alpha_4.4", "4.6": "m2_alpha_4.6", "4.8": "base_trees",
         "5.0": "m2_alpha_5.0", "5.2": "m2_alpha_5.2", "5.8": "m2_alpha_5.8", "6.8": "m2_alpha_6.8"}
AGES = (5, 10, 15, 20, 30, 40, 50, 60)


def curve(item: dict, si: float, age: float) -> float | None:
    """Height on the SI curve at total age, or None before breast height."""
    p = item["parameters"]
    bh = age - t13_years(item, si)
    if bh <= 0:
        return None
    return eriksson_1997_height(si, bh, p["asi"], p["beta"], p["b2"], float(item["reference_age_years"]))


def reads_as(item: dict, height: float, age: float) -> float | None:
    """The site index whose curve passes through this height at this age."""
    lo, hi = 8.0, 60.0
    a, b = curve(item, lo, age), curve(item, hi, age)
    if a is None or b is None or not a <= height <= b:
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        h = curve(item, mid, age)
        if h is None or h < height:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def mean_height(folder: Path, age: int) -> float:
    values = []
    for d in folder.glob("*_stand"):
        py = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
        values.append(py[age]["height_m"])
    return statistics.fmean(values)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    chosen = dict(a.split("=", 1) for a in sys.argv[1:]) or SWEEP
    item = load_approved_targets("targets-approved")["tree_allometry"]["site_index_curves"]
    print("**The curves themselves, height (m) by total age, approved equation and T13 rule:**\n")
    print("| SI | " + " | ".join(str(a) for a in AGES) + " |\n|---|" + "---|" * len(AGES))
    for si in (20, 22, 26, 29, 32):
        print(f"| {si} | " + " | ".join("-" if (h := curve(item, si, a)) is None else f"{h:.2f}" for a in AGES) + " |")
    print("| Ratio SI 32 to SI 22 | " + " | ".join(
        "-" if curve(item, 22, a) is None or curve(item, 32, a) is None else f"{curve(item, 32, a) / curve(item, 22, a):.2f}" for a in AGES) + " |")
    heights = {}
    for name, folder in chosen.items():
        if (E / folder).exists() and len(list((E / folder).glob("*_stand"))) == 20:
            heights[name] = {a: mean_height(E / folder, a) for a in AGES}
    print("\n**Model's mean height (m), stand trees, 20 seeds:**\n")
    print("| Alpha | " + " | ".join(str(a) for a in AGES) + " |\n|---|" + "---|" * len(AGES))
    for name, h in heights.items():
        print(f"| {name} | " + " | ".join(f"{h[a]:.2f}" for a in AGES) + " |")
    first, last = ("3.5", "6.8") if chosen is SWEEP else (list(heights)[-1], list(heights)[0])
    print(f"| Ratio {last} to {first} | " + " | ".join(f"{heights[last][a] / heights[first][a]:.2f}" for a in AGES) + " |")
    print("\n**The site index that height reads as at each age. On one curve, a row would be level. Ages under 20: information only.**\n")
    print("| Alpha | " + " | ".join(str(a) for a in AGES) + " |\n|---|" + "---|" * len(AGES))
    for name, h in heights.items():
        print(f"| {name} | " + " | ".join("-" if (x := reads_as(item, h[a], a)) is None else f"{x:.1f}" for a in AGES) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
