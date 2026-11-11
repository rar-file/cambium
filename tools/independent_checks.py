"""Reported rows beside the scorecard: checks that sit outside the approved targets (review 2026-11-09, top 5, item 2).

    python tools/independent_checks.py out/bench/ensemble/node_f5_trees out/bench/ensemble/node_f5_plots
    python tools/scorecard.py --ensemble out/bench/ensemble/node_f5_plots --independent      # the same rows, after the scorecard's

Nothing here is PASS or FAIL, and nothing here is an approved target: each row shows the model's ensemble mean beside
a published figure, and says whether any model value was ever set against that figure ("kind").  A row with no
published figure in the repository says so; a target for it has to be proposed to the maintainer and approved first.

Reference figures and where they come from (none is in the approved targets as a scored band):
* Repola 2008, Silva Fennica 42(4):605, Eqs. 7 and 9, as coded in tools/m3_wood.py: stem wood and living branches
  from the tree's own over-bark diameter and height.  Model wood has no bark; Repola's branches include it.
* Repola 2008, Eq. A3 (tools/m3_wood.py repola_a3): living branches from diameter, height and living crown length,
  the equation he recommends for crown parts.  Branch wood is shown against all three side by side (design round
  2026-11-11): Eq. 9, A3 at the tree's own crown length, and A3 at his sample's mean crown ratio, 0.58, which takes
  the model's crown length out of the comparison.  His sample trees were 2.5-38.0 cm at breast height: each of these
  rows says how many stems are inside that, and reads INFO when under two thirds are.
* Hagemeier & Leuschner 2019, Forests 10(3):265, Table 3, as quoted in reference/targets.yaml (stand_density.measures):
  site 1, 45 yr: dbh 19 +- 6 cm, height 20 +- 3 m; site 2, 67 yr: 25 +- 3 cm, 25 +- 3 m.  Basal area 25.2 and
  28.5 m2/ha as quoted in reports/birch_v1_final.md; those printed figures don't add up (QUESTIONS.md Q32).
* Hagemeier & Leuschner 2019b, Forests 10(10):925: median light 14.8 %, as in reference/targets.yaml.

Diameters: a stand tree's yearly row holds its wood diameter, so bark is added here (tools/bark.py).  A plot's tree
list holds the diameter over bark already (tools/tree_list.py), so none is added to it: adding it twice made plot
branch wood read about 1.3 times better than it is (reports/design/2026-11-11_branch_wood_challenge.md, problem 1).
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bark import dbh_over_bark  # noqa: E402
from m3_wood import REPOLA_CROWN_RATIO, REPOLA_D_RANGE_CM, repola, repola_a3  # noqa: E402

AGES = (30, 45, 50, 60)
LIGHT_MEDIAN_PCT = 14.8
HAGEMEIER = {45: {"dbh": (19.0, 6.0), "height": (20.0, 3.0), "basal_area": 25.2},
             67: {"dbh": (25.0, 3.0), "height": (25.0, 3.0), "basal_area": 28.5}}

INDEPENDENT = "independent"
SEEN = "seen"
TUNED = "tuned against"
PARTLY = "partly"
INFO_UNDER = 2.0 / 3.0      # an equation row reads INFO when fewer of its stems than this are inside the equation's diameters

# the three branch equations, in the order they are shown
BRANCH_EQUATIONS = (("eq9", "Repola's Eq. 9, from diameter and height"),
                    ("a3_own", "Repola's Eq. A3, at the tree's own crown length"),
                    ("a3_mean", f"Repola's Eq. A3, at his sample's mean crown ratio, {REPOLA_CROWN_RATIO:g}"))


def _mean(xs: list) -> str:
    xs = [float(x) for x in xs]
    if not xs:
        return "not saved"
    return f"{statistics.fmean(xs):.3g} ({min(xs):.3g}-{max(xs):.3g}), n {len(xs)}"


def _gmean(xs: list) -> str:
    """A ratio's mean on the log scale, with the plain mean beside it: one tree far over doesn't pull it up."""
    xs = [float(x) for x in xs if x and x > 0.0]
    if not xs:
        return "not saved"
    return f"{math.exp(statistics.fmean(math.log(x) for x in xs)):.3g} ({min(xs):.3g}-{max(xs):.3g}), n {len(xs)}; plain mean {statistics.fmean(xs):.3g}"


def _row(what, age, model, reference, kind, note, inside=None) -> dict:
    """inside: (stems inside the equation's diameter range, stems), for a row read off an equation."""
    row = {"what": what, "age": age, "model": model, "reference": reference, "kind": kind, "note": note, "inside": None, "reads": None}
    if inside is not None and inside[1]:
        row["inside"] = inside[0] / inside[1]
        row["inside_text"] = f"{inside[0]} of {inside[1]}"
        row["reads"] = "INFO" if row["inside"] < INFO_UNDER else None
    return row


def branch_equations(d_ob_cm: float, h_m: float, crown_base_m) -> dict:
    """Repola's living branches for one tree (kg), three ways.  d_ob_cm: over bark.  The tree's own crown length is its height less
    its crown base; None for a tree with no crown base to read."""
    own = None if crown_base_m is None else repola_a3(d_ob_cm, h_m, max(h_m - float(crown_base_m), 0.0))
    return {"eq9": repola(d_ob_cm, h_m)[1], "a3_own": own, "a3_mean": repola_a3(d_ob_cm, h_m, REPOLA_CROWN_RATIO * h_m)}


def in_range(d_ob_cm: float) -> bool:
    return REPOLA_D_RANGE_CM[0] <= d_ob_cm <= REPOLA_D_RANGE_CM[1]


def branch_kind() -> tuple:
    """(kind, note) for the branch rows, read off the species file's own label of the value that sets branch wood, not written
    here: its comment on pipe_model.branch_sapwood_senescence says what that value was set against."""
    from treegen import species_schema as schema

    try:
        said = schema.tuned_in_comments((ROOT / "species" / "betula_pendula.yaml").read_text(encoding="utf-8")).get("pipe_model.branch_sapwood_senescence", "")
    except OSError:
        said = ""
    if "Repola" in said:
        return TUNED, "the species file's own label of pipe_model.branch_sapwood_senescence: \"" + said.split(":")[0].strip() + "\""
    return INDEPENDENT, "the species file labels no value as set against it"


def tree_rows(folder: Path, ages=AGES) -> list:
    """Stand trees grown by tools/tree_table.py: wood against Repola at the tree's own size, and stem volume a hectare."""
    runs = []
    for d in sorted(Path(folder).glob("*_stand")):
        if (d / "tree.json").exists() and (d / "stats.json").exists():
            snaps = {s["age"]: s for s in json.loads((d / "tree.json").read_text(encoding="utf-8"))["snapshots"]}
            years = {r["year"]: r for r in json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]}
            runs.append((snaps, years))
    kind, why = branch_kind()
    rows = []
    for age in ages:
        stem, vol, inside = [], [], 0
        branch = {k: [] for k, _ in BRANCH_EQUATIONS}
        for snaps, years in runs:
            s, y = snaps.get(age), years.get(age)
            if s is None or y is None or not y.get("dbh_cm"):
                continue
            d_ob, h = float(dbh_over_bark(float(y["dbh_cm"]))), float(y["height_m"])     # the yearly row's diameter is wood: bark is added once, here
            stem.append(s["stem_kg"] / repola(d_ob, h)[0])
            inside += in_range(d_ob)
            for k, kg in branch_equations(d_ob, h, y.get("crown_base_height_m")).items():
                if kg:
                    branch[k].append(s["branch_kg"] / kg)
            if y.get("lai") and y.get("leaf_area_m2"):
                vol.append(s["stem_m3"] * float(y["lai"]) * 1e4 / float(y["leaf_area_m2"]))
        if not stem:
            continue
        rows.append(_row("stem wood over Repola's at its own DBH and height (ratio)", age, _mean(stem), "1.0", SEEN,
                         "seen, not independent: no value was fitted to it, but ring_share_max was chosen while this ratio was watched (it ran 12-20 % over without it)"))
        for k, name in BRANCH_EQUATIONS:
            rows.append(_row(f"branch wood over {name} (ratio, mean on the log scale)", age, _gmean(branch[k]), "1.0; Repola's branches include bark, the model's don't",
                             kind, why, (inside, len(stem))))
        rows.append(_row("stem volume, wood only (m3/ha), stand tree x its stems/ha", age, _mean(vol), "none in the repository", INDEPENDENT,
                         "needs a yield table read at its source: proposed, not approved"))
    return rows


