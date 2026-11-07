"""On the node: the four golden runs with settings off and on, compared, the result where tools/node/fetch.sh can reach it.

    tools/node/submit.sh <commit> node_speed_gold tools/speed_node_proof.py node_speed_gold --set speed.compiled_carbon=true ...

Writes out/bench/ensemble/<label>/golden_compare.txt: IDENTICAL or DIFFERENT, with the time and memory table.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import golden  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--only", default=None)
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()
    only = a.only.split(",") if a.only else None
    out = ROOT / "out" / "bench" / "ensemble" / a.label
    out.mkdir(parents=True, exist_ok=True)
    off = golden.record(a.label + "_off", only)
    on = golden.record(a.label + "_on", only, sets=a.set)
    same, lines, table = golden.compare(off, on)
    text = [f"settings on: {a.set}", *lines, "", "| Run | Seconds, off | Seconds, on | Peak MB, off | Peak MB, on |", "|---|---|---|---|---|"]
    text += ["| " + " | ".join(str(x) for x in row) + " |" for row in table]
    text += ["", "IDENTICAL" if same else "DIFFERENT"]
    (out / "golden_compare.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    print("IDENTICAL" if same else "DIFFERENT", flush=True)


if __name__ == "__main__":
    main()
