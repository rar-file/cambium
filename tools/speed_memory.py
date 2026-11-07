"""What one tree's state holds, by age: for the game, memory per tree matters as much as time.

    python tools/speed_memory.py --seed 1 --years 60 [--set key=json ...]

Light grids and the soil grid belong to a place, not a tree, so they're counted apart.  'Live only' is what the arrays would hold
with dead nodes dropped; 'and single precision' is that with 8-byte numbers as 4.  Both are sums over what the arrays hold now,
not runs: nothing here shows those smaller forms grow the same tree.  The pickle is what a save would write, with no light.
"""
from __future__ import annotations

import argparse
import gzip
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from profile_run import memory_by_attribute  # noqa: E402

AGES = (10, 20, 30, 40, 50, 60)
PLACE = ("model._field", "model.light", "model._plot_view", "model.roots.field", "model.roots._kept_soil", "model.soil")


def tree_arrays(T, n, alive):
    full = live = live32 = 0
    for name in list(T.VEC) + list(T.SCALAR):
        a = getattr(T, name)
        one = a.dtype.itemsize * (a.shape[1] if a.ndim == 2 else 1)
        full += one * T.cap
        live += one * alive
        live32 += (one // 2 if a.dtype.itemsize == 8 else one) * alive
    return full, live, live32


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    import cli
    from treegen import checkpoint
    from treegen.growth import GrowthModel

    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, a.set)
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    print("| Age | Nodes | Live | Roots, nodes, live | Tree's state (MB) | Crown arrays | Root arrays | Other | Crown + roots, live only | And single precision | Place: light, soil (MB) | Save, pickled, gzip (MB) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _ in range(a.years):
        m.step()
        if m.year not in AGES:
            continue
        sizes = memory_by_attribute(m, "model")
        place = sum(v for k, v in sizes.items() if k.startswith(PLACE))
        state = sum(sizes.values()) - place
        crown = sum(v for k, v in sizes.items() if k.startswith("model.tree."))
        roots = sum(v for k, v in sizes.items() if k.startswith("model.roots.tree."))
        T, R = m.tree, m.roots.tree
        n, nr = T.n, R.n
        al, alr = int((T.death[:n] < 0).sum()), int((R.death[:nr] < 0).sum())
        _, live, live32 = tree_arrays(T, n, al)
        _, liver, liver32 = tree_arrays(R, nr, alr)
        keep = m._field, getattr(m, "_plot_view", None), m.light, m.roots.field, getattr(m.roots, "_kept_soil", None)
        m._field = m._plot_view = None
        m.roots.field = None
        m.roots._kept_soil = None
        light = m.light
        m.light = None
        blob = pickle.dumps(m, protocol=pickle.HIGHEST_PROTOCOL)
        m._field, m._plot_view, m.light, m.roots.field, m.roots._kept_soil = keep
        zipped = len(gzip.compress(blob, 1))
        mb = 2 ** 20
        print(f"| {m.year} | {n} | {al} | {nr}, {alr} | {state / mb:.1f} | {crown / mb:.1f} | {roots / mb:.1f} | {(state - crown - roots) / mb:.1f} | {(live + liver) / mb:.1f} | {(live32 + liver32) / mb:.1f} | {place / mb:.1f} | {len(blob) / mb:.1f}, {zipped / mb:.1f} |", flush=True)
    top = sorted(((v, k) for k, v in sizes.items() if not k.startswith(PLACE)), reverse=True)[:18]
    print("\nLargest in the tree's state at the end (MB): " + ", ".join(f"{k.replace('model.', '')} {v / 2 ** 20:.2f}" for v, k in top))


if __name__ == "__main__":
    main()
