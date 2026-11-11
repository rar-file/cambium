"""scorecard.py: Evaluate simulation outputs against approved acceptance targets.

Reads reference/targets.yaml at the git tag 'targets-approved' and compares
saved run outputs (plot.json, stats.json) with each target, only within the
condition labels the target gives (scenario, mode, age, density, options
required).  Every range and value comes from the tagged file; the script holds
no target numbers of its own and adds no tolerances.  A target marked
'scoring: info' is shown as INFO, never PASS/FAIL.  A quantity the run did not
save is NOT APPLICABLE; nothing is filled in.

Verdicts come from an ensemble of seeds on one machine (PROTOCOL.md section 2): the
ensemble mean against the target band, with the spread and the share of seeds inside
the band.  One run alone is shown as before, but isn't a verdict.

Kinds (DECISIONS 110, items 4 and 12): every target in targets.yaml says whether the model
follows it (by design), was tuned against it, saw it while a value was chosen, meets it out
of sample, or is independent of it.  The rows print in one block per kind.  The band check
is kept as each row's 'status'; what is printed is 'reads':
  * outside the band: FAIL, in every block;
  * inside, by design: HELD (by design); tuned against: IN BAND (tuned); seen: IN BAND (seen);
    out of sample: IN BAND (out of sample); a target with no kind: IN BAND (no kind);
  * inside, independent: PASS only when all seven parts of pass_rule hold, otherwise
    "IN BAND, not a pass" with the parts that don't.
The header counts the independent rows that apply at ages 50 and 60 and how many pass.  A row
tied by a formula in the model to a figure that isn't independent (a tie written on either row counts,
and every tie is followed to the end) is never counted; an in-band row with a value in fewer than 20 runs
of its own isn't counted, but a clean independent row that reads FAIL always is.  A tie that can't be read
(a tied_to that isn't a list, or names no target) can't be followed, so while one is in the targets read no
independent row is clean.  'scoring: info' is read whatever its case.
Plots: the per-tree rows (top height, crown ratio, lowest live branch) are read from the
plots' own tree lists (trees_NNN.json, tools/tree_list.py) when no per-tree stats are saved,
so no plot verdict needs working by hand (review 2026-11-09, finding 9).

    python tools/scorecard.py --ensemble out/bench/ensemble/base
    python tools/scorecard.py --ensemble out/bench/ensemble/base --age 20 --age 60
    python tools/scorecard.py out/bench/p38_nat out/1_stand --age 20 --age 60
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
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
ELFVING_CURVE = "height_curve_at_100_thickest_per_ha"

# The kinds a target may have (targets.yaml 'kind'), in the order their blocks print, and the words an
# in-band row reads in each.  Only 'independent' can read PASS.
INDEPENDENT = "independent"
BLOCKS = (
    ("by design", "A. BY DESIGN: the model follows these (a curve it is driven by, a cap, an input). "
                  "Inside shows the machinery holds, nothing more."),
    ("tuned against", "B. TUNED AGAINST: a species value was set with this figure on the table. Inside is expected."),
    ("seen", "C. SEEN: the figure was watched while a value was chosen. Inside is not a test."),
    ("out of sample", "D. OUT OF SAMPLE: the quantity was tuned on other stands; this source is a new one. Inside is not a pass."),
    (INDEPENDENT, "E. INDEPENDENT: no species value was set against these. Only here can a row read PASS, "
                  "and only when all seven parts of the pass rule hold."),
    (None, "F. NO KIND: the targets file read has no kind for these (a file from before the kinds). Never PASS."),
)
KINDS = tuple(k for k, _ in BLOCKS if k)
IN_BAND_WORDS = {"by design": "HELD (by design)", "tuned against": "IN BAND (tuned)", "seen": "IN BAND (seen)",
                 "out of sample": "IN BAND (out of sample)", None: "IN BAND (no kind)"}
# Part 4 of the pass rule: the band bases that can carry a PASS (validation design, section 5)
PASS_BASES = ("three or more stands", "published SD between stands", "equation's between-stand spread")
MIN_RUNS = 20          # part 5: 20 runs on the shipped defaults at one commit
# Overrides that only set a run up, as tools/forest.py writes them with its defaults (settings(): 16,000 stems/ha at
# the start, mortality on); any other is a changed default.  Only the plot's area may take any value.
SETUP_OVERRIDES = ("plot.stand_measures=true", "plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=16000.0",
                   "mortality.enabled=true")
SETUP_ANY_VALUE = ("plot.natural_start.area_m2=",)
PASS_RULE = (
    "1 independent: no value set against it, and not tied to a figure that isn't independent (a tie written on either row counts; ties followed to the end)",
    "2 approved and opened: in the approved targets.yaml, its page read at an allowed place (source_opened)",
    "3 matched: species, natural or planted, density and site agree with the runs (matched)",
    "4 a band with a stated basis: three or more stands, a published SD between stands, or an equation's between-stand spread; not INFO",
    "5 20 runs on the shipped defaults at one commit, the row itself with a value in at least 20 of them, the mean inside the band",
    "6 frozen first: targets read at the approved tag, and the tag is in the runs' commit history",
    "7 written by the scorecard: this script, from the saved outputs",
)


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
        "tree_lists": {},
        "snapshots": {},
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
            # The plot's tree lists (tools/tree_list.py): the living trees at each saved stand year
            for tl in sorted(p.glob("trees_[0-9][0-9][0-9].json")):
                with open(tl, "r", encoding="utf-8") as tf:
                    doc = json.load(tf)
                year = int(doc.get("plot_year", int(tl.stem.split("_")[1])))
                data["tree_lists"][year] = {"area_m2": float(doc.get("area_m2", data["plot_data"].get("area_m2", 0.0))),
                                            "trees": [t for t in doc.get("trees", []) if t.get("alive")]}
        elif stats_json.exists():
            with open(stats_json, "r", encoding="utf-8") as f:
                data["tree_stats"] = json.load(f)
            data["is_tree"] = True
            tree_json = p / "tree.json"    # tools/tree_table.py: stem and branch wood every 5 years
            if tree_json.exists():
                with open(tree_json, "r", encoding="utf-8") as f:
                    data["snapshots"] = {int(s["age"]): s for s in json.load(f).get("snapshots", []) if "age" in s}
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


def naslund_top_height(records: list[dict[str, Any]], area_m2: float) -> tuple[float, float, float]:
    """Elfving 2010 p. 58: "Top height is defined as the height according to the height curve at
    the mean diameter of the 100 by diameter largest trees per hectare."  The report names no
    curve, so a Naslund curve, the form the maintainer chose for the cross-check: h = 1.3 + d^2 / (a + b d)^2,
    fitted to the plot's live trees as a straight line of d / sqrt(h - 1.3) on d, and read at those
    trees' mean diameter.  The last tree counts with its fractional share.  Returns (height on the
    curve, trees counted, those trees' mean height); nan if too few trees to fit."""
    import numpy as np

    rows = [(float(r["dbh_cm"]), float(r["height_m"])) for r in records if r.get("dbh_cm") and r.get("height_m")]
    n = 100.0 * area_m2 / 1e4
    usable = [(d, h) for d, h in rows if h > 1.3]
    if len(usable) < 3:
        return float("nan"), 0.0, float("nan")
    d_all, h_all = np.array([x[0] for x in usable]), np.array([x[1] for x in usable])
    b, a = np.polyfit(d_all, d_all / np.sqrt(h_all - 1.3), 1)
    w_sum = d_sum = h_sum = 0.0
    for d, h in sorted(rows, key=lambda x: x[0], reverse=True):
        w = min(1.0, n - w_sum)
        if w <= 0.0:
            break
        w_sum += w
        d_sum += w * d
        h_sum += w * h
    mean_d = d_sum / w_sum
    return 1.3 + mean_d * mean_d / (a + b * mean_d) ** 2, w_sum, h_sum / w_sum


