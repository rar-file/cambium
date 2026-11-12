"""Tables from the stem-top records and from runs with the thinning switches on.  Only reads saved JSON.

    python tools/stem_top_table.py plots <folder> [--ages 30,45,50,60]
        # <folder>/plot_<seed>/ from 'tools/forest.py plots ... --set log.stem_tops=true': top height on the approved
        # definition and the spread of height, each on highest points and on stem tops, and the trees standing over
        # their stems; each figure worked out again from that age's tree list and held against the year's row
    python tools/stem_top_table.py changed <control folder> <arm folder> [--ages 50,60]
        # <folder>/<seed>_stand/ from 'tools/tree_table.py run': for each seed both have, the first year any figure of
        # stats.json differs and which, the first year one differs that is more than the schedule's own two (the
        # spacing and the leaf area index, which is leaf area times stems), the years the yearly row holds another
        # schedule row, and the changed trees' rows at the ages

What the records are: treegen/logs.py (log.stem_tops).  What the switches are: species block stand (thinning_stays,
thinning_on_stem_top) and GrowthModel._schedule_height.  The note: reports/design/2026-11-12_height_faults.md.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SCHEDULE_ONLY = ("stand_spacing_m", "lai")      # a yearly row's two figures that are the schedule's row itself, not the tree


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _f(v, places: int = 3) -> str:
    return "-" if v is None else f"{v:.{places}f}"


def stems_of(spacing_m) -> int | None:
    """Stems a hectare of a yearly row's hexagonal spacing (GrowthModel.stems_per_ha), to the nearest 5: the row keeps the
    spacing to 0.001 m, which is the schedule's own figure to within 1."""
    return None if not spacing_m else 5 * round(2.0 * 10000.0 / (math.sqrt(3.0) * spacing_m * spacing_m) / 5.0)


def from_list(doc: dict) -> dict:
    """A tree list's living trees read as the year's row of stem_log reads them (treegen/logs.py stem_top_row)."""
    from treegen import logs

    trees = [t for t in doc["trees"] if t["alive"]]
    d = [t["dbh_cm"] or 0.0 for t in trees]
    return logs.stem_top_row(doc["plot_year"], d, [t["height_m"] for t in trees], [t["stem_top_m"] for t in trees], doc["area_m2"])


def plots(folder: Path, ages: list) -> int:
    print("| Plot (seed) | Age | Trees | Top height, approved: highest points; stem tops; difference, m | Height SD: highest points; stem tops; difference, m "
          "| Trees more than 0.3 m over their stem (most) | Tree list gives the same |")
    print("|---|---|---|---|---|---|---|")
    bad = 0
    for d in sorted(folder.glob("plot_*"), key=lambda p: int(p.name[5:])):
        if not (d / "stem_log.json").exists():
            print(f"{d.name}: no stem_log.json (run with --set log.stem_tops=true)")
            bad += 1
            continue
        rows = {r["year"]: r for r in _load(d / "stem_log.json")["rows"]}
        for age in ages:
            r = rows.get(age)
            if r is None:
                continue
            lst = d / f"trees_{age:03d}.json"
            same = "no list"
            if lst.exists():
                again = from_list(_load(lst))
                same = "yes" if again == r else "NO"
                bad += again != r
            top, stem, sd, sd_stem = r["top_height_approved_m"], r["top_height_approved_stem_m"], r["height_sd_m"], r["height_sd_stem_m"]
            share = 100.0 * r["trees_over"] / r["trees"] if r["trees"] else 0.0
            print(f"| {d.name[5:]} | {age} | {r['trees']} | {_f(top)}; {_f(stem)}; {'-' if top is None or stem is None else f'{top - stem:+.3f}'} "
                  f"| {_f(sd)}; {_f(sd_stem)}; {'-' if sd is None or sd_stem is None else f'{sd - sd_stem:+.3f}'} "
                  f"| {r['trees_over']}, {share:.1f} % ({_f(r['over_most_m'], 2)} m) | {same} |")
    return 1 if bad else 0


def first_change(a: list, b: list) -> tuple:
    """(first year any figure of two runs' yearly rows differs, the names that differ that year, the first year a name other
    than SCHEDULE_ONLY differs, the names that year); None and [] where nothing does.  Rows are paired by year."""
    rows_b = {r["year"]: r for r in b}
    any_year = tree_year = None
    any_keys, tree_keys = [], []
    for ra in a:
        rb = rows_b.get(ra["year"])
        if rb is None:
            continue
        keys = sorted(k for k in set(ra) | set(rb) if json.dumps(ra.get(k), sort_keys=True) != json.dumps(rb.get(k), sort_keys=True))
        if keys and any_year is None:
            any_year, any_keys = ra["year"], keys
        more = [k for k in keys if k not in SCHEDULE_ONLY]
        if more and tree_year is None:
            tree_year, tree_keys = ra["year"], more
            break
    return any_year, any_keys, tree_year, tree_keys


