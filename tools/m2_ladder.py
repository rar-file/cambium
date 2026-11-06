"""M2: does a knob make a ladder that keeps the site-index curves' shape?  On the curves, one site reads as one
site index at every age, so the gap between two sites stays level.  So: read each run's height as a site index,
age by age, and see whether the gap between a better and a poorer setting stays level.  Ages under 20 are outside
the target's band, and the indices may be too: information only.  Pairs must be on one machine.  Reads saved outputs.

    python tools/m2_ladder.py "root share=pc_rootshare0.15,pc_rootshare0.40" "alpha=pc_cc_a5.0,pc_cc_a3.5"
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from m2_shape import E, mean_height, reads_as  # noqa: E402
from scorecard import load_approved_targets  # noqa: E402

AGES = (15, 20, 30, 40, 50, 60)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pairs = argv if argv is not None else sys.argv[1:]
    item = load_approved_targets("targets-approved")["tree_allometry"]["site_index_curves"]
    print("| Knob | Row | " + " | ".join(str(a) for a in AGES) + " |\n|---|---|" + "---|" * len(AGES))
    for pair in pairs:
        name, folders = pair.split("=", 1)
        hi, lo = folders.split(",")
        rh = [mean_height(E / hi, a) for a in AGES]
        rl = [mean_height(E / lo, a) for a in AGES]
        sh = [reads_as(item, h, a) for h, a in zip(rh, AGES)]
        sl = [reads_as(item, h, a) for h, a in zip(rl, AGES)]
        print(f"| {name} | Better setting's height (m) | " + " | ".join(f"{x:.2f}" for x in rh) + " |")
        print(f"| | Poorer setting's height (m) | " + " | ".join(f"{x:.2f}" for x in rl) + " |")
        print(f"| | Height ratio | " + " | ".join(f"{a / b:.2f}" for a, b in zip(rh, rl)) + " |")
        print(f"| | Better reads as SI | " + " | ".join(f"{x:.1f}" for x in sh) + " |")
        print(f"| | Poorer reads as SI | " + " | ".join(f"{x:.1f}" for x in sl) + " |")
        print(f"| | Gap in SI; level would keep the shape | " + " | ".join(f"{a - b:.1f}" for a, b in zip(sh, sl)) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
