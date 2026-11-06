"""Do two ensembles hold the same numbers?  For the --set control (reports/reviews/2026-11-06_M1c_audit_M2start_review.md, FIX 1).

    python tools/ensembles_identical.py base_trees m2_ctrl_a4.8
    python tools/ensembles_identical.py --screen resource.alpha__x1.25 m2_ctrl_a6.0

The first compares every per_year value of every seed.  --screen compares against the node's 20-seed
screen, which saved only some fields at some ages; those are the ones compared.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "out" / "bench" / "ensemble"
SCREEN = ROOT / "out" / "bench" / "node" / "screen20"
SCREEN_FIELDS = {"height_m": "height_m", "lai": "lai", "diffuse_light_pct": "subcanopy_diffuse_light_pct", "leaf_area_m2": "leaf_area_m2"}


def per_year(folder: Path, seed: int) -> list:
    return json.loads((folder / f"{seed}_stand" / "stats.json").read_text(encoding="utf-8"))["per_year"]


def walk(a, b, path=""):
    """Every place two nested values differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield f"{path}/{k}", a.get(k), b.get(k)
            else:
                yield from walk(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{path}/len", len(a), len(b)
        for i, (x, y) in enumerate(zip(a, b)):
            yield from walk(x, y, f"{path}/{i}")
    elif a != b:
        yield path, a, b


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("first")
    ap.add_argument("second")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--seeds", type=int, default=20)
    a = ap.parse_args(argv)
    compared = differ = 0
    first_seen = None
    for s in range(1, a.seeds + 1):
        rows = per_year(E / a.second, s)
        if a.screen:
            saved = json.loads((SCREEN / f"{a.first}__s{s}.json").read_text())
            for age, fields in saved.items():
                if not str(age).isdigit():
                    continue
                for screen_key, key in SCREEN_FIELDS.items():
                    if screen_key not in fields:
                        continue
                    compared += 1
                    if fields[screen_key] != rows[int(age)][key]:
                        differ += 1
                        first_seen = first_seen or (s, age, key, fields[screen_key], rows[int(age)][key])
        else:
            base = per_year(E / a.first, s)
            found = list(walk(base, rows))
            compared += sum(len(r) for r in rows)
            differ += len(found)
            if found and first_seen is None:
                first_seen = (s, *found[0])
    verdict = "IDENTICAL" if differ == 0 and compared else "DIFFERENT"
    print(f"{a.first} against {a.second}: {verdict}; {a.seeds} seeds, {compared} {'values' if a.screen else 'top-level fields'} compared, {differ} differences")
    if first_seen:
        print(f"first difference: {first_seen}")
    return 0 if verdict == "IDENTICAL" else 1


if __name__ == "__main__":
    sys.exit(main())