def plot_branch_wood(trees: list, area_m2: float) -> dict:
    """One plot's living stems past 1.3 m: branch wood a hectare (t/ha) as the model has it (None if the list saved no wood) and by
    Repola's three equations at each tree's own size, and how many stems are inside his diameters.  trees: a tree list's rows,
    whose dbh_cm is over bark already.  A tree with no crown base is left out of the own-crown-length sums, both sides."""
    stems = [t for t in trees if t.get("alive") and t.get("dbh_cm")]
    out = {"stems": len(stems), "inside": sum(in_range(float(t["dbh_cm"])) for t in stems), "repola": {}, "model": {}}
    per = [(t, branch_equations(float(t["dbh_cm"]), float(t["height_m"]), t.get("crown_base_m"))) for t in stems]
    saved = bool(stems) and all(t.get("branch_kg") is not None for t in stems)
    for k, _ in BRANCH_EQUATIONS:
        used = [(t, eq[k]) for t, eq in per if eq[k]]
        out["repola"][k] = sum(kg for _, kg in used) / area_m2 * 10.0
        out["model"][k] = sum(float(t["branch_kg"]) for t, _ in used) / area_m2 * 10.0 if saved else None
    out["model_t_ha"] = sum(float(t["branch_kg"]) for t in stems) / area_m2 * 10.0 if saved else None
    return out


