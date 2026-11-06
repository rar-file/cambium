"""A species' accuracy, in one place: is its file complete, where do its values come from, and how
many of its targets does a saved ensemble pass?  This wraps tools/scorecard.py and doesn't change it.

    python tools/species_report.py                                   # every species in species/, values only
    python tools/species_report.py --species betula_pendula --ensemble out/bench/ensemble/base_trees
    python tools/species_report.py --species path/to/new.yaml --reference path/to/folder --ensemble runs --age 10
    python tools/species_report.py --write-template                  # species/_template.yaml from the schema and birch
    python tools/species_report.py --species new_species --init-labels   # every value VERIFY, to start from

What belongs to a species, for a species called <name>:

    species/<name>.yaml              its values
    reference/<name>/labels.yaml     where each value came from (treegen/species_schema.py)
    reference/<name>/targets.yaml    what it must measure up to, in the form of reference/targets.yaml
    reference/<name>/accuracy.yaml   optional: read the targets elsewhere (birch's stay in reference/targets.yaml)

A target in tools/scorecard.py's list is scored there.  Any other target can name a saved 'metric' (a key of a
year's record in stats.json or plot.json) and a 'target_range', and is scored here.
"""
from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import yaml  # noqa: E402

import scorecard  # noqa: E402
from treegen import species_schema as schema  # noqa: E402

SPECIES_DIR = ROOT / "species"
DEFAULT_AGES = (50, 60)
LABEL_RANK = {"sourced": 0, "TUNED": 1, "VERIFY": 2}


def species_files() -> list:
    return sorted(p for p in SPECIES_DIR.glob("*.yaml") if not p.name.startswith("_"))


def species_path(name: str) -> Path:
    p = Path(name)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return p
    p = SPECIES_DIR / f"{name}.yaml"
    if not p.exists():
        raise SystemExit(f"no species file for {name!r} in {SPECIES_DIR}")
    return p


