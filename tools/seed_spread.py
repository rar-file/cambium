"""How much the default tree varies between seeds (for M2, reports/M2_design_draft.md).

The cut rule's margin has to exceed this, or a candidate could be cut for a bad seed.
Runs the stand tree at many seeds, each its own unchanged, lean process, within the
machine's limits (tools/batch.py), and reports the spread at each age.

    python tools/seed_spread.py --seeds 30 --out out/bench/seeds
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

AGES = (10, 15, 20, 30, 40, 50, 60)
METRICS = ("height_m", "dbh_cm", "leaf_area_m2", "lai", "crown_ratio", "subcanopy_diffuse_light_pct")


def table(rows: dict) -> str:
    lines = [f"Stand tree, {len(rows)} seeds. Standard deviation in the metric's own units, then as % of the mean.", "",
             "| Age | Metric | Mean | SD | SD % | Lowest | Highest |", "|---|---|---|---|---|---|---|"]
    for age in AGES:
        for k in METRICS:
            v = [r[age][k] for r in rows.values() if r.get(age) and r[age].get(k) is not None]
            if len(v) < 2:
                continue
            m, sd = statistics.fmean(v), statistics.stdev(v)
            lines.append(f"| {age} | {k} | {m:.2f} | {sd:.2f} | {100 * sd / m if m else 0:.1f} | {min(v):.2f} | {max(v):.2f} |")
    return "\n".join(lines) + "\n"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--out", default="out/bench/seeds")
    a = ap.parse_args()
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out
    jobs = []
    for seed in range(1, a.seeds + 1):
        cmd = [sys.executable, str(ROOT / "cli.py"), "--stand", "--seed", str(seed), "--years", str(a.years), "--lean", "--quiet",
               "--out", str(out)]
        jobs.append(Job(f"seed {seed}", cmd, out / f"{seed}_stand" / "manifest.json"))
    code = run_batch(jobs, 0.6, log=out / "runs.csv")
    if code:
        sys.exit(code)
    rows = {}
    for seed in range(1, a.seeds + 1):
        st = json.loads((out / f"{seed}_stand" / "stats.json").read_text(encoding="utf-8"))["per_year"]
        rows[seed] = {r["year"]: r for r in st if r["year"] in AGES}
    text = table(rows)
    (out / "spread.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
