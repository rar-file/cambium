"""An ensemble's verdicts at two versions of the targets, side by side, with spread and share.

    python tools/verdict_table.py out/bench/ensemble/base_trees --refs targets-approved master

For when targets have changed but aren't yet approved: it shows which verdicts depend on them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from scorecard import commit_of, ensemble_folders, evaluate_ensemble, load_approved_targets, load_run_data  # noqa: E402


def table(folder: Path, refs: list, ages: list) -> str:
    runs = [load_run_data(str(d)) for d in ensemble_folders(folder)]
    sides = [{r["target"]: r for r in evaluate_ensemble(load_approved_targets(ref), runs, ages)} for ref in refs]
    names = list(sides[-1]) + [t for t in sides[0] if t not in sides[-1]]
    head = ["Target", "Mean +- SD"] + [f"{ref} ({commit_of(ref)}): band, verdict, share inside" for ref in refs]
    lines = [f"**{folder.as_posix()}: {len(runs)} runs**", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for t in names:
        rows = [s.get(t) for s in sides]
        scored = [r for r in rows if r and r["mean"] is not None]
        if not scored:
            continue
        mean = f"{scored[0]['mean']:.3f} +- {scored[0]['sd']:.3f}"
        means = {round(r["mean"], 6) for r in scored}
        cells = []
        for r in rows:
            if r is None:
                cells.append("not in this version")
            elif r["mean"] is None:
                cells.append(f"{r['status']}: {r['notes'][:70]}")
            else:
                cells.append(f"{r['target_range']}, **{r['status']}**, {100 * r['share']:.0f} %" + ("" if len(means) == 1 else f", mean {r['mean']:.3f}"))
        lines.append(f"| `{t}` | {mean} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="+")
    ap.add_argument("--refs", nargs=2, default=["targets-approved", "master"])
    ap.add_argument("--age", action="append", type=int, default=None)
    a = ap.parse_args(argv)
    for f in a.folder:
        print(table(Path(f), a.refs, a.age or [20, 30, 40, 50, 60]))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