def row_years(a: list, b: list) -> str:
    """The years in which two runs' yearly rows hold a different schedule row, as 'years: control; arm' in stems a hectare."""
    rows_b = {r["year"]: r for r in b}
    spans = []
    for ra in a:
        rb = rows_b.get(ra["year"])
        if rb is None:
            continue
        pair = (stems_of(ra.get("stand_spacing_m")), stems_of(rb.get("stand_spacing_m")))
        if pair[0] == pair[1]:
            continue
        if spans and spans[-1][1] == ra["year"] - 1 and spans[-1][2] == pair:
            spans[-1][1] = ra["year"]
        else:
            spans.append([ra["year"], ra["year"], pair])
    return ", ".join(f"{y0 if y0 == y1 else f'{y0}-{y1}'}: {p[0]}; {p[1]}" for y0, y1, p in spans) or "none"


def changed(control: Path, arm: Path, ages: list) -> int:
    names = sorted({p.name for p in control.glob("*_stand")} & {p.name for p in arm.glob("*_stand")}, key=lambda n: int(n.split("_")[0]))
    print(f"control: {control}\narm:     {arm}\n")
    print("| Seed | Any figure of stats.json | The tree itself (more than the schedule's own spacing and leaf area index) "
          "| Years the yearly row holds another schedule row: control; arm, stems/ha |")
    print("|---|---|---|---|")
    moved = []
    for name in names:
        a, b = _load(control / name / "stats.json")["per_year"], _load(arm / name / "stats.json")["per_year"]
        year, keys, tree_year, tree_keys = first_change(a, b)
        seed = name.split("_")[0]
        if year is None:
            print(f"| {seed} | the same in all {len(a)} years | the same | none |")
            continue
        moved.append((seed, a, b, arm / name))
        tree = "the same" if tree_year is None else f"from year {tree_year}: {', '.join(tree_keys[:6])}{' and more' if len(tree_keys) > 6 else ''}"
        print(f"| {seed} | from year {year}: {', '.join(keys[:6])}{' and more' if len(keys) > 6 else ''} | {tree} | {row_years(a, b)} |")
    print(f"\n{len(names)} seeds on both sides, {len(moved)} changed: {', '.join(s for s, *_ in moved) or 'none'}")
    if moved:
        print("\nEach cell: control; arm.  The stem's top is the arm's own (tree.json, log.stem_tops), where it kept one.")
        print("\n| Seed | Age | Height, m | Stem top (arm), m | DBH, wood, cm | Schedule row, stems/ha | LAI | Leaf area, m2 | Crown base, m | Lowest live branch, m |")
        print("|---|---|---|---|---|---|---|---|---|---|")
    for seed, a, b, folder in moved:
        tops = {}
        if (folder / "tree.json").exists():
            tops = {r["year"]: r.get("stem_top_m") for r in _load(folder / "tree.json")["yearly"]}
        ra, rb = {r["year"]: r for r in a}, {r["year"]: r for r in b}
        for age in ages:
            if age not in ra or age not in rb:
                continue
            x, y = ra[age], rb[age]

            def pair(key, places=2):
                return f"{_f(x.get(key), places)}; {_f(y.get(key), places)}"

            print(f"| {seed} | {age} | {pair('height_m')} | {_f(tops.get(age), 2)} | {pair('dbh_cm')} | {stems_of(x.get('stand_spacing_m'))}; {stems_of(y.get('stand_spacing_m'))} "
                  f"| {pair('lai')} | {pair('leaf_area_m2', 1)} | {pair('crown_base_height_m')} | {pair('lowest_live_branch_m')} |")
    return 0


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="what", required=True)
    p = sub.add_parser("plots")
    p.add_argument("folder")
    p.add_argument("--ages", default="30,45,50,60")
    c = sub.add_parser("changed")
    c.add_argument("control")
    c.add_argument("arm")
    c.add_argument("--ages", default="50,60")
    a = ap.parse_args(argv)
    ages = [int(x) for x in a.ages.split(",") if x.strip()]
    if a.what == "plots":
        return plots(Path(a.folder), ages)
    return changed(Path(a.control), Path(a.arm), ages)


if __name__ == "__main__":
    sys.exit(main())
