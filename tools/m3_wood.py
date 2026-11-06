"""M3b: how much of the tree is stem?  Wood of the stem and of the living branches at set ages, beside
Repola 2008's equations at the tree's own diameter and height.  Reads the model as it grows; changes
nothing in it, and nothing in its saved outputs.

    python tools/m3_wood.py run --label pc_wood_base --seeds 20 [--set key=json ...]
    python tools/m3_wood.py table pc_wood_base pc_wood_ahead

Repola 2008, Silva Fennica 42(4):605, birch, multivariate model 1 (Table 3), with dS = 2 + 1.25 d, d in cm
over bark at 1.3 m, h in m, y in kg dry mass, each with its bias correction:
    stem wood (Eq. 7):       ln y = -4.879 + 9.651 dS/(dS + 12) + 1.012 ln h,          exp((0.00263 + 0.00544)/2)
    living branches (Eq. 9): ln y = -4.152 + 15.874 dS/(dS + 16) - 4.407 h/(h + 10),   exp((0.02733 + 0.07662)/2)
Model wood is pi r^2 L x 530 kg/m3: wood only, no bark.  Repola's living branches include bark and no
foliage, and its range has limits, so these are for a look, not a verdict.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "out" / "bench" / "wood"
AGES = (10, 20, 30, 40, 50, 60)
DENSITY = 530.0


def repola(d_cm: float, h: float) -> tuple:
    ds = 2.0 + 1.25 * d_cm
    stem = math.exp(-4.879 + 9.651 * ds / (ds + 12.0) + 1.012 * math.log(h) + (0.00263 + 0.00544) / 2.0)
    branch = math.exp(-4.152 + 15.874 * ds / (ds + 16.0) - 4.407 * h / (h + 10.0) + (0.02733 + 0.07662) / 2.0)
    return stem, branch


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
        volume = np.where(alive, math.pi * T.radius[:n] ** 2 * T.length[:n], 0.0)
        stem_nodes = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
        stem_v = float(volume[stem_nodes].sum())
        total_v = float(volume.sum())
        leaf_kg = float(s["carbon"]["leaf_dm_g"]) / 1000.0
        rows.append({"age": year, "dbh_cm": s["dbh_cm"], "height_m": s["height_m"], "stem_kg": stem_v * DENSITY, "branch_kg": (total_v - stem_v) * DENSITY,
                     "leaf_kg": leaf_kg, "leaf_area_m2": s["leaf_area_m2"]})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows), encoding="utf-8")
    return 0


def run(label: str, seeds: int, sets: list) -> int:
    from batch import Job, run_batch

    folder = OUT / label
    extra = [x for v in sets for x in ("--set", v)]
    jobs = [Job(f"seed {s}", [sys.executable, str(Path(__file__).resolve()), "one", "--seed", str(s), "--out", str(folder / f"{s}.json"), *extra], folder / f"{s}.json")
            for s in range(1, seeds + 1)]
    return run_batch(jobs, 0.6, log=folder / "runs.csv")


def table(labels: list) -> None:
    from bark import dbh_over_bark

    print("Wood only for the model; Repola's branches include bark. Means over seeds. Repola is at the model's own height and its diameter over bark (tools/bark.py); the diameter shown is wood only.\n")
    print("| Ensemble | Age | Stem diameter (cm) | Height (m) | Stem wood (kg) | Repola stem wood at that size (kg) | Branch wood (kg) | Repola branches (kg) | Leaves (kg) | Stem share of above-ground, % |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        rows = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((OUT / label).glob("*.json"))]
        for i, age in enumerate(AGES):
            at = [r[i] for r in rows]
            rep = [repola(float(dbh_over_bark(r["dbh_cm"])), r["height_m"]) for r in at]
            shares = [100.0 * r["stem_kg"] / (r["stem_kg"] + r["branch_kg"] + r["leaf_kg"]) for r in at]
            m = lambda k: statistics.fmean(r[k] for r in at)
            print(f"| `{label}` | {age} | {m('dbh_cm'):.1f} | {m('height_m'):.1f} | {m('stem_kg'):.0f} | {statistics.fmean(x[0] for x in rep):.0f} | {m('branch_kg'):.1f} | {statistics.fmean(x[1] for x in rep):.1f} | {m('leaf_kg'):.1f} | {statistics.fmean(shares):.1f} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("run", "one", "table"))
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out")
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args(argv)
    if a.what == "one":
        return one(a.seed, a.set, Path(a.out))
    if a.what == "run":
        return run(a.label, a.seeds, a.set)
    table(a.labels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
