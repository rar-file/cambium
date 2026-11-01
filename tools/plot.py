"""Grow a plot of independent trees sharing one light field and soil, and
export every tree as it finishes (removed, dead, or alive at the end).

    python tools/plot.py --trees 25 --years 60 --seed 1 --out out/plot_1 [--mode natural]
    python tools/plot.py --out out/plot_1 --resume          # continue from the last checkpoint

Every --checkpoint-every years each tree's history goes to disk, the plot is
pickled to <out>/checkpoint.pkl and <out>/plot.json is rewritten, so memory
holds only the trees' current state and a stopped run can resume.  Trees
that leave the plot (thinned or dead) get timeline.json and stats.json;
trees alive at the end also get meshes (unless --no-mesh).
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli  # noqa: E402
from treegen import export  # noqa: E402
from treegen.plot import Plot  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--environment", default="sweden_open_field")
    ap.add_argument("--trees", type=int, default=25, help="trees left at the managed programme's final stem density (sets the plot area)")
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mode", choices=["managed", "natural"], default="managed")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-mesh", action="store_true")
    ap.add_argument("--checkpoint-every", type=int, default=5)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON",
                    help="override a species value, e.g. tropism.gravitropism_per_m=[2,3.5,2,0.5]")
    args = ap.parse_args(argv)
    out = Path(args.out or f"out/plot_{args.seed}")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.resume:
        plot = Plot.resume(out)
        sp = plot.trees[plot.alive[0]].sp
        print(f"resumed at year {plot.year}: {len(plot.alive)} trees", flush=True)
    else:
        sp, _ = cli.load_species(args.species)
        for item in args.set:
            key, val = item.split("=", 1)
            obj = sp
            for part in key.split(".")[:-1]:
                obj = getattr(obj, part)
            setattr(obj, key.split(".")[-1], json.loads(val))
        env_p, _ = cli.load_environment(args.environment)
        plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), args.trees, args.seed, args.mode)
        print(f"plot {plot.L:.1f} m square, {len(plot.trees)} trees at start, {plot.mode}", flush=True)
    meta_base = {"species": sp.species.scientific_name, "environment": args.environment, "mode": f"plot ({plot.mode})",
                 "plot_seed": args.seed}

    def write_plot_json():
        (out / "plot.json").write_text(json.dumps({"area_m2": plot.area, "side_m": plot.L, "mode": plot.mode, "year": plot.year,
                                                   "trees": plot.info, "stats": plot.stats,
                                                   "runtime_s": round(time.time() - t0), "peak_mb": round(cli.peak_memory_mb())},
                                                  indent=1))

    def export_tree(k, cause, meshes):
        m = plot.trees[k]
        d = out / f"tree_{k:03d}"
        d.mkdir(exist_ok=True)
        m.restore_history(d / "history")
        meta = dict(meta_base, seed=plot.info[k]["seed"], fate=cause)
        anchorage = cli.anchorage_numbers(m, m.sp)
        export.write_timeline(d / "timeline.json", m, meta)
        export.write_stats(d / "stats.json", m, meta, cli.reference_block(m.sp, m.stats), anchorage)
        if meshes:
            cli.export_all(m, m.sp, d, meta, anchorage, [], 400_000, {}, {})
        plot.info[k]["leader_losses"] = [list(x) for x in m.leader_losses]
        for f in (d / "history").glob("history_*.npz"):
            f.unlink()

    plot.on_finish = lambda k, cause: export_tree(k, cause, meshes=False)
    while plot.year < args.years:
        plot.step()
        s = plot.stats[-1]
        if s["year"] % 5 == 0:
            print(f"year {s['year']}: {s['trees']} trees ({s['stems_per_ha']}/ha, {s['died_total']} died), DBH {s['dbh_mean_cm']} +- "
                  f"{s['dbh_sd_cm']} cm, H max {s['height_max_m']} m, LAI {s['lai']}, {time.time() - t0:.0f} s, "
                  f"peak {cli.peak_memory_mb():.0f} MB", flush=True)
        if args.checkpoint_every and plot.year % args.checkpoint_every == 0 and plot.year < args.years:
            plot.checkpoint(out)
            write_plot_json()
    for k in list(plot.alive):
        export_tree(k, "alive", meshes=not args.no_mesh)
        plot.trees[k] = None              # free its memory before the next export
        print(f"exported tree {k} ({time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB)", flush=True)
    write_plot_json()
    print(f"done in {time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB -> {out}")


if __name__ == "__main__":
    main()
