"""Are two saved single-tree runs the same tree?  Compares every per_year value in
stats.json and every array in timeline.npz, exactly.  Keys that only one run
saved are listed, not counted as differences (an output-only change adds keys).

    python tools/compare_runs.py out/bench/p40_default_v3/1_stand out/bench/m1/default/1_stand
"""
import json
import sys
from pathlib import Path

import numpy as np


def diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield ("only_one", f"{path}.{k}", None, None)
            else:
                yield from diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield ("differ", f"{path} length", len(a), len(b))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                yield from diff(x, y, f"{path}[{i}]")
    elif a != b:
        yield ("differ", path, a, b)


def main():
    A, B = Path(sys.argv[1]), Path(sys.argv[2])
    pa = json.loads((A / "stats.json").read_text())["per_year"]
    pb = json.loads((B / "stats.json").read_text())["per_year"]
    print(f"per_year rows: {len(pa)} and {len(pb)}")
    found = list(diff(pa, pb))
    extra = sorted({f.split(".", 1)[1] for kind, f, _, _ in found if kind == "only_one"})
    differ = [x for x in found if x[0] == "differ"]
    print(f"keys only one run saved: {extra}")
    print(f"per_year values that differ: {len(differ)}")
    for _, f, x, y in differ[:12]:
        print(f"  {f}: {x} vs {y}")
    na, nb = np.load(A / "timeline.npz"), np.load(B / "timeline.npz")
    only = sorted(set(na.files) ^ set(nb.files))
    arrays = [k for k in sorted(set(na.files) & set(nb.files)) if not np.array_equal(na[k], nb[k])]
    print(f"timeline arrays: {len(na.files)} and {len(nb.files)}; only in one: {only}; differ: {arrays}")
    same = not differ and not arrays and len(pa) == len(pb)
    print("SAME TREE" if same else "DIFFERENT")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
