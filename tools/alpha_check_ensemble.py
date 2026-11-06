"""Does alpha's derivation hold on an ensemble?  tools/alpha_check.py's figure, for every seed.

    python tools/alpha_check_ensemble.py out/bench/ensemble/base_trees
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

G_C_PER_UNIT = 0.305
DERIVED_G_C = 329.0
AGES = (10, 20, 30, 40, 50, 60)


def main(argv=None) -> int:
    folder = Path((sys.argv[1:] if argv is None else argv)[0])
    runs = [json.loads(f.read_text(encoding="utf-8"))["per_year"] for f in sorted(folder.glob("*_stand/stats.json"))]
    print(f"{len(runs)} seeds; {folder.as_posix()}; {G_C_PER_UNIT} g C per unit; derived {DERIVED_G_C:.0f} g C per m2 of leaf")
    print("| Age | g C per m2 of leaf, mean +- SD | Ratio to the derived | CUE, mean +- SD |")
    print("|---|---|---|---|")
    for age in AGES:
        per, cue = [], []
        for rows in runs:
            r = rows[age]
            c = r.get("carbon") or {}
            if c.get("fixed") and r.get("leaf_area_m2"):
                per.append(c["fixed"] / r["leaf_area_m2"] * G_C_PER_UNIT)
            if c.get("cue") is not None:
                cue.append(c["cue"])
        m, s = statistics.fmean(per), statistics.stdev(per)
        cue_text = f"{statistics.fmean(cue):.2f} +- {statistics.stdev(cue):.2f}" if len(cue) > 1 else "not saved"
        print(f"| {age} | {m:.0f} +- {s:.0f} | {m / DERIVED_G_C:.2f} | {cue_text} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
