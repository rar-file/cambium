"""Why do a stand tree's lower limbs live?  Grows stand trees with shedding.log_limbs on (which changes nothing) and, each year the tree
is in a height window, reads every limb as the two shedding tests read it: its leaves' light against the light line, and its own
carbon against its upkeep.  A limb dies of light only below the line (from 0 at the line to certain at (1 - shade_softness) of it),
and of carbon only when its own carbon falls short of its upkeep.

    python tools/limb_fates.py --label node_lf --seeds 3 --years 35 --hmin 8 --hmax 15 [--set KEY=JSON ...]

Writes out/bench/ensemble/<label>/limb_fates.json and prints, by the limb's height on the stem as a share of the tree's height,
how many limbs, their median light and carbon/upkeep, and the shares under the light line, under 0.21 and short of upkeep.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def grow(seed: int, sets: list, years: int, hmin: float, hmax: float) -> list:
    from treegen import checkpoint
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, list(sets) + ["shedding.log_limbs=true"])
    env_p, _ = load_environment("sweden_open_field")
    m = GrowthModel(sp, make_environment(env_p), seed, stand=True, soil=make_soil(env_p), lean=True)
    rows = []
    for _ in range(years):
        m.step()
        s = m.stats[-1]
        h = float(s["height_m"])
        lg, lc = getattr(m, "_limb_log", None), getattr(m, "_limb_carbon", None)
        if not (hmin <= h <= hmax) or lg is None:
            continue
        for k in range(len(lg["node"])):
            rows.append({"kind": "light", "seed": seed, "year": int(s["year"]), "h": h, "lowest": s.get("lowest_live_branch_m"),
                         "base": s.get("crown_base_height_m"), "light_pct": s.get("subcanopy_diffuse_light_pct"), "z": float(lg["z"][k]),
                         "ratio": float(lg["ratio"][k]), "leaves": float(lg["leaves"][k])})
        if lc is not None:
            for k in range(len(lc["node"])):
                rows.append({"kind": "carbon", "seed": seed, "year": int(s["year"]), "h": h, "z": float(lc["z"][k]),
                             "own": float(lc["own"][k]), "upkeep": float(lc["upkeep"][k])})
    return rows


def summary(rows: list, line: float) -> list:
    out = []
    for lo, hi in ((0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.7), (0.7, 1.0)):
        r = [x for x in rows if x["kind"] == "light" and lo <= x["z"] / x["h"] < hi]
        if not r:
            continue
        q = np.array([x["ratio"] for x in r])
        c = np.array([x["own"] / x["upkeep"] for x in rows if x["kind"] == "carbon" and lo <= x["z"] / x["h"] < hi and x["upkeep"] > 0])
        out.append({"rel_height": f"{lo:.1f}-{hi:.1f}", "limb_years": len(r), "z_m": round(float(np.mean([x["z"] for x in r])), 2),
                    "light_median": round(float(np.median(q)), 3), "light_p10": round(float(np.percentile(q, 10)), 3),
                    "under_line": round(float(np.mean(q < line)), 3), "under_0.21": round(float(np.mean(q < 0.21)), 3),
                    "leaves_median": round(float(np.median([x["leaves"] for x in r])), 1),
                    "carbon_over_upkeep_median": round(float(np.median(c)), 2) if len(c) else None,
                    "short_of_upkeep": round(float(np.mean(c < 1.0)), 3) if len(c) else None})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--years", type=int, default=35)
    ap.add_argument("--hmin", type=float, default=8.0)
    ap.add_argument("--hmax", type=float, default=15.0)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    a = ap.parse_args(argv)
    rows = []
    for seed in range(1, a.seeds + 1):
        rows += grow(seed, a.set, a.years, a.hmin, a.hmax)
        print(f"seed {seed}: {len(rows)} limb-years so far", flush=True)
    from treegen.params import load_species
    from treegen import checkpoint
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, a.set)
    line = float(sp.shedding.light_per_leaf_threshold)
    summ = summary(rows, line)
    years = sorted({(x["seed"], x["year"], x["h"], x.get("lowest"), x.get("base"), x.get("light_pct")) for x in rows if x["kind"] == "light"})
    out = ROOT / "out" / "bench" / "ensemble" / a.label
    out.mkdir(parents=True, exist_ok=True)
    (out / "limb_fates.json").write_text(json.dumps({"sets": a.set, "line": line, "summary": summ, "years": years, "rows": rows}), encoding="utf-8")
    for y in years:
        print("seed %d year %d: height %.1f m, lowest live branch %s, crown base %s, light at 1-2 m %s %%" % y)
    for s in summ:
        print(json.dumps(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
