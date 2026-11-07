"""A plot-year as a plain list of trees, in JSON: what a stand template could be made from.

    python tools/forest.py run --seed 1 --area 1000 --years 60 --tree-lists 20,30,40,50,60 --out out/forest/a
        # writes out/forest/a/trees_020.json and so on, as the run passes those years
    python tools/tree_list.py out/some_plot --out trees.json
        # from a tools/plot.py folder with a checkpoint: the year that checkpoint holds

Each tree: position in metres from the plot's centre (the plot repeats at its edges, so a list tiles),
species, age, height, DBH over bark (null below 1.3 m), crown base, crown width, alive or dead.  A dead
tree is given as it was in its last year, with the year it died and why; the model has no standing
dead, so dead_years only says how long back to list them.  No decay or fall is implied.
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from treegen.thinning import over_bark_cm  # noqa: E402

BARK = (-0.48552367, 0.04957885, 0.84676248)     # tools/bark.py; for plots whose species has no mortality block


def _row(id_: int, x: float, y: float, species: str, last: dict, bark) -> dict:
    wood = last.get("dbh_cm")
    return {"id": id_, "x_m": round(x, 3), "y_m": round(y, 3), "species": species, "age_years": int(last["age_years"]),
            "height_m": round(float(last["height_m"]), 3),
            "dbh_cm": None if wood is None else round(float(over_bark_cm(wood, bark)), 2),
            "crown_base_m": None if last.get("crown_base_height_m") is None else round(float(last["crown_base_height_m"]), 3),
            "crown_width_m": round(float(last.get("crown_width_m") or 0.0), 3)}


def last_year_of(model) -> dict:
    """What a list needs from a living tree's last yearly row."""
    s = model.stats[-1]
    return {"age_years": model.year, "height_m": s["height_m"], "dbh_cm": s.get("dbh_cm"),
            "crown_base_height_m": s.get("crown_base_height_m"), "crown_width_m": s.get("crown_width_m")}


def tree_list(plot, dead_years: int = 10, run: dict | None = None) -> dict:
    """The plot as it stands at the end of plot.year, and what died in the dead_years before it."""
    species = plot.species.species.scientific_name
    bark = getattr(getattr(plot.species, "mortality", None), "bark_double_mm", BARK)
    sides = plot._sides()
    trees = []
    for k in plot.alive:
        i = plot.info[k]
        trees.append(dict(_row(k, i["x"], i["y"], species, last_year_of(plot.trees[k]), bark), alive=True))
    for i in plot.info:
        removed = i.get("removed")
        if removed is None or removed <= plot.year - dead_years or "last" not in i:
            continue
        trees.append(dict(_row(i["id"], i["x"], i["y"], species, i["last"], bark), alive=False, died_year=removed, cause=i.get("cause")))
    return {"plot_year": plot.year, "years_since_stand_began": plot.year, "side_x_m": sides[0], "side_y_m": sides[1], "area_m2": plot.area,
            "repeats_at_edges": True, "origin": "centre of the plot", "dbh": "over bark at 1.3 m, tools/bark.py; null below 1.3 m",
            "crown_width": "mean of the widths along x and y", "seed": plot.seed, "mode": plot.mode, "run": run or {},
            "trees_alive": len(plot.alive), "trees": trees}


def write(plot, path, dead_years: int = 10, run: dict | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree_list(plot, dead_years, run), indent=0), encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", help="a plot folder with a checkpoint.pkl (tools/plot.py); read only")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dead-years", type=int, default=10)
    a = ap.parse_args()
    # not Plot.resume: that tidies the folder for a run that carries on
    with open(Path(a.folder) / "checkpoint.pkl", "rb") as f:
        plot = pickle.load(f)
    print(write(plot, a.out, a.dead_years))


if __name__ == "__main__":
    main()
