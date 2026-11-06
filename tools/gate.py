"""The adoption gate's numbers (PROTOCOL.md section 9), for two ensembles on one machine.

    python tools/gate.py out/bench/ensemble/base out/bench/ensemble/option --kind option --ref master
    python tools/gate.py out/bench/ensemble/base out/bench/ensemble/fix --kind correction --ref master

Refuses to compare ensembles on different machines, with too few seeds or different seeds, and
for a new option, on different code.  A run from the node's early code has no commit in its
manifest: state it with --base-code or --option-code, after checking the files (DECISIONS.md row 35).

For every approved target with a band, at every age: the ensemble verdict on each side, from the
scorecard's own evaluate_ensemble, and whether the ensemble mean's distance from its band changed
by more than 2 standard errors of the paired difference.  Then the gate's questions:
  - new option: no PASS to FAIL; no target significantly worse, on a rerun if one looks it (below);
    at least one target improved by more than 2 standard errors.
  - correction of a documented error: needn't improve anything.  If it makes a target significantly
    worse, or takes one from PASS to FAIL, it isn't reverted: it goes in QUESTIONS.md.
  - a target scored on one side and not on the other stops the comparison until someone looks.

If a sourced new option looks significantly worse on a row, rerun the option and the baseline once
on new seeds, with no change between.  It's blocked only if the same row is worse again (the maintainer,
2026-11-06): with this many rows, some will cross 2 standard errors by chance.

Only the numbers.  The gate also asks for a published basis, passing tests and the three checkers.
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
from scorecard import (ensemble_folders, evaluate_ensemble, evaluate_targets, load_approved_targets, load_run_data)  # noqa: E402

REQUIRED_SEEDS = {"tree": 20, "plot": 5}   # PROTOCOL.md section 2
CAVEAT = ("With this many rows, some cross 2 standard errors by chance, and linked metrics move together, "
          "so a lone improvement is a reason to look further, not a result.")


def manifest_of(run: dict) -> dict:
    doc = run["plot_data"] if run.get("is_plot") else run.get("tree_stats", {})
    return doc.get("run_manifest") or {}


def machine_of(run: dict) -> tuple:
    m = manifest_of(run).get("machine") or {}
    return m.get("computer"), m.get("cpu"), m.get("numpy_openblas_kernel"), m.get("scipy_openblas_kernel")


def code_of(run: dict) -> tuple:
    m = manifest_of(run)
    return m.get("git_commit"), m.get("uncommitted_sha256")


class Refused(SystemExit):
    pass


def check_like_for_like(base: list, option: list, names: tuple, kind: str, base_code: str | None, option_code: str | None) -> dict:
    """Same seeds, enough of them, one machine; for a new option, one code version.  Refuses otherwise."""
    if not base or not option:
        raise Refused("an ensemble has no runs")
    if sorted(names[0]) != sorted(names[1]):
        raise Refused(f"the ensembles have different seeds: {sorted(set(names[0]) ^ set(names[1]))}")
    what = "plot" if base[0].get("is_plot") else "tree"
    if len(base) < REQUIRED_SEEDS[what]:
        raise Refused(f"{len(base)} seeds; PROTOCOL.md section 2 asks for {REQUIRED_SEEDS[what]} for a {what}")
    machines = {machine_of(r) for r in base + option}
    if len(machines) != 1 or None in next(iter(machines))[:2]:
        raise Refused(f"not one known machine: {sorted(machines, key=str)}")
    codes_base, codes_option = {code_of(r) for r in base}, {code_of(r) for r in option}
    if len(codes_base) != 1 or len(codes_option) != 1:
        raise Refused(f"more than one code version inside an ensemble: {codes_base} {codes_option}")
    a, b = next(iter(codes_base)), next(iter(codes_option))
    if base_code:
        a = (base_code, a[1])
    if option_code:
        b = (option_code, b[1])
    if kind == "option":
        if a[0] is None or b[0] is None:
            raise Refused("a manifest has no commit: state it with --base-code or --option-code")
        if a != b:
            raise Refused(f"a new option is tested on the baseline's code; these differ: {a} {b}")
    return {"machine": next(iter(machines)), "base_code": a, "option_code": b, "what": what}


def per_seed(targets: dict, runs: list, ages: list) -> list:
    """For each run: {target row: (value, band)}, for rows with a number and a band, not INFO."""
    out = []
    for run in runs:
        rows = evaluate_targets(targets, [run], ages=ages)[0]
        out.append({r["target"]: (r["value"], r["band"]) for r in rows
                    if r.get("value") is not None and r.get("band") is not None and r["status"] != "INFO"})
    return out


def compare(base: list, option: list, base_verdicts: dict, option_verdicts: dict) -> tuple:
    """Rows for every target both sides scored, and the targets one side scored and the other didn't."""
    names = []
    for side in (base, option):
        for seed in side:
            for t in seed:
                if t not in names:
                    names.append(t)
    rows, unscored = [], []
    for t in names:
        if sum(t in s for s in base) != len(base) or sum(t in s for s in option) != len(option):
            unscored.append(f"{t}: {sum(t in s for s in base)} of {len(base)} baseline seeds, {sum(t in s for s in option)} of {len(option)} option seeds")
            continue
        lo, hi = base[0][t][1]
        b_values, o_values = [s[t][0] for s in base], [s[t][0] for s in option]
        move = band_move(b_values, o_values, lo, hi)
        rows.append({"target": t, "n": len(base), "lo": lo, "hi": hi,
                     "base_mean": statistics.fmean(b_values), "option_mean": statistics.fmean(o_values),
                     "base_verdict": base_verdicts.get(t), "option_verdict": option_verdicts.get(t),
                     "difference": move["mean"], "se": move["se"], "moved": move["moved"]})
    return rows, unscored


