"""M2: the rerun of DECISIONS.md rows 66(a) and 68: first draw, fresh draw, and all seeds together, set
against row 62's lines.  Row 68: the no on the first 20 seeds stands; the fresh seeds are a better
estimate, not a second chance.  Reads saved outputs.

    python tools/m2_fresh.py both=m2_cc,m2_cc_fresh y50=m2_cc_young0.50,m2_cc_y50_fresh
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from scorecard import ensemble_folders, evaluate_ensemble, load_approved_targets, load_run_data  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
HEIGHT, LAI, LIGHT = "tree_allometry.site_index_curves", "stand_canopy.lai_hagemeier", "stand_canopy.subcanopy_light_transmittance"
AGES = (20, 30, 40, 50, 60)


def line(name: str, runs: list, targets: dict) -> str:
    rows = {r["target"]: r for r in evaluate_ensemble(targets, runs, list(AGES))}
    heights = [rows[f"{HEIGHT} (age {a})"] for a in AGES]
    lai = [rows[f"{LAI} (age {a})"] for a in (50, 60)]
    light = [rows[f"{LIGHT} (age {a})"] for a in (50, 60)]
    ok = all(h["status"] == "PASS" for h in heights) and all(x["mean"] >= 3.60 for x in lai)
    cells = ", ".join(f"{h['mean']:.2f}{'' if h['status'] == 'PASS' else ' F'}" for h in heights)
    se = lai[0]["sd"] / len(runs) ** 0.5
    return (f"| {name} | {len(runs)} | {cells} | {lai[0]['mean']:.3f} +- {se:.3f}, {lai[1]['mean']:.3f} | "
            f"{light[0]['mean']:.1f}, {light[1]['mean']:.1f} | {'yes' if ok else 'no'} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("settings", nargs="+", help="name=first,fresh")
    a = ap.parse_args(argv)
    targets = load_approved_targets("targets-approved")
    print("Means. F: height outside its band. LAI at 50 is shown +- its standard error between seeds.\n")
    print("| Setting and draw | Seeds | Height at 20, 30, 40, 50, 60 (m) | LAI at 50, 60 | Light at 50, 60 (%) | Meets row 62's lines? |")
    print("|---|---|---|---|---|---|")
    for s in a.settings:
        name, folders = s.split("=", 1)
        first, fresh = folders.split(",")
        r1 = [load_run_data(str(d)) for d in ensemble_folders(E / first)]
        r2 = [load_run_data(str(d)) for d in ensemble_folders(E / fresh)]
        print(line(f"{name}, seeds 1-20", r1, targets))
        print(line(f"{name}, seeds 21-40", r2, targets))
        print(line(f"{name}, all", r1 + r2, targets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
