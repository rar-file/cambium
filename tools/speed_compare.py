"""Does a speed setting leave a run's numbers alone, and how fast is it?  Paired, on this machine, one process per run.

    python tools/speed_compare.py lossless --years 30 --seeds 1,2 --set speed.compiled_carbon=true
    python tools/speed_compare.py lossless --years 30 --testA --set speed.compiled_carbon=true

Each pair runs lean trees off and on, alternating; every yearly stat and the final tree arrays must match bit for bit.  Prints
seconds off, on, and every difference found.  One worker: run it when the PC isn't busy for timings that mean anything, and
repeat them: other agents share the PC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

TEST_A = ["height_driver.enabled=true", "height_driver.ring_share_max=0.5", "height_driver.lateral_cap_ratio=0.6", "stats.limbs_on_leader=true",
          "pipe_model.heartwood_by_own_foliage=true", "pipe_model.branch_sapwood_senescence=0.30", "resource.apical_dominance=0.75",
          "bud_fate.long_shoot_threshold=5", "bud_fate.density_control.enabled=true", "bud_fate.density_control.after_growth=true",
          "shedding.shade_softness=0.5", "shedding.light_per_leaf_threshold=0.18", "bud_fate.short_shoot_survival_light=0.18"]
ARRAYS = ("pos", "dir", "ref", "term_dir", "lat_dir", "sym_side", "parent", "main_child", "lat_child", "birth", "death", "order", "axis", "length",
          "term", "lat", "lat_age", "spur_birth", "own_pipe", "radius", "leaf_scale", "leaves", "leaf_size", "lma", "wood_area", "sap_area", "no_axil")


def one(seed: int, years: int, sets: list, plot_trees: int = 0) -> dict:
    """A lean tree, or a lean plot: seconds, a digest of each year's stats, and a digest of every tree array at the end."""
    import cli
    from treegen import checkpoint
    from treegen.growth import GrowthModel
    from treegen.plot import Plot

    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, sets)
    env_p, _ = cli.load_environment("sweden_open_field")
    t0 = time.perf_counter()

    def digest(model):
        h = hashlib.sha256()
        n = model.tree.n
        for name in ARRAYS:
            h.update(getattr(model.tree, name)[:n].tobytes())
        if model.roots is not None:
            m = model.roots.tree.n
            for name in ("pos", "radius", "death"):
                h.update(getattr(model.roots.tree, name)[:m].tobytes())
        return h.hexdigest()

    if plot_trees:
        stages = sorted(sp.stand.thinning, key=lambda s: float(s.from_height_m))
        n_final = plot_trees * float(stages[-1].stems_per_ha) / float(stages[0].stems_per_ha)
        plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), n_final, seed, "natural", lean=True)
        for _ in range(years):
            plot.step()
        seconds = time.perf_counter() - t0
        tree_years = sum(int(s.get("trees", 0)) for s in plot.stats)
        return {"seconds": seconds, "stats": [hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest() for s in plot.stats],
                "trees": {str(k): digest(plot.trees[k]) for k in plot.alive}, "alive": len(plot.alive), "nodes": sum(plot.trees[k].tree.n for k in plot.alive),
                "tree_years": tree_years, "peak_mb": cli.peak_memory_mb()}
    model = GrowthModel(sp, cli.make_environment(env_p), seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    for _ in range(years):
        model.step()
    seconds = time.perf_counter() - t0
    return {"seconds": seconds, "stats": [hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest() for s in model.stats],
            "trees": {"0": digest(model)}, "alive": 1, "nodes": int(model.tree.n), "peak_mb": cli.peak_memory_mb()}


def child(seed, years, sets, plot_trees) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "one", "--seed", str(seed), "--years", str(years), "--plot-trees", str(plot_trees)]
    for s in sets:
        cmd += ["--set", s]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr[-3000:])
    return json.loads(p.stdout.strip().splitlines()[-1])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["one", "lossless", "times"])
    ap.add_argument("--sets", default="", help="times: names from tools/speed_queue.py SETS, comma separated; each is run with the lossless settings")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seeds", default="1")
    ap.add_argument("--years", type=int, default=30)
    ap.add_argument("--plot-trees", type=int, default=0, help="a lean plot with this many trees at the start, instead of a stand tree")
    ap.add_argument("--testA", action="store_true")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    base = TEST_A if a.testA else []
    if a.what == "one":
        print(json.dumps(one(a.seed, a.years, a.set, a.plot_trees)))
        return
    if a.what == "times":
        # each set in turn, round after round, so the PC's other work falls on all of them; the quickest of each is the table
        from speed_queue import LOSSLESS, SETS

        names = a.sets.split(",")
        seeds = [int(x) for x in a.seeds.split(",")]
        best = {n: {} for n in names}
        peak = {n: 0.0 for n in names}
        for _ in range(a.repeats):
            for seed in seeds:
                for n in names:
                    if n.startswith("OFF_"):
                        sets = SETS[n[4:]][0]        # settings of that name with no speed settings at all
                    else:
                        sets = LOSSLESS + SETS[n][0]
                    r = child(seed, a.years, sets, a.plot_trees)
                    best[n][seed] = min(best[n].get(seed, 1e9), r["seconds"])
                    peak[n] = max(peak[n], r.get("peak_mb") or 0.0)
                    print(f"{n} seed {seed}: {r['seconds']:.1f} s, peak {r.get('peak_mb', 0):.0f} MB", flush=True)
        print("\n| Set | " + " | ".join(f"Seed {s} (s)" for s in seeds) + " | Mean (s) | Against the first | Peak (MB) |")
        print("|---|" + "---|" * (len(seeds) + 3))
        first = sum(best[names[0]].values())
        for n in names:
            total = sum(best[n].values())
            print(f"| `{n}` | " + " | ".join(f"{best[n][s]:.1f}" for s in seeds) + f" | {total / len(seeds):.1f} | {first / total:.2f}x | {peak[n]:.0f} |")
        return
    all_same = True
    print(f"settings on: {a.set}; {'Test A' if a.testA else 'default'}; {a.plot_trees or 'stand tree'}; to {a.years}")
    print("| Seed | Off (s) | On (s) | On / off | Nodes | Identical |")
    print("|---|---|---|---|---|---|")
    for seed in [int(x) for x in a.seeds.split(",")]:
        off, on = [], []
        for _ in range(a.repeats):
            r0 = child(seed, a.years, base, a.plot_trees)
            r1 = child(seed, a.years, base + a.set, a.plot_trees)
            off.append(r0["seconds"])
            on.append(r1["seconds"])
        same = r0["stats"] == r1["stats"] and r0["trees"] == r1["trees"]
        all_same &= same
        first = next((i + 1 for i, (x, y) in enumerate(zip(r0["stats"], r1["stats"])) if x != y), None)
        print(f"| {seed} | {min(off):.1f} | {min(on):.1f} | {min(on) / min(off):.3f} | {r0['nodes']} | {'yes' if same else f'NO, first at year {first}'} |", flush=True)
    print("IDENTICAL" if all_same else "DIFFERENT")
    sys.exit(0 if all_same else 1)


if __name__ == "__main__":
    main()