def decide(rows: list, unscored: list, kind: str) -> dict:
    """The gate's numeric questions.  'ok' is whether these items let it through."""
    pass_to_fail = [r["target"] for r in rows if r["base_verdict"] == "PASS" and r["option_verdict"] == "FAIL"]
    further = [r["target"] for r in rows if r["moved"] == "further"]
    closer = [r["target"] for r in rows if r["moved"] == "closer"]
    if kind == "correction":
        ok = not unscored
        note = "A correction needn't improve anything."
        if further or pass_to_fail:
            note += " It makes targets significantly worse or takes them to FAIL: don't revert it, put it in QUESTIONS.md, because it may be exposing a hidden second error."
    else:
        ok = not unscored and not pass_to_fail and not further and bool(closer)
        note = "A new option must improve at least one target by more than 2 standard errors, and make none significantly worse."
        if further:
            note += " Rows look worse: rerun the option and the baseline once on new seeds, with no change between. It's blocked only if the same row is worse again."
    if unscored:
        note += " A target is scored on one side and not the other: look at why before going on."
    return {"pass_to_fail": pass_to_fail, "further": further, "closer": closer, "unscored": unscored, "ok": ok, "note": note}


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("base")
    ap.add_argument("option")
    ap.add_argument("--kind", choices=("option", "correction"), required=True, help="a new option added to improve the fit, or a correction of a documented error")
    ap.add_argument("--ref", required=True, help="git ref for reference/targets.yaml; say which, because the bands differ")
    ap.add_argument("--age", action="append", type=int, default=None)
    ap.add_argument("--base-code", default=None, help="the baseline's commit, if its manifests have none")
    ap.add_argument("--option-code", default=None, help="the option's commit, if its manifests have none")
    a = ap.parse_args(argv)
    ages = a.age or [20, 30, 40, 50, 60]
    targets = load_approved_targets(a.ref)
    folders = ensemble_folders(Path(a.base)), ensemble_folders(Path(a.option))
    base_runs, option_runs = [load_run_data(str(d)) for d in folders[0]], [load_run_data(str(d)) for d in folders[1]]
    like = check_like_for_like(base_runs, option_runs, ([d.name for d in folders[0]], [d.name for d in folders[1]]), a.kind, a.base_code, a.option_code)
    verdicts = [{r["target"]: r["status"] for r in evaluate_ensemble(targets, runs, ages)} for runs in (base_runs, option_runs)]
    rows, unscored = compare(per_seed(targets, base_runs, ages), per_seed(targets, option_runs, ages), verdicts[0], verdicts[1])
    print(f"{len(folders[0])} paired {like['what']} seeds; machine {like['machine'][0]}, {like['machine'][1]}; targets at {a.ref}; {a.kind}")
    print(f"Code: baseline {like['base_code']}, option {like['option_code']}\n")
    print("| Target | Seeds | Band | Baseline | Option | Difference | SE | Verdicts | Moved |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| `{r['target']}` | {r['n']} | {r['lo']:.2f}-{r['hi']:.2f} | {r['base_mean']:.3f} | {r['option_mean']:.3f} | {r['difference']:+.3f} | {r['se']:.3f} | "
              f"{r['base_verdict']} to {r['option_verdict']} | {r['moved']} |")
    d = decide(rows, unscored, a.kind)
    print(f"\nPASS to FAIL: {d['pass_to_fail'] or 'none'}")
    print(f"Significantly worse: {d['further'] or 'none'}")
    print(f"Improved: {d['closer'] or 'none'}")
    print(f"Scored on one side only: {d['unscored'] or 'none'}")
    print(f"\n{d['note']}\n{CAVEAT}")
    print(f"These items: {'pass' if d['ok'] else 'FAIL'}. The gate also needs a published basis, passing tests and the three checkers.")
    return 0 if d["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
