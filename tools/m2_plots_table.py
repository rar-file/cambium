"""M2: plots at several settings, judged by DECISIONS.md row 52, written before they were read.
Means of 5 seeds; a setting fits only if, at both 50 and 60, top height on the curve is inside its
band and LAI is inside both approved bands (3.6-4.5).  Light is shown beside it.  Reads saved outputs.

    python tools/m2_plots_table.py 4.8=base_plots 4.0=m2_alpha_plots_4.0 3.5=m2_alpha_plots_3.5
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
HEIGHT, HAG, BALTIC, LIGHT = "tree_allometry.site_index_curves", "stand_canopy.lai_hagemeier", "stand_canopy.lai_baltic_chronosequence", "stand_canopy.subcanopy_light_transmittance"


def rows_of(folder: Path, targets: dict) -> dict:
    runs = [load_run_data(str(d)) for d in ensemble_folders(folder)]
    rows = {r["target"]: r for r in evaluate_ensemble(targets, runs, [20, 30, 40, 50, 60])}
    rows["__n"] = len(runs)
    return rows


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("settings", nargs="+", help="name=folder")
    ap.add_argument("--ref", default="targets-approved")
    a = ap.parse_args(argv)
    targets = load_approved_targets(a.ref)
    print(f"Targets at {a.ref}. Means, with SD between seeds. Height is top height on the curve; bands at 50, 60: 18.76-25.12, 20.72-26.73 m.\n")
    print("| Setting | Seeds | Top height at 50 (m) | at 60 (m) | Over band top at 50, 60 (m) | LAI at 50 | at 60 | Light at 50 (%) | at 60 (%) | Stems/ha at 45 | Fits by row 52? |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for s in a.settings:
        name, folder = s.split("=", 1)
        if not (E / folder).exists():
            print(f"| {name} | not there yet |")
            continue
        r = rows_of(E / folder, targets)
        h50, h60 = r[f"{HEIGHT} (age 50)"], r[f"{HEIGHT} (age 60)"]
        l50, l60 = r[f"{HAG} (age 50)"], r[f"{HAG} (age 60)"]
        b50, b60 = r[f"{BALTIC} (age 50)"], r[f"{BALTIC} (age 60)"]
        q50, q60 = r[f"{LIGHT} (age 50)"], r[f"{LIGHT} (age 60)"]
        fits = all(x["status"] == "PASS" for x in (h50, h60, l50, l60, b50, b60))
        top50, top60 = 25.1239, 26.7328
        density = r.get("stand_canopy.stand_density (age 45)", {}).get("mean")
        print(f"| {name} | {r['__n']} | {h50['mean']:.2f} +- {h50['sd']:.2f} | {h60['mean']:.2f} +- {h60['sd']:.2f} | {h50['mean'] - top50:+.2f}, {h60['mean'] - top60:+.2f} | "
              f"{l50['mean']:.2f} +- {l50['sd']:.2f} | {l60['mean']:.2f} +- {l60['sd']:.2f} | {q50['mean']:.1f} +- {q50['sd']:.1f} | {q60['mean']:.1f} +- {q60['sd']:.1f} | "
              f"{density:.0f} | {'yes' if fits else 'no'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
