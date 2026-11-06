"""One value at several settings, each as a full ensemble, one after another.

    python tools/ensemble_sweep.py trees --param resource.alpha --values 2.7,3.5,4.0 --label m2_alpha --seeds 20
    python tools/ensemble_sweep.py table --param resource.alpha --values 2.7,3.5,4.0 --label m2_alpha --base base_trees --base-value 4.8

Each setting goes to out/bench/ensemble/<label>_<value>, and finished seeds are kept, so a stopped
sweep can be started again.  'table' prints the means, with spread and share inside the band, at
each age: it reads only saved outputs, at the targets of --ref.
"""
from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

ENSEMBLES = ROOT / "out" / "bench" / "ensemble"
ROWS = (("site_index_curves", "Height (m)"), ("lai_hagemeier", "LAI"), ("subcanopy_light_transmittance", "Light (%)"))


def run(what: str, param: str, values: list, label: str, seeds: int, extra: list) -> int:
    for v in values:
        cmd = [sys.executable, str(ROOT / "tools" / "ensemble.py"), what, "--label", f"{label}_{v}", "--seeds", str(seeds), "--set", f"{param}={v}", *extra]
        print(" ".join(cmd[1:]), flush=True)
        done = subprocess.run(cmd, cwd=str(ROOT))
        if done.returncode:
            return done.returncode
    return 0


def table(values: list, label: str, base: str | None, base_value: str | None, ref: str, ages: list) -> None:
    from scorecard import ensemble_folders, evaluate_ensemble, load_approved_targets, load_run_data

    targets = load_approved_targets(ref)
    folders = [(v, ENSEMBLES / f"{label}_{v}") for v in values]
    if base:
        folders.append((base_value, ENSEMBLES / base))
    folders.sort(key=lambda x: float(x[0]))
    rows = {}
    seeds = {}
    for v, folder in folders:
        runs = [load_run_data(str(d)) for d in ensemble_folders(folder)]
        seeds[v] = len(runs)
        for r in evaluate_ensemble(targets, runs, ages):
            rows[(v, r["target"])] = r
    print(f"Targets at {ref}. Seeds per setting: {seeds}\n")
    for key, title in ROWS:
        names = [n for n in dict.fromkeys(t for _, t in rows) if key in n and rows.get((folders[0][0], n), {}).get("mean") is not None]
        if not names:
            continue
        print(f"**{title}, mean +- SD, verdict, share of seeds inside**\n")
        print("| Setting | " + " | ".join(n.split("(")[-1].rstrip(")") for n in names) + " |")
        print("|---|" + "---|" * len(names))
        for v, _ in folders:
            cells = []
            for n in names:
                r = rows.get((v, n))
                cells.append("-" if not r or r["mean"] is None else f"{r['mean']:.2f} +- {r['sd']:.2f}, {r['status']}, {100 * r['share']:.0f} %")
            print(f"| {v} | " + " | ".join(cells) + " |")
        print()
    print("Band: " + "; ".join(sorted({rows[k]['target_range'] for k in rows if key_in(k[1])})))


def key_in(name: str) -> bool:
    return "lai_hagemeier" in name or "subcanopy" in name


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("trees", "plots", "table"))
    ap.add_argument("--param", required=True)
    ap.add_argument("--values", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--no-saves", action="store_true")
    ap.add_argument("--base", default=None, help="table: the baseline's ensemble folder name")
    ap.add_argument("--base-value", default=None)
    ap.add_argument("--ref", default="master")
    ap.add_argument("--age", action="append", type=int, default=None)
    a = ap.parse_args(argv)
    values = a.values.split(",")
    if a.what == "table":
        table(values, a.label, a.base, a.base_value, a.ref, a.age or [20, 30, 40, 50, 60])
        return 0
    return run(a.what, a.param, values, a.label, a.seeds, ["--no-saves"] if a.no_saves else [])


if __name__ == "__main__":
    sys.exit(main())
