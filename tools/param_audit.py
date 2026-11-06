"""Parameter audit (campaign M1c): one row per value in the species file.

Reads species/betula_pendula.yaml line by line so each value keeps the comment
written above it, and merges what was checked by hand from
reports/parameter_checks.csv.  A row nobody has checked says so: read level
"none", page support "not checked".  Status comes from the checks file if the row
was checked; otherwise from the comment's own words, as a first pass:

    calibrated  the comment says calibrated, fitted or tuned
    VERIFY      the comment says VERIFY, or there is no source in it
    sourced     the comment cites a source and doesn't say VERIFY (not yet opened)

    python tools/param_audit.py                 # writes reports/parameter_audit.csv
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "species" / "betula_pendula.yaml"
CHECKS = ROOT / "reports" / "parameter_checks.csv"
OUT = ROOT / "reports" / "parameter_audit.csv"
SCREEN = ROOT / "out" / "bench" / "node" / "screen5" / "ranking.csv"    # every value, 5 seeds, on the node
SCREEN_TOP = ROOT / "out" / "bench" / "node" / "screen20" / "ranking.csv"   # its top 15 again, 20 seeds

KEY = re.compile(r"^(\s*)([A-Za-z_]\w*):(?:\s+(.*))?$")
CITE = re.compile(r"\[[A-Z]+\d*\]|\b(?:19|20)\d\d\b|doi|PMC\d+", re.I)
CALIBRATED = re.compile(r"calibrat|fitted|tuned|re-tuned|ESTIMATE", re.I)
COLUMNS = ["path", "value", "cited_source", "read_level", "page_supports", "page_or_table", "species_in_source",
           "applies_to_silver_birch_sweden", "status", "used_by_code", "influence_rank", "max_change_pct", "effect_over_noise", "within_noise", "screen_seeds", "note"]


def flatten(o, p=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flatten(v, f"{p}.{k}" if p else str(k)))
    else:
        out[p] = o
    return out


def comments_by_path(lines):
    """path -> the comment written for it: the block just above the key plus any
    inline comment.  A key with no comment of its own shares the block above its
    sibling (a block often covers several values)."""
    stack: list[tuple[int, str]] = []
    pending: list[str] = []
    last_block: dict[int, str] = {}
    out = {}
    for raw in lines:
        line = raw.rstrip("\n")
        s = line.strip()
        if s.startswith("#"):
            pending.append(s.lstrip("#").strip())
            continue
        if not s:
            pending = []
            continue
        if s.startswith("- "):
            continue
        m = KEY.match(line)
        if not m:
            continue
        indent, key, rest = len(m.group(1)), m.group(2), m.group(3) or ""
        while stack and stack[-1][0] >= indent:
            stack.pop()
        for k in [k for k in last_block if k > indent]:
            del last_block[k]
        inline = rest.split(" # ", 1)[1].strip() if " # " in rest else ""
        path = ".".join([k for _, k in stack] + [key])
        block = " ".join(pending)
        if block:
            last_block[indent] = block
        text = (block or last_block.get(indent, "")) + (" " + inline if inline else "")
        out[path] = text.strip()
        stack.append((indent, key))
        pending = []
    return out


def code_text():
    parts = [(ROOT / "cli.py").read_text(encoding="utf-8")]
    for folder in ("treegen", "tools"):
        for f in sorted((ROOT / folder).glob("*.py")):
            if f.name != "param_audit.py" and f.name != "sensitivity_screen.py":
                parts.append(f.read_text(encoding="utf-8"))
    return "\n".join(parts)


def first_pass_status(comment):
    if CALIBRATED.search(comment):
        return "calibrated"
    if "VERIFY" in comment or not CITE.search(comment):
        return "VERIFY"
    return "sourced"


def load_csv(path, key):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {r[key]: r for r in csv.DictReader(f)}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = SPECIES.read_text(encoding="utf-8")
    values = flatten(yaml.safe_load(text))
    comments = comments_by_path(text.splitlines())
    missing = [p for p in values if p not in comments]
    if missing:
        raise SystemExit(f"no comment entry for {missing}: the line parser and the YAML disagree")
    checks = load_csv(CHECKS, "path")
    screen = load_csv(SCREEN, "path")
    top = load_csv(SCREEN_TOP, "path")
    # the top 15 take their places from the 20-seed run; the rest keep their order behind them
    rest = sorted((r for p, r in screen.items() if p not in top), key=lambda r: int(r["rank"]))
    for k, r in enumerate(rest):
        r["rank"] = str(len(top) + k + 1)
    screen.update(top)
    unknown = sorted(set(checks) - set(values))
    if unknown:
        raise SystemExit(f"parameter_checks.csv names values not in the species file: {unknown}")
    code = code_text()
    rows = []
    for path, value in values.items():
        if path.startswith("species."):
            continue   # the species' names, not parameters
        comment = comments[path]
        c = checks.get(path, {})
        s = screen.get(path, {})
        name = path.split(".")[-1]
        rows.append({
            "path": path,
            "value": value,
            "cited_source": c.get("cited_source") or ("in the comment; see note" if CITE.search(comment) else "none"),
            "read_level": c.get("read_level", "none"),
            "page_supports": c.get("page_supports", "not checked"),
            "page_or_table": c.get("page_or_table", ""),
            "species_in_source": c.get("species_in_source", ""),
            "applies_to_silver_birch_sweden": c.get("applies_to_silver_birch_sweden", ""),
            "status": c.get("status") or first_pass_status(comment),
            "used_by_code": "yes" if re.search(rf"\b{re.escape(name)}\b", code) else "no",
            "influence_rank": s.get("rank", "not calculated"),
            "max_change_pct": s.get("max_change_pct", ""),
            "effect_over_noise": s.get("effect_over_noise", ""),
            "within_noise": s.get("within_noise", ""),
            "screen_seeds": s.get("seeds", ""),
            "note": c.get("note") or comment[:300],
        })
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} values written to {OUT.relative_to(ROOT)}")
    by = {}
    for r in rows:
        by[r["status"]] = by.get(r["status"], 0) + 1
    print("status:", dict(sorted(by.items())))
    print("checked by hand:", sum(1 for r in rows if r["read_level"] != "none"),
          "; not read by any code:", [r["path"] for r in rows if r["used_by_code"] == "no"])


if __name__ == "__main__":
    main()
