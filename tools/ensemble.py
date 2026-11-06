"""Ensembles of seeds, the basis of every verdict (PROTOCOL.md section 2; the maintainer, 2026-11-06).

One seed isn't a typical tree: a parameter change of a few parts in a million moves height
by up to 6 % and leaf area by up to 28 % (out/bench/node/noise_floor.md).  So verdicts come
from the ensemble mean against the target band, on one machine.

    python tools/ensemble.py trees --label base --seeds 20
    python tools/ensemble.py trees --label option --seeds 20 --set resource.alpha=4.2
    python tools/ensemble.py plots --label base_plots --seeds 5 --mode natural
    python tools/ensemble.py median --label base           # the example tree for renders

Single trees run lean and in parallel.  Plots are heavy runs: on the node they run within
its limits (PROTOCOL.md section 6), and on the main PC only one at a time.  Finished seeds
are kept, so a stopped ensemble can be started again.

--no-saves is for the node, whose disk other services share: five plots writing save files
left 10.7 GB free by age 35 (DECISIONS.md row 33).  Without save files a plot holds its history
in memory, so it needs more of that.  Output is the same on what's been tested so far
(out/bench/p0/checkpoint_proof.txt); the full-size test is out/bench/route_check on the node.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import Job, run_batch  # noqa: E402

BASE = ROOT / "out" / "bench" / "ensemble"
TREE_PEAK_GB, PLOT_PEAK_GB = 0.6, 7.0   # plots: 6.1-6.7 GB measured with no save files, 100 trees to 60
MEDIAN_METRICS = ("height_m", "dbh_cm", "lai", "crown_ratio")


def run_trees(label: str, seeds: int, years: int, values: list, first_seed: int = 1) -> int:
    out = BASE / label
    sets = [x for v in values for x in ("--set", v)]
    jobs = [Job(f"seed {s}", [sys.executable, str(ROOT / "cli.py"), "--stand", "--seed", str(s), "--years", str(years), "--lean", "--quiet",
                              "--out", str(out), *sets], out / f"{s}_stand" / "manifest.json")
            for s in range(first_seed, first_seed + seeds)]
    return run_batch(jobs, TREE_PEAK_GB, log=out / "runs.csv")


def run_plots(label: str, seeds: int, years: int, mode: str, trees: int, values: list, no_saves: bool = False, first_seed: int = 1) -> int:
    out = BASE / label
    sets = [x for v in values for x in ("--set", v)]
    jobs = [Job(f"plot {s}", [sys.executable, str(ROOT / "tools" / "plot.py"), "--trees", str(trees), "--mode", mode, "--seed", str(s),
                              "--years", str(years), "--no-mesh", *(["--checkpoint-every", "0"] if no_saves else []),
                              "--out", str(out / f"plot_{s}"), *sets], out / f"plot_{s}" / "done.txt")
            for s in range(first_seed, first_seed + seeds)]
    # plot.py writes no marker of its own, so wrap each one to leave done.txt only if it finishes
    for j in jobs:
        j.cmd = [sys.executable, str(Path(__file__).resolve()), "--mark-done", str(j.done), "--", *j.cmd]
    return run_batch(jobs, PLOT_PEAK_GB, log=out / "runs.csv")


def median_seed(rows: dict, age: int = 60) -> int:
    """The seed closest to the ensemble's median: smallest summed distance from each metric's
    median, in that metric's standard deviations.  Height, DBH, LAI and crown ratio at 60.
    This rule is my own, for choosing the example tree; no source sets it."""
    score = {s: 0.0 for s in rows}
    for k in MEDIAN_METRICS:
        v = {s: r[k] for s, r in rows.items() if r.get(k) is not None}
        if len(v) < 2:
            continue
        med, sd = statistics.median(v.values()), statistics.stdev(v.values()) or 1.0
        for s, x in v.items():
            score[s] += abs(x - med) / sd
    return min(score, key=lambda s: (score[s], s))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2 and sys.argv[1] == "--mark-done":
        import subprocess
        marker = Path(sys.argv[2])
        done = subprocess.run(sys.argv[4:], cwd=str(ROOT))
        if done.returncode == 0:
            marker.write_text("done\n")
        sys.exit(done.returncode)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["trees", "plots", "median"])
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--mode", default="natural")
    ap.add_argument("--trees", type=int, default=25, help="plots: trees left at the final stem density; 25 gives 100 at the start")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON", help="an option's change, from the start of each run")
    ap.add_argument("--no-saves", action="store_true", help="plots: write no save files, on the node; see above")
    ap.add_argument("--first-seed", type=int, default=1, help="for a rerun on fresh seeds (PROTOCOL.md section 9)")
    ap.add_argument("--age", type=int, default=60)
    a = ap.parse_args()
    if a.what == "trees":
        sys.exit(run_trees(a.label, a.seeds or 20, a.years, a.set, a.first_seed))
    if a.what == "plots":
        sys.exit(run_plots(a.label, a.seeds or 5, a.years, a.mode, a.trees, a.set, a.no_saves, a.first_seed))
    rows = {}
    for d in sorted((BASE / a.label).glob("*_stand")):
        per_year = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
        rows[int(d.name.split("_")[0])] = next(r for r in per_year if r["year"] == a.age)
    print(median_seed(rows, a.age))


if __name__ == "__main__":
    main()
