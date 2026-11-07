"""Are two tree ensembles the same, number for number?  Every yearly stat, and every row of tree.json: new shoots, snapshots at set
ages (wood, branches, crown shape), and the count of what fell.  For a setting that should change no result in a lean run.
Differences are listed by what they're in, with the largest relative size: a sum a tool does over a shorter array rounds in the last
digits, which isn't a difference in the tree.

    python tools/speed_same.py pc_speed_t_A_base pc_speed_t_A_droponly
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
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
    stats_n = stats_diff = 0
    kinds = defaultdict(lambda: [0, 0.0, None])
    for s in seeds:
        pa, pb = E / a / f"{s}_stand", E / b / f"{s}_stand"
        sa = json.loads((pa / "stats.json").read_text(encoding="utf-8"))["per_year"]
        sb = json.loads((pb / "stats.json").read_text(encoding="utf-8"))["per_year"]
        stats_n += sum(len(r) for r in sa)
        stats_diff += sum(1 for _ in walk(sa, sb))
        ta = json.loads((pa / "tree.json").read_text(encoding="utf-8"))
        tb = json.loads((pb / "tree.json").read_text(encoding="utf-8"))
        for path, x, y in walk(ta, tb):
            kind = re.sub(r"/\d+", "/*", path)
            k = kinds[kind]
            k[0] += 1
            if isinstance(x, (int, float)) and isinstance(y, (int, float)) and x:
                k[1] = max(k[1], abs(y - x) / abs(x))
            else:
                k[1] = float("inf")
            k[2] = (s, path, x, y)
    print(f"{len(seeds)} seeds. Yearly stats: {stats_n} fields, {stats_diff} differ.")
    print("\n| In tree.json | Values that differ | Largest relative difference | An example: seed, where, first, second |")
    print("|---|---|---|---|")
    for kind, (n, rel, ex) in sorted(kinds.items(), key=lambda kv: -kv[1][1]):
        print(f"| {kind} | {n} | {rel:.1e} | {ex} |"[:220])
    worst = max((k[1] for k in kinds.values()), default=0.0)
    print("\n" + ("IDENTICAL" if not kinds and not stats_diff else
                  f"Yearly stats {'identical' if not stats_diff else 'DIFFER'}; tree.json differs by at most {worst:.1e} relative"))


if __name__ == "__main__":
    main()
