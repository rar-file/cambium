"""Grow a plot of independent trees sharing one light field and soil, and
export every tree as it finishes (removed, dead, or alive at the end).

    python tools/plot.py --trees 25 --years 60 --seed 1 --out out/plot_1 [--mode natural]
    python tools/plot.py --out out/plot_1 --resume          # continue from the last checkpoint
    python tools/plot.py --start-trees 25 --mode natural --years 20    # 25 trees at the start
    python tools/plot.py --trees 2 --dense-start 10000 --mode natural --years 10    # dense regeneration
    python tools/plot.py --out out/a --save-at 30 --mode natural --years 60            # keep the state at 30
    python tools/plot.py --branch-from out/a/state_030 --out out/b --mode managed      # another scenario from there

Every --checkpoint-every years each tree's history goes to disk, the plot is
pickled to <out>/checkpoint.pkl and <out>/plot.json is rewritten, so memory
holds only the trees' current state and a stopped run can resume.  Trees
that leave the plot (thinned or dead) get timeline.json and stats.json;
trees alive at the end also get meshes (unless --no-mesh).
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli  # noqa: E402
from treegen import checkpoint, checks, export  # noqa: E402
from treegen.params import SettingError, run_manifest  # noqa: E402
from treegen.plot import Plot  # noqa: E402


def _check(args, out: Path) -> None:
    """Every argument and the output folder, before anything grows: a slip costs a second, not a run."""
    checks.seed(args.seed)
    checks.years(args.years)
    checks.whole("--trees", args.trees, 1)
    if args.start_trees is not None:
        checks.whole("--start-trees", args.start_trees, 1)
    if args.dense_start is not None:
        checks.positive("--dense-start", args.dense_start)
    checks.whole("--checkpoint-every", args.checkpoint_every, 0)
    checks.wholes("--save-at", args.save_at, 1, args.years)
    if args.branch_from:
        if not (Path(args.branch_from) / "checkpoint.pkl").is_file():
            raise ValueError(f"--branch-from: no saved state in {args.branch_from}")
        if out.exists():
            raise ValueError(f"--branch-from copies the state into a new folder, and {out} is already there")
        checks.folder(out.parent)
    elif args.resume:
        if not (out / "checkpoint.pkl").is_file():
            raise ValueError(f"--resume: no checkpoint in {out}")
    else:
        checks.inputs(args.species, args.environment, args.set)
        checks.folder(out)


def main(argv=None):
    ap = checks.Parser()
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--environment", default="sweden_open_field")
    ap.add_argument("--trees", type=int, default=25, help="trees left at the managed programme's final stem density (sets the plot area)")
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mode", choices=["managed", "natural"], default=None, help="default managed; with --branch-from, keeps the saved mode")
    ap.add_argument("--out", default=None)
    ap.add_argument("--start-trees", type=int, default=None,
                    help="trees at the start of the plot, instead of --trees (which counts those left at the final stem density)")
    ap.add_argument("--dense-start", type=float, default=None, metavar="STEMS_PER_HA",
                    help="start at this stem density on the same ground as --trees sets: the dense-regeneration test")
    ap.add_argument("--no-mesh", action="store_true")
    ap.add_argument("--checkpoint-every", type=int, default=5)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--save-at", default="", help="comma-separated years: keep a full copy of the state in <out>/state_YYY")
    ap.add_argument("--branch-from", default=None, help="copy a saved state to --out and carry on from it, for a scenario")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON",
                    help="override a species value, e.g. tropism.gravitropism_per_m=[2,3.5,2,0.5]")
    ap.add_argument("--regeneration", action="store_true",
                    help="natural regeneration: seed rain, germination and recruits (treegen/regeneration.py)")
    args = ap.parse_args(argv)
    out = Path(args.out or f"out/plot_{args.seed}")
    try:
        _check(args, out)
    except (ValueError, FileNotFoundError) as exc:
        raise checks.stop("plot.py", exc) from None
    if args.branch_from:
        shutil.copytree(args.branch_from, out)
    out.mkdir(parents=True, exist_ok=True)
    save_at = {int(x) for x in args.save_at.split(",") if x.strip()}
    t0 = time.time()
    if args.resume or args.branch_from:
        plot = Plot.resume(out)
        sp = plot.trees[plot.alive[0]].sp
        print(f"resumed at year {plot.year}: {len(plot.alive)} trees", flush=True)
        if args.branch_from:   # a scenario; a plain --resume carries on as the run was
            if args.mode:
                plot.mode = args.mode
            for item in args.set:   # every living tree, and the template for recruits
                for target in [plot.trees[k].sp for k in plot.alive] + [plot.species]:
                    try:
                        checkpoint.set_values(target, [item])
                    except SettingError as exc:   # on the saved values, before the first year grows
                        raise checks.stop("plot.py", exc) from None
        elif args.mode or args.set:
            print("--mode and --set are ignored on a plain --resume; use --branch-from for a scenario", flush=True)
    else:
        sp, _ = cli.load_species(args.species)
        checkpoint.set_values(sp, args.set)
        env_p, _ = cli.load_environment(args.environment)
        stages = sorted(sp.stand.thinning, key=lambda s: float(s.from_height_m))
        n_final = args.trees
        if args.start_trees is not None:
            n_final = args.start_trees * float(stages[-1].stems_per_ha) / float(stages[0].stems_per_ha)
        if args.dense_start is not None:
            stages[0].stems_per_ha = float(args.dense_start)
        plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), n_final, args.seed, args.mode or "managed")
        if args.regeneration:
            plot.enable_regeneration()
        print(f"plot {plot.L:.1f} m square, {len(plot.trees)} trees at start, {plot.mode}"
              f"{', regeneration' if args.regeneration else ''}", flush=True)
    meta_base = {"species": sp.species.scientific_name, "environment": args.environment, "mode": f"plot ({plot.mode})",
                 "plot_seed": plot.seed}
    manifest, options = run_manifest(args.species, args.environment, sp)
    # --set overrides change the parameters used without changing the file;
    # a resumed run reports the files as they are now, not as at its start
    manifest.update({"overrides": args.set, "resumed": bool(args.resume)})
    meta_base.update({"run_manifest": manifest, "options": options})

    def write_plot_json():
        (out / "plot.json").write_text(json.dumps({"area_m2": plot.area, "side_m": plot.L, "mode": plot.mode, "year": plot.year,
                                                   "run_manifest": manifest, "options": options,
                                                   "trees": plot.info, "stats": plot.stats,
                                                   **({"damage_log": plot.damage_log} if getattr(plot, "damage_log", None) else {}),
                                                   "runtime_s": round(time.time() - t0), "peak_mb": round(cli.peak_memory_mb())},
                                                  indent=1))

    # A dead tree's history stays until a checkpoint no longer counts it as alive: a run
    # stopped before then resumes from a checkpoint where that tree still has to die.
    stale_history = []

    def clear_stale_history():
        for folder in stale_history:
            for f in folder.glob("history_*.npz"):
                f.unlink()
        stale_history.clear()

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
        stale_history.append(d / "history")

    plot.on_finish = lambda k, cause: export_tree(k, cause, meshes=False)
    while plot.year < args.years:
        plot.step()
        s = plot.stats[-1]
        if not plot.alive:
            print(f"year {s['year']}: no trees left ({s['died_total']} died)", flush=True)
            break
        if s["year"] % 5 == 0:
            print(f"year {s['year']}: {s['trees']} trees ({s['stems_per_ha']}/ha, {s['died_total']} died), DBH {s['dbh_mean_cm']} +- "
                  f"{s['dbh_sd_cm']} cm, H max {s['height_max_m']} m, LAI {s['lai']}, {time.time() - t0:.0f} s, "
                  f"peak {cli.peak_memory_mb():.0f} MB", flush=True)
        # one checkpoint a year at most: a second one would write an empty history over the first
        regular = args.checkpoint_every and plot.year % args.checkpoint_every == 0 and plot.year < args.years
        if regular or plot.year in save_at:
            plot.checkpoint(out)
            clear_stale_history()
            write_plot_json()
        if plot.year in save_at:
            shutil.copytree(out, out / f"state_{plot.year:03d}", ignore=shutil.ignore_patterns("state_*"))
    for k in list(plot.alive):
        export_tree(k, "alive", meshes=not args.no_mesh)
        plot.trees[k] = None              # free its memory before the next export
        print(f"exported tree {k} ({time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB)", flush=True)
    write_plot_json()         # before the histories go: a run stopped here can still resume
    clear_stale_history()
    print(f"done in {time.time() - t0:.0f} s, peak {cli.peak_memory_mb():.0f} MB -> {out}")


if __name__ == "__main__":
    main()