def plot_live_records(run: dict[str, Any], age: int) -> list[dict[str, Any]]:
    """Per-tree records of the trees alive in stand year `age`.  A tree's
    per_year 'year' counts from its germination, so stand year = year +
    germination; a tree removed in or before `age` is left out.  A plot that
    saved no per-tree stats is read from its tree list for that year, if any
    (DBH over bark there; crown ratio = (height - crown base) / height, as
    growth.py's stats compute it)."""
    if not run.get("trees_py"):
        return list_records(run, age)
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


def list_records(run: dict[str, Any], age: int) -> list[dict[str, Any]]:
    """The living trees of a plot's tree list at stand year `age`, in the per-tree record form."""
    tl = (run.get("tree_lists") or {}).get(age)
    if tl is None:
        return []
    out = []
    for t in tl["trees"]:
        h, cb = t.get("height_m"), t.get("crown_base_m")
        out.append({"dbh_cm": t.get("dbh_cm"), "height_m": h, "lowest_live_branch_m": t.get("lowest_live_branch_m"),
                    "crown_ratio": None if cb is None or not h or h <= 0 else (float(h) - float(cb)) / float(h)})
    return out


def records_from(run: dict[str, Any]) -> str:
    """Where a plot's per-tree records come from, for the notes."""
    return "per-tree stats" if run.get("trees_py") else "the plot's tree list (DBH over bark)"


def thickest_mean(records: list[dict[str, Any]], area_m2: float, field: str) -> tuple[float, float]:
    """Mean of `field` over the 100 thickest trees per hectare (the last one at its fractional
    share), as dominant_height ranks them.  Returns (mean, trees counted)."""
    n = 100.0 * area_m2 / 1e4
    recs = sorted((r for r in records if r.get("dbh_cm") and r.get(field) is not None),
                  key=lambda r: float(r["dbh_cm"]), reverse=True)
    w_sum = v_sum = 0.0
    for r in recs:
        w = min(1.0, n - w_sum)
        if w <= 0.0:
            break
        w_sum += w
        v_sum += w * float(r[field])
    return (v_sum / w_sum if w_sum > 0 else float("nan")), w_sum


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


def _row(target, model_value, target_range, source, status, notes, value=None, band=None):
    """value and band are the numbers behind the text, for an ensemble's mean."""
    return {"target": target, "model_value": model_value, "target_range": target_range,
            "source": source, "status": status, "notes": notes, "value": value, "band": band}


