"""Forest plots: natural density, self-thinning, spreading.  A run writes one plot.json with
the stand's yearly measures, and no files per tree, so thousands of trees can come and go.

    python tools/forest.py run --seed 1 --years 60 --area 1000 --out out/forest/a
    python tools/forest.py run --seed 1 --years 40 --strip 150 10 --patch 20 --stems 3000 --spread --out out/forest/b
    python tools/forest.py plots --label thin1 --seeds 5 --years 60 --area 1000    # the node, in turn
    python tools/stand_table.py out/bench/forest/thin1

'run' sets mortality.enabled, plot.natural_start.enabled and plot.stand_measures; --spread sets
regeneration.spread.enabled and switches regeneration on.  --set takes any other species value.
Without --mortality-off the carbon rule and the new mortality both act.

The trees are lean: nothing is kept that only an export would read, so none can be exported.
Time and peak memory are written per year as year_log, the place to read a run's real cost.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import cli  # noqa: E402
from batch import free_gb  # noqa: E402
from treegen import checkpoint  # noqa: E402
from treegen.params import run_manifest  # noqa: E402
from treegen.plot import Plot  # noqa: E402

BASE = ROOT / "out" / "bench" / "forest"


def settings(a) -> list:
    """Every value this run changes, as --set items, so a run's manifest holds them all."""
    out = ["plot.stand_measures=true", "plot.natural_start.enabled=true", f"plot.natural_start.stems_per_ha={a.stems}"]
    if not a.mortality_off:
        out.append("mortality.enabled=true")
    if a.strip:
        out += [f"plot.natural_start.side_x_m={a.strip[0]}", f"plot.natural_start.side_y_m={a.strip[1]}"]
        if a.patch:
            out.append(f"plot.natural_start.patch_x_m={a.patch}")
    else:
        out.append(f"plot.natural_start.area_m2={a.area}")
    if a.spread:
        out.append("regeneration.spread.enabled=true")
    return out + list(a.set)


def run(a) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sp, _ = cli.load_species(a.species)
    items = settings(a)
    checkpoint.set_values(sp, items)
    env_p, _ = cli.load_environment(a.environment)
    t0 = time.time()
    plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), seed=a.seed, mode="natural", lean=True)
    if a.spread or a.regeneration:
        plot.enable_regeneration()
    print(f"plot {plot._sides()[0]:.1f} x {plot._sides()[1]:.1f} m, {len(plot.trees)} trees at start, "
          f"{time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB", flush=True)
    manifest, options = run_manifest(a.species, a.environment, sp)
    manifest["overrides"] = items
    year_log = []

    def write():
        sides = plot._sides()
        doc = {"area_m2": plot.area, "side_m": sides[0], "side_y_m": sides[1], "mode": plot.mode, "year": plot.year,
               "seed": a.seed, "run_manifest": manifest, "options": options, "stats": plot.stats, "year_log": year_log,
               "trees_ever": len(plot.trees), "runtime_s": round(time.time() - t0), "peak_mb": round(cli.peak_memory_mb())}
        if a.tree_table:
            doc["trees"] = plot.info
        tmp = out / "plot.json.tmp"
        tmp.write_text(json.dumps(doc), encoding="utf-8")
        tmp.replace(out / "plot.json")

    while plot.year < a.years and plot.alive:
        y0 = time.time()
        plot.step()
        if a.gap_at and plot.year == a.gap_at:
            print(f"year {plot.year}: a windthrow of {a.gap_radius} m radius took {plot.open_gap(0.0, 0.0, a.gap_radius)} trees", flush=True)
        s = plot.stats[-1]
        # year, seconds, peak MB, trees, crown and root nodes held (live and dead)
        year_log.append([plot.year, round(time.time() - y0, 1), round(cli.peak_memory_mb()), len(plot.alive),
                         sum(plot.trees[k].tree.n for k in plot.alive), sum(plot.trees[k].roots.tree.n for k in plot.alive)])
        if plot.year % a.print_every == 0 or plot.year == a.years:
            print(f"year {plot.year}: {s['stems_per_ha']}/ha, G {s.get('basal_area_ob_m2_ha')}, Dg {s.get('dg_ob_cm')}, "
                  f"RD {s.get('relative_density')}, top {s.get('top_height_m')} m, gap {s.get('gap_fraction')}, "
                  f"new {s.get('new_trees')}, {time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB", flush=True)
            write()
        if a.stop_free_gb and free_gb() < a.stop_free_gb:
            print(f"STOPPED at year {plot.year}: {free_gb():.1f} GB free, under the {a.stop_free_gb} GB this run may leave", flush=True)
            write()
            sys.exit(4)
    write()
    (out / "done.txt").write_text("done\n")
    print(f"done in {time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB -> {out}", flush=True)


def plots(a) -> int:
    """Several seeds in turn, through the batch runner's memory check."""
    from batch import Job, run_batch
    folder = BASE / a.label
    jobs = []
    for s in range(a.first_seed, a.first_seed + a.seeds):
        cmd = [sys.executable, str(Path(__file__).resolve()), "run", "--seed", str(s), "--years", str(a.years),
               "--stems", str(a.stems), "--out", str(folder / f"plot_{s}")]
        if a.strip:
            cmd += ["--strip", str(a.strip[0]), str(a.strip[1])]
        else:
            cmd += ["--area", str(a.area)]
        if a.patch:
            cmd += ["--patch", str(a.patch)]
        for flag, on in (("--spread", a.spread), ("--regeneration", a.regeneration), ("--mortality-off", a.mortality_off), ("--tree-table", a.tree_table)):
            if on:
                cmd.append(flag)
        for item in a.set:
            cmd += ["--set", item]
        jobs.append(Job(f"plot {s}", cmd, folder / f"plot_{s}" / "done.txt"))
    return run_batch(jobs, a.peak_gb, log=folder / "runs.csv")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["run", "plots"])
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--environment", default="sweden_open_field")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--stems", type=float, default=12000.0, help="stems/ha at the start, where the start's trees stand")
    ap.add_argument("--area", type=float, default=1000.0, help="square plot of this many m2")
    ap.add_argument("--strip", type=float, nargs=2, default=None, metavar=("X", "Y"), help="a rectangle of ground, m")
    ap.add_argument("--patch", type=float, default=None, help="the start's trees only in the first metres of x")
    ap.add_argument("--spread", action="store_true", help="regeneration that spreads: seed, light, open ground")
    ap.add_argument("--regeneration", action="store_true", help="the plain regeneration")
    ap.add_argument("--mortality-off", action="store_true")
    ap.add_argument("--tree-table", action="store_true", help="keep a row for every tree that ever lived in plot.json")
    ap.add_argument("--print-every", type=int, default=5)
    ap.add_argument("--gap-at", type=int, default=None, help="a windthrow in the middle of the plot in this year")
    ap.add_argument("--gap-radius", type=float, default=10.0)
    ap.add_argument("--stop-free-gb", type=float, default=None, help="stop and save if free memory falls under this, on a shared machine")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--peak-gb", type=float, default=8.0, help="plots: what the memory check allows for each run")
    a = ap.parse_args()
    if a.what == "plots":
        sys.exit(plots(a))
    run(a)


if __name__ == "__main__":
    main()
