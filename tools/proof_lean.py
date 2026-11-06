"""Proof for P0 A1: a lean run scores the same as a full one, over a whole run.

Compares every scored value, every year, between a lean run's stats.json and a full run's,
same seed, same machine.  tests/test_lean.py covers 8 years at each commit; this is for 60.

    python tools/proof_lean.py LEAN_FOLDER FULL_FOLDER [LEAN_FOLDER FULL_FOLDER ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from example_tree import differences  # noqa: E402
from treegen.runhash import SCORED_KEYS  # noqa: E402


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or len(args) % 2:
        sys.exit(__doc__)
    bad = 0
    for lean, full in zip(args[::2], args[1::2]):
        a = json.loads((Path(lean) / "stats.json").read_text(encoding="utf-8"))
        b = json.loads((Path(full) / "stats.json").read_text(encoding="utf-8"))
        wrong = differences(a["per_year"], b["per_year"])
        ma, mb = a["run_manifest"].get("machine", {}).get("computer"), b["run_manifest"].get("machine", {}).get("computer")
        print(f"{lean} ({ma}) against {full} ({mb}): {len(b['per_year'])} years, {len(SCORED_KEYS)} scored keys, {len(wrong)} values differ")
        for w in wrong[:5]:
            print(" ", w)
        bad += len(wrong) > 0 or ma != mb
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