def _status(item: dict[str, Any], val: float, rng) -> str:
    if is_info(item):
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
                             _status(item, float(val), rng), "; ".join(notes), float(val), rng))

    elif name == "stand_canopy.subcanopy_light_transmittance":
        rng = item["target_range_pct"]
        for age in ages:
            label = f"{name} (age {age})"
            why, notes = applicability(item, run, age)
            yearly = None
            if not why:
                yearly = plot_stat(run, age) if scen == "plot" else tree_record(run, age)
            val = yearly.get("subcanopy_diffuse_light_pct") if yearly else None
            if not why and val is None:
                # the target measures diffuse light; the sky-and-sun value is
                # not the same measure, so it is shown but never scored
                weighted = yearly.get("subcanopy_light_pct") if yearly else None
                why = "diffuse subcanopy light not saved in run output"
                if weighted is not None:
                    why += f" (sky-and-sun light {float(weighted):.1f} %, not scored: not the target's measure)"
            if why:
                na(label, f"{format_val(rng)} %", why)
                continue
            rows.append(_row(label, f"{float(val):.1f} %", f"{format_val(rng)} %", source,
                             _status(item, float(val), rng), "; ".join(notes + ["diffuse light at 1.0-2.0 m, this year"]),
                             float(val), rng))

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
                what = f"mean crown ratio of {len(crs)} live trees, from {records_from(run)}"
            else:
                rec = tree_record(run, age)
                crs = [rec["crown_ratio"]] if rec and rec.get("crown_ratio") is not None else []
                what = "crown ratio of the stand tree"
            if not crs:
                na(label, rng_txt, f"no live tree records at age {age}")
                continue
            val = sum(crs) / len(crs)
            rows.append(_row(label, f"{val:.2f}", rng_txt, source, _status(item, val, rng),
                             "; ".join([what] + notes), val, rng))

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
                             _status(item, val, (item[key], item[key])), "; ".join(notes), val, (item[key], item[key])))

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
                if definition != ELFVING_CURVE and definition not in DOMINANT_RANK:
                    na(label, band_txt, f"dominant_height_definition is '{definition}' in targets.yaml")
                    continue
                recs = plot_live_records(run, age)
                need = 100.0 * float(run["plot_data"]["area_m2"]) / 1e4
                if definition == ELFVING_CURVE:
                    h, counted, simple = naslund_top_height(recs, float(run["plot_data"]["area_m2"]))
                    what = (f"top height on a Naslund curve at the mean diameter of {counted:.2f} of {need:.2f} trees on the plot; "
                            f"those trees' mean height {simple:.2f} m")
                else:
                    h, counted = dominant_height(recs, float(run["plot_data"]["area_m2"]), DOMINANT_RANK[definition])
                    what = f"dominant height, {definition}: {counted:.2f} of {need:.2f} trees on the plot"
                if counted < 10.0:   # the maintainer, 2026-11-06: say so, the figure gets noisy
                    what += "; fewer than 10 such trees, so this is noisy"
                what += f"; from {records_from(run)}"
            else:
                rec = tree_record(run, age)
                h = rec.get("height_m") if rec else None
                what = "dominant height = the stand tree's height (neighbours are copies of it)"
            if h is None or h != h:
                na(label, band_txt, f"no height at age {age}")
                continue
            rows.append(_row(label, f"{float(h):.2f} m", band_txt, source,
                             _status(item, float(h), band), "; ".join([what] + notes), float(h), band))

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
                             _status(item, val, (expected, expected)), "; ".join(notes), val, (expected, expected)))

    elif "at_top_height_m" in item and "lowest_live_branch_m" in item:
        # Q40 (the maintainer, 2026-11-11): the lowest live branch in the year the stand's top height is in the source's range
        rng = item["lowest_live_branch_m"]
        h_lo, h_hi = item["at_top_height_m"]
        label = f"{name} (top height {h_lo:g}-{h_hi:g} m)"
        rng_txt = f"{format_val(rng)} m"
        why, notes = applicability(item, run, None)
        if why:
            na(label, rng_txt, why)
        elif scen == "plot":
            seen, found = [], None
            for year in sorted(run.get("tree_lists") or {}):
                recs = list_records(run, year)
                area = float(run["tree_lists"][year]["area_m2"])
                th = naslund_top_height(recs, area)[0]
                seen.append(f"{year}: {th:.2f} m")
                if th == th and h_lo <= th <= h_hi:
                    val, counted = thickest_mean(recs, area, "lowest_live_branch_m")
                    found = (year, th, val, counted)
                    break
            if found is None:
                na(label, rng_txt, f"no tree list in a year top height (the approved definition) was {h_lo:g}-{h_hi:g} m; "
                                   f"top height at the saved lists: {', '.join(seen) or 'no lists saved'}")
            else:
                year, th, val, counted = found
                rows.append(_row(label, f"{val:.2f} m", rng_txt, source, _status(item, val, rng),
                                 "; ".join([f"this run: lowest live branch of the {counted:.2f} thickest trees on the plot (100 a ha) at stand age "
                                            f"{year}, top height {th:.2f} m, from the plot's tree list"] + notes), val, rng))
        else:
            py = sorted((run.get("tree_stats") or {}).get("per_year", []), key=lambda r: r.get("year", 0))
            r = next((r for r in py if r.get("height_m") is not None and h_lo <= float(r["height_m"]) <= h_hi), None)
            if r is None or r.get("lowest_live_branch_m") is None:
                na(label, rng_txt, f"no year with the tree {h_lo:g}-{h_hi:g} m tall and its lowest live branch saved")
            else:
                val = float(r["lowest_live_branch_m"])
                rows.append(_row(label, f"{val:.2f} m", rng_txt, source, _status(item, val, rng),
                                 "; ".join([f"this run: lowest live branch in the first year the stand tree was {h_lo:g}-{h_hi:g} m tall "
                                            f"(age {r.get('year')}, {float(r['height_m']):.2f} m; a stand tree's height is the "
                                            "stand's dominant height)"] + notes), val, rng))

    elif name in ("tree_allometry.branch_biomass_repola", "tree_allometry.stem_biomass_repola"):
        # DECISIONS 110 item 6a: branch wood against Repola's Eq. A3 at the tree's own crown length, beside Eq. 9.
        # Eq. A3 is coded by the T1 tooling (tools/m3_wood.py repola_a3, branch tools-logging); it isn't written
        # again here, so until that is merged the A3 row says it can't be read.
        import m3_wood
        from bark import dbh_over_bark
        repola, repola_a3 = m3_wood.repola, getattr(m3_wood, "repola_a3", None)
        d_lo, d_hi = item.get("dbh_range_cm", (0.0, float("inf")))
        branch = name.endswith("branch_biomass_repola")
        eqs = (("Eq. A3 at own crown length", "branch_kg"), ("Eq. 9", "branch_kg")) if branch else (("Eq. 7", "stem_kg"),)
        for age in ages:
            why, notes = applicability(item, run, age)
            rec = tree_record(run, age) if not why else None
            snap = (run.get("snapshots") or {}).get(age) if not why else None
            if not why and (rec is None or snap is None or not rec.get("dbh_cm") or not rec.get("height_m")):
                why = f"age {age}: no wood snapshot (tree.json) or no DBH and height saved"
            for eq, part in eqs:
                label = f"{name} (age {age}, {eq})"
                if why:
                    na(label, "1.0 (ratio)", why)
                    continue
                dob = float(dbh_over_bark(float(rec["dbh_cm"])))
                h = float(rec["height_m"])
                stem_ref, branch_ref = repola(dob, h)
                extra = ""
                if eq.startswith("Eq. A3"):
                    if repola_a3 is None:
                        na(label, "1.0 (ratio)", "Eq. A3 is not in tools/m3_wood.py yet: it comes with the T1 tooling (repola_a3, branch tools-logging)")
                        continue
                    if rec.get("crown_base_height_m") is None:
                        na(label, "1.0 (ratio)", f"age {age}: no crown base saved")
                        continue
                    cl = h - float(rec["crown_base_height_m"])
                    ref, extra = repola_a3(dob, h, cl), f", crown length {cl:.2f} m"
                else:
                    ref = branch_ref if branch else stem_ref
                val = float(snap[part]) / ref
                inside = "inside" if d_lo <= dob <= d_hi else "outside"
                parts = [f"this run: model {float(snap[part]):.1f} kg against {ref:.1f} kg at DBH over bark {dob:.1f} cm, height {h:.2f} m{extra}",
                         f"DBH {inside} Repola's sample, {d_lo:g}-{d_hi:g} cm"]
                if branch:
                    parts.append("Repola's branches include bark, the model's don't")
                rows.append(_row(label, f"{val:.3f}", "1.0 (ratio)", source, _status(item, val, (1.0, 1.0)),
                                 "; ".join(parts + notes), val, (1.0, 1.0)))

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
                             _status(item, float(h), rng), "; ".join([f"height at age {at}"] + notes), float(h), rng))

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
    for r in rows:
        r["key"] = name
    return rows


