"""Are two tree ensembles the same, number for number?  Every yearly stat, and every row of tree.json: new shoots, snapshots at set
ages (wood, branches, crown shape), and the count of what fell.  For a setting that should change no result in a lean run.

    python tools/speed_same.py pc_speed_t_A_base pc_speed_t_A_droponly
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ensembles_identical import walk  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a, b = sys.argv[1], sys.argv[2]
    seeds = sorted(int(p.name.split("_")[0]) for p in (E / a).glob("*_stand") if (E / b / p.name / "manifest.json").exists() and (p / "manifest.json").exists())
    print("| Seed | Yearly stats compared | Differ | tree.json values compared | Differ | First difference |")
    print("|---|---|---|---|---|---|")
    bad = 0
    for s in seeds:
        pa, pb = E / a / f"{s}_stand", E / b / f"{s}_stand"
        sa = json.loads((pa / "stats.json").read_text(encoding="utf-8"))["per_year"]
        sb = json.loads((pb / "stats.json").read_text(encoding="utf-8"))["per_year"]
        ta = json.loads((pa / "tree.json").read_text(encoding="utf-8"))
        tb = json.loads((pb / "tree.json").read_text(encoding="utf-8"))
        d1 = list(walk(sa, sb))
        d2 = list(walk(ta, tb))
        n1 = sum(len(r) for r in sa)
        n2 = len(json.dumps(ta)) // 12          # a rough count of values, for scale
        first = (d1 or d2 or [("", "", "")])[0]
        bad += len(d1) + len(d2)
        print(f"| {s} | {n1} | {len(d1)} | about {n2} | {len(d2)} | {first[0]} {first[1]} {first[2]} |"[:230])
    print(f"\n{len(seeds)} seeds: " + ("IDENTICAL" if not bad and seeds else f"{bad} differences"))


if __name__ == "__main__":
    main()
