"""M2: apical settings, set against the lines of DECISIONS.md row 62, as tightened by row 68.

    python tools/m2_grid_table.py both=m2_cc y50=m2_cc_young0.50 --outside y50_ahead=m2_cc_y50_ahead

A setting meets the lines only if, as means, height is inside its band at 20, 30, 40, 50 and 60 and LAI
is at least 3.60 at 50 and 60.  A star marks a mean that depends on the draw: a height within 0.2 m of a
band edge, or an LAI within 0.12 of 3.60, the size by which runs at the same or almost the same setting
differ (row 68).  --outside marks settings that row 62's frame doesn't cover: they never read as fits.
Reads saved outputs.  Warns and exits 1, after the table, if a set mixes machines or code versions, or
has other than 20 seeds, the number row 62 and PROTOCOL.md section 2 ask of trees.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from gate import REQUIRED_SEEDS, code_of, machine_of, per_seed  # noqa: E402
from scorecard import ensemble_folders, evaluate_ensemble, load_approved_targets, load_run_data  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
HEIGHT, LIGHT = "tree_allometry.site_index_curves", "stand_canopy.subcanopy_light_transmittance"
LAI = "stand_canopy.lai_hagemeier"
LAI_FLOOR, HEIGHT_EDGE, LAI_EDGE = 3.60, 0.2, 0.12
AGES = (20, 30, 40, 50, 60)


def seed_meets_every_line(row: dict) -> bool:
    for age in AGES:
        value, band = row[f"{HEIGHT} (age {age})"]
        if not band[0] <= value <= band[1]:
            return False
    return all(row[f"{LAI} (age {age})"][0] >= LAI_FLOOR for age in (50, 60))


def line_of(name: str, folder: str, targets: dict, outside: bool) -> str:
    runs = [load_run_data(str(d)) for d in ensemble_folders(E / folder)]
    rows = {r["target"]: r for r in evaluate_ensemble(targets, runs, list(AGES))}
    cells, ok, near_edge = [], True, False
    for age in AGES:
        r = rows[f"{HEIGHT} (age {age})"]
        lo, hi = (float(x) for x in re.match(r"([0-9.]+)-([0-9.]+)", r["target_range"]).groups())
        near = min(abs(r["mean"] - lo), abs(r["mean"] - hi)) <= HEIGHT_EDGE
        near_edge = near_edge or near
        ok = ok and r["status"] == "PASS"
        cells.append(f"{r['mean']:.2f}{'*' if near else ''}{'' if r['status'] == 'PASS' else ' F'}")
    lai, lai_cells = {}, []
    for age in (50, 60):
        lai[age] = rows[f"{LAI} (age {age})"]
        near = abs(lai[age]["mean"] - LAI_FLOOR) <= LAI_EDGE
        near_edge = near_edge or near
        ok = ok and lai[age]["mean"] >= LAI_FLOOR
        lai_cells.append(f"{lai[age]['mean']:.3f}{'*' if near else ''}")
    q50, q60 = rows[f"{LIGHT} (age 50)"]["mean"], rows[f"{LIGHT} (age 60)"]["mean"]
    h60 = rows[f"{HEIGHT} (age 60)"]
    share = sum(seed_meets_every_line(s) for s in per_seed(targets, runs, list(AGES))) / len(runs)
    verdict = "no"
    if ok:
        verdict = "numbers yes, outside the frame" if outside else ("yes, depends on the draw" if near_edge else "yes")
    elif outside:
        verdict = "no, outside the frame"
    return (f"| {name} | {len(runs)} | " + " | ".join(cells) + f" | {h60['sd']:.2f} | " + " | ".join(lai_cells)
            + f" | {lai[50]['sd']:.2f} | {q50:.1f} | {q60:.1f} | {100 * share:.0f} % | {verdict} |"), runs


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("settings", nargs="+", help="name=folder")
    ap.add_argument("--outside", action="append", default=[], metavar="NAME=FOLDER")
    ap.add_argument("--ref", default="targets-approved")
    a = ap.parse_args(argv)
    targets = load_approved_targets(a.ref)
    print(f"Targets at {a.ref}. Means. * depends on the draw: height within {HEIGHT_EDGE} m of a band edge, LAI within {LAI_EDGE} of {LAI_FLOOR}. F: height outside its band.\n")
    print("| Setting | Seeds | Height at 20 | 30 | 40 | 50 | 60 (m) | SD at 60 | LAI at 50 | 60 | SD at 50 | Light at 50 | 60 (%) | Seeds meeting every line | Meets row 62's lines? |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    every = []
    for s, outside in [(x, False) for x in a.settings] + [(x, True) for x in a.outside]:
        name, folder = s.split("=", 1)
        line, runs = line_of(name, folder, targets, outside)
        print(line)
        every.append(runs)
    machines = {machine_of(r) for runs in every for r in runs}
    codes = {code_of(r) for runs in every for r in runs}
    counts = {len(runs) for runs in every}
    print(f"\nMachines: {sorted(m[0] or '?' for m in machines)}. Commits: {sorted(str(c[0]) for c in codes)}. Seeds per set: {sorted(counts)}.")
    if len(machines) != 1 or len(codes) != 1 or counts != {REQUIRED_SEEDS["tree"]}:
        print("NOT LIKE FOR LIKE: this table mixes machines or code versions, or has other than 20 seeds in a set.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
