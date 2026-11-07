"""After a broken top, does the stem keep thickening without its crown?  Each seed is grown twice, the same settings: untouched,
and with the stem taken off just above the crown base at AGE (treegen/damage.py, apply_top_break).  Only reads the model.

    python tools/top_break_check.py run --label X --seeds 20 --age 40 [--set key=json ...]
    python tools/top_break_check.py table X Y
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

E = ROOT / "out" / "bench" / "ensemble"


def one(seed: int, age: int, sets: list, out: Path) -> int:
    from treegen import checkpoint
    from treegen.damage import apply_top_break
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    def build():
        sp, _ = load_species("betula_pendula")
        checkpoint.set_values(sp, sets)
        env, _ = load_environment("sweden_open_field")
        return GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)

    whole, hurt = build(), build()
    rows = []
    broke = None
    for y in range(1, 61):
        if y == age + 1:
            z = (hurt.stats[-1]["crown_base_height_m"] or 1.0) + 0.5
            broke = {"z_m": z, "applied": bool(apply_top_break(hurt, z, y))}
        whole.step()
        hurt.step()
        if y >= age:
            a, b = whole.stats[-1], hurt.stats[-1]
            rows.append({"year": y, "whole_h": a["height_m"], "whole_dbh": a["dbh_cm"], "whole_la": a["leaf_area_m2"],
                         "broken_h": b["height_m"], "broken_dbh": b["dbh_cm"], "broken_la": b["leaf_area_m2"],
                         "broken_fixed": b["carbon"].get("fixed", 0.0)})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"seed": seed, "age": age, "break": broke, "rows": rows}), encoding="utf-8")
    return 0


def run(label: str, seeds: int, first: int, age: int, sets: list) -> int:
    folder = E / label
    extra = [x for v in sets for x in ("--set", v)]
    jobs = [Job(f"seed {s}", [sys.executable, str(Path(__file__).resolve()), "one", "--seed", str(s), "--age", str(age), "--out", str(folder / f"{s}.json"), *extra], folder / f"{s}.json")
            for s in range(first, first + seeds)]
    return run_batch(jobs, 1.2, log=folder / "runs.csv")


def table(labels: list) -> None:
    print("Means over seeds; the stem diameter is wood only. Ring: what the stem added at 1.3 m in the 20 years after the break, broken against untouched.\n")
    print("| Set | Seeds | Break at age | Leaf area just before (m2) | The year after (m2) | At 60, broken (m2) | At 60, untouched (m2) | Height at 60, broken (m) | Untouched (m) | DBH at the break (cm) | DBH at 60, broken | DBH at 60, untouched | Broken stems' DBH gain, share of untouched's |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((E / label).glob("*.json"), key=lambda p: int(p.stem))]
        if not runs:
            continue
        m = lambda f: statistics.fmean(f(r) for r in runs)
        gain = lambda r: (r["rows"][-1]["broken_dbh"] - r["rows"][0]["broken_dbh"]) / max(r["rows"][-1]["whole_dbh"] - r["rows"][0]["whole_dbh"], 1e-9)
        shares = [gain(r) for r in runs]
        print(f"| `{label}` | {len(runs)} | {runs[0]['age']} | {m(lambda r: r['rows'][0]['whole_la']):.1f} | {m(lambda r: r['rows'][1]['broken_la']):.1f} | {m(lambda r: r['rows'][-1]['broken_la']):.1f} | {m(lambda r: r['rows'][-1]['whole_la']):.1f} | "
              f"{m(lambda r: r['rows'][-1]['broken_h']):.1f} | {m(lambda r: r['rows'][-1]['whole_h']):.1f} | {m(lambda r: r['rows'][0]['whole_dbh']):.1f} | {m(lambda r: r['rows'][-1]['broken_dbh']):.1f} | {m(lambda r: r['rows'][-1]['whole_dbh']):.1f} | "
              f"{100 * statistics.fmean(shares):.0f} % ({100 * min(shares):.0f}-{100 * max(shares):.0f}) |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("run", "one", "table"))
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--age", type=int, default=40)
    ap.add_argument("--out")
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args(argv)
    if a.what == "one":
        return one(a.seed, a.age, a.set, Path(a.out))
    if a.what == "run":
        return run(a.label, a.seeds, a.first_seed, a.age, a.set)
    table(a.labels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
