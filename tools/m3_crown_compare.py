"""M3c: crown diameter of measured birches (Evo TLS 2024) beside the model's stand trees.  Not a target
yet: a target needs checker A and a move of the tag (PROTOCOL.md section 9).  The Evo table stays in
birch-data, never in the repo.  Birches there are silver and downy together, leaf-off, in mixed stands.

    python tools/m3_crown_compare.py base_trees
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "out" / "bench" / "ensemble"
EVO = Path("../birch-data/evo2024/Evo_TLS_2024_treelist_v3.csv")
BINS = ((5, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 35), (35, 45))


def evo_rows() -> list:
    rows = []
    with EVO.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["tree_sp"] == "3":
                rows.append({"d_cm": 100.0 * float(r["stem_diam"]), "h": float(r["tree_height"]), "crown": float(r["crown_diam"]), "slice": float(r["slice_height"]), "area": float(r["crown_area"])})
    return rows


def model_rows(folder: Path) -> list:
    rows = []
    for d in folder.glob("*_stand"):
        for r in json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]:
            if r["year"] in (20, 30, 40, 50, 60):
                rows.append({"age": r["year"], "d_cm": r["dbh_cm"], "h": r["height_m"], "crown": r["crown_width_m"], "projected": r.get("crown_projected_diameter_m")})
    return rows


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", default="base_trees")
    a = ap.parse_args(argv)
    evo = evo_rows()
    print(f"Evo birches: {len(evo)}. Stem diameter is at the height the tree was found: slice height median {statistics.median(r['slice'] for r in evo):.2f} m, 5-95 %: "
          f"{statistics.quantiles([r['slice'] for r in evo], n=20)[0]:.2f}-{statistics.quantiles([r['slice'] for r in evo], n=20)[18]:.2f} m.\n")
    model = model_rows(E / a.folder)
    print("| Stem diameter (cm) | Evo trees | Evo crown diameter, median (m) | Evo 10-90 % (m) | Evo height, median (m) | Model seed-ages | Model widest crown, median (m) | Model projected diameter, median (m) | Model height, median (m) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for lo, hi in BINS:
        e = [r for r in evo if lo <= r["d_cm"] < hi]
        m = [r for r in model if lo <= r["d_cm"] < hi]
        if len(e) >= 2:
            q = statistics.quantiles([r["crown"] for r in e], n=10)
            ev = f"{len(e)} | {statistics.median(r['crown'] for r in e):.2f} | {q[0]:.2f}-{q[8]:.2f} | {statistics.median(r['h'] for r in e):.1f}"
        else:
            ev = f"{len(e)} | - | - | -"
        mo = (f"{len(m)} | {statistics.median(r['crown'] for r in m):.2f} | {statistics.median(r['projected'] for r in m if r['projected'] is not None):.2f} | {statistics.median(r['h'] for r in m):.1f}"
              if m else "0 | - | - | -")
        print(f"| {lo}-{hi} | {ev} | {mo} |")
    print("\n**Model by age (`" + a.folder + "`, means over seeds):**\n")
    print("| Age | Stem diameter (cm) | Height (m) | Widest crown (m) | Projected diameter (m) |\n|---|---|---|---|---|")
    for age in (20, 30, 40, 50, 60):
        m = [r for r in model if r["age"] == age]
        print(f"| {age} | {statistics.fmean(r['d_cm'] for r in m):.1f} | {statistics.fmean(r['h'] for r in m):.1f} | {statistics.fmean(r['crown'] for r in m):.2f} | {statistics.fmean(r['projected'] for r in m):.2f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