# -- kinds and the pass rule ------------------------------------------------------------------------------

def kind_of(item: dict[str, Any] | None) -> str | None:
    """The target's kind, or None when the file read has none (or an unknown word)."""
    k = (item or {}).get("kind")
    return k if k in KINDS else None


def is_info(item: dict[str, Any] | None) -> bool:
    """'scoring: info', whatever its case ('INFO', 'Info ' and 'info' are the same)."""
    s = (item or {}).get("scoring")
    return isinstance(s, str) and s.strip().lower() == "info"


def ties_of(item: dict[str, Any] | None) -> list[str]:
    """The names in a target's tied_to when it is a list of names; anything else gives none here, and
    tie_text_problems says why no independent row is clean while it is there."""
    t = (item or {}).get("tied_to")
    return [x for x in t if isinstance(x, str)] if isinstance(t, list) else []


def tie_text_problems(targets: dict[str, Any]) -> list[str]:
    """Ties written so they can't be read, anywhere in the targets read: a tied_to that is not a list (a plain
    string, 0, false, empty), or a name in it that is no target (misspelt, short, wrong case, a trailing space).
    A tie that can't be read can't be followed, so while any is there every independent row is unclean
    (pass rule part 1).  Each reason names the row and the text."""
    flat = flatten_targets(targets)
    names = {n for n, _ in flat}
    out = []
    for name, item in flat:
        if "tied_to" not in item:
            continue
        t = item["tied_to"]
        if not isinstance(t, list):
            out.append(f"tied_to on {name} is not a list: {t!r}")
            continue
        out += [f"tied_to on {name} names no target: {x!r}" for x in t if not isinstance(x, str) or x not in names]
    return out


def tie_graph(targets: dict[str, Any]) -> dict[str, list[str]]:
    """Every target's ties, both ways: a tie written on either row ties the two (a formula in the model
    links two figures whichever row names the other).  Order kept as written, own ties first."""
    graph: dict[str, list[str]] = {}
    for name, item in flatten_targets(targets):
        for t in ties_of(item):
            for a, b in ((name, t), (t, name)):
                graph.setdefault(a, [])
                if b not in graph[a]:
                    graph[a].append(b)
    return graph