def load_targets(folder: Path, name: str) -> tuple:
    """(targets, where they came from, approved?).  A pointer file reads them at a git ref; otherwise
    reference/<name>/targets.yaml, approved if a tag targets-approved-<name> holds it."""
    pointer = folder / "accuracy.yaml"
    if pointer.exists():
        p = yaml.safe_load(pointer.read_text(encoding="utf-8"))
        file, ref = p["targets_file"], p["git_ref"]
    else:
        file, ref = (folder / "targets.yaml").resolve(), f"targets-approved-{name}"
        try:
            file = file.relative_to(ROOT).as_posix()
        except ValueError:
            file = None
    if file is not None:
        proc = subprocess.run(["git", "show", f"{ref}:{file}"], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
        if proc.returncode == 0:
            return yaml.safe_load(proc.stdout), f"{file} at {ref}", True
    local = folder / "targets.yaml"
    if local.exists():
        return yaml.safe_load(local.read_text(encoding="utf-8")), f"{local} (working copy, not approved)", False
    return None, f"no targets in {folder}", False


def score_metric(name: str, item: dict, runs: list, ages: list) -> list:
    """A target naming a saved value: the ensemble mean against its range, at each age."""
    rows = []
    lo, hi = item["target_range"]
    for age in ages:
        values = []
        for run in runs:
            if scorecard.applicability(item, run, age)[0]:
                continue
            rec = scorecard.plot_stat(run, age) if run["is_plot"] else scorecard.tree_record(run, age)
            if rec and rec.get(item["metric"]) is not None:
                values.append(float(rec[item["metric"]]))
        row = {"target": f"{name} (age {age})", "mean": None, "sd": None, "seeds": len(values), "target_range": f"{lo:g} to {hi:g}",
               "status": "NOT APPLICABLE", "share": None, "source": item.get("source"), "notes": ""}
        if values:
            mean = statistics.fmean(values)
            status = "INFO" if item.get("scoring") == "info" else ("PASS" if lo <= mean <= hi else "FAIL")
            row.update(mean=mean, sd=statistics.stdev(values) if len(values) > 1 else 0.0, status=status,
                       share=sum(lo <= v <= hi for v in values) / len(values))
        rows.append(row)
    return rows


def score_targets(targets: dict, folders: list, ages: list) -> tuple:
    """Rows for every target over each ensemble in turn, and the number of runs.  Targets naming a metric
    are scored here, the rest by the scorecard.  With several ensembles a target scored on two of them
    counts for each, with the ensemble's name; one it applies to in neither is listed once."""
    rows, n_runs = [], 0
    metric_items = {name: item for name, item in scorecard.flatten_targets(targets) if "metric" in item}
    for folder in folders:
        runs = [scorecard.load_run_data(str(d)) for d in scorecard.ensemble_folders(Path(folder))]
        if not runs:
            raise SystemExit(f"no runs in {folder}")
        n_runs += len(runs)
        got = [r for r in scorecard.evaluate_ensemble(targets, runs, ages) if base_name(r["target"]) not in metric_items]
        for name, item in metric_items.items():
            got += score_metric(name, item, runs, ages)
        rows.append((Path(folder).name, got))
    if len(rows) == 1:
        return rows[0][1], n_runs
    scored = {base_name(r["target"]) for _, got in rows for r in got if r["mean"] is not None}
    out, seen = [], set()
    for tag, got in rows:
        for r in got:
            name = base_name(r["target"])
            if name in scored and r["mean"] is not None:
                age = age_of(r["target"])
                out.append({**r, "target": f"{name} [{tag}]" + (f" (age {age})" if age is not None else "")})
            elif name not in scored and r["target"] not in seen:
                seen.add(r["target"])
                out.append(r)
    return out, n_runs


def base_name(target: str) -> str:
    return re.sub(r" \(age \d+\)$", "", target)


def age_of(target: str) -> int | None:
    m = re.search(r" \(age (\d+)\)$", target)
    return int(m.group(1)) if m else None


def value_counts(labels: dict) -> dict:
    c = {"values": len(labels), "sourced": 0, "checked": 0, "TUNED": 0, "VERIFY": 0, "changed": 0}
    for lab in labels.values():
        c[lab.status] = c.get(lab.status, 0) + 1
        c["checked"] += lab.status == "sourced" and lab.checked == "page"
        c["changed"] += lab.changed
    return c


def target_verdicts(rows: list) -> dict:
    """target -> its statuses at each age scored.  A target passes only if it passes at every age."""
    out = {}
    for r in rows:
        if r["status"] in ("PASS", "FAIL", "INFO"):
            out.setdefault(base_name(r["target"]), []).append(r["status"])
    return out


def summary_line(name: str, counts: dict, rows: list | None, n_runs: int, ages: list, approved: bool) -> str:
    values = f"{counts['sourced']} of {counts['values']} values sourced, {counts['TUNED']} tuned, {counts['VERIFY']} unchecked"
    if rows is None:
        return f"{name}: no runs scored; {values}."
    verdicts = target_verdicts(rows)
    scored = {k: v for k, v in verdicts.items() if "INFO" not in v}
    passed = sum(all(s == "PASS" for s in v) for v in scored.values())
    ages_txt = " and ".join(str(a) for a in ages)
    note = "" if approved else " (targets not approved)"
    return (f"{name}: {passed} of {len(scored)} scored targets pass at ages {ages_txt}, over {n_runs} runs{note}; "
            f"{sum(s == 'PASS' for v in scored.values() for s in v)} of {sum(len(v) for v in scored.values())} age checks pass; {values}.")


def print_targets(rows: list, ages: list) -> None:
    head = " | ".join(f"At {a}" for a in ages)
    print(f"| Target | {head} | Band | Verdict | Share of seeds inside |")
    print("|---|" + ":---:|" * len(ages) + ":---:|:---:|:---:|")
    by_name = {}
    for r in rows:
        by_name.setdefault(base_name(r["target"]), []).append(r)
    skipped = []
    for name, group in by_name.items():
        if all(r["mean"] is None for r in group):
            skipped.append(name)
            continue
        at = {age_of(r["target"]): r for r in group}
        cells = [f"{at[a]['mean']:.2f}" if a in at and at[a]["mean"] is not None else "-" for a in ages]
        scored = [r for r in group if r["mean"] is not None]
        # a target can set its own ages (stand density at 45 and 67, as its source measured)
        verdict = ", ".join(r["status"] if age_of(r["target"]) in ages else f"{r['status']} at {age_of(r['target'])}: {r['mean']:.0f}" for r in scored)
        share = ", ".join(f"{100 * r['share']:.0f} %" for r in scored)
        print(f"| `{name}` | {' | '.join(cells)} | {scored[0]['target_range']} | {verdict} | {share} |")
    if skipped:
        print(f"\nNot scored on these runs ({len(skipped)}): " + ", ".join(f"`{s}`" for s in skipped))


def report(path: Path, folder: Path, ensembles: list, ages: list) -> int:
    name = path.stem
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    check = schema.validate(raw)
    label_file = schema.load_labels(folder / "labels.yaml")
    labels = schema.read_labels(raw, text, label_file)
    problems = schema.check_labels(raw, label_file)
    counts = value_counts(labels)
    title = (raw.get("species") or {}).get("scientific_name", name) if isinstance(raw, dict) else name
    print(f"## {title} ({name})\n")
    print(f"Species file: {len(check.errors)} errors, {len(check.warnings)} warnings.")
    for e in check.errors:
        print(f"- ERROR {e}")
    for w in check.warnings:
        print(f"- warning: {w}")
    for p in problems:
        print(f"- labels: {p}")
    print(f"\nValues: {counts['values']}: {counts['sourced']} sourced ({counts['checked']} checked against the page), "
          f"{counts['TUNED']} TUNED, {counts['VERIFY']} unchecked (VERIFY), of which {counts['changed']} changed since labelled. "
          "Switches and choices aren't counted.\n")
    rows, n_runs, approved = None, 0, True
    if ensembles:
        targets, where, approved = load_targets(folder, name)
        if targets is None:
            print(where)
        else:
            rows, n_runs = score_targets(targets, ensembles, ages)
            print(f"Targets: {where}. Runs: {', '.join(str(e) for e in ensembles)}, {n_runs} runs.\n")
            print_targets(rows, ages)
            print()
    print("ACCURACY " + summary_line(name, counts, rows, n_runs, ages, approved) + "\n")
    return 1 if check.errors else 0


def write_template() -> Path:
    """species/_template.yaml: every key the schema knows, in birch's order, with birch's value as the
    starting point and what the value means, its unit and its range beside it."""
    raw = yaml.safe_load((SPECIES_DIR / "betula_pendula.yaml").read_text(encoding="utf-8"))
    lines = [
        "# Template for a new species.  See docs/adding_a_species.md.",
        "# Written by tools/species_report.py --write-template; birch's values are only a starting point.",
        "# Copy this file to species/<name>.yaml, then replace each value you have a source for or can",
        "# tune against, and say which in reference/<name>/labels.yaml.  A value left as it is stays VERIFY.",
        "",
    ]

    def dump(v):
        return yaml.safe_dump(v, default_flow_style=True, width=10000, allow_unicode=True).replace("\n...\n", "").strip()

    def walk(node, prefix, indent):
        pad = "  " * indent
        for k, v in node.items():
            path = f"{prefix}{k}"
            if isinstance(v, dict):
                lines.append(f"{pad}{k}:")
                walk(v, path + ".", indent + 1)
                if indent == 0:
                    lines.append("")
                continue
            f = schema.BY_PATH.get(path)
            if f is None:
                continue
            bits = [f.what]
            if f.kind in ("number", "integer", "numbers"):
                unit = "" if f.unit in ("", "-") else f" {f.unit}"
                bits.append(f"{f.lo:g} to {f.hi:g}{unit}")
            elif f.kind == "choice":
                bits.append(" | ".join(f.choices))
            lines.append(f"{pad}# {'; '.join(bits)}")
            if path == "species.scientific_name":
                v = "Genus species Author"
            elif path == "species.common_name":
                v = "common name"
            lines.append(f"{pad}{k}: {dump(v)}")

    walk(raw, "", 0)
    out = SPECIES_DIR / "_template.yaml"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out


def init_labels(path: Path, folder: Path) -> Path:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    out = {p: {"status": "VERIFY", "value": v} for p, v in schema.flatten(raw).items()
           if not p.startswith("species.") and not schema.is_setting(p, v)}
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "labels.yaml"
    if target.exists():
        raise SystemExit(f"{target} already exists")
    target.write_text("# status: sourced (add source:) | TUNED (add against:) | VERIFY.  See docs/adding_a_species.md.\n"
                      + yaml.safe_dump(out, sort_keys=False, width=10000, default_flow_style=None), encoding="utf-8")
    return target


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--species", default=None, help="a name in species/, or a path; default every species")
    ap.add_argument("--reference", default=None, help="folder with its labels and targets; default reference/<name>")
    ap.add_argument("--ensemble", action="append", default=[], help="a folder of saved runs, one per seed; repeatable")
    ap.add_argument("--age", type=int, action="append", default=None, help=f"default {DEFAULT_AGES}")
    ap.add_argument("--write-template", action="store_true")
    ap.add_argument("--init-labels", action="store_true")
    a = ap.parse_args(argv)
    if a.write_template:
        print(write_template())
        return 0
    paths = [species_path(a.species)] if a.species else species_files()
    if a.init_labels:
        print(init_labels(paths[0], Path(a.reference) if a.reference else ROOT / "reference" / paths[0].stem))
        return 0
    worst = 0
    for p in paths:
        folder = Path(a.reference) if a.reference else ROOT / "reference" / p.stem
        worst = max(worst, report(p, folder, a.ensemble, a.age or list(DEFAULT_AGES)))
    return worst


if __name__ == "__main__":
    sys.exit(main())
