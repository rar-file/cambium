"""tools/tree_table.py only reads the model: measuring a tree as it grows changes no number."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import tree_table  # noqa: E402

from treegen.environment import make_environment, make_soil  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402
from treegen.params import load_environment, load_species  # noqa: E402


def _model(seed: int = 4):
    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    return GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)


def test_measuring_changes_nothing():
    plain, read = _model(), _model()
    for year in range(1, 13):
        plain.step()
        read.step()
        tree_table.snapshot(read, year)
        tree_table.shed_events(read)
    assert json.dumps(plain.stats, sort_keys=True) == json.dumps(read.stats, sort_keys=True)


def test_shed_events_count_each_axis_once():
    model = _model()
    for _ in range(14):
        model.step()
    events = tree_table.shed_events(model)
    T = model.tree
    dead_firsts = ((T.death[: T.n] >= 0) & T.is_lateral[: T.n]).sum()
    counted = sum(row["branches"] + row["twigs"] for row in events.values())
    assert 0 < counted <= dead_firsts
    # a short shoot's leaves have this season's flush, so its death is logged for next year
    assert all(int(year) <= model.year + 1 for year in events)


def test_a_flip_is_a_year_far_under_the_years_around_it():
    new = {y: {"new_lateral_m": 10.0} for y in range(1, 21)}
    assert tree_table.crown_flips({"new": new}, 3, 18) == 0
    new[10]["new_lateral_m"] = 1.0
    assert tree_table.crown_flips({"new": new}, 3, 18) == 1
    new[10]["new_lateral_m"] = 0.0
    assert tree_table.crown_flips({"new": new}, 3, 18) == 1