def tie_problems(item: dict[str, Any], targets: dict[str, Any]) -> list[str]:
    """Why an independent target isn't clean: values set against it, or a figure tied to it that isn't clean.
    Ties are two-way (tie_graph: a row named in another row's tied_to is tied to it) and are followed through
    independent targets to the end: a tied target must itself be independent, with no value set against it
    and no tie of its own, either way, to a figure that isn't clean.  A tie anywhere in the targets that can't
    be read (tie_text_problems) makes every independent row unclean."""
    flat = flatten_targets(targets)
    by_name = dict(flat)
    graph = tie_graph(targets)
    # the item's name in these targets (the same object, or failing that an equal copy), so ties written on other rows are found
    own = next((n for n, it in flat if it is item), None) or next((n for n, it in flat if item and it == item), None)
    out = tie_text_problems(targets)
    if item.get("values_set"):
        out.append(f"values set against it ({', '.join(item['values_set'])})")
    first = ties_of(item)
    first += [t for t in graph.get(own, []) if t not in first]
    queue, seen = [(t, t) for t in first], {own}
    while queue:
        t, path = queue.pop(0)
        if t in seen:
            continue
        seen.add(t)
        other = by_name.get(t)
        k = kind_of(other)
        if k != INDEPENDENT:
            out.append(f"tied to {path} ({k or 'no kind'})")
        elif other.get("values_set"):
            out.append(f"tied to {path} (values set against it: {', '.join(other['values_set'])})")
        else:
            nxt = ties_of(other) + [u for u in graph.get(t, []) if u not in ties_of(other)]
            queue += [(u, f"{path} -> {u}") for u in nxt]
    return out


def run_manifest(run: dict[str, Any]) -> dict[str, Any]:
    for key in ("plot_data", "tree_stats", "seedling_data"):
        if run.get(key) and isinstance(run[key].get("run_manifest"), dict):
            return run[key]["run_manifest"]
    return {}


def file_sha_at(commit: str, path: str) -> str | None:
    """sha256 of a file at a commit, or None when the commit or the file isn't here."""
    import hashlib
    proc = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=str(ROOT), capture_output=True)
    return hashlib.sha256(proc.stdout).hexdigest() if proc.returncode == 0 else None


def species_sha_at(commit: str) -> str | None:
    """sha256 of species/betula_pendula.yaml at a commit, or None when the commit isn't here."""
    return file_sha_at(commit, "species/betula_pendula.yaml")


def ensemble_facts(runs: list[dict[str, Any]], check_git: bool = True) -> dict[str, Any]:
    """What part 5 of the pass rule needs: the number of runs, one commit, a clean tree, the species file
    and the environment file of that commit (by their hashes in the manifest), and no override beyond
    setting the run up."""
    problems = []
    if len(runs) < MIN_RUNS:
        problems.append(f"{len(runs)} runs, not {MIN_RUNS}")
    mans = [run_manifest(r) for r in runs]
    commits = {m.get("git_commit") for m in mans}
    commit = next(iter(commits)) if len(commits) == 1 else None
    if commit is None:
        problems.append("runs not at one recorded commit")
    if any(m.get("git_tracked_changes") or m.get("uncommitted_sha256") or m.get("uncommitted_files") for m in mans):
        problems.append("uncommitted changes in a run")
    extra = sorted({o for m in mans for o in (m.get("overrides") or [])
                    if o not in SETUP_OVERRIDES and not o.startswith(SETUP_ANY_VALUE)})
    if extra:
        problems.append(f"defaults changed: {', '.join(extra)}")
    if commit and check_git:
        sha = species_sha_at(commit)
        if sha is None:
            problems.append(f"commit {commit} not in this repository")
        elif any(m.get("species_sha256") != sha for m in mans):
            problems.append(f"species file not the one at {commit}")
        envs = {m.get("environment_file") for m in mans}
        env = next(iter(envs)) if len(envs) == 1 else None
        if not env:
            problems.append("runs not on one recorded environment file")
        elif sha is not None:
            env_sha = file_sha_at(commit, env)
            if env_sha is None:
                problems.append(f"environment file {env} not in commit {commit}")
            elif any(m.get("environment_sha256") != env_sha for m in mans):
                problems.append(f"environment file not the one at {commit}")
    return {"runs": len(runs), "commit": commit, "problems": problems}


def frozen_first(run_commit: str | None, ref: str = TAG) -> bool:
    """Part 6: the approved tag is the runs' commit or one of its ancestors, so the band came first."""
    if not run_commit:
        return False
    proc = subprocess.run(["git", "merge-base", "--is-ancestor", f"{ref}^{{commit}}", run_commit],
                          cwd=str(ROOT), capture_output=True)
    return proc.returncode == 0


def row_runs_problem(seeds: int | None, facts: dict[str, Any] | None) -> str | None:
    """Part 5 for one row: the row itself must have a value in at least MIN_RUNS runs, not only the folder."""
    if seeds is None or seeds < MIN_RUNS:
        of = f" of {facts['runs']}" if facts else ""
        return f"a value in {seeds or 0}{of} runs, not {MIN_RUNS}"
    return None


def source_opened_ok(value: Any) -> bool:
    """Part 2: source_opened is text saying where and when the page was read, with the date (YYYY-MM-DD).
    True, a bare word or any other value is not enough, nor is text that starts with 'not' or 'false'
    ('not opened, checked 2026-11-11'), whatever its case."""
    return (isinstance(value, str) and re.search(r"\b\d{4}-\d{2}-\d{2}\b", value) is not None
            and re.match(r"\s*(not|false)\b", value, re.IGNORECASE) is None)


