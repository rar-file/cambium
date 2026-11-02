"""scorecard.py: Evaluate simulation outputs against approved acceptance targets.

Reads reference/targets.yaml at the git tag 'targets-approved' and compares
saved run outputs (plot.json, stats.json) with each target, only within the
target's stated conditions (age, stand type, scenario).  Every range and value
comes from the tagged file; the script holds no target numbers of its own and
adds no tolerances.  A target given as a single value without a range is
reported as NO RANGE, not PASS/FAIL.  A quantity the run did not save is NOT
APPLICABLE; nothing is filled in.

    python tools/scorecard.py out/bench/p38_nat                # ages 50 and 60
    python tools/scorecard.py out/bench/p38_nat --age 15 --age 20
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

try:
    import yaml
except ImportError:
    # If ran outside venv, try to import from .venv
    venv_site = ROOT / ".venv" / "Lib" / "site-packages"
    if venv_site.exists():
        sys.path.insert(0, str(venv_site))
        import yaml
    else:
        raise

TAG = "targets-approved"

# Condition keys in targets.yaml that give a stand age range [lo, hi] in years.
AGE_KEYS = ("age_range_years", "age_years", "stand_age_years")

# How the script reads the free-text part of each target's conditions as a run
# type it can check in the saved output: (output kind, run mode or None for any
# mode, stand age range written only in the text or None).  These are readings
# of the yaml text, not targets; each is printed with its result.  The yaml
# text quoted on the right is the authority.
RUN_READINGS: dict[str, tuple[str, str | None, tuple[int, int] | None]] = {
    # "unthinned / natural self-thinning on fertile abandoned farmland"
    "stand_canopy.lai_baltic_chronosequence": ("plot", "natural", None),
    # "mature monospecific Betula pendula stands"
    "stand_canopy.lai_hagemeier": ("plot", None, None),
    # "mature closed canopy (age 45-65)"
    "stand_canopy.subcanopy_light_transmittance": ("plot", None, (45, 65)),
    # "Managed stands; silvicultural guideline prescribing ... thinning"
    "stand_canopy.live_crown_ratio.silvicultural_recommendation": ("plot", "managed", None),
    # "Dense unmanaged natural stands subject to dense lateral shading"
    "stand_canopy.live_crown_ratio.dense_unmanaged_stand": ("plot", "natural", None),
    # "Self-thinned mature monospecific stands on sandy plains in Lower Saxony"
    "stand_canopy.stand_density": ("plot", "natural", None),
    # "Open-grown, solitary silver birch with unconstrained lateral branch expansion"
    "tree_allometry.crown_width_open_grown": ("tree", "open", None),
}


def load_approved_targets() -> dict[str, Any]:
    """Load reference/targets.yaml as it is at the git tag 'targets-approved'.
    There is no fallback to the working copy: an unapproved file never scores."""
    proc = subprocess.run(
        ["git", "show", f"{TAG}:reference/targets.yaml"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot read reference/targets.yaml at tag '{TAG}': {proc.stderr.strip()}")
    return yaml.safe_load(proc.stdout)


def approved_commit() -> str:
    proc = subprocess.run(["git", "rev-parse", "--short", f"{TAG}^{{commit}}"],
                          cwd=str(ROOT), capture_output=True, text=True)
    return proc.stdout.strip() or "unknown"


def load_run_data(path_str: str) -> dict[str, Any]:
    """Inspect and load data from a file or directory path."""
    p = Path(path_str)
    if not p.is_absolute():
        p = ROOT / p

    data: dict[str, Any] = {
        "path": str(p),
        "is_plot": False,
        "is_tree": False,
        "is_seedling": False,
        "plot_data": None,
        "tree_stats": None,
        "seedling_data": None,
        "trees_py": {},
    }

    if p.is_dir():
        plot_json = p / "plot.json"
        stats_json = p / "stats.json"
        if plot_json.exists():
            with open(plot_json, "r", encoding="utf-8") as f:
                data["plot_data"] = json.load(f)
            data["is_plot"] = True
            # Load individual trees if present
            trees_info = data["plot_data"].get("trees", [])
            for k in range(len(trees_info)):
                tp = p / f"tree_{k:03d}" / "stats.json"
                if tp.exists():
                    with open(tp, "r", encoding="utf-8") as tf:
                        data["trees_py"][k] = json.load(tf).get("per_year", [])
        elif stats_json.exists():
            with open(stats_json, "r", encoding="utf-8") as f:
                data["tree_stats"] = json.load(f)
            data["is_tree"] = True
    elif p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if "stats" in raw and "trees" in raw and "area_m2" in raw:
            data["plot_data"] = raw
            data["is_plot"] = True
        elif "per_year" in raw:
            data["tree_stats"] = raw
            data["is_tree"] = True
        elif "h" in raw and "rs" in raw:
            data["seedling_data"] = raw
            data["is_seedling"] = True
        else:
            # Generic dict
            data["generic"] = raw

    return data


def format_val(val: Any) -> str:
    if val is None:
        return "N/A"
    if isinstance(val, float):
        return f"{val:.3f}" if abs(val) < 10 else f"{val:.2f}"
    if isinstance(val, (list, tuple)):
        return "[" + ", ".join(f"{x:.2f}" if isinstance(x, float) else str(x) for x in val) + "]"
    return str(val)


def flatten_targets(targets: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every entry with a 'source' is a target; a group without one (e.g.
    live_crown_ratio) holds targets one level down."""
    flat = []
    for section, entries in targets.items():
        if not isinstance(entries, dict):
            continue
        for name, item in entries.items():
            if not isinstance(item, dict):
                continue
            if "source" in item:
                flat.append((f"{section}.{name}", item))
            else:
                for sub, sitem in item.items():
                    if isinstance(sitem, dict) and "source" in sitem:
                        flat.append((f"{section}.{name}.{sub}", sitem))
    return flat


