"""How high each tree's black base goes, year by year, with no export and nothing rendered.

Grows each seed as tools/crown_look.py does and reads the bark's own rule at that tree's DBH.  Black: the height at
which half of the bark round the stem has gone over (Jones et al. 2021 measured the height at which smooth silver
bark dominates).  It also checks each year's DBH and black against the year before, since a tree's black must only
rise and must never jump.  Writes black_heights.json next to crown_look's sheets, and prints the table.

    python tools/black_height.py --label node_x --seeds 1,2,3 --ages 50,60 --sets cases/crown2.txt --set speed.light_layers=true
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

E = ROOT / "out" / "bench" / "ensemble"
U = (np.arange(256) + 0.5) / 256.0
Z = np.linspace(0.02, 12.0, 600)


def measure(look: dict, seed: int, age: int, dbh_ob: float) -> dict:
    """What one stem's base comes to, from the same rule the bake reads."""
    from treegen import textures as tx

    edge = tx.UnevenTop(look, float(age), seed, dbh_ob)
    gone = edge.gone_over(U, Z, Z)
    share = np.convolve(gone.mean(1), np.ones(21) / 21.0, mode="same")
    columns = Z[gone.shape[0] - 1 - np.argmax((gone > 0.5)[::-1], axis=0)]
    return {"dbh_ob_cm": round(dbh_ob, 2), "black_m": round(edge.black, 2), "half_measured_m": round(float(Z[10:][np.argmax(share[10:] < 0.5)]), 2),
            "lowest_edge_m": round(float(columns.min()), 2), "highest_edge_m": round(float(columns.max()), 2), "lowest_metre_share": round(float(gone[Z < 1.0].mean()), 3)}


def one(seed: int, sets: list, ages: list, stand: bool) -> dict:
    from treegen import appearance as ap
    from treegen import checkpoint
    from treegen import textures as tx
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    sp, raw = load_species("betula_pendula")
    checkpoint.set_values(sp, sets)
    env_p, _ = load_environment("sweden_open_field")
    model = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p))
    last = max(ages)
    while model.year < last:
        model.step()
    model.run(0)
    look = ap.load_look(raw)
    look["bark"]["uneven_top"]["strength"] = 1.0
    years = list(range(1, min(last, len(model.stats) - 1) + 1))
    dbh = [float(ap.over_bark_dbh_cm(look, model.stats[y]["dbh_cm"])) for y in years]
    black = [tx.tree_black(look, seed, d) for d in dbh]
    ratio = [b / a for a, b in zip(black, black[1:]) if a > 0.01]
    out = {"seed": seed, "ages": {str(a): measure(look, seed, a, dbh[years.index(a)]) for a in ages},
           "falls": sum(1 for a, b in zip(black, black[1:]) if b < a - 1e-9), "largest_year_rise": round(max(ratio), 3) if ratio else None,
           "by_year": {str(y): round(b, 2) for y, b in zip(years, black) if y % 5 == 0}}
    return out


def main(argv=None) -> int:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap_.add_argument("--label", required=True)
    ap_.add_argument("--seeds", default="3,5,7")
    ap_.add_argument("--ages", default="50,60")
    ap_.add_argument("--open", action="store_true")
    ap_.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap_.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap_.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    seeds = [int(x) for x in a.seeds.split(",")]
    ages = [int(x) for x in a.ages.split(",")]
    workers = min(int(os.environ.get("ORIGIN_MAX_WORKERS", "2")), len(seeds))
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(one, seeds, [a.set] * len(seeds), [ages] * len(seeds), [not a.open] * len(seeds)))
    out = E / a.label
    out.mkdir(parents=True, exist_ok=True)
    (out / "black_heights.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("seed " + " ".join(f"| {g}: DBH black half edges low-high lowest-m " for g in ages) + "| falls largest-year-rise")
    for r in rows:
        cells = " ".join(f"| {r['ages'][str(g)]['dbh_ob_cm']:5.1f} {r['ages'][str(g)]['black_m']:5.2f} {r['ages'][str(g)]['half_measured_m']:5.2f} "
                         f"{r['ages'][str(g)]['lowest_edge_m']:5.2f}-{r['ages'][str(g)]['highest_edge_m']:5.2f} {r['ages'][str(g)]['lowest_metre_share']:4.2f}" for g in ages)
        print(f"{r['seed']:4d} {cells} | {r['falls']} {r['largest_year_rise']}", flush=True)
    for g in ages:
        v = np.array([r["ages"][str(g)]["black_m"] for r in rows])
        print(f"age {g}: mean {v.mean():.2f} m, CV {100 * v.std() / v.mean():.0f} %, lowest {v.min():.2f}, highest {v.max():.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
