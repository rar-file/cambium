"""scorecard.py: Evaluate simulation outputs against approved acceptance targets.

Reads reference/targets.yaml at the git tag 'targets-approved' and compares
saved run outputs (plot.json, stats.json) with each target, only within the
condition labels the target gives (scenario, mode, age, density, options
required).  Every range and value comes from the tagged file; the script holds
no target numbers of its own and adds no tolerances.  A target marked
'scoring: info' is shown as INFO, never PASS/FAIL.  A quantity the run did not
save is NOT APPLICABLE; nothing is filled in.

    python tools/scorecard.py out/bench/p38_nat                # ages 50 and 60
    python tools/scorecard.py out/bench/p38_nat out/1_stand --age 20 --age 60
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

from treegen.reference import eriksson_1997_height  # noqa: E402

TAG = "targets-approved"

# Condition label for the age range, and older spellings of it.
AGE_KEYS = ("age_years", "age_range_years", "stand_age_years")
DENSITY_KEYS = ("density_stems_ha", "density_range_stems_ha")

# Scenario and mode of a single-tree output (stats.json 'mode').  Stand-tree
# runs follow the thinning programme (managed); runs without --stand are
# open-grown.
TREE_MODES = {"stand": ("stand-tree", "managed"), "open": ("single-tree", "open-grown")}

# targets.yaml dominant_height_definition -> the per-tree value that ranks the
# 100 trees per hectare
DOMINANT_RANK = {"100_thickest_per_ha": "dbh_cm", "100_tallest_per_ha": "height_m"}


def load_approved_targets(ref: str = TAG) -> dict[str, Any]:
    """Load reference/targets.yaml as it is at `ref` (default: the tag
    'targets-approved').  There is no fallback to the working copy."""
    proc = subprocess.run(
        ["git", "show", f"{ref}:reference/targets.yaml"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot read reference/targets.yaml at '{ref}': {proc.stderr.strip()}")
    return yaml.safe_load(proc.stdout)


def commit_of(ref: str = TAG) -> str:
    proc = subprocess.run(["git", "rev-parse", "--short", f"{ref}^{{commit}}"],
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
    """(scenario, mode) of a run as targets.yaml labels them; mode None when
    the output does not record it."""
    if run is None:
        return None, None
    if run["is_plot"]:
        return "plot", run["plot_data"].get("mode")
    if run["is_tree"]:
        m = run["tree_stats"].get("mode")
        return TREE_MODES.get(m, (f"tree ({m})", None))
    if run["is_seedling"]:
        return "single-seedling", run["seedling_data"].get("mode")
    return None, None


def run_options(run: dict[str, Any]) -> dict[str, Any] | None:
    """Species options the run recorded as used ('options' in its output)."""
    for key in ("plot_data", "tree_stats", "seedling_data"):
        if run.get(key) and isinstance(run[key].get("options"), dict):
            return run[key]["options"]
    return None


def conditions_of(item: dict[str, Any]) -> dict[str, Any]:
    cond = item.get("conditions")
    if isinstance(cond, str):
        return {"text": cond}
    return cond or {}


def plot_stat(run: dict[str, Any], age: int) -> dict[str, Any] | None:
    return next((s for s in (run.get("plot_data") or {}).get("stats", []) if s.get("year") == age), None)


def tree_record(run: dict[str, Any], age: int) -> dict[str, Any] | None:
    return next((r for r in (run.get("tree_stats") or {}).get("per_year", []) if r.get("year") == age), None)


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


def dominant_height(records: list[dict[str, Any]], area_m2: float, rank_by: str) -> tuple[float, float]:
    """Mean height of the 100 trees per hectare ranked first by `rank_by`
    (dbh_cm: thickest, height_m: tallest).  On a plot of area_m2 that is
    100 * area_m2 / 1e4 trees; the last one counts with its fractional share.
    Returns (height, trees counted); with fewer trees than that, all count."""
    n = 100.0 * area_m2 / 1e4
    recs = sorted((r for r in records if r.get("height_m") is not None),
                  key=lambda r: r.get(rank_by) or 0.0, reverse=True)
    w_sum = h_sum = 0.0
    for r in recs:
        w = min(1.0, n - w_sum)
        if w <= 0.0:
            break
        w_sum += w
        h_sum += w * float(r["height_m"])
    return (h_sum / w_sum if w_sum > 0 else float("nan")), w_sum


def applicability(item: dict[str, Any], run: dict[str, Any] | None, age: int | None) -> tuple[str | None, list[str]]:
    """(reason the target does not apply to this run at this age or None,
    notes on conditions that could not be checked)."""
    notes: list[str] = []
    cond = conditions_of(item)
    scen, mode = run_type(run)
    if run is None:
        return f"needs a {' or '.join(cond.get('scenario', ['matching']))} run", notes
    if "scenario" in cond and scen not in cond["scenario"]:
        return f"scenario {scen} not in {cond['scenario']}", notes
    if "mode" in cond:
        if mode is None:
            notes.append(f"run mode not in output, mode {cond['mode']} not checked")
        elif mode not in cond["mode"]:
            return f"mode {mode} not in {cond['mode']}", notes
    if age is not None:
        for key in AGE_KEYS:
            if key in cond:
                lo, hi = cond[key]
                if not lo <= age <= hi:
                    return f"age {age} outside {key} [{lo}, {hi}]", notes
    for key in DENSITY_KEYS:
        if key in cond and age is not None and isinstance(cond[key], (list, tuple)):
            lo, hi = cond[key]
            st = plot_stat(run, age) if scen == "plot" else None
            if st is None:
                notes.append(f"stand density not checked ({key} [{lo}, {hi}])")
            elif not lo <= st.get("stems_per_ha", 0) <= hi:
                return f"{st.get('stems_per_ha')} stems/ha outside {key} [{lo}, {hi}]", notes
    if cond.get("options_required"):
        opts = run_options(run)
        if opts is None:
            return "options used are not recorded in the run output", notes
        for k, v in cond["options_required"].items():
            if opts.get(k) != v:
                return f"{k} was {opts.get(k)}, needs {v}", notes
    return None, notes


def _row(target, model_value, target_range, source, status, notes):
    return {"target": target, "model_value": model_value, "target_range": target_range,
            "source": source, "status": status, "notes": notes}


def _status(item: dict[str, Any], val: float, rng) -> str:
    if item.get("scoring") == "info":
        return "INFO"
    lo, hi = rng
    return "PASS" if lo <= val <= hi else "FAIL"


def t13_years(item: dict[str, Any], si: float) -> float:
    """Years to breast height at site index si.  With a 'time_to_breast_height'
    rule in the target, T13 = numerator / SIS, SIS being the top height at
    sis_total_age_years on this site's own curve, so T13 and SIS are solved
    together.  A targets file from before that rule gives a fixed number."""
    rule = item.get("time_to_breast_height")
    if rule is None:
        return float(item["years_to_breast_height"])
    p = item["parameters"]
    t_ref = float(item["reference_age_years"])
    num, sis_age = float(rule["numerator"]), float(rule["sis_total_age_years"])
    t = num / si
    for _ in range(200):
        t_new = num / eriksson_1997_height(si, sis_age - t, p["asi"], p["beta"], p["b2"], t_ref)
        if abs(t_new - t) < 1e-10:
            return t_new
        t = t_new
    return t


def _keyed_ages(item: dict[str, Any], pattern: str) -> list[tuple[int, str]]:
    """Ages written in keys, e.g. 'stems_per_ha_45yr' or 'age_2_years_m'."""
    out = []
    for key in item:
        m = re.search(pattern, key)
        if m:
            out.append((int(m.group(1)), key))
    return sorted(out)


def evaluate_run(name: str, item: dict[str, Any], run: dict[str, Any] | None,
                 ages: list[int]) -> list[dict[str, Any]]:
    """Rows for one target and one run (run None: no run of its scenario)."""
    source = item.get("source", "N/A")
    rows: list[dict[str, Any]] = []
    scen, _ = run_type(run)

    def na(label, rng_txt, why):
        rows.append(_row(label, "N/A", rng_txt, source, "NOT APPLICABLE", why))

    if name in ("stand_canopy.lai_baltic_chronosequence", "stand_canopy.lai_hagemeier"):
        rng = item["target_range"] if "target_range" in item else item["stand_range"]
        for age in ages:
            label = f"{name} (age {age})"
            why, notes = applicability(item, run, age)
            if why:
                na(label, format_val(rng), why)
                continue
            if scen == "plot":
                st = plot_stat(run, age)
                val, dens = (st["lai"], st.get("stems_per_ha")) if st else (None, None)
            else:
                rec = tree_record(run, age)
                val, dens = (rec.get("lai"), None) if rec else (None, None)
            if val is None:
                na(label, format_val(rng), f"age {age} not in output")
                continue
            notes.insert(0, f"stand LAI at {dens} stems/ha" if dens else "stand LAI")
            rows.append(_row(label, f"{float(val):.3f}", format_val(rng), source,
                             _status(item, float(val), rng), "; ".join(notes)))

    elif name == "stand_canopy.subcanopy_light_transmittance":
        rng = item["target_range_pct"]
        for age in ages:
            label = f"{name} (age {age})"
            why, notes = applicability(item, run, age)
            val = (run.get("plot_data") or run.get("tree_stats") or {}).get("subcanopy_light_pct") if not why else None
            if not why and val is None:
                why = "subcanopy light not saved in run output"
            if why:
                na(label, f"{format_val(rng)} %", why)
                continue
            rows.append(_row(label, f"{float(val):.1f} %", f"{format_val(rng)} %", source,
                             _status(item, float(val), rng), "; ".join(notes + ["run-level value"])))

    elif name.startswith("stand_canopy.live_crown_ratio."):
        if "min_ratio" in item:
            rng, rng_txt = (float(item["min_ratio"]), float("inf")), f">= {item['min_ratio']}"
        elif "target_range" in item:
            rng, rng_txt = item["target_range"], format_val(item["target_range"])
        else:
            rng = item["range"]
            rng_txt = f"{format_val(rng)} (mean {item.get('mean_ratio')})"
        for age in ages:
            label = f"{name} (age {age})"
            why, notes = applicability(item, run, age)
            if why:
                na(label, rng_txt, why)
                continue
            if scen == "plot":
                crs = [r["crown_ratio"] for r in plot_live_records(run, age) if r.get("crown_ratio") is not None]
                what = f"mean crown ratio of {len(crs)} live trees"
            else:
                rec = tree_record(run, age)
                crs = [rec["crown_ratio"]] if rec and rec.get("crown_ratio") is not None else []
                what = "crown ratio of the stand tree"
            if not crs:
                na(label, rng_txt, f"no live tree records at age {age}")
                continue
            val = sum(crs) / len(crs)
            rows.append(_row(label, f"{val:.2f}", rng_txt, source, _status(item, val, rng),
                             "; ".join([what] + notes)))

    elif name == "stand_canopy.stand_density":
        for at, key in _keyed_ages(item, r"_(\d+)yr$"):
            label = f"{name} (age {at})"
            why, notes = applicability(item, run, at)
            st = plot_stat(run, at) if not why else None
            if not why and st is None:
                why = f"age {at} not in plot output"
            if why:
                na(label, f"{item[key]} stems/ha", why)
                continue
            val = float(st["stems_per_ha"])
            rows.append(_row(label, f"{st['stems_per_ha']} stems/ha", f"{item[key]} stems/ha", source,
                             _status(item, val, (item[key], item[key])), "; ".join(notes)))

    elif name == "tree_allometry.site_index_curves":
        p = item["parameters"]
        lo_si, hi_si = item["swedish_boreal_range_m"]
        t_ref = float(item["reference_age_years"])
        t_lo, t_hi = t13_years(item, lo_si), t13_years(item, hi_si)
        definition = item.get("dominant_height_definition", "unconfirmed")
        for age in ages:
            label = f"{name} (age {age})"
            age_lo, age_hi = age - t_lo, age - t_hi
            if min(age_lo, age_hi) <= 0:
                na(label, "N/A", f"breast-height age {min(age_lo, age_hi):g} <= 0")
                continue
            band = (eriksson_1997_height(lo_si, age_lo, p["asi"], p["beta"], p["b2"], t_ref),
                    eriksson_1997_height(hi_si, age_hi, p["asi"], p["beta"], p["b2"], t_ref))
            ages_txt = f"{age_lo:g}" if t_lo == t_hi else f"{age_lo:.1f}-{age_hi:.1f}"
            band_txt = f"{band[0]:.2f}-{band[1]:.2f} m (SI{lo_si:g}-SI{hi_si:g}, bh age {ages_txt})"
            why, notes = applicability(item, run, age)
            if why:
                na(label, band_txt, why)
                continue
            if scen == "plot":
                if definition not in DOMINANT_RANK:
                    na(label, band_txt, f"dominant_height_definition is '{definition}' in targets.yaml")
                    continue
                recs = plot_live_records(run, age)
                h, counted = dominant_height(recs, float(run["plot_data"]["area_m2"]), DOMINANT_RANK[definition])
                need = 100.0 * float(run["plot_data"]["area_m2"]) / 1e4
                what = f"dominant height, {definition}: {counted:.2f} of {need:.2f} trees on the plot"
            else:
                rec = tree_record(run, age)
                h = rec.get("height_m") if rec else None
                what = "dominant height = the stand tree's height (neighbours are copies of it)"
            if h is None or h != h:
                na(label, band_txt, f"no height at age {age}")
                continue
            rows.append(_row(label, f"{float(h):.2f} m", band_txt, source,
                             _status(item, float(h), band), "; ".join([what] + notes)))

    elif name == "tree_allometry.crown_width_open_grown":
        m = re.search(r"=\s*([-\d.]+)\s*\+\s*([-\d.]+)\s*\*\s*DBH_over_bark_cm", item.get("formula", ""))
        for age in ages:
            label = f"{name} (age {age})"
            why, notes = applicability(item, run, age)
            rec = tree_record(run, age) if not why else None
            if not why and m is None:
                why = "formula in targets.yaml not in the form 'a + b * DBH_over_bark_cm'"
            if not why and rec is None:
                why = f"age {age} not in tree output"
            if why:
                na(label, item.get("formula", "See yaml"), why)
                continue
            from bark import dbh_over_bark
            dbh_ob = float(dbh_over_bark(float(rec.get("dbh_cm") or 0.0)))
            expected = float(m.group(1)) + float(m.group(2)) * dbh_ob
            val = float(rec["crown_width_m"])
            notes.insert(0, f"DBH over bark {dbh_ob:.1f} cm (tools/bark.py, the bark model named in targets.yaml)")
            rows.append(_row(label, f"{val:.2f} m", f"{expected:.2f} m (formula)", source,
                             _status(item, val, (expected, expected)), "; ".join(notes)))

    elif name == "juvenile_establishment.natural_clearcut_heights":
        for at, key in _keyed_ages(item, r"^age_(\d+)_years_m$"):
            rng = item[key]
            label = f"{name} (age {at})"
            why, notes = applicability(item, run, at)
            h = None
            if not why:
                if scen == "single-seedling":
                    hs = run["seedling_data"].get("h", {})
                    h = hs.get(str(at), hs.get(at))
                elif scen == "plot":
                    why = "plot seedling heights are not scored yet"
            if not why and h is None:
                why = f"age {at} not in output"
            if why:
                na(label, f"{format_val(rng)} m", why)
                continue
            rows.append(_row(label, f"{float(h):.3f} m", f"{format_val(rng)} m", source,
                             _status(item, float(h), rng), "; ".join([f"height at age {at}"] + notes)))

    else:
        why, _ = applicability(item, run, None)
        reasons = {
            "stand_canopy.dominant_height_invariance": "needs runs at several densities",
            "juvenile_establishment.field_layer": "field-layer sward properties not saved in run output",
        }
        if why:
            na(name, "See yaml", why)
        elif name in reasons:
            na(name, "See yaml", reasons[name])
        else:
            rows.append(_row(name, "N/A", "See yaml", source, "NOT SCORED",
                             "scorecard.py computes no model value for this target"))
    return rows


def evaluate_targets(
    targets: dict[str, Any], runs: list[dict[str, Any]], target_age: int | None = None,
    ages: list[int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate every target on every run whose scenario its conditions allow
    (age: stand age for plots, tree age for single runs)."""
    if ages is None:
        ages = [target_age] if target_age is not None else default_ages(runs)
    results: list[dict[str, Any]] = []
    unconditioned: list[dict[str, Any]] = []

    for name, item in flatten_targets(targets):
        source = item.get("source", "N/A")

        # RULE: If conditions aren't written in targets.yaml, mark NOT APPLICABLE and list for approval
        if item.get("conditions") is None:
            unconditioned.append({"target": name, "source": source, "item": item})
            results.append(_row(name, "N/A", "See yaml", source, "NOT APPLICABLE",
                                "No conditions written in targets.yaml; listed for the maintainer's approval"))
            continue

        scenarios = conditions_of(item).get("scenario")
        matching = [r for r in runs if scenarios is None or run_type(r)[0] in scenarios]
        for run in matching or [None]:
            rows = evaluate_run(name, item, run, ages)
            if len(runs) > 1 and run is not None:
                tag = Path(run["path"]).name
                for r in rows:
                    r["target"] = f"{r['target']} [{tag}]"
            results.extend(rows)

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

    lines.append("")
    lines.append("### Targets without conditions in targets.yaml (listed for the maintainer's approval)")
    for u in unconditioned:
        lines.append(f"- `{u['target']}` (Source: {u['source']}): marked NOT APPLICABLE because no conditions block is defined in `targets.yaml`.")
    if not unconditioned:
        lines.append("- none")

    lines.append("")
    lines.append("INFO: information only (scoring: info in targets.yaml), never PASS/FAIL. "
                 "NOT SCORED: the script computes no model value for that target.")
    return "\n".join(lines)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Evaluate simulation outputs against approved targets.")
    parser.add_argument("paths", nargs="+", help="Paths to run outputs (plot.json, stats.json, or output directories)")
    parser.add_argument("--age", type=int, action="append", default=None,
                        help="Age to evaluate (repeatable); default 50 and 60 where the run reaches them")
    parser.add_argument("--ref", default=TAG,
                        help=f"git ref to read reference/targets.yaml from (default: the tag {TAG})")
    args = parser.parse_args()

    targets = load_approved_targets(args.ref)
    runs = [load_run_data(p) for p in args.paths]

    results, unconditioned = evaluate_targets(targets, runs, ages=args.age)
    header = f"Targets: reference/targets.yaml at {args.ref} (commit {commit_of(args.ref)})."
    if commit_of(args.ref) != commit_of(TAG):
        header += f" NOT the approved tag {TAG} (commit {commit_of(TAG)}): results are a preview, not approved."
    header += f" Runs: {', '.join(args.paths)}"
    print(print_scorecard(results, unconditioned, header))


if __name__ == "__main__":
    main()
