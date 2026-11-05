"""Compare scorecard verdicts for saved runs between two git refs of
reference/targets.yaml.  Prints every row whose status or target text changed.

    python tools/rescore_compare.py <old ref> <new ref> run1 run2 ... [--age 20 ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from scorecard import evaluate_targets, load_approved_targets, load_run_data  # noqa: E402


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--age", type=int, action="append", default=None)
    a = ap.parse_args()
    ages = a.age or [20, 30, 40, 50, 60]
    t_old, t_new = load_approved_targets(a.old), load_approved_targets(a.new)
    print("| Run | Target | Model | Band before | Before | Band after | After |")
    print("|---|---|---|---|---|---|---|")
    changed = 0
    for path in a.runs:
        run = load_run_data(path)
        ro, _ = evaluate_targets(t_old, [run], ages=ages)
        rn, _ = evaluate_targets(t_new, [run], ages=ages)
        new_by_name = {r["target"]: r for r in rn}
        for r in ro:
            n = new_by_name.get(r["target"])
            if n is None:
                print(f"| {path} | {r['target']} | {r['model_value']} | {r['target_range']} | {r['status']} | removed | - |")
                changed += 1
            elif r["status"] != n["status"] or r["target_range"] != n["target_range"]:
                print(f"| {path} | {r['target']} | {r['model_value']} | {r['target_range']} | {r['status']} | {n['target_range']} | {n['status']} |")
                changed += r["status"] != n["status"]
    print(f"\nVerdicts changed: {changed}")


if __name__ == "__main__":
    main()