def pass_rule(item: dict[str, Any], targets: dict[str, Any], facts: dict[str, Any] | None, frozen: bool,
              seeds: int | None = None) -> list[str]:
    """The parts of the seven-part pass rule (PASS_RULE) an in-band row does not meet; [] means PASS.
    facts None: one run, not an ensemble.  seeds: how many runs gave this row a value."""
    unmet = []
    ties = tie_problems(item, targets)
    if kind_of(item) != INDEPENDENT or ties:
        unmet.append("1 (" + ("; ".join(ties) if ties else f"kind {kind_of(item) or 'none'}") + ")")
    if not source_opened_ok(item.get("source_opened")) or not item.get("page_table"):
        unmet.append("2 (source not opened: source_opened must say where and when, with a date, and page_table the page)")
    if item.get("matched") is not True:
        unmet.append("3 (not matched" + (f": {item['match_note']}" if item.get("match_note") else "") + ")")
    if is_info(item) or item.get("band_basis") not in PASS_BASES:
        unmet.append(f"4 (band basis: {item.get('band_basis') or 'not stated'}" + ("; INFO" if is_info(item) else "") + ")")
    if facts is None:
        unmet.append("5 (one run is not a verdict)")
    else:
        problems = list(facts["problems"])
        mine = row_runs_problem(seeds, facts)
        if mine:
            problems.append(mine)
        if problems:
            unmet.append("5 (" + "; ".join(problems) + ")")
    if not frozen:
        unmet.append("6 (targets not read at the approved tag, or the tag isn't in the runs' history)")
    return unmet


def reads_for(row: dict[str, Any], item: dict[str, Any], targets: dict[str, Any],
              facts: dict[str, Any] | None = None, frozen: bool = False) -> str:
    """The word a row prints, from its band check ('status'), its target's kind and the pass rule."""
    status = row["status"]
    if status == "FAIL":
        return "FAIL"
    if status != "PASS" and status != "INFO":
        return status                                    # NOT APPLICABLE, NOT SCORED
    if status == "INFO":
        band, value = row.get("band"), row.get("value", row.get("mean"))
        if band and value is not None and band[0] < band[1] and not band[0] <= value <= band[1]:
            return "INFO; outside the band (a miss)"
        return "INFO"
    kind = kind_of(item)
    if kind != INDEPENDENT:
        return IN_BAND_WORDS[kind]
    unmet = pass_rule(item, targets, facts, frozen, row.get("seeds"))
    return "PASS" if not unmet else "IN BAND, not a pass: rule " + ", ".join(unmet)


def counts_as_independent(item: dict[str, Any], targets: dict[str, Any]) -> bool:
    """A scored independent row with no value set against it and no tie (either way) to a figure that isn't independent."""
    return kind_of(item) == INDEPENDENT and not is_info(item) and not tie_problems(item, targets)


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
            r = _row(name, "N/A", "See yaml", source, "NOT APPLICABLE",
                     "No conditions written in targets.yaml; listed for the maintainer's approval")
            r.update(key=name, kind=kind_of(item), reads="NOT APPLICABLE")
            results.append(r)
            continue

        scenarios = conditions_of(item).get("scenario")
        matching = [r for r in runs if scenarios is None or run_type(r)[0] in scenarios]
        for run in matching or [None]:
            rows = evaluate_run(name, item, run, ages)
            if len(runs) > 1 and run is not None:
                tag = Path(run["path"]).name
                for r in rows:
                    r["target"] = f"{r['target']} [{tag}]"
            for r in rows:      # one run is never a verdict: an independent row can't PASS here (pass rule part 5)
                r["kind"] = kind_of(item)
                r["reads"] = reads_for(r, item, targets)
            results.extend(rows)

    return results, unconditioned


def ensemble_folders(folder: Path) -> list[Path]:
    """The runs of an ensemble: each folder directly inside it with a stats.json or plot.json."""
    return sorted((d for d in Path(folder).iterdir() if d.is_dir() and ((d / "stats.json").exists() or (d / "plot.json").exists())),
                  key=lambda d: d.name)


def evaluate_ensemble(targets: dict[str, Any], runs: list[dict[str, Any]], ages: list[int],
                      facts: dict[str, Any] | None = None, frozen: bool = False) -> list[dict[str, Any]]:
    """One row per target and age: the ensemble mean against the band is the band check ('status');
    the spread and the share of seeds inside the band go next to it.  'reads' is what prints:
    an independent row reads PASS only when the pass rule holds, with facts about the runs
    (ensemble_facts, worked out here when not given) and frozen (the approved tag is in the
    runs' history, worked out by the caller; False unless said)."""
    if facts is None:
        facts = ensemble_facts(runs)
    flat = dict(flatten_targets(targets))
    out = _ensemble_rows(targets, runs, ages)
    for r in out:
        item = flat.get(r["key"], {})
        r["kind"] = kind_of(item)
        r["reads"] = reads_for(r, item, targets, facts, frozen)
    return out


def _ensemble_rows(targets: dict[str, Any], runs: list[dict[str, Any]], ages: list[int]) -> list[dict[str, Any]]:
    per_run = [evaluate_targets(targets, [r], ages=ages)[0] for r in runs]
    order, grouped = [], {}
    for rows in per_run:
        for r in rows:
            if r["target"] not in grouped:
                order.append(r["target"])
                grouped[r["target"]] = []
            grouped[r["target"]].append(r)
    out = []
    for name in order:
        rows = grouped[name]
        scored = [r for r in rows if r.get("value") is not None]
        first = rows[0]
        if not scored:
            out.append({"target": name, "mean": None, "sd": None, "seeds": 0, "target_range": first["target_range"],
                        "status": first["status"], "share": None, "source": first["source"], "notes": first["notes"],
                        "key": first.get("key", name), "band": None})
            continue
        values = [r["value"] for r in scored]
        mean = statistics.fmean(values)
        lo, hi = scored[0]["band"]
        inside = sum(1 for r in scored if r["band"][0] <= r["value"] <= r["band"][1])
        info = any(r["status"] == "INFO" for r in scored)
        status = "INFO" if info else ("PASS" if lo <= mean <= hi else "FAIL")
        notes = scored[0]["notes"]
        if "subcanopy_light_transmittance" in name:
            # the band is the range of single readings, so show how far the mean is from their median too (the maintainer, 2026-11-06)
            median = targets.get("stand_canopy", {}).get("subcanopy_light_transmittance", {}).get("target_median_pct")
            if median is not None:
                notes = f"{mean - float(median):+.1f} points from the paper's median of {float(median):g} %; {notes}"
        out.append({"target": name, "mean": mean, "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "seeds": len(values), "target_range": scored[0]["target_range"], "status": status,
                    "share": inside / len(values), "source": first["source"], "notes": notes,
                    "key": first.get("key", name), "band": (lo, hi)})
    return out


