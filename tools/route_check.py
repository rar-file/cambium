"""Did two routes to the same plot give the same plot?  (Disk review, 2026-11-06.)

    python tools/route_check.py years out/bench/stopped_plots/plot_3 out/bench/ensemble/base_plots/plot_3
    python tools/route_check.py files out/bench/route_check/plot_1 out/bench/ensemble/base_plots/plot_1

years: every yearly plot figure the first run reached, and each tree that died by then.  For a run
that was stopped partway, against a full run.  files: the same hash as the golden runs, every file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from golden import hash_tree  # noqa: E402

RUN_ONLY = {"runtime_s", "peak_mb"}


def compare_years(first: Path, second: Path) -> dict:
    a = json.loads((first / "plot.json").read_text(encoding="utf-8"))
    b = json.loads((second / "plot.json").read_text(encoding="utf-8"))
    last = a["year"]
    wrong, values = [], 0
    by_year = {s["year"]: s for s in b["stats"]}
    for s in a["stats"]:
        if s["year"] > last:
            continue
        for k, v in s.items():
            if k in RUN_ONLY:
                continue
            values += 1
            if by_year[s["year"]].get(k) != v:
                wrong.append(f"year {s['year']} {k}: {v} and {by_year[s['year']].get(k)}")
    # the trees that had died by the first run's last checkpoint
    died, tree_wrong = 0, []
    for k, info in enumerate(a["trees"]):
        removed = info.get("removed") if isinstance(info, dict) else None
        if removed is None or removed > last:
            continue
        died += 1
        name = f"tree_{k:03d}/stats.json"
        pa, pb = json.loads((first / name).read_text(encoding="utf-8")), json.loads((second / name).read_text(encoding="utf-8"))
        if pa["per_year"] != pb["per_year"]:
            tree_wrong.append(name)
    return {"last_year": last, "values": values, "wrong": wrong, "died": died, "tree_wrong": tree_wrong}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("how", choices=("years", "files"))
    ap.add_argument("first")
    ap.add_argument("second")
    a = ap.parse_args(argv)
    first, second = Path(a.first), Path(a.second)
    if a.how == "years":
        r = compare_years(first, second)
        same = not r["wrong"] and not r["tree_wrong"]
        print(f"{first} against {second}: to year {r['last_year']}, {r['values']} plot values, {len(r['wrong'])} differ; "
              f"{r['died']} dead trees' yearly stats, {len(r['tree_wrong'])} differ. {'IDENTICAL' if same else 'DIFFERENT'}")
        for w in (r["wrong"] + r["tree_wrong"])[:8]:
            print(" ", w)
        return 0 if same else 1
    ha, hb = hash_tree(first), hash_tree(hb_path := second)
    differ = sorted(k for k in set(ha) & set(hb) if ha[k] != hb[k])
    only = sorted(set(ha) ^ set(hb))
    print(f"{first} against {hb_path}: {len(set(ha) & set(hb)) - len(differ)} files identical, {len(differ)} differ, {len(only)} in one only. "
          f"{'IDENTICAL' if not differ and not only else 'DIFFERENT'}")
    for k in (differ + only)[:8]:
        print(" ", k)
    return 0 if not differ and not only else 1


if __name__ == "__main__":
    sys.exit(main())
