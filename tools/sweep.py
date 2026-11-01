"""Seed spread and parameter sensitivity.

    python tools/sweep.py seeds --seeds 1-10 --modes open,stand --workers 4 --out out/sweep_seeds.json
    python tools/sweep.py nudge --param resource.alpha --factor 1.1 --seeds 1-3 --modes open --out out/nudge.json

Runs growth only (no meshes) and stores the stats of every run at the
report ages (default 50 and 60), plus runtime and peak memory.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

KEYS = ("height_m", "dbh_cm", "crown_width_m", "crown_base_height_m", "crown_ratio", "living_internodes",
        "leaf_area_m2", "mean_hanging_twig_length_m")


def _seeds(text: str) -> list[int]:
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def _run(job: dict) -> dict:
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    if job.get("param"):
        parts = job["param"].split(".")
        obj = sp
        for p in parts[:-1]:
            obj = getattr(obj, p)
        old = getattr(obj, parts[-1])
        new = [x * job["factor"] for x in old] if isinstance(old, list) else old * job["factor"]
        setattr(obj, parts[-1], new)
    from cli import peak_memory_mb

    t = time.time()
    m = GrowthModel(sp, make_environment(env), job["seed"], stand=job["mode"] == "stand", soil=make_soil(env))
    m.run(int(job.get("years", 60)))
    s = m.stats[-1]
    ages = [a for a in job.get("ages", [50, 60]) if a <= m.year]
    return {**job, "runtime_s": round(time.time() - t, 1), "peak_memory_mb": peak_memory_mb(), "final": s,
            "by_age": {str(a): m.stats[a] for a in ages}}


def _band(v):
    import numpy as np
    v = np.asarray(v, float)
    if not np.isfinite(v).any():
        return None
    return {"mean": round(float(np.nanmean(v)), 3), "sd": round(float(np.nanstd(v)), 3),
            "min": round(float(np.nanmin(v)), 3), "max": round(float(np.nanmax(v)), 3)}


def summarize(results: list[dict]) -> dict:
    import numpy as np
    out = {}
    for mode in sorted({r["mode"] for r in results}):
        rs = [r for r in results if r["mode"] == mode]
        row = {"runs": len(rs), "runtime_mean_s": round(float(np.mean([r["runtime_s"] for r in rs])), 1),
               "peak_memory_max_mb": max(r.get("peak_memory_mb", 0) for r in rs)}
        for age in sorted({a for r in rs for a in r.get("by_age", {})}, key=int):
            st = [r["by_age"][age] for r in rs if age in r.get("by_age", {})]
            blk = {k: _band([s[k] if s.get(k) is not None else np.nan for s in st]) for k in KEYS}
            roots = [s.get("roots") or {} for s in st]
            for k in ("root_max_depth_m", "root_depth_90pct_m", "root_share_top_30cm", "root_spread_max_m",
                      "root_spread_95pct_m", "root_centroid_offset_m"):
                blk[k] = _band([x.get(k, np.nan) for x in roots])
            sc = [s.get("scaffold") or {} for s in st]
            for k in ("limbs_over_5cm", "limbs_over_10cm", "largest_scaffold_limb_to_trunk_ratio",
                      "leaf_share_five_biggest_limbs", "leaf_share_inner_40pct_radius", "leaf_share_outer_shell_60pct_plus"):
                blk[k] = _band([x.get(k) if x.get(k) is not None else np.nan for x in sc])
            row[f"age_{age}"] = blk
        out[mode] = row
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["seeds", "nudge"])
    ap.add_argument("--seeds", default="1-10")
    ap.add_argument("--modes", default="open,stand")
    ap.add_argument("--param", default=None)
    ap.add_argument("--factor", type=float, default=1.0)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    jobs = [{"seed": s, "mode": m, "years": a.years, "param": a.param, "factor": a.factor, "ages": [50, 60]}
            for m in a.modes.split(",") for s in _seeds(a.seeds)]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(_run, jobs))
    doc = {"jobs": jobs, "results": results, "summary": summarize(results)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(doc, indent=1))
    print(json.dumps(doc["summary"], indent=1))


if __name__ == "__main__":
    main()
