"""Proof for P0 A4: a straight run and a run saved partway then resumed give the same
hashes.  Tree: straight to 60 against saved at 30 and resumed.  Plot: 25 trees, straight
to 20 against saved at 10 and resumed.  Heavy for the plot, so run it when nothing else
is running.  Writes out/bench/p0/checkpoint_proof.txt.

    python tools/proof_checkpoint.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import FLOOR_GB, free_gb  # noqa: E402
from golden import hash_tree  # noqa: E402

WORK = ROOT / "out" / "bench" / "p0" / "checkpoint_proof"
PEAK_GB = 1.5


def run(args):
    free = free_gb()
    if free - PEAK_GB < FLOOR_GB:
        sys.exit(f"STOP: {free:.2f} GB free; this needs about {FLOOR_GB + PEAK_GB:.2f} GB (PROTOCOL.md section 6)")
    done = subprocess.run([sys.executable] + [str(a) for a in args], cwd=str(ROOT), capture_output=True, text=True)
    if done.returncode != 0:
        sys.exit(f"failed: {args}\n{done.stdout[-800:]}\n{done.stderr[-800:]}")


def same(a: Path, b: Path) -> tuple:
    ha, hb = hash_tree(a), hash_tree(b)
    differ = sorted(k for k in set(ha) | set(hb) if ha.get(k) != hb.get(k))
    return not differ, len(ha), differ


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    tree = ["cli.py", "--stand", "--seed", 1, "--no-mesh", "--no-preview", "--quiet"]
    run(tree + ["--years", 60, "--out", WORK / "tree_straight"])
    run(tree + ["--years", 30, "--save-at", 30, "--out", WORK / "tree_first"])
    run(tree + ["--years", 60, "--resume-state", WORK / "tree_first" / "1_stand" / "states" / "state_030.pkl", "--out", WORK / "tree_resumed"])
    t_ok, t_n, t_diff = same(WORK / "tree_straight" / "1_stand", WORK / "tree_resumed" / "1_stand")

    plot = ["tools/plot.py", "--start-trees", 25, "--mode", "natural", "--seed", 1, "--no-mesh"]
    run(plot + ["--years", 20, "--out", WORK / "plot_straight"])
    run(plot + ["--years", 20, "--save-at", 10, "--out", WORK / "plot_first"])
    run(["tools/plot.py", "--no-mesh", "--years", 20, "--branch-from", WORK / "plot_first" / "state_010", "--out", WORK / "plot_resumed"])
    p_ok, p_n, p_diff = same(WORK / "plot_straight", WORK / "plot_resumed")

    lines = [f"Tree, straight to 60 against saved at 30 and resumed: {'IDENTICAL' if t_ok else 'DIFFERENT'} ({t_n} files) {t_diff[:10]}",
             f"Plot, 25 trees, straight to 20 against saved at 10 and resumed: {'IDENTICAL' if p_ok else 'DIFFERENT'} ({p_n} files) {p_diff[:10]}"]
    print("\n".join(lines))
    (ROOT / "out" / "bench" / "p0" / "checkpoint_proof.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.exit(0 if t_ok and p_ok else 1)


if __name__ == "__main__":
    main()