def plot_rows(folder: Path, ages=AGES) -> list:
    """Forest plots grown by tools/forest.py: basal area, the spread of diameters and heights, light against the median, and branch
    wood a hectare against Repola's three equations."""
    plots = []
    for d in sorted(Path(folder).glob("plot_*")):
        if (d / "plot.json").exists():
            stats = {s["year"]: s for s in json.loads((d / "plot.json").read_text(encoding="utf-8"))["stats"]}
            plots.append((d, stats))
    kind, why = branch_kind()
    rows = []
    for age in ages:
        ref = HAGEMEIER.get(age) or (HAGEMEIER[67] if age == 60 else None)
        at = "" if age in HAGEMEIER or ref is None else " (the 67-year stand, not this age)"
        ba, light, cv, d_mean, h_sd, h_mean, wood = [], [], [], [], [], [], []
        for d, stats in plots:
            s = stats.get(age)
            if s is None:
                continue
            if s.get("basal_area_ob_m2_ha") is not None:
                ba.append(s["basal_area_ob_m2_ha"])
            if s.get("subcanopy_diffuse_light_pct") is not None:
                light.append(s["subcanopy_diffuse_light_pct"] - LIGHT_MEDIAN_PCT)
            lst = d / f"trees_{age:03d}.json"
            if lst.exists():
                doc = json.loads(lst.read_text(encoding="utf-8"))
                trees = [t for t in doc["trees"] if t["alive"] and t.get("dbh_cm")]
                if len(trees) >= 3:
                    ds, hs = [t["dbh_cm"] for t in trees], [t["height_m"] for t in trees]
                    d_mean.append(statistics.fmean(ds))
                    cv.append(statistics.stdev(ds) / statistics.fmean(ds))
                    h_mean.append(statistics.fmean(hs))
                    h_sd.append(statistics.stdev(hs))
                if trees and doc.get("area_m2"):
                    wood.append(plot_branch_wood(trees, float(doc["area_m2"])))
        if not (ba or light):
            continue
        rows.append(_row("basal area over bark (m2/ha)", age, _mean(ba), f"{ref['basal_area']}{at}; Q32 open" if ref else "none at this age", TUNED,
                         "stems/ha and Dg were tuned against Hagemeier (wind_speed, sdi_max, rate_at_max), so basal area follows"))
        rows.append(_row("light under the canopy, points from the 14.8 % median", age, _mean(light), "0", TUNED,
                         "shedding thresholds and death lines were set against light"))
        if cv:
            rows.append(_row("mean DBH over bark of stems past 1.3 m (cm)", age, _mean(d_mean), f"{ref['dbh'][0]:g}{at}" if ref else "none at this age", TUNED,
                             "Dg was tuned against"))
            rows.append(_row("spread of DBH: SD over mean", age, _mean(cv), f"{ref['dbh'][1] / ref['dbh'][0]:.2f}{at}" if ref else "none at this age", INDEPENDENT,
                             "no value was set against the spread"))
            rows.append(_row("mean height of stems past 1.3 m (m)", age, _mean(h_mean), f"{ref['height'][0]:g}{at}" if ref else "none at this age", PARTLY,
                             "top height follows the curve by design; the mean of all stems doesn't"))
            rows.append(_row("spread of height: SD (m)", age, _mean(h_sd), f"{ref['height'][1]:g}{at}" if ref else "none at this age", INDEPENDENT,
                             "no value was set against it; a tree's height limit goes with its drawn vigour (plot.vigour_sd)"))
        if wood:
            inside = (sum(w["inside"] for w in wood), sum(w["stems"] for w in wood))
            saved = [w for w in wood if w["model_t_ha"] is not None]
            for k, name in BRANCH_EQUATIONS:
                ratios = [w["model"][k] / w["repola"][k] for w in saved if w["repola"][k] > 0.0]
                repola_t = statistics.fmean(w["repola"][k] for w in wood)
                model = _gmean(ratios) if ratios else "the tree lists saved no wood (runs before 2026-11-11)"
                rows.append(_row(f"plot branch wood over {name} (ratio of the plot's sums over stems past 1.3 m, mean on the log scale)", age, model,
                                 f"1.0; Repola's side is {repola_t:.3g} t/ha, bark included; the tree lists' DBH is over bark already", kind, why, inside))
            if saved:
                rows.append(_row("plot branch wood, stems past 1.3 m (t/ha, wood only)", age, _mean([w["model_t_ha"] for w in saved]), "see the three rows above", kind, why))
    return rows