def row_age(row: dict[str, Any]) -> int | None:
    m = re.search(r"\(age (\d+)", row["target"])
    return int(m.group(1)) if m else None


def independent_header(rows: list[dict[str, Any]], targets: dict[str, Any], ages=(50, 60)) -> str:
    """How many independent rows apply at each age, and how many of them read PASS.  A row applies when
    it is scored (not INFO), is not tied (either way) to a figure that isn't independent, and either has a
    value in at least MIN_RUNS runs itself (pass rule part 5) or reads FAIL: too few runs keeps a row from
    passing, never takes a failing row out of the count.  Rows left out for too few runs are listed with what
    they read."""
    flat = dict(flatten_targets(targets))
    parts_apply, parts_pass, short = [], [], []
    for age in ages:
        independent = [r for r in rows if row_age(r) == age and r["status"] in ("PASS", "FAIL")
                       and counts_as_independent(flat.get(r["key"], {}), targets)]
        apply = [r for r in independent if (r.get("seeds") or 0) >= MIN_RUNS or r["reads"] == "FAIL"]
        short += [f"{r['target']}, a value in {r.get('seeds') or 0} runs, reads {r['reads']}"
                  for r in independent if r not in apply]
        passed = sum(1 for r in apply if r["reads"] == "PASS")
        parts_apply.append(f"age {age}: {len(apply)}")
        parts_pass.append(f"{passed} of {len(apply)} at {age}")
    out = (f"Independent rows that apply: {', '.join(parts_apply)}.  Independent passes: {'; '.join(parts_pass)}.  "
           f"A row tied (either way) to a figure that isn't independent, or with a value set against it, is never counted; "
           f"an in-band row with a value in fewer than {MIN_RUNS} runs isn't counted, and a clean independent row that reads FAIL always is.")
    unread = tie_text_problems(targets)
    if unread:
        out += f"  No independent row is clean while a tie can't be read: {'; '.join(unread)}."
    if short:
        out += f"  Not counted, too few runs with a value: {'; '.join(short)}."
    return out


def _detail(item: dict[str, Any], name: str | None = None, graph: dict[str, list[str]] | None = None) -> str:
    """Stands, values set and ties, for the notes of a row: its own ties, and ties written on other rows that
    name it (graph: tie_graph of the targets; name: the row's target)."""
    bits = []
    if item.get("stands") not in (None, ""):
        bits.append(f"stands: {item['stands']}")
    if item.get("values_set"):
        bits.append(f"values set: {', '.join(item['values_set'])}")
    own = ties_of(item)
    if "tied_to" in item and not isinstance(item["tied_to"], list):
        bits.append(f"tied_to not a list: {item['tied_to']!r}")
    elif own:
        bits.append(f"tied to: {', '.join(own)}")
    others = [u for u in (graph or {}).get(name, []) if u not in own] if name else []
    if others:
        bits.append(f"tied to (written on the other row): {', '.join(others)}")
    return "; ".join(bits)


def blocks(rows: list[dict[str, Any]], targets: dict[str, Any], line_of) -> list[str]:
    """The rows in one block per kind (BLOCKS, from each row's 'kind'), each block under its own heading;
    empty blocks say so.  The targets give each row's stands, values set and ties for its notes."""
    flat = dict(flatten_targets(targets))
    graph = tie_graph(targets)
    lines = []
    for kind, title in BLOCKS:
        mine = [r for r in rows if r.get("kind") == kind]
        if kind is None and not mine:
            continue
        lines += ["", f"### {title}", ""]
        if not mine:
            lines.append("- none")
            continue
        lines += line_of(None)
        lines += [line_of(r, _detail(flat.get(r.get("key"), {}), r.get("key"), graph)) for r in mine]
        if kind == INDEPENDENT:
            lines += ["", "The pass rule (all seven must hold for PASS):"] + [f"- {p}" for p in PASS_RULE]
    return lines


