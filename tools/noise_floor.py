"""The sensitivity screen's noise floor: how far do results move when a parameter changes
by almost nothing?

A change of a few parts in a million has no real effect, so any movement it causes is
the model's own chaos: once a tree's branching diverges, it may wander like a new seed.
An effect in the screen smaller than this can't be told from noise.  Runs the default
and many tiny changes, each its own lean process, and reports each metric's largest move
and its spread, measured the way the screen measures its ranking.

    python tools/noise_floor.py --out out/bench/noise_floor
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

AGES = ("30", "50", "60")
METRICS = ("height_m", "dbh_cm", "leaf_area_m2", "fixed", "lai", "crown_ratio", "diffuse_light_pct")
PARAMETERS = ("resource.alpha", "resource.gravimorphism", "light.extinction_coefficient", "resource.apical_dominance")
SCREEN = ROOT / "tools" / "sensitivity_screen.py"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="out/bench/noise_floor")
    ap.add_argument("--steps", type=int, default=7, help="tiny changes per parameter")
    ap.add_argument("--years", type=int, default=60)
    a = ap.parse_args()
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    jobs = [Job("baseline", [sys.executable, str(SCREEN), "--one", "", "--factor", "1.0", "--years", str(a.years),
                             "--result", str(out / "baseline.json")], out / "baseline.json")]
    for p in PARAMETERS:
        for k in range(1, a.steps + 1):
            factor = 1.0 + k * 1e-6
            target = out / f"{p}__{k}.json"
            jobs.append(Job(f"{p} x{factor}", [sys.executable, str(SCREEN), "--one", p, "--factor", repr(factor),
                                               "--years", str(a.years), "--result", str(target)], target))
    code = run_batch(jobs, 0.6, log=out / "runs.csv")
    if code:
        sys.exit(code)
    base = json.loads((out / "baseline.json").read_text())
    runs = {f.stem: json.loads(f.read_text()) for f in sorted(out.glob("*__*.json"))}
    lines = [f"{len(runs)} runs, each a parameter changed by 1 to {a.steps} parts in a million, against the default.", "",
             "| Age | Metric | Default | Largest move (%) | Spread, SD of the moves (%) |", "|---|---|---|---|---|"]
    for age in AGES:
        for m in METRICS:
            moves = [100.0 * (r[age][m] / base[age][m] - 1.0) for r in runs.values() if base[age].get(m) and r.get(age) and r[age].get(m) is not None]
            if len(moves) >= 2:
                lines.append(f"| {age} | {m} | {base[age][m]} | {max(moves, key=abs):+.2f} | {statistics.stdev(moves):.2f} |")
    same = sum(1 for r in runs.values() if r.get("scored_digest") == base.get("scored_digest"))
    worst = []
    for name, r in runs.items():
        w = max((abs(100.0 * (r[age][m] / base[age][m] - 1.0)) for age in AGES for m in ("height_m", "dbh_cm", "leaf_area_m2", "fixed")
                 if base[age].get(m) and r.get(age) and r[age].get(m) is not None), default=0.0)
        worst.append(w)
    lines += ["", f"Runs with exactly the default's output: {same} of {len(runs)}.",
              f"The screen's own measure (largest change in height, DBH, leaf area or carbon at 30, 50, 60), for these tiny changes: "
              f"median {statistics.median(worst):.1f} %, largest {max(worst):.1f} %. An effect in the screen below this can't be told from noise."]
    text = "\n".join(lines) + "\n"
    (out / "noise_floor.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
