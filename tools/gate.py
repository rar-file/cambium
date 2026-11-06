"""The adoption gate's numbers (PROTOCOL.md section 9), for two ensembles on one machine.

    python tools/gate.py out/bench/ensemble/base out/bench/ensemble/option --kind option --ref master
    python tools/gate.py out/bench/ensemble/base out/bench/ensemble/fix --kind correction --ref master

For every approved target with a band, at every age: the verdict in each ensemble, and whether
the ensemble mean moved towards its band or away from it by more than 2 standard errors of the
paired difference.  Then the gate's three questions:
  - did any target go from PASS to FAIL?
  - did any target get significantly worse (further from its band)?
  - did any target improve (closer to its band)?  A new option must have one; a correction needn't.
    A correction that makes a target significantly worse isn't reverted: it goes in QUESTIONS.md.

Only the numbers.  The gate also asks for a published basis, passing tests and the three checkers.

With many targets and ages, some will pass 2 standard errors by chance alone (about 1 in 20 of
the rows where nothing changed), and linked metrics move together: leaf area and light are one
failure (tools/light_lai_link.py).  So a lone improvement is a reason to look further, not a result.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from paired import band_move  # noqa: E402
from scorecard import (TAG, ensemble_folders, evaluate_targets, load_approved_targets, load_run_data)  # noqa: E402


def per_seed(targets: dict, folder: Path, ages: list) -> dict:
    """seed folder name -> {target row: (value, band)}, for rows with a number and a band."""
    out = {}
    for d in ensemble_folders(folder):
        rows = evaluate_targets(targets, [load_run_data(str(d))], ages=ages)[0]
        out[d.name] = {r["target"]: (r["value"], r["band"], r["status"]) for r in rows if r.get("value") is not None and r.get("band") is not None}
    return out


def verdict(mean: float, lo: float, hi: float) -> str:
    return "PASS" if lo <= mean <= hi else "FAIL"


def compare(base: dict, option: dict) -> tuple:
    """Rows for every target both ensembles scored, on the seeds both have."""
    seeds = sorted(set(base) & set(option))
    if not seeds:
        raise SystemExit("the two ensembles share no seed folder")
    names = []
    for s in seeds:
        for t in base[s]:
            if t not in names:
                names.append(t)
    rows = []
    for t in names:
        paired = [(base[s][t], option[s][t]) for s in seeds if t in base[s] and t in option[s]]
        if len(paired) < 2 or any(b[2] == "INFO" for b, _ in paired):
            continue
        lo, hi = paired[0][0][1]
        b_values, o_values = [p[0][0] for p in paired], [p[1][0] for p in paired]
        move = band_move(b_values, o_values, lo, hi)
        rows.append({"target": t, "n": len(paired), "lo": lo, "hi": hi,
                     "base_mean": statistics.fmean(b_values), "option_mean": statistics.fmean(o_values),
                     "base_verdict": verdict(statistics.fmean(b_values), lo, hi),
                     "option_verdict": verdict(statistics.fmean(o_values), lo, hi),
                     "difference": move["mean"], "se": move["se"], "moved": move["moved"]})
    return rows, seeds


def decide(rows: list, kind: str) -> dict:
    """The gate's three numeric questions.  'ok' is whether these items let it through."""
    pass_to_fail = [r["target"] for r in rows if r["base_verdict"] == "PASS" and r["option_verdict"] == "FAIL"]
    further = [r["target"] for r in rows if r["moved"] == "further"]
    closer = [r["target"] for r in rows if r["moved"] == "closer"]
    if kind == "correction":
        ok = not pass_to_fail
        note = "A correction needn't improve anything." + (" It makes targets significantly worse: don't revert it, put it in QUESTIONS.md." if further else "")
    else:
        ok = not pass_to_fail and not further and bool(closer)
        note = "A new option must improve at least one target by more than 2 standard errors, and make none significantly worse."
    return {"pass_to_fail": pass_to_fail, "further": further, "closer": closer, "ok": ok, "note": note}


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("base")
    ap.add_argument("option")
    ap.add_argument("--kind", choices=("option", "correction"), required=True, help="a new option added to improve the fit, or a correction of a documented error")
    ap.add_argument("--ref", default=TAG, help="git ref for reference/targets.yaml")
    ap.add_argument("--age", action="append", type=int, default=None)
    a = ap.parse_args(argv)
    ages = a.age or [20, 30, 40, 50, 60]
    targets = load_approved_targets(a.ref)
    rows, seeds = compare(per_seed(targets, Path(a.base), ages), per_seed(targets, Path(a.option), ages))
    print(f"{len(seeds)} paired seeds; targets at {a.ref}; {a.kind}\n")
    print("| Target | Band | Baseline | Option | Difference | SE | Verdicts | Moved |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| `{r['target']}` | {r['lo']:.2f}-{r['hi']:.2f} | {r['base_mean']:.3f} | {r['option_mean']:.3f} | {r['difference']:+.3f} | {r['se']:.3f} | "
              f"{r['base_verdict']} to {r['option_verdict']} | {r['moved']} |")
    d = decide(rows, a.kind)
    print(f"\nPASS to FAIL: {d['pass_to_fail'] or 'none'}")
    print(f"Significantly worse: {d['further'] or 'none'}")
    print(f"Improved: {d['closer'] or 'none'}")
    print(f"\n{d['note']}")
    print(f"These items: {'pass' if d['ok'] else 'FAIL'}. The gate also needs a published basis, passing tests and the three checkers.")
    return 0 if d["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