def print_ensemble(rows: list[dict[str, Any]], header: str, targets: dict[str, Any] | None = None) -> str:
    def line_of(r, detail=""):
        if r is None:
            return ["| Target | Ensemble mean | SD | Seeds | Target Range / Value | Reads | Share of seeds inside | Source | Notes |",
                    "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|"]
        notes = "; ".join(x for x in (r["notes"], detail) if x)
        reads = r["reads"]          # never the band check alone: a tuned or by-design row inside its band isn't a PASS
        if r["mean"] is None:
            return f"| `{r['target']}` | N/A | N/A | 0 | {r['target_range']} | **{reads}** | N/A | {r['source']} | {notes} |"
        return (f"| `{r['target']}` | {r['mean']:.3f} | {r['sd']:.3f} | {r['seeds']} | {r['target_range']} | **{reads}** | "
                f"{100 * r['share']:.0f} % | {r['source']} | {notes} |")

    targets = targets or {}
    lines = [header, "", independent_header(rows, targets)]
    lines += blocks(rows, targets, line_of)
    lines += ["", "The band check is the ensemble mean against the band. The band shown is the first seed's where it depends on the seed.",
              "Reads: FAIL is outside the band, in every block. Inside, a row reads by its kind: HELD (by design), IN BAND (tuned), "
              "IN BAND (seen), IN BAND (out of sample); an independent row reads PASS only under the pass rule.",
              "INFO: information only (scoring: info in targets.yaml), never PASS/FAIL; \"outside the band (a miss)\" says the value is outside its range."]
    return "\n".join(lines)


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
                    header: str | None = None, targets: dict[str, Any] | None = None) -> str:
    """Single runs: the same blocks as an ensemble.  One run is never a verdict, so no row reads PASS.
    Without the targets, the rows' own kinds are used."""
    def line_of(r, detail=""):
        if r is None:
            return ["| Target | Model Value | Target Range / Value | Reads | Source | Stated Conditions / Notes |",
                    "|---|:---:|:---:|:---:|:---:|---|"]
        notes = "; ".join(x for x in (r["notes"], detail) if x)
        return f"| `{r['target']}` | {r['model_value']} | {r['target_range']} | **{r['reads']}** | {r['source']} | {notes} |"

    lines = []
    if header:
        lines.append(header)
    lines.append("One run is not a verdict (PROTOCOL 2): no row reads PASS here.")
    lines += blocks(results, targets or {}, line_of)

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


# Reported rows of tools/independent_checks.py whose figure is a target here: their kind is taken from targets.yaml,
# so the --independent table never contradicts the blocks above it.
WOOD_TARGETS = (("stem wood", "tree_allometry.stem_biomass_repola"), ("branch wood", "tree_allometry.branch_biomass_repola"))


def wood_kinds_from_targets(rows: list[dict[str, Any]], targets: dict[str, Any]) -> list[dict[str, Any]]:
    """Each reported row about stem or branch wood against Repola takes the kind and reason of its target in the
    targets read; when that file has no kind (one from before the kinds), the working copy's reference/targets.yaml
    gives it, and the note says so."""
    flat = dict(flatten_targets(targets))
    local = None
    out = []
    for r in rows:
        for word, key in WOOD_TARGETS:
            if word in r.get("what", ""):
                item, where = flat.get(key), "the targets read"
                if kind_of(item) is None:
                    if local is None:
                        with open(ROOT / "reference" / "targets.yaml", encoding="utf-8") as f:
                            local = dict(flatten_targets(yaml.safe_load(f)))
                    item, where = local.get(key), "the working copy of reference/targets.yaml (the targets read have no kind)"
                kind = kind_of(item) or "no kind"
                r = dict(r, kind=kind, note=f"kind of {key} in {where}: {(item or {}).get('kind_reason', 'none given')}")
                break
        out.append(r)
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Evaluate simulation outputs against approved targets.")
    parser.add_argument("paths", nargs="*", help="Paths to run outputs (plot.json, stats.json, or output directories)")
    parser.add_argument("--ensemble", default=None, help="a folder holding one run per seed: the verdict is the ensemble mean")
    parser.add_argument("--age", type=int, action="append", default=None,
                        help="Age to evaluate (repeatable); default 50 and 60 where the run reaches them")
    parser.add_argument("--ref", default=TAG,
                        help=f"git ref to read reference/targets.yaml from (default: the tag {TAG})")
    parser.add_argument("--independent", action="store_true",
                        help="with --ensemble: also print the reported rows of tools/independent_checks.py, which are outside the approved targets and never PASS/FAIL")
    args = parser.parse_args()

    targets = load_approved_targets(args.ref)
    if args.ensemble:
        folders = ensemble_folders(Path(args.ensemble))
        if not folders:
            parser.error(f"no runs in {args.ensemble}")
        runs = [load_run_data(str(d)) for d in folders]
        ages = args.age or default_ages(runs)
        approved = commit_of(args.ref) == commit_of(TAG)
        header = f"Targets: reference/targets.yaml at {args.ref} (commit {commit_of(args.ref)})."
        if not approved:
            header += f" NOT the approved tag {TAG} (commit {commit_of(TAG)}): results are a preview, not approved."
        facts = ensemble_facts(runs)
        frozen = approved and frozen_first(facts["commit"])
        header += f" Ensemble: {args.ensemble}, {len(runs)} runs at commit {facts['commit'] or 'more than one or unknown'}."
        print(print_ensemble(evaluate_ensemble(targets, runs, ages, facts=facts, frozen=frozen), header, targets))
        if args.independent:
            import independent_checks
            print()
            rows = wood_kinds_from_targets(independent_checks.rows_for(args.ensemble), targets)
            print(independent_checks.table(rows, "Reported checks, outside the approved targets"))
        return
    if not args.paths:
        parser.error("give run paths or --ensemble")
    runs = [load_run_data(p) for p in args.paths]

    results, unconditioned = evaluate_targets(targets, runs, ages=args.age)
    header = f"Targets: reference/targets.yaml at {args.ref} (commit {commit_of(args.ref)})."
    if commit_of(args.ref) != commit_of(TAG):
        header += f" NOT the approved tag {TAG} (commit {commit_of(TAG)}): results are a preview, not approved."
    header += f" Runs: {', '.join(args.paths)}"
    print(print_scorecard(results, unconditioned, header, targets))


if __name__ == "__main__":
    main()
