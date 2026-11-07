"""Does each speed setting still give the plain model's numbers on these settings?  One setting at a time, then all together.

    python tools/speed_drift.py --seeds 1,2,3 --years 30                       # the Crown agent's settings, stand trees
    python tools/speed_drift.py --seeds 1 --years 30 --plot-trees 16           # the same on a small plot
    python tools/speed_drift.py --seeds 1,2 --years 30 --base testA            # or default

Each seed runs once with no speed setting, and then once per setting, in its own process.  Same means every yearly stat and every
tree array, bit for bit.  drop_dead renumbers the arrays by design, so for it only the yearly stats are compared.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from speed_compare import CROWN, TEST_A, child  # noqa: E402

SIX = ["speed.compiled_carbon=true", "speed.compiled_mechanics=true", "speed.light_layers=true", "speed.keep_soil_grids=true", "speed.quick_solve=true", "speed.quick_levels=true"]
EXTRA = ["speed.drop_dead=true"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--years", type=int, default=30)
    ap.add_argument("--plot-trees", type=int, default=0)
    ap.add_argument("--base", choices=["crown", "testA", "default"], default="crown")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--only", default="", help="comma-separated settings to try, instead of all")
    ap.add_argument("--label", default="", help="also append the table to out/bench/ensemble/<label>/drift.txt")
    a = ap.parse_args()
    base = {"crown": CROWN, "testA": TEST_A, "default": []}[a.base]
    seeds = [int(x) for x in a.seeds.split(",")]
    cases = {"none": []}
    for s in ([x if "=" in x else f"speed.{x}=true" for x in a.only.split(",") if x and x != "six"] or SIX + EXTRA):
        cases[s.split("=")[0].replace("speed.", "")] = [s]
    if a.only == "six":
        cases = {"none": []}
    if not a.only or a.only == "six":
        cases["all six"] = SIX
    jobs = [(name, seed) for seed in seeds for name in cases]

    def run(job):
        name, seed = job
        try:
            return job, child(seed, a.years, base + cases[name], a.plot_trees)
        except SystemExit as e:     # child() stops with the failed run's error: a crash is a result here
            return job, {"crash": str(e).strip().splitlines()[-1][:90], "seconds": 0.0}

    with ThreadPoolExecutor(a.workers) as pool:
        out = dict(pool.map(run, jobs))
    lines = [f"{a.base} settings, {'plot of ' + str(a.plot_trees) + ' trees at the start' if a.plot_trees else 'stand trees'}, to {a.years}, seeds {seeds}\n",
             "| Setting | " + " | ".join(f"Seed {s}" for s in seeds) + " | Seconds, against none |", "|---|" + "---|" * len(seeds) + "---|"]
    bad = False
    for name in cases:
        if name == "none":
            continue
        cells, secs, off = [], 0.0, 0.0
        for seed in seeds:
            r0, r1 = out[("none", seed)], out[(name, seed)]
            if "crash" in r1 or "crash" in r0:
                cells.append(f"**crashes: {r1.get('crash') or r0.get('crash')}**")
                bad = True
                continue
            first = next((i + 1 for i, (x, y) in enumerate(zip(r0["stats"], r1["stats"])) if x != y), None)
            arrays = r0["trees"] == r1["trees"]
            if first is not None:
                cells.append(f"**differs from year {first}**")
                bad = True
            elif not arrays and name != "drop_dead":
                cells.append("**stats same, arrays differ**")
                bad = True
            else:
                cells.append("same" if arrays else "stats same")
            secs += r1["seconds"]
            off += r0["seconds"]
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {secs:.0f} / {off:.0f} |")
    lines += ["", "DIFFERENT" if bad else "ALL THE SAME"]
    text = "\n".join(lines) + "\n"
    print(text, flush=True)
    if a.label:     # on the node: where tools/node/fetch.sh can reach it
        out = ROOT / "out" / "bench" / "ensemble" / a.label
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "drift.txt", "a", encoding="utf-8") as f:
            f.write(text + "\n")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
