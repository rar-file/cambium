"""Run time against how many runs were going at once, from a batch's runs.csv.

For each run, the runs going at once is the time-weighted mean over its own life of
how many runs were alive, itself included.  Parameter changes alter a run's time too,
so compare groups, not single runs.  Also the batch's throughput while it ran.

    python tools/batch_report.py out/bench/m1/screen_16threads/runs.csv out/bench/m1/screen/runs.csv
"""
import csv
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean, median


def load(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["exit"] != "0":
                continue
            t0 = datetime.fromisoformat(r["started"]).timestamp()
            rows.append({"job": r["job"], "t0": t0, "t1": t0 + float(r["seconds"]), "secs": float(r["seconds"])})
    return rows


def at_once(run, rows):
    """Time-weighted mean of the runs alive during this run, itself included."""
    edges = sorted({run["t0"], run["t1"]} | {t for o in rows for t in (o["t0"], o["t1"]) if run["t0"] < t < run["t1"]})
    total = 0.0
    for a, b in zip(edges, edges[1:]):
        mid = 0.5 * (a + b)
        total += (b - a) * sum(1 for o in rows if o["t0"] <= mid < o["t1"])
    return total / max(run["t1"] - run["t0"], 1e-9)


def main():
    for path in sys.argv[1:]:
        rows = load(path)
        print(f"\n{path}: {len(rows)} finished runs")
        if not rows:
            continue
        groups = {}
        for r in rows:
            groups.setdefault(round(at_once(r, rows)), []).append(r["secs"])
        print("| Runs at once | Runs | Mean run time (s) | Median run time (s) | Runs per hour at that level |")
        print("|---|---|---|---|---|")
        for n in sorted(groups):
            v = groups[n]
            print(f"| {n} | {len(v)} | {mean(v):.0f} | {median(v):.0f} | {3600.0 * n / mean(v):.0f} |")
        wall = max(r["t1"] for r in rows) - min(r["t0"] for r in rows)
        print(f"Overall: {len(rows)} runs in {wall:.0f} s, {3600.0 * len(rows) / wall:.0f} runs per hour, "
              f"{mean(r['secs'] for r in rows):.0f} s mean run time, {sum(r['secs'] for r in rows) / wall:.1f} runs at once on average")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