def run_type(run: dict[str, Any] | None) -> tuple[str | None, str | None]:
    """('plot', 'natural' | 'managed'), ('tree', 'open' | 'stand' | ...),
    ('seedling', None); mode None when the output does not record it."""
    if run is None:
        return None, None
    if run["is_plot"]:
        return "plot", run["plot_data"].get("mode")
    if run["is_tree"]:
        return "tree", run["tree_stats"].get("mode")
    if run["is_seedling"]:
        return "seedling", None
    return None, None


def plot_stat(run: dict[str, Any], age: int) -> dict[str, Any] | None:
    return next((s for s in run["plot_data"].get("stats", []) if s.get("year") == age), None)


def plot_live_records(run: dict[str, Any], age: int) -> list[dict[str, Any]]:
    """Per-tree records of the trees alive in stand year `age`.  A tree's
    per_year 'year' counts from its germination, so stand year = year +
    germination; a tree removed in or before `age` is left out."""
    info = run["plot_data"].get("trees", [])
    recs = []
    for k, py in run["trees_py"].items():
        t = info[k] if k < len(info) else {}
        removed = t.get("removed")
        if removed is not None and removed <= age:
            continue
        y = age - int(t.get("germination", 0) or 0)
        r = next((r for r in py if r.get("year") == y), None)
        if r is not None:
            recs.append(r)
    return recs


def applicability(name: str, item: dict[str, Any], run: dict[str, Any] | None,
                  age: int | None) -> tuple[str | None, list[str]]:
    """(reason the target does not apply to this run at this age or None,
    notes on conditions that could not be checked)."""
    notes: list[str] = []
    kind, mode, text_age = RUN_READINGS.get(name, (None, None, None))
    rkind, rmode = run_type(run)
    if run is None or (kind is not None and rkind != kind):
        return f"needs a {kind or 'matching'} run", notes
    if mode is not None:
        if rmode is None:
            notes.append(f"run mode not in output, condition read as '{mode}' not checked")
        elif rmode != mode:
            return f"condition read as {mode} {kind}; run mode is {rmode}", notes
    cond = item.get("conditions")
    if isinstance(cond, dict) and age is not None:
        for key in AGE_KEYS:
            if key in cond:
                lo, hi = cond[key]
                if not lo <= age <= hi:
                    return f"age {age} outside {key} [{lo}, {hi}]", notes
        if "density_range_stems_ha" in cond and rkind == "plot":
            st = plot_stat(run, age)
            lo, hi = cond["density_range_stems_ha"]
            if st is not None and not lo <= st.get("stems_per_ha", 0) <= hi:
                return f"{st.get('stems_per_ha')} stems/ha outside density_range_stems_ha [{lo}, {hi}]", notes
    if text_age is not None and age is not None and not text_age[0] <= age <= text_age[1]:
        return f"age {age} outside {list(text_age)} (read from the condition text)", notes
    return None, notes


