"""What treegen/damage.py would do to trees already grown: nothing is grown or changed, and the damage settings
needn't be on.  Yearly chances at ages 50 and 60 over a saved ensemble of stand trees or plots.

    python tools/damage_check.py out/bench/ensemble/base_trees
    python tools/damage_check.py out/bench/ensemble/base_plots --age 50 --age 60

A saved run holds root numbers for its last year only (and a plot's living trees none), so at other ages a tree's
critical turning moment is Krisans' regression on its size.  Crown wood is taken as 17 % of the stem's, the share
in Repola's functions at this size (66-73 kg on 390-413 kg, reports/reset_brief.md).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from treegen import damage  # noqa: E402
from treegen.params import load_species  # noqa: E402

CROWN_WOOD_SHARE = 0.17
SNOW_LOADS = 5          # points across the load range
DRAWS = 100             # draws per tree of how a hit tree fails


def stems_from_thinning(sp, height: float) -> float:
    rows = sorted(sp.stand.thinning, key=lambda r: float(r.from_height_m))
    return next(float(r.stems_per_ha) for r in reversed(rows) if height >= float(r.from_height_m))


def state_of(record: dict, age: int, sp, stems: float, basal: float | None, anchorage=None) -> damage.TreeState:
    h, d = float(record["height_m"]), float(record["dbh_cm"])
    if basal is None:
        basal = stems * math.pi / 4.0 * (d * float(sp.damage.dbh_over_bark_factor) / 100.0) ** 2
    stem_kg = float(sp.mechanics.wood_density) * float(sp.damage.stem_form_factor) * math.pi / 4.0 * (d / 100.0) ** 2 * h
    return damage.TreeState(age, h, d, record.get("crown_base_height_m"), float(record.get("crown_width_m") or 0.0),
                            stems, basal, False, 0.0, CROWN_WOOD_SHARE * stem_kg, anchorage)


def chances(state: damage.TreeState, sp, rng) -> dict:
    """Yearly chance, per tree: wind damage, of which how much uproots or kills; snow failure; old age; any death."""
    dp = sp.damage
    wind = 1.0 - (1.0 - damage.wind_damage_probability(state, dp)) ** (1.0 / float(dp.wind.period_years))
    uproot = fatal = 0
    for _ in range(DRAWS):
        weather = damage.draw_weather(rng, dp)
        event = damage._failure(state, weather, sp, rng, "wind")
        uproot += event.plate is not None
        fatal += event.fatal
    lo, hi = (float(v) for v in dp.snow.load_range_kg_m2)
    overload = float(np.mean([damage.snow_overload_probability(state, load, sp) for load in np.linspace(lo, hi, SNOW_LOADS)]))
    snow = overload * float(dp.snow.break_share) / float(dp.snow.return_years)
    old = damage.old_age_hazard(state.age, dp.old_age)
    return {"hd": state.height_m / (float(state.dbh_cm) * float(dp.dbh_over_bark_factor)), "wind": wind, "uproot_share": uproot / DRAWS,
            "wind_death": wind * fatal / DRAWS, "snow": snow, "snow_death": snow * fatal / DRAWS, "old": old,
            "death": wind * fatal / DRAWS + snow * fatal / DRAWS + old}


def trees_of(folder: Path, age: int, sp) -> tuple:
    """(states, label, stems per hectare): saved stand trees, or the living trees of saved plots."""
    states = []
    stems_all = []
    stands = sorted(folder.glob("*_stand"))
    for d in stands:
        s = json.loads((d / "stats.json").read_text(encoding="utf-8"))
        r = next((r for r in s["per_year"] if r.get("year") == age), None)
        if r and r.get("dbh_cm"):
            last = s["per_year"][-1]["year"] == age
            stems = stems_from_thinning(sp, float(r["height_m"]))
            states.append(state_of(r, age, sp, stems, None, s.get("anchorage") if last else None))
            stems_all.append(stems)
    if stands:
        return states, f"{len(stands)} stand trees", float(np.mean(stems_all)) if stems_all else 0.0
    plots = sorted(p for p in folder.iterdir() if (p / "plot.json").exists())
    factor = float(sp.damage.dbh_over_bark_factor)
    for p in plots:
        plot = json.loads((p / "plot.json").read_text(encoding="utf-8"))
        rows = []
        for k, t in enumerate(plot["trees"]):
            f = p / f"tree_{k:03d}" / "stats.json"
            if not f.exists() or (t.get("removed") is not None and t["removed"] <= age):
                continue
            y = age - int(t.get("germination", 0) or 0)
            r = next((r for r in json.loads(f.read_text(encoding="utf-8"))["per_year"] if r.get("year") == y), None)
            if r and r.get("dbh_cm"):
                rows.append((r, y))
        ha = float(plot["area_m2"]) / 1e4
        # the overstorey, as in damage.plot_year
        over = [float(r["dbh_cm"]) * factor / 100.0 for r, _ in rows if float(r["dbh_cm"]) * factor >= float(sp.damage.wind.min_dbh_cm)]
        stems = len(over) / ha
        basal = sum(math.pi / 4.0 * d ** 2 for d in over) / ha
        states += [state_of(r, y, sp, stems, basal) for r, y in rows]
        stems_all.append(len(rows) / ha)
    return states, f"{len(states)} trees on {len(plots)} plots", float(np.mean(stems_all)) if stems_all else 0.0


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ensemble")
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--age", type=int, action="append", default=None)
    a = ap.parse_args(argv)
    sp, _ = load_species(a.species)
    print(f"{a.ensemble}: chances per tree per year, % (nothing grown)\n")
    print("| Age | Trees | Stems/ha | H/D over bark | Wind damage | of which uprooted | Snow failure | Old age | Death from all three | Stems/ha lost per decade |")
    print("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    rng = np.random.default_rng(1)
    for age in a.age or [50, 60]:
        states, label, stems = trees_of(Path(a.ensemble), age, sp)
        if not states:
            print(f"| {age} | none at this age | | | | | | | | |")
            continue
        rows = [chances(s, sp, rng) for s in states]
        mean = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
        print(f"| {age} | {label} | {stems:.0f} | {mean['hd']:.2f} | {100 * mean['wind']:.3f} | {100 * mean['uproot_share']:.0f} % | "
              f"{100 * mean['snow']:.3f} | {100 * mean['old']:.4f} | {100 * mean['death']:.3f} | {stems * 10 * mean['death']:.0f} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
