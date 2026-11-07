"""How fast a forest could cross open ground, far beyond what a plot of whole trees can hold.

    python tools/spread_estimate.py --curve out/forest/t500_s2 --length 2000 --width 20 --years 100

This isn't the tree model.  Trees here are points: a stem size and height by age read from a
real plot's yearly stats (--curve), with their spread between trees drawn once per tree.  Everything
that decides the advance is the model's own code and values: the seed kernel, fecundity, seedbeds,
canopy cover rule and recruit cell of SpreadRegeneration, and the hazards of treegen/thinning.py.
What it leaves out is any feedback of crowding on growth.  Use it for the speed of the front, and
check it against whole trees over the first steps (tools/forest.py --strip, tools/stand_table.py --spread).

Seconds to minutes, a few hundred MB, so it may run anywhere.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import cli  # noqa: E402
from stand_table import fronts, stat  # noqa: E402
from treegen import checkpoint  # noqa: E402
from treegen.regeneration import SpreadRegeneration  # noqa: E402
from treegen.thinning import Mortality  # noqa: E402


def crown_radius_m(d_cm):
    """In the model the crown of a stand tree, DBH over bark 25-30 cm, is about 3.2 m across (reset
    brief; Evo 2024: 5.2 m).  This form is a fit by eye to the first, for the cover rule only."""
    return 0.5 * (1.0 + 0.08 * d_cm)


def size_by_age(folder: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Age, wood DBH (cm) and height (m) of the mean stem of a plot's cohort, from year 1."""
    stats = json.loads((Path(folder) / "plot.json").read_text(encoding="utf-8"))["stats"]
    ages = np.array([0.0] + [s["year"] for s in stats])
    # Dg over bark to wood: the bark share at these sizes is about 8 %
    dbh = np.array([0.0] + [0.92 * float(s.get("dg_ob_cm") or 0.0) for s in stats])
    height = np.array([0.0] + [float(s.get("height_mean_m") or 0.0) for s in stats])
    return ages, dbh, height


def run(a) -> dict:
    sp, _ = cli.load_species(a.species)
    checkpoint.set_values(sp, ["regeneration.spread.enabled=true"] + list(a.set))
    env_p, _ = cli.load_environment(a.environment)
    soil = cli.make_soil(env_p)
    rng = np.random.default_rng([a.seed, 7001])
    lx, ly = float(a.length), float(a.width)
    R = SpreadRegeneration(sp.regeneration, sp.bud_fate.short_shoot_survival_light, soil, lx, ly, a.seed)
    M = Mortality(sp.mortality, lx, ly, -lx / 2, -ly / 2)
    ages, dbh_curve, h_curve = size_by_age(Path(a.curve))
    n0 = max(1, int(round(a.stems * a.patch * ly / 1e4)))
    x = list(rng.uniform(-lx / 2, -lx / 2 + a.patch, n0))
    y = list(rng.uniform(-ly / 2, ly / 2, n0))
    born = [-int(getattr(a, "patch_age", 0) or 0)] * n0     # a grown forest's edge, not a new band
    size = list(np.exp(rng.normal(0.0, a.size_sd, n0)))
    rows = []
    bins = np.arange(0.0, lx + 10.0, 10.0)
    for year in range(1, a.years + 1):
        X, Y = np.array(x), np.array(y)
        age = year - np.array(born, float)
        sf = np.array(size)
        d = np.interp(age, ages, dbh_curve) * sf
        h = np.interp(age, ages, h_curve) * sf
        d_prev = np.interp(age - float(sp.mortality.vigour.window_years), ages, dbh_curve) * sf
        rings = np.where(d > 0.0, 5.0 * (d - d_prev) / float(sp.mortality.vigour.window_years), 0.0)
        # who dies
        hz = M.hazards(np.stack([X, Y], 1), d, rings, age, float(year))
        keep = np.ones(len(x), bool)
        for n, _ in M.draw(hz, rng):
            keep[n] = False
        X, Y, age, d, h = X[keep], Y[keep], age[keep], d[keep], h[keep]
        x, y = X.tolist(), Y.tolist()
        born = (year - age).astype(int).tolist()
        size = sf[keep].tolist()
        if not x:
            break
        # seed, cover and light
        seeds = np.array([R.fecundity(float(di) / 100.0, int(ai)) for di, ai in zip(d, age)])
        give = seeds > 0.0
        R.count_trees(np.stack([X, Y], 1)[d >= float(sp.regeneration.spread.tree_dbh_cm)])
        tall = h >= 2.0
        pts = []
        if tall.any():
            r = crown_radius_m(d[tall])
            th = np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False)
            for f in (0.0, 0.5, 1.0):
                pts.append(np.stack([np.repeat(X[tall], 8) + f * np.repeat(r, 8) * np.tile(np.cos(th), tall.sum()),
                                     np.repeat(Y[tall], 8) + f * np.repeat(r, 8) * np.tile(np.sin(th), tall.sum()),
                                     np.full(8 * tall.sum(), 10.0)], 1))
        leaves = np.concatenate(pts) if pts else None
        if leaves is not None:
            leaves[:, 0] = (leaves[:, 0] + lx / 2) % lx - lx / 2
            leaves[:, 1] = (leaves[:, 1] + ly / 2) % ly - ly / 2
        # each tree's leaf area, shared over its crown's points: a stand of 4 m2/m2 at full cover
        area = None
        if tall.any():
            per_point = (4.0 * math.pi * r * r) / (3 * 8)
            area = np.tile(np.repeat(per_point, 8), 3)
        R.read_canopy(leaves, area)
        light = np.where(R.overhead >= float(sp.regeneration.spread.canopy_lai_max), 0.25, 1.0)
        occupied = np.zeros(R.cx.shape, bool)
        i, j = R._cell(np.stack([X, Y], 1))
        occupied[i, j] = True
        new = R.step(np.stack([X, Y], 1)[give], seeds[give], light, 0.38, occupied)
        for nx, ny, _ in new:
            x.append(float(nx))
            y.append(float(ny))
            born.append(year)
            size.append(float(math.exp(rng.normal(0.0, a.size_sd))))
        xs = X + lx / 2
        rows.append({"year": year, "stems_along_x": np.histogram(xs[h >= 2.0], bins=bins)[0].tolist(),
                     "seedlings_along_x": np.histogram(xs[h < 2.0], bins=bins)[0].tolist(), "new_trees": len(new), "trees": len(x)})
    return {"rows": rows, "side_y_m": ly, "side_m": lx}