def rows_for(folder) -> list:
    folder = Path(folder)
    return tree_rows(folder) + plot_rows(folder)


def table(rows: list, header: str = "") -> str:
    lines = ([header, ""] if header else []) + ["| Check | Age | Model: mean (lowest-highest), runs | Published figure | Kind | Stems inside the equation's diameters | Note |",
                                                "|---|:---:|:---:|:---:|:---:|:---:|---|"]
    for r in rows:
        inside = "-" if r.get("inside") is None else r["inside_text"] + ("; **INFO**: under two thirds" if r.get("reads") else "")
        lines.append(f"| {r['what']} | {r['age']} | {r['model']} | {r['reference']} | **{r['kind']}** | {inside} | {r['note']} |")
    lines += ["", "Reported rows, never PASS/FAIL: none of these is an approved target. Kind: independent = no model value was set against it; seen = no value was fitted to it, but it was watched while a value was chosen. "
                  f"A row read off an equation is INFO when under two thirds of its stems are inside the equation's diameters ({REPOLA_D_RANGE_CM[0]:g}-{REPOLA_D_RANGE_CM[1]:g} cm "
                  "over bark for Repola's branch equations)."]
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for folder in sys.argv[1:]:
        print(table(rows_for(folder), f"Reported checks, outside the approved targets: {folder}"))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
