"""Proof for P0 A4: a straight run and a run saved partway then resumed give the same
hashes.  Tree: straight to 60 against saved at 30 and resumed.  Plot: 25 trees, straight
to 20 against saved at 10 and resumed.  Dense plot: stopped hard after a tree has died
since the last checkpoint, then resumed: that tree has to die again, and needs its history
back.  Heavy for the plot, so run it when nothing else is running.  Writes
out/bench/p0/checkpoint_proof.txt.

    python tools/proof_checkpoint.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
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


def stopped_hard_after_a_death(command: list, out: Path) -> int:
    """Run a plot, and stop it at once when a tree has died since its first checkpoint.
    Returns how many trees had died since."""
    free = free_gb()
    if free - PEAK_GB < FLOOR_GB:
        sys.exit(f"STOP: {free:.2f} GB free; this needs about {FLOOR_GB + PEAK_GB:.2f} GB (PROTOCOL.md section 6)")
    out.mkdir(parents=True)
    p = subprocess.Popen([sys.executable] + [str(a) for a in command] + ["--out", str(out)], cwd=str(ROOT),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def finished():
        return len(list(out.glob("tree_*/stats.json")))

    while not (out / "checkpoint.pkl").exists() and p.poll() is None:
        time.sleep(0.05)
    at_checkpoint = finished()
    while finished() == at_checkpoint and p.poll() is None:
        time.sleep(0.05)
    since = finished() - at_checkpoint
    if p.poll() is None:
        if sys.platform == "win32":   # a venv's python.exe is a launcher: stop its child too
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            p.kill()
    p.wait()
    return since


def stopped_inside_a_checkpoint(command: list, out: Path, year: int) -> bool:
    """Run a plot, and stop it at once when trees have spilled for this year's checkpoint.
    Returns whether the stop did land inside: the newest pickle can't be this year's yet."""
    free = free_gb()
    if free - PEAK_GB < FLOOR_GB:
        sys.exit(f"STOP: {free:.2f} GB free; this needs about {FLOOR_GB + PEAK_GB:.2f} GB (PROTOCOL.md section 6)")
    out.mkdir(parents=True)
    p = subprocess.Popen([sys.executable] + [str(a) for a in command] + ["--out", str(out)], cwd=str(ROOT),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pattern = f"tree_*/history/history_{year:03d}.npz"
    while not list(out.glob(pattern)) and p.poll() is None:
        time.sleep(0.005)
    if p.poll() is None:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            p.kill()
    p.wait()
    pickle_time = (out / "checkpoint.pkl").stat().st_mtime
    return any(f.stat().st_mtime > pickle_time for f in out.glob(pattern))


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

    dense = ["tools/plot.py", "--trees", 2, "--dense-start", 10000, "--mode", "natural", "--seed", 2, "--no-mesh", "--years", 10]   # not seed 1: a resume once wrote the wrong seed as a label
    run(dense + ["--out", WORK / "dense_straight"])
    since = stopped_hard_after_a_death(dense, WORK / "dense_stopped")
    run(["tools/plot.py", "--no-mesh", "--years", 10, "--resume", "--out", WORK / "dense_stopped"])
    d_ok, d_n, d_diff = same(WORK / "dense_straight", WORK / "dense_stopped")
    d_word = ("IDENTICAL" if d_ok else "DIFFERENT") if since > 0 else "VOID: no tree died after the checkpoint"
    d_ok = d_ok and since > 0

    run(dense + ["--checkpoint-every", 0, "--out", WORK / "dense_none"])
    n_ok, n_n, n_diff = same(WORK / "dense_straight", WORK / "dense_none")

    inside = stopped_inside_a_checkpoint(dense + ["--checkpoint-every", 3], WORK / "dense_inside", 6)
    run(["tools/plot.py", "--no-mesh", "--years", 10, "--resume", "--checkpoint-every", 0, "--out", WORK / "dense_inside"])
    i_ok, i_n, i_diff = same(WORK / "dense_straight", WORK / "dense_inside")
    i_word = ("IDENTICAL" if i_ok else "DIFFERENT") if inside else "VOID: the stop didn't land inside the checkpoint"
    i_ok = i_ok and inside

    lines = [f"Dense plot, stopped hard with {since} trees dead since its last checkpoint, then resumed: {d_word} ({d_n} files) {d_diff[:10]}",
             f"Dense plot, no checkpoints at all, against every 5 years: {'IDENTICAL' if n_ok else 'DIFFERENT'} ({n_n} files) {n_diff[:10]}",
             f"Dense plot, stopped hard inside its year-6 checkpoint, then resumed with no more: {i_word} ({i_n} files) {i_diff[:10]}",
             f"Tree, straight to 60 against saved at 30 and resumed: {'IDENTICAL' if t_ok else 'DIFFERENT'} ({t_n} files) {t_diff[:10]}",
             f"Plot, 25 trees, straight to 20 against saved at 10 and resumed: {'IDENTICAL' if p_ok else 'DIFFERENT'} ({p_n} files) {p_diff[:10]}"]
    print("\n".join(lines))
    (ROOT / "out" / "bench" / "p0" / "checkpoint_proof.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.exit(0 if t_ok and p_ok and d_ok and n_ok and i_ok else 1)


if __name__ == "__main__":
    main()