def speed(series: list, key: str, top: float) -> float | None:
    """Metres a year: a straight line through a front while it moves and is short of the far end."""
    ys = [s["year"] for s in series if 0.0 < s[key] < top]
    xs = [s[key] for s in series if 0.0 < s[key] < top]
    return float(np.polyfit(ys, xs, 1)[0]) if len(ys) >= 5 and max(xs) > min(xs) else None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--curve", required=True, help="a tools/forest.py plot to read size by age from")
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--environment", default="sweden_open_field")
    ap.add_argument("--length", type=float, default=2000.0)
    ap.add_argument("--width", type=float, default=20.0)
    ap.add_argument("--patch", type=float, default=30.0)
    ap.add_argument("--stems", type=float, default=1000.0, help="stems/ha of the first band")
    ap.add_argument("--patch-age", type=int, default=0, help="age of the first band's trees at year 0: a grown forest's edge")
    ap.add_argument("--years", type=int, default=100)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--size-sd", type=float, default=0.25, help="lognormal spread of size between trees; a guess, not a tuned value")
    ap.add_argument("--min-stems", type=float, default=150.0)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    all_series = []
    for s in range(a.seed, a.seed + a.seeds):
        a_s = argparse.Namespace(**vars(a))
        a_s.seed = s
        out = run(a_s)
        all_series.append([dict(fronts(r, out["side_y_m"], a.min_stems), year=r["year"], new=r["new_trees"], trees=r["trees"]) for r in out["rows"]])
    print(f"Points, not whole trees: {a.length:.0f} x {a.width:.0f} m, {a.seeds} seeds, sizes from {a.curve}.  Settings: {a.set or 'as the species file'}\n")
    print("| Year | Furthest tree 2 m tall (m) | Forest edge (m) | Furthest seedling (m) | Trees on the ground |\n|---|---|---|---|---|")
    for y in range(10, a.years + 1, 10):
        rows = [s[y - 1] for s in all_series if len(s) >= y]
        print(f"| {y} | {stat([r['first'] for r in rows])} | {stat([r['forest'] for r in rows])} | {stat([r['seedling'] for r in rows])} | {stat([r['trees'] for r in rows])} |")
    top = 0.9 * a.length
    print(f"\nSpeed, a line fitted while inside the ground: furthest tree {stat([speed(s, 'first', top) for s in all_series])} m a year; "
          f"forest edge {stat([speed(s, 'forest', top) for s in all_series])} m a year.")


if __name__ == "__main__":
    main()
