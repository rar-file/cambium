"""M3c: first-order branches beside Lintunen 2013 Table 3.  Reads the model as it grows; changes nothing in it.

    python tools/m3_branches.py run --label pc_branch_base --seeds 20 [--set key=json ...]
    python tools/m3_branches.py table pc_branch_base

Lintunen 2013, Dissertationes Forestales 165, doi:10.14214/df.165, Table 3, p. 23, as read in the notes: first-order
branches 102.0 (7.0) cm long, 5.2 (0.3) per 10 % of crown length, 73 B. pendula next to B. pendula, Finland 60-63 N,
mixed stands, MT sites.  Ages 4-32 and heights 2-17 m are site means.  Not a target until checker A has seen it, so this
is for a look.  A first-order branch is a living lateral axis on the stem; its length is the path along its main axis.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "out" / "bench" / "branches"
AGES = (10, 20, 30, 40, 50, 60)


def one(seed: int, sets: list, out: Path) -> int:
    import numpy as np

    from treegen import checkpoint
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    checkpoint.set_values(sp, sets)
    model = GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)
    rows = []
    for year in range(1, max(AGES) + 1):
        model.step()
        if year not in AGES:
            continue
        T, s = model.tree, model.stats[-1]
        n = T.n
        alive = T.death[:n] < 0
        starts = np.nonzero(alive & T.is_lateral[:n] & (T.order[:n] == 1))[0]
        lengths = []
        for start in starts:
            total, node = 0.0, int(start)
            while node >= 0 and alive[node]:
                total += float(T.length[node])
                node = int(T.main_child[node])
            lengths.append(total)
        ratio = s.get("crown_ratio") or 0.0
        crown = ratio * s["height_m"]
        real = [x for x in lengths if x >= 0.05]
        rows.append({"age": year, "height_m": s["height_m"], "dbh_cm": s["dbh_cm"], "crown_ratio": ratio, "crown_length_m": crown,
                     "branches": len(real), "mean_length_m": statistics.mean(real) if real else 0.0,
                     "median_length_m": statistics.median(real) if real else 0.0,
                     "per_10pct_crown": len(real) / 10.0 if ratio > 0 else 0.0,
                     "crown_width_m": s.get("crown_width_m")})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows), encoding="utf-8")
    return 0


def run(label: str, seeds: int, first: int, sets: list) -> int:
    from concurrent.futures import ProcessPoolExecutor
    import os

    workers = int(os.environ.get("ORIGIN_MAX_WORKERS", "3"))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        jobs = [ex.submit(one, s, sets, OUT / label / f"{s}.json") for s in range(first, first + seeds)]
        for j in jobs:
            j.result()
    return 0


def table(labels: list) -> None:
    print("Lintunen 2013 Table 3, as read in the notes: first-order branches 102.0 (7.0) cm long, 5.2 (0.3) per 10 % of crown length, ages 4-32, heights 2-17 m. Medians over seeds, because a seed whose stem changed axis reads as an outlier: its old leader counts as a first-order branch.\n")
    print("| Set | Age | Seeds | Height (m) | Crown length (m) | Living first-order branches | Per 10 % of crown length | Each seed's mean length (m), median (range) | Median length (m) | Crown width (m) | Seeds over 3 x the median |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        rows = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((OUT / label).glob("*.json"))]
        for i, age in enumerate(AGES):
            at = [r[i] for r in rows]
            m = lambda k: statistics.median(r[k] for r in at)
            q = sorted(r["mean_length_m"] for r in at)
            print(f"| `{label}` | {age} | {len(at)} | {m('height_m'):.1f} | {m('crown_length_m'):.1f} | {m('branches'):.0f} | {m('per_10pct_crown'):.1f} | {m('mean_length_m'):.2f} ({q[0]:.2f}-{q[-1]:.2f}) | {m('median_length_m'):.2f} | {m('crown_width_m'):.2f} | {sum(x > 3 * m('mean_length_m') for x in q)} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["run", "table"])
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args(argv)
    if a.what == "run":
        return run(a.label, a.seeds, a.first_seed, a.set)
    table(a.labels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
