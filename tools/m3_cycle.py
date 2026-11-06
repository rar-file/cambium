"""M3a: why does the whole tree grow long shoots only in some years?  Diagnosis, nothing adopted.

Grows a stand tree and records, each year, what the carbon solve saw (treegen/growth.py,
_growth_factor): the pool, what the current foliage's rings and leaves take first (c0), and the
factor lambda it found.  The model's numbers aren't changed: the solver is wrapped and read.

    python tools/m3_cycle.py --seed 1 --out out/bench/m3/cycle_s1.json [--set key=json ...]
    python tools/m3_cycle.py --read out/bench/m3/cycle_s1.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from treegen import checkpoint  # noqa: E402
from treegen.environment import make_environment, make_soil  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402
from treegen.params import load_environment, load_species  # noqa: E402


def buds(model) -> dict:
    """How many buds competed for the pool this year, and how many got enough to grow."""
    d = model.diag
    bf = model.sp.bud_fate
    v_t, v_l = d["v_term"], d["v_lat"]
    return {"tips": int(len(v_t)), "tips_grew": int((v_t >= float(getattr(bf, "min_tip_extension", 1.0))).sum()),
            "tips_one_metamer": int((v_t >= 1.0).sum()),
            "lat_sinks": int((v_l > 0).sum()), "lat_grew": int((v_l >= float(bf.long_shoot_threshold)).sum()),
            "tip_v_median": float(np.median(v_t)) if len(v_t) else 0.0, "tip_v_max": float(v_t.max()) if len(v_t) else 0.0}


def run(seed: int, years: int, sets: list) -> list:
    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    checkpoint.set_values(sp, sets)
    model = GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)
    seen = {}
    solve = model._growth_factor

    def recording(pool, *args, **kwargs):
        lam, ring = solve(pool, *args, **kwargs)
        seen.update(pool=float(pool), lam=float(lam), c0=float(model._ring_need))
        return lam, ring

    model._growth_factor = recording
    rows = []
    height = 0.0
    for year in range(1, years + 1):
        seen.clear()
        n0 = model.tree.n
        model.step()
        s = model.stats[-1]
        new = list(range(n0, model.tree.n))
        rows.append({"year": year, "height_m": s["height_m"], "height_increment_m": s["height_m"] - height,
                     "new_internodes": len(new), "new_metres": float(sum(model.tree.length[new])) if new else 0.0,
                     "leaf_area_m2": s["leaf_area_m2"], "living_spurs": s["living_spurs"], "living_internodes": s["living_internodes"],
                     "fixed": s["carbon"]["fixed"], "upkeep": s["carbon"]["upkeep"], "pool": seen.get("pool"), "c0": seen.get("c0"), "lam": seen.get("lam"),
                     "lai": s["lai"], "mean_bud_light": s["carbon"]["mean_bud_light"], **buds(model)})
        height = s["height_m"]
    return rows


def read(path: Path) -> None:
    rows = json.loads(path.read_text(encoding="utf-8"))
    print("| Year | Height (m) | Height growth (m) | New shoot length (m) | Leaf area (m2) | Pool | Taken first (c0) | c0 / pool | Lambda | Tips | Tips that grew | Lateral sinks | Laterals that grew |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        ratio = r["c0"] / r["pool"] if r["pool"] else float("nan")
        print(f"| {r['year']} | {r['height_m']:.2f} | {r['height_increment_m']:.2f} | {r['new_metres']:.1f} | {r['leaf_area_m2']:.1f} | {r['pool']:.0f} | {r['c0']:.0f} | {ratio:.2f} | {r['lam']:.2f} | {r['tips']} | {r['tips_grew']} | {r['lat_sinks']} | {r['lat_grew']} |")
    off = [r for r in rows if r["year"] >= 5 and r["height_increment_m"] < 0.01]
    print(f"\nYears 5 and on with no height growth: {len(off)} of {sum(r['year'] >= 5 for r in rows)}. "
          f"Of those, the solver found lambda 0 in {sum(r['lam'] == 0 for r in off)}.")
    grown = [r["new_metres"] for r in rows if r["year"] >= 5]
    print(f"New shoot length, years 5 and on: median {statistics.median(grown):.1f} m, max {max(grown):.1f} m; SD of the year-to-year change {statistics.stdev([b - a for a, b in zip(grown, grown[1:])]):.1f} m.")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--out")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--read")
    a = ap.parse_args(argv)
    if a.read:
        read(Path(a.read))
        return 0
    rows = run(a.seed, a.years, a.set)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows), encoding="utf-8")
    read(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
