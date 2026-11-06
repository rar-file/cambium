"""Do two plot ensembles hold the same numbers?  For the plots' --set control (DECISIONS.md row 59).

    python tools/plots_identical.py base_plots m2_ctrl_plots_a4.8

Compares each plot.json, and each tree's stats.json, leaving out run metadata as the golden check does.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ensembles_identical import walk  # noqa: E402
from golden import strip_metadata  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a, b = (argv or sys.argv[1:])[:2]
    compared = 0
    found = []
    for plot in sorted(p.name for p in (E / a).iterdir() if p.is_dir()):
        names = sorted(f.relative_to(E / a / plot).as_posix() for f in (E / a / plot).rglob("*.json") if f.name in ("plot.json", "stats.json"))
        for name in names:
            other = E / b / plot / name
            if not other.exists():
                found.append((plot, name, "missing"))
                continue
            x = strip_metadata(json.loads((E / a / plot / name).read_text(encoding="utf-8")))
            y = strip_metadata(json.loads(other.read_text(encoding="utf-8")))
            compared += 1
            found += [(plot, name, *d) for d in walk(x, y)]
    print(f"{a} against {b}: {'IDENTICAL' if not found and compared else 'DIFFERENT'}; {compared} files compared, {len(found)} differences")
    for row in found[:12]:
        print(str(row)[:180])
    return 0 if not found else 1


if __name__ == "__main__":
    sys.exit(main())