def _row(target, model_value, target_range, source, status, notes):
    return {"target": target, "model_value": model_value, "target_range": target_range,
            "source": source, "status": status, "notes": notes}


def _in_range(val: float, rng) -> str:
    lo, hi = rng
    return "PASS" if lo <= val <= hi else "FAIL"


def _keyed_ages(item: dict[str, Any], pattern: str) -> list[tuple[int, str]]:
    """Ages written in keys, e.g. 'unmanaged_natural_45yr' or 'age_2_years_m'."""
    out = []
    for key in item:
        m = re.search(pattern, key)
        if m:
            out.append((int(m.group(1)), key))
    return sorted(out)


def evaluate_targets(
    targets: dict[str, Any], runs: list[dict[str, Any]], target_age: int | None = None,
    ages: list[int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate runs against all targets at each age (stand age for plots,
    tree age for single trees)."""
    if ages is None:
        ages = [target_age] if target_age is not None else default_ages(runs)
    results: list[dict[str, Any]] = []
    unconditioned: list[dict[str, Any]] = []

    plot_run = next((r for r in runs if r["is_plot"]), None)
    tree_run = next((r for r in runs if r["is_tree"]), None)
    seedling_run = next((r for r in runs if r["is_seedling"]), None)

    for name, item in flatten_targets(targets):
        source = item.get("source", "N/A")

        # RULE: If conditions aren't written in targets.yaml, mark NOT APPLICABLE and list for approval
        if item.get("conditions") is None:
            unconditioned.append({"target": name, "source": source, "item": item})
            results.append(_row(name, "N/A", "See yaml", source, "NOT APPLICABLE",
                                "No conditions written in targets.yaml; listed for the maintainer's approval"))
            continue

        if name in ("stand_canopy.lai_baltic_chronosequence", "stand_canopy.lai_hagemeier"):
            rng = item["target_range"] if "target_range" in item else item["stand_range"]
            for age in ages:
                why, notes = applicability(name, item, plot_run, age)
                st = plot_stat(plot_run, age) if plot_run and not why else None
                if not why and st is None:
                    why = f"age {age} not in plot output"
                if why:
                    results.append(_row(f"{name} (age {age})", "N/A", format_val(rng), source, "NOT APPLICABLE", why))
                    continue
                val = float(st["lai"])
                notes.insert(0, f"plot LAI at {st.get('stems_per_ha')} stems/ha")
                results.append(_row(f"{name} (age {age})", f"{val:.3f}", format_val(rng), source,
                                    _in_range(val, rng), "; ".join(notes)))

        elif name == "stand_canopy.subcanopy_light_transmittance":
            rng = item["target_range_pct"]
            for age in ages:
                why, notes = applicability(name, item, plot_run, age)
                val = plot_run["plot_data"].get("subcanopy_light_pct") if plot_run and not why else None
                if not why and val is None:
                    why = "subcanopy light not saved in plot output"
                if why:
                    results.append(_row(f"{name} (age {age})", "N/A", f"{format_val(rng)} %", source, "NOT APPLICABLE", why))
                    continue
                results.append(_row(f"{name} (age {age})", f"{float(val):.1f} %", f"{format_val(rng)} %", source,
                                    _in_range(float(val), rng), "; ".join(notes + ["plot-level value from plot.json"])))

        elif name in ("stand_canopy.live_crown_ratio.silvicultural_recommendation",
                      "stand_canopy.live_crown_ratio.dense_unmanaged_stand"):
            if "min_ratio" in item:
                rng, rng_txt = (float(item["min_ratio"]), float("inf")), f">= {item['min_ratio']}"
            else:
                rng, rng_txt = item["target_range"], format_val(item["target_range"])
            for age in ages:
                why, notes = applicability(name, item, plot_run, age)
                recs = plot_live_records(plot_run, age) if plot_run and not why else []
                crs = [r["crown_ratio"] for r in recs if r.get("crown_ratio") is not None]
                if not why and not crs:
                    why = f"no live tree records at age {age}"
                if why:
                    results.append(_row(f"{name} (age {age})", "N/A", rng_txt, source, "NOT APPLICABLE", why))
                    continue
                val = sum(crs) / len(crs)
                notes.insert(0, f"mean crown ratio of {len(crs)} live trees")
                results.append(_row(f"{name} (age {age})", f"{val:.2f}", rng_txt, source,
                                    _in_range(val, rng), "; ".join(notes)))

        elif name == "stand_canopy.stand_density":
            for at, key in _keyed_ages(item, r"_(\d+)yr$"):
                why, notes = applicability(name, item, plot_run, at)
                st = plot_stat(plot_run, at) if plot_run and not why else None
                if not why and st is None:
                    why = f"age {at} not in plot output"
                if why:
                    results.append(_row(f"{name} (age {at})", "N/A", f"{item[key]} stems/ha", source, "NOT APPLICABLE", why))
                    continue
                results.append(_row(f"{name} (age {at})", f"{st['stems_per_ha']} stems/ha", f"{item[key]} stems/ha",
                                    source, "NO RANGE", "; ".join(notes + ["single value, no range in targets.yaml"])))

        elif name == "tree_allometry.crown_width_open_grown":
            m = re.search(r"=\s*([-\d.]+)\s*\+\s*([-\d.]+)\s*\*\s*DBH_over_bark_cm", item.get("formula", ""))
            for age in ages:
                why, notes = applicability(name, item, tree_run, age)
                rec = next((r for r in tree_run["tree_stats"].get("per_year", []) if r.get("year") == age), None) \
                    if tree_run and not why else None
                if not why and m is None:
                    why = "formula in targets.yaml not in the form 'a + b * DBH_over_bark_cm'"
                if not why and rec is None:
                    why = f"age {age} not in tree output"
                if why:
                    results.append(_row(f"{name} (age {age})", "N/A", item.get("formula", "See yaml"), source, "NOT APPLICABLE", why))
                    continue
                from bark import dbh_over_bark
                dbh_ob = float(dbh_over_bark(float(rec.get("dbh_cm") or 0.0)))
                expected = float(m.group(1)) + float(m.group(2)) * dbh_ob
                notes.insert(0, f"DBH over bark {dbh_ob:.1f} cm (tools/bark.py, the bark model named in targets.yaml)")
                results.append(_row(f"{name} (age {age})", f"{float(rec['crown_width_m']):.2f} m", f"{expected:.2f} m (formula)",
                                    source, "NO RANGE", "; ".join(notes + ["formula value, no range in targets.yaml"])))

        elif name == "juvenile_establishment.natural_clearcut_heights":
            # condition: "naturally regenerated ... with typical field-layer
            # competition"; a run counts only if its output records that
            # field-layer competition was on
            srun = seedling_run or tree_run
            src = (srun or {}).get("seedling_data") or (srun or {}).get("tree_stats") or {}
            for at, key in _keyed_ages(item, r"^age_(\d+)_years_m$"):
                rng = item[key]
                if srun is None:
                    why = "needs a seedling or single-tree run"
                elif not src.get("field_layer_competition"):
                    why = "field-layer competition not recorded as on in the run output"
                else:
                    why = None
                h = None
                if not why:
                    if srun.get("seedling_data"):
                        h = src.get("h", {}).get(str(at), src.get("h", {}).get(at))
                    else:
                        rec = next((r for r in src.get("per_year", []) if r.get("year") == at), None)
                        h = rec.get("height_m") if rec else None
                    if h is None:
                        why = f"age {at} not in output"
                if why:
                    results.append(_row(f"{name} (age {at})", "N/A", f"{format_val(rng)} m", source, "NOT APPLICABLE", why))
                    continue
                results.append(_row(f"{name} (age {at})", f"{float(h):.3f} m", f"{format_val(rng)} m", source,
                                    _in_range(float(h), rng), f"height at age {at}"))

        elif name == "stand_canopy.dominant_height_invariance":
            results.append(_row(name, "N/A", "See yaml", source, "NOT APPLICABLE",
                                "needs runs at several densities; not scored by this script"))

        elif name == "juvenile_establishment.field_layer":
            results.append(_row(name, "N/A", "See yaml", source, "NOT APPLICABLE",
                                "field-layer sward properties not saved in run output"))

        else:
            results.append(_row(name, "N/A", "See yaml", source, "NOT SCORED",
                                "conditions written but scorecard.py has no evaluator for this target"))

    return results, unconditioned


def default_ages(runs: list[dict[str, Any]]) -> list[int]:
    """Ages 50 and 60 where the runs reach them, else the last saved year."""
    years: set[int] = set()
    for r in runs:
        if r["is_plot"]:
            years |= {s["year"] for s in r["plot_data"].get("stats", []) if "year" in s}
        elif r["is_tree"]:
            years |= {p["year"] for p in r["tree_stats"].get("per_year", []) if "year" in p}
    picks = [a for a in (50, 60) if a in years]
    return picks or ([max(years)] if years else [])


def print_scorecard(results: list[dict[str, Any]], unconditioned: list[dict[str, Any]],
                    header: str | None = None) -> str:
    lines = []
    if header:
        lines.append(header)
        lines.append("")
    lines.append("| Target | Model Value | Target Range / Value | Status | Source | Stated Conditions / Notes |")
    lines.append("|---|:---:|:---:|:---:|:---:|---|")
    for r in results:
        lines.append(
            f"| `{r['target']}` | {r['model_value']} | {r['target_range']} | **{r['status']}** | {r['source']} | {r['notes']} |"
        )

    if unconditioned:
        lines.append("")
        lines.append("### Targets without conditions in targets.yaml (listed for the maintainer's approval)")
        for u in unconditioned:
            lines.append(f"- `{u['target']}` (Source: {u['source']}): marked NOT APPLICABLE because no conditions block is defined in `targets.yaml`.")

    no_range = sorted({r["target"].split(" (")[0] for r in results if r["status"] == "NO RANGE"})
    if no_range:
        lines.append("")
        lines.append("### Targets with a value but no range in targets.yaml (listed for the maintainer's approval)")
        for t in no_range:
            lines.append(f"- `{t}`: the model value is shown next to the target value; no PASS/FAIL without an approved range.")

    readings = sorted({r["target"].split(" (")[0] for r in results} & set(RUN_READINGS))
    if readings:
        lines.append("")
        lines.append("### How the written conditions were read (proposed as structured fields for the maintainer's approval)")
        for t in readings:
            kind, mode, text_age = RUN_READINGS[t]
            extra = f", stand age {text_age[0]}-{text_age[1]}" if text_age else ""
            lines.append(f"- `{t}`: {mode or 'any'} {kind} run{extra}")

    return "\n".join(lines)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Evaluate simulation outputs against approved targets.")
    parser.add_argument("paths", nargs="+", help="Paths to run outputs (plot.json, stats.json, or output directories)")
    parser.add_argument("--age", type=int, action="append", default=None,
                        help="Age to evaluate (repeatable); default 50 and 60 where the run reaches them")
    args = parser.parse_args()

    targets = load_approved_targets()
    runs = [load_run_data(p) for p in args.paths]

    results, unconditioned = evaluate_targets(targets, runs, ages=args.age)
    header = (f"Targets: reference/targets.yaml at tag {TAG} (commit {approved_commit()}). "
              f"Runs: {', '.join(args.paths)}")
    print(print_scorecard(results, unconditioned, header))


if __name__ == "__main__":
    main()
