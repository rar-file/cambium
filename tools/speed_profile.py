"""Where a run's time and memory go now: by year, by tree size, for a single stand tree and for trees in a plot.

    python tools/speed_profile.py tree --label tree_default --years 60 --seed 1 [--set key=json ...]
    python tools/speed_profile.py plot --label plot_default --start-trees 25 --years 60 --seed 1 [--set key=json ...]
    python tools/speed_profile.py table tree_default tree_testA      # ages 10-60, side by side

Measures only: timers wrap the model's functions from outside (tools/profile_run.py's Clock: each function's own time, so
nothing is counted twice), and the run prints a digest so you can check that measuring changed nothing.  Runs lean, as
ensembles and plots with no saves do; --full keeps the history a run with save files keeps.  Results in out/bench/speed/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from profile_run import Clock, memory_by_attribute, top_entries, working_set_mb  # noqa: E402

OUT = ROOT / "out" / "bench" / "speed"
AGES = (10, 20, 30, 40, 50, 60)


def instrument(clock: Clock) -> None:
    from treegen import hydraulics, light as light_mod, mechanics
    from treegen.growth import GrowthModel
    from treegen.light import LightField, ShadowPropagation
    from treegen.plot import Plot
    from treegen.roots import RootSystem, SharedSoil
    from treegen.structure import Tree

    table = {
        "light: sweep": [(ShadowPropagation, "compute")],
        "light: transfer": [(ShadowPropagation, "_transfer")],
        "light: blur": [(light_mod, "gaussian_filter")],
        "light: sources": [(GrowthModel, "light_sources"), (GrowthModel, "wood_sources"), (GrowthModel, "_stand_cell")],
        "light: own shade": [(ShadowPropagation, "own_shade")],
        "light: reads": [(LightField, "exposure"), (LightField, "sample"), (LightField, "optimal_direction"),
                         (LightField, "relative_light_at_heights"), (LightField, "diffuse_light_at_heights"),
                         (GrowthModel, "_crown_light_asymmetry"), (GrowthModel, "_herb_factor")],
        "water: solve": [(hydraulics, "solve"), (GrowthModel, "conducting_area")],
        "water: roots": [(RootSystem, "update_uptake"), (GrowthModel, "_fine_root_mass"), (RootSystem, "availability_field"), (SharedSoil, "update")],
        "carbon solve": [(GrowthModel, "_growth_factor"), (GrowthModel, "_leaf_costs")],
        "shoot growth": [(GrowthModel, "_grow_shoots"), (GrowthModel, "_shed"), (GrowthModel, "_reiterate"), (GrowthModel, "_leader_damage")],
        "rings": [(GrowthModel, "_update_radii"), (GrowthModel, "_stress_area"), (GrowthModel, "_wind_load_scale")],
        "mechanics": [(mechanics, "bend_and_correct")],
        "roots": [(RootSystem, "step"), (RootSystem, "update_radii")],
        "stats": [(GrowthModel, "measure"), (Plot, "measure")],
        "levels": [(Tree, "levels")],
        "subtree sums": [(Tree, "basipetal")],
        "rest of the year step": [(GrowthModel, "step"), (GrowthModel, "_finish_year"), (Plot, "step")],
        "regeneration": [(Plot, "_regenerate")],
    }
    for component, targets in table.items():
        for owner, name in targets:
            clock.patch(owner, name, component)
    # the sweep's own parts; a year's step calls these from nowhere else (checked by grep)
    clock.patch(np.fft, "rfft2", "light: fft forward")
    clock.patch(np.fft, "irfft2", "light: fft inverse")
    clock.patch(np, "tensordot", "light: weighting")


def tree_size(model) -> dict:
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    r = model.roots
    return {"nodes": int(n), "alive": int(alive.sum()), "root_nodes": int(r.tree.n) if r is not None else 0,
            "buds": int(((T.term[:n] == 1) & alive).sum() + (alive & (T.lat[:n] != 0)).sum()),
            "height_m": float(model.stats[-1]["height_m"]) if model.stats else 0.0}


def run_tree(a, clock):
    import cli
    from treegen import checkpoint
    from treegen.growth import GrowthModel
    from treegen.runhash import output_digest

    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, a.set)
    env_p, _ = cli.load_environment("sweden_open_field")
    model = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=not a.full)
    rows, last, mem = {}, {}, {}
    for _ in range(a.years):
        t0 = time.perf_counter()
        model.step()
        wall = time.perf_counter() - t0
        now = dict(clock.totals)
        field = getattr(model, "_field", None)
        rows[model.year] = {"wall": wall, "by": {k: now.get(k, 0.0) - last.get(k, 0.0) for k in now}, **tree_size(model),
                            "grid": list(field.S.shape) if field is not None else None, "rss_mb": working_set_mb()}
        last = now
        if model.year % 10 == 0 or model.year == a.years:
            sizes = memory_by_attribute(model, "model")
            mem[model.year] = {"model_mb": round(sum(sizes.values()) / 2 ** 20, 1), "top": top_entries(sizes, 14)}
    return rows, mem, {"digest": output_digest(model)}


def run_plot(a, clock):
    import cli
    from treegen import checkpoint
    from treegen.growth import GrowthModel
    from treegen.plot import Plot

    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, a.set)
    env_p, _ = cli.load_environment("sweden_open_field")
    stages = sorted(sp.stand.thinning, key=lambda s: float(s.from_height_m))
    n_final = a.start_trees * float(stages[-1].stems_per_ha) / float(stages[0].stems_per_ha)
    plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), n_final, a.seed, "natural", lean=not a.full)
    per_tree: list = []
    # each tree's own year, by its size: what a tree costs in a shared forest, the shared light apart
    real_step = GrowthModel.step

    def timed_step(self):
        t0 = time.perf_counter()
        real_step(self)
        per_tree.append((plot.year + 1, int(self.tree.n), int((self.tree.death[: self.tree.n] < 0).sum()), time.perf_counter() - t0))

    GrowthModel.step = timed_step
    rows, last, mem = {}, {}, {}
    for _ in range(a.years):
        t0 = time.perf_counter()
        start = len(per_tree)
        plot.step()
        wall = time.perf_counter() - t0
        now = dict(clock.totals)
        trees = [plot.trees[k] for k in plot.alive]
        steps = per_tree[start:]
        rows[plot.year] = {"wall": wall, "by": {k: now.get(k, 0.0) - last.get(k, 0.0) for k in now},
                           "trees": len(trees), "stepped": len(steps), "tree_steps_s": sum(s[3] for s in steps),
                           "nodes": sum(int(m.tree.n) for m in trees), "alive": sum(int((m.tree.death[: m.tree.n] < 0).sum()) for m in trees),
                           "rss_mb": working_set_mb()}
        last = now
        print(f"year {plot.year}: {wall:.1f} s, {len(trees)} trees, {rows[plot.year]['alive']} live nodes, {rows[plot.year]['rss_mb']:.0f} MB", flush=True)
        if plot.year % 10 == 0 or plot.year == a.years:
            sizes = memory_by_attribute(plot, "plot")
            mem[plot.year] = {"model_mb": round(sum(sizes.values()) / 2 ** 20, 1), "top": top_entries(sizes, 14)}
        if not trees:
            break
    GrowthModel.step = real_step
    return rows, mem, {"per_tree": per_tree, "area_m2": plot.area}


def main_run(a):
    OUT.mkdir(parents=True, exist_ok=True)
    clock = Clock()
    instrument(clock)
    t0 = time.perf_counter()
    rows, mem, extra = (run_tree if a.what == "tree" else run_plot)(a, clock)
    seconds = time.perf_counter() - t0
    doc = {"what": a.what, "label": a.label, "years": a.years, "seed": a.seed, "sets": a.set, "seconds": seconds,
           "totals": dict(clock.totals), "rows": {str(k): v for k, v in rows.items()}, "memory": {str(k): v for k, v in mem.items()}, **extra}
    (OUT / f"{a.label}.json").write_text(json.dumps(doc), encoding="utf-8")
    print(f"{a.label}: {seconds:.1f} s; {extra.get('digest', '')}")


def table(labels):
    for label in labels:
        d = json.loads((OUT / f"{label}.json").read_text(encoding="utf-8"))
        rows = {int(k): v for k, v in d["rows"].items()}
        total = sum(d["totals"].values())
        print(f"\n## {label}: {d['seconds']:.1f} s, {d['what']}, seed {d['seed']}, {len(d.get('sets', []))} settings changed\n")
        comps = sorted(d["totals"], key=lambda k: -d["totals"][k])
        ages = [x for x in AGES if x in rows]
        print("| Component | Seconds | Share | " + " | ".join(f"Year {x}" for x in ages) + " |")
        print("|---|---|---|" + "---|" * len(ages))
        for c in comps:
            print(f"| {c} | {d['totals'][c]:.2f} | {100 * d['totals'][c] / total:.1f} % | " + " | ".join(f"{rows[x]['by'].get(c, 0.0):.3f}" for x in ages) + " |")
        print("| **All, wall** |  |  | " + " | ".join(f"{rows[x]['wall']:.2f}" for x in ages) + " |")
        keys = [k for k in ("trees", "nodes", "alive", "root_nodes", "buds", "height_m", "rss_mb") if ages and k in rows[ages[0]]]
        for k in keys:
            print(f"| {k} |  |  | " + " | ".join(f"{rows[x][k]:.0f}" for x in ages) + " |")
        if ages and rows[ages[0]].get("grid"):
            print("| grid |  |  | " + " | ".join("x".join(str(v) for v in rows[x]["grid"]) for x in ages) + " |")
        for age, m in d["memory"].items():
            if int(age) in (20, 40, 60):
                print(f"\nMemory, year {age}: {m['model_mb']} MB in the model's attributes: " + ", ".join(f"{t['what']} {t['mb']}" for t in m["top"][:10]))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["tree", "plot", "table"])
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label", default=None)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--start-trees", type=int, default=25)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    if a.what == "table":
        table(a.labels)
    else:
        a.label = a.label or f"{a.what}_{a.seed}"
        main_run(a)


if __name__ == "__main__":
    main()
