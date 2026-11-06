"""M2: the apical grid, judged by DECISIONS.md row 62, which was written before its results were read.

    python tools/m2_grid_table.py both=m2_cc y50=m2_cc_young0.50 y54_o54=m2_cc_y54_o54 ...

A setting fits only if, as means of 20 seeds, height is inside its band at 20, 30, 40, 50 and 60 and LAI
is at least 3.60 at 50 and 60.  A height within 0.2 m of a band edge counts as depending on the draw.
Reads saved outputs.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from scorecard import ensemble_folders, evaluate_ensemble, load_approved_targets, load_run_data  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
HEIGHT, LAI_FLOOR, LIGHT = "tree_allometry.site_index_curves", 3.60, "stand_canopy.subcanopy_light_transmittance"
LAI = "stand_canopy.lai_hagemeier"
AGES = (20, 30, 40, 50, 60)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("settings", nargs="+", help="name=folder")
    ap.add_argument("--ref", default="targets-approved")
    a = ap.parse_args(argv)
    targets = load_approved_targets(a.ref)
    print(f"Targets at {a.ref}. Means. A star marks a height within 0.2 m of a band edge.\n")
    print("| Setting | Seeds | Height at 20 | 30 | 40 | 50 | 60 (m) | LAI at 50 | 60 | Light at 50 | 60 (%) | Fits by row 62? |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in a.settings:
        name, folder = s.split("=", 1)
        runs = [load_run_data(str(d)) for d in ensemble_folders(E / folder)]
        rows = {r["target"]: r for r in evaluate_ensemble(targets, runs, list(AGES))}
        cells, ok, edge = [], True, False
        for age in AGES:
            r = rows[f"{HEIGHT} (age {age})"]
            lo, hi = (float(x) for x in re.match(r"([0-9.]+)-([0-9.]+)", r["target_range"]).groups())
            near = min(abs(r["mean"] - lo), abs(r["mean"] - hi)) <= 0.2
            edge = edge or near
            ok = ok and r["status"] == "PASS"
            cells.append(f"{r['mean']:.2f}{'*' if near else ''} {'' if r['status'] == 'PASS' else 'F'}".strip())
        l50, l60 = rows[f"{LAI} (age 50)"]["mean"], rows[f"{LAI} (age 60)"]["mean"]
        ok = ok and l50 >= LAI_FLOOR and l60 >= LAI_FLOOR
        q50, q60 = rows[f"{LIGHT} (age 50)"]["mean"], rows[f"{LIGHT} (age 60)"]["mean"]
        verdict = "yes" if ok else "no"
        if ok and edge:
            verdict = "yes, depends on the draw"
        print(f"| {name} | {len(runs)} | " + " | ".join(cells) + f" | {l50:.3f} | {l60:.3f} | {q50:.1f} | {q60:.1f} | {verdict} |")
    print("\nF marks a height outside its band.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
