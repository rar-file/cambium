"""Open-grown trees for several seeds, in parallel, for a quick before/after check of the open-grown look and size.

    python tools/open_trees.py --label LABEL --seeds 10 [--first-seed 1] [--years 60] [--jobs 4] [--set key=value ...]

Each seed runs cli.py (open-grown, --lean --quiet) into out/bench/ensemble/LABEL/<seed>/.  Reads nothing back;
compare stats.json files afterwards.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    out = ROOT / "out" / "bench" / "ensemble" / a.label
    out.mkdir(parents=True, exist_ok=True)
    sets = [x for s in a.set for x in ("--set", s)]

    def run(seed: int) -> str:
        cmd = [sys.executable, str(ROOT / "cli.py"), "--species", "betula_pendula", "--seed", str(seed),
               "--years", str(a.years), "--lean", "--quiet", "--no-mesh", "--no-preview", "--out", str(out), *sets]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return f"seed {seed}: exit {r.returncode}"

    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for line in ex.map(run, range(a.first_seed, a.first_seed + a.seeds)):
            print(line, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
