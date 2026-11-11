"""The switch-off rule: do two sets of runs match bit for bit?

    python tools/switch_off.py <first folder> <second folder>
    python tools/switch_off.py out/bench/ensemble/control out/bench/ensemble/arm --seeds 1,2 --switched shedding.log_limbs

The plan of 2026-11-11 (reports/design/2026-11-11_plan.md, section 4) asks it of every model switch while the switch is
off, and of the logs while every log is on: "Plots seeds 1-2 and trees seeds 1-3 match the control bit for bit."

Each folder is what 'tools/forest.py plots' wrote (plot_<seed>/), what 'tools/tree_table.py run' wrote (<seed>_stand/),
or both.  Runs are paired by name.  It prints what it compared and ends with IDENTICAL (exit 0) or DIFFERENT (exit 1).
It only reads, and needs no package beyond Python's own.

What has to be the same value in every place, a number to its last bit (and 1 is not 1.0):

    plot_<seed>/plot.json      all of it but what is left out below: the yearly stand measures, the damage log, and each
                               year's count of trees and of crown and root nodes
    plot_<seed>/trees_*.json   for each year both sides have: the same trees in the same order, and every header item
                               and every column both sides have
    <seed>_stand/stats.json    all of it but what is left out below
    <seed>_stand/tree.json     every item both sides have; inside "yearly" and "snapshots", every key both have
    any other .json file       all of it, where both sides have the file (stand_log.json, limbs.json)

Left out, because a run says it about itself and not about the trees:

    run_manifest, runtime_s, peak_mb, timings, peak_memory, files_mb      the commit, the machine, time and memory, at
                               any depth (tools/golden.py's METADATA_KEYS); and manifest.json, which holds only those
    year_log's 2nd and 3rd numbers     a plot year's seconds and peak memory
    a tree list's "run"        the commit and the settings asked for
    options that may differ    log.* (the records kept beside a run, treegen/logs.py), any name given with --switched,
                               and an option only one side has that is off there (a switch added since, left off).
                               Every such option is printed.  Any other option that differs counts as a difference

What only one side has (a file, a tree list's year, a column a newer tool writes) is listed, not compared.  So compare
runs with the same logs on, or a run against a commit from before the logs: a tree list holds a dead tree's wood only
when log.stand was on, and with it on one side only those columns differ.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# as tools/golden.py has them (tests/test_switch_off.py holds the two together); not imported, so this needs no numpy
METADATA_KEYS = frozenset({"run_manifest", "timings", "peak_memory", "peak_mb", "runtime_s", "files_mb"})
LEFT_OUT = ("Left out: " + ", ".join(sorted(METADATA_KEYS)) + " at any depth; manifest.json; each plot year's seconds and peak memory in year_log; "
            "a tree list's \"run\"; and the options printed above as allowed to differ.")
_MISSING = object()


def canonical(o) -> str:
    """One way of writing a JSON value, so two are the same only if every digit is."""
    return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=True)


def sha(o) -> str:
    return hashlib.sha256(canonical(o).encode("utf-8")).hexdigest()


def strip(o):
    """Without what a run says about itself, at any depth."""
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in METADATA_KEYS}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def where(a, b, path: str = "", out: list | None = None, limit: int = 6) -> list:
    """Where two JSON values differ: up to `limit` places, each as a path and the two values."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if len(out) >= limit:
                break
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in the {'second' if k not in a else 'first'}")
            else:
                where(a[k], b[k], f"{path}/{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: {len(a)} items against {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            if len(out) >= limit:
                break
            where(x, y, f"{path}[{i}]", out, limit)
    elif canonical(a) != canonical(b):
        out.append(f"{path}: {canonical(a)[:48]} against {canonical(b)[:48]}")
    return out


def _show(v) -> str:
    return "absent" if v is _MISSING else canonical(v)


def options_apart(a: dict, b: dict, switched=()) -> tuple:
    """(allowed, real): the options whose values differ, as 'name: first against second'.  Allowed: log.*, a name in
    `switched`, and an option only one side has that is off there.  Real: every other."""
    allowed, real = [], []
    for name in sorted(set(a) | set(b)):
        va, vb = a.get(name, _MISSING), b.get(name, _MISSING)
        if va is not _MISSING and vb is not _MISSING and canonical(va) == canonical(vb):
            continue
        off_on_one_side = (va is _MISSING and (vb is False or vb is None)) or (vb is _MISSING and (va is False or va is None))
        (allowed if name.startswith("log.") or name in switched or off_on_one_side else real).append(f"{name}: {_show(va)} against {_show(vb)}")
    return allowed, real


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _content(doc: dict) -> dict:
    """A plot.json or a stats.json without its run metadata, its options (compared on their own) and its timings."""
    doc = strip(doc)
    doc.pop("options", None)
    if isinstance(doc.get("year_log"), list):
        # [year, seconds, peak MB, trees, crown nodes, root nodes, crown nodes alive]: tools/forest.py
        doc["year_log"] = [row[:1] + row[3:] if isinstance(row, list) else row for row in doc["year_log"]]
    return doc


def whole_file(name: str, a: dict, b: dict, switched, lines: list) -> bool:
    """plot.json or stats.json: all of it but what is left out.  Adds its lines; True if the same."""
    ca, cb = _content(a), _content(b)
    allowed, real = options_apart(a.get("options") or {}, b.get("options") or {}, switched)
    same = canonical(ca) == canonical(cb)
    if same:
        lines.append(f"  {name}: identical, sha256 {sha(ca)[:16]}")
    else:
        lines.append(f"  {name}: DIFFERS")
        lines.extend(f"    {x}" for x in where(ca, cb))
    if allowed:
        lines.append(f"    options allowed to differ: {'; '.join(allowed)}")
    if real:
        lines.append(f"    options that DIFFER: {'; '.join(real)}")
    return same and not real


def shared_rows(what: str, ra: list, rb: list, problems: list, extra: set) -> int:
    """Rows paired in order: every key both rows have must be the same.  Returns how many values were compared."""
    if len(ra) != len(rb):
        problems.append(f"{what}: {len(ra)} rows against {len(rb)}")
        return 0
    compared = 0
    for i, (x, y) in enumerate(zip(ra, rb)):
        if not isinstance(x, dict) or not isinstance(y, dict):
            compared += 1
            if canonical(x) != canonical(y):
                problems.append(f"{what} row {i}")
            continue
        both = set(x) & set(y)
        extra |= {f"{what}.{k}" for k in set(x) ^ set(y)}
        if not both:
            problems.append(f"{what} row {i}: no key in common")
        bad = sorted(k for k in both if canonical(x[k]) != canonical(y[k]))
        if bad:
            name = x.get("id", x.get("year", x.get("age", i)))
            problems.append(f"{what} {name}: {', '.join(bad[:8])}{' and more' if len(bad) > 8 else ''}")
        compared += len(both)
    return compared


def shared_file(a: dict, b: dict, lists: tuple, skip: tuple = ()) -> tuple:
    """A file of which only what both sides have is compared: every top-level item both have, and inside each list
    named in `lists` every key both sides' rows have.  Returns (problems, what only one side has, values compared)."""
    problems, extra, compared = [], set(), 0
    for k in sorted(set(a) | set(b)):
        if k in skip:
            continue
        if k not in a or k not in b:
            extra.add(k)
        elif k in lists and isinstance(a[k], list) and isinstance(b[k], list):
            compared += shared_rows(k, a[k], b[k], problems, extra)
        else:
            compared += 1
            if canonical(strip(a[k])) != canonical(strip(b[k])):
                problems.append("; ".join(where(strip(a[k]), strip(b[k]), k, limit=3)))
    return problems, extra, compared


def _other_files(pa: Path, pb: Path, special, lines: list) -> bool:
    """Every other .json file: compared whole where both sides have it, listed where one has it."""
    same = True
    fa = {p.name for p in pa.glob("*.json")} - {"manifest.json"}
    fb = {p.name for p in pb.glob("*.json")} - {"manifest.json"}
    for name in sorted((fa | fb) - set(special)):
        if special_list(name):
            continue
        if name in fa and name in fb:
            ca, cb = strip(_load(pa / name)), strip(_load(pb / name))
            if canonical(ca) == canonical(cb):
                lines.append(f"  {name}: identical, sha256 {sha(ca)[:16]}")
            else:
                same = False
                lines.append(f"  {name}: DIFFERS")
                lines.extend(f"    {x}" for x in where(ca, cb))
        else:
            lines.append(f"  {name}: only in the {'first' if name in fa else 'second'}, not compared")
    return same


def special_list(name: str) -> bool:
    return re.fullmatch(r"trees_\d+\.json", name) is not None


def compare_plot(pa: Path, pb: Path, switched, lines: list) -> bool:
    same = whole_file("plot.json", _load(pa / "plot.json"), _load(pb / "plot.json"), switched, lines)
    la = {p.name for p in pa.glob("trees_*.json") if special_list(p.name)}
    lb = {p.name for p in pb.glob("trees_*.json") if special_list(p.name)}
    problems, extra, compared, rows = [], set(), 0, 0
    for name in sorted(la & lb):
        a, b = _load(pa / name), _load(pb / name)
        p, e, c = shared_file(a, b, ("trees",), skip=("run",))
        problems += [f"{name}: {x}" for x in p]
        extra |= e
        compared += c
        rows += len(a.get("trees", []))
    if la & lb:
        years = ", ".join(str(int(n[6:-5])) for n in sorted(la & lb))
        if problems:
            same = False
            lines.append(f"  tree lists: DIFFER in {len(problems)} places")
            lines.extend(f"    {x}" for x in problems[:8])
        else:
            lines.append(f"  tree lists: identical in all {compared} values both sides have, {rows} tree rows over {len(la & lb)} years ({years})")
        if extra:
            lines.append(f"    only one side has, not compared: {', '.join(sorted(extra))}")
    for name in sorted(la ^ lb):
        lines.append(f"  {name}: only in the {'first' if name in la else 'second'}, not compared")
    return _other_files(pa, pb, ("plot.json",), lines) and same


def compare_tree(pa: Path, pb: Path, switched, lines: list) -> bool:
    same = whole_file("stats.json", _load(pa / "stats.json"), _load(pb / "stats.json"), switched, lines)
    if (pa / "tree.json").exists() and (pb / "tree.json").exists():
        problems, extra, compared = shared_file(_load(pa / "tree.json"), _load(pb / "tree.json"), ("yearly", "snapshots"))
        if problems:
            same = False
            lines.append(f"  tree.json: DIFFERS in {len(problems)} places")
            lines.extend(f"    {x}" for x in problems[:8])
        else:
            lines.append(f"  tree.json: identical in all {compared} values both sides have")
        if extra:
            lines.append(f"    only one side has, not compared: {', '.join(sorted(extra))}")
    return _other_files(pa, pb, ("stats.json", "tree.json"), lines) and same


def runs_in(folder: Path) -> dict:
    """name -> folder, for each plot and each single tree under a label's folder."""
    return {p.name: p for p in sorted(folder.iterdir()) if p.is_dir() and re.fullmatch(r"plot_\d+|\d+_stand", p.name)}


def _seed(name: str) -> int:
    return int(name[5:]) if name.startswith("plot_") else int(name.split("_")[0])


def compare(first: Path, second: Path, seeds=None, switched=()) -> tuple:
    """(identical?, lines to print).  seeds: only these, each of which both sides must then have."""
    first, second = Path(first), Path(second)
    ra, rb = runs_in(first), runs_in(second)
    names = sorted(set(ra) | set(rb), key=lambda n: (not n.startswith("plot_"), _seed(n)))
    if seeds is not None:
        names = [n for n in names if _seed(n) in set(seeds)]
    lines = [f"first:  {first}", f"second: {second}", ""]
    counts = {"identical": 0, "differ": 0, "on one side only": 0, "not finished": 0}
    for name in names:
        lines.append(name)
        if name not in ra or name not in rb:
            counts["on one side only"] += 1
            lines.append(f"  only in the {'first' if name in ra else 'second'}")
            continue
        plot = name.startswith("plot_")
        # what each tool writes last
        last = "done.txt" if plot else "manifest.json"
        unfinished = [side for side, p in (("first", ra[name]), ("second", rb[name])) if not (p / last).exists()]
        if unfinished:
            counts["not finished"] += 1
            lines.append(f"  not finished in the {' and the '.join(unfinished)} (no {last})")
            continue
        ok = (compare_plot if plot else compare_tree)(ra[name], rb[name], switched, lines)
        counts["identical" if ok else "differ"] += 1
    same = bool(names) and counts["identical"] == len(names)
    if seeds is not None:
        for s in sorted(set(seeds) - {_seed(n) for n in names}):
            same = False
            lines.append(f"seed {s}: on neither side")
    lines += ["", LEFT_OUT, f"{len(names)} runs: " + ", ".join(f"{v} {k}" for k, v in counts.items()),
              "IDENTICAL" if same else ("DIFFERENT" if names else "DIFFERENT: no runs found")]
    return same, lines


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("first", help="a label's folder: the control")
    ap.add_argument("second", help="a label's folder: the run to hold against it")
    ap.add_argument("--seeds", default=None, help="comma-separated: compare only these seeds; both sides must have each")
    ap.add_argument("--switched", action="append", default=[], metavar="OPTION", help="an option that was set differently on purpose and changes no result; printed, not counted")
    a = ap.parse_args()
    seeds = None if a.seeds is None else [int(x) for x in a.seeds.split(",") if x.strip()]
    same, lines = compare(Path(a.first), Path(a.second), seeds, tuple(a.switched))
    print("\n".join(lines))
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
