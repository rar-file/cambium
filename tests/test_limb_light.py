"""shedding.log_limbs's limb_light.json (tools/limb_wood.py limb_light_rows, written by tools/tree_table.py): each limb's
light as the shedding test read it, what kind of limb it is, and its fork axes.  No tree is grown here: a made-up tree,
and runs of no years."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from treegen import logs
from treegen.params import load_species

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import limb_wood  # noqa: E402
import tree_table  # noqa: E402


def _made_up(year: int = 7, drop_dead: bool = False):
    """A stem of three nodes (axis 0) and four limbs on it.  A (node 3, axis 1) carries a living fork (axis 2); B (node 6, axis 3)
    is reiterated and its one fork (axis 6) is dead; C (node 7, axis 4) is reiterated and the second top; D (node 8) is dead."""
    parent = np.array([-1, 0, 1, 1, 3, 4, 2, 2, 0, 6])
    axis = np.array([0, 0, 0, 1, 1, 2, 3, 4, 5, 6])
    lateral = np.array([False, False, False, True, False, True, True, True, True, True])
    death = np.array([-1, -1, -1, -1, -1, -1, -1, -1, 3, 2])
    tree = SimpleNamespace(n=10, parent=parent, axis=axis, is_lateral=lateral, death=death)
    sp = SimpleNamespace(speed=SimpleNamespace(drop_dead=drop_dead), shedding=SimpleNamespace(log_limbs=True))
    model = SimpleNamespace(tree=tree, sp=sp, leader_axes={0}, reit={6: (35, 0.4), 7: (40, 0.4)}, _frame_second_top=4,
                            _frame_fork_of={2: 3, 6: 6},
                            _limb_log={"year": year, "node": np.array([3, 6, 8]), "ratio": np.array([0.812345678, 0.3, 0.1])})
    return model


def test_each_living_limb_has_its_light_its_kind_and_its_living_forks():
    model = _made_up()
    rows = limb_wood.limb_light_rows(model, 7)
    assert rows == [[7, 3, 0.81235, "limb", 1], [7, 6, 0.3, "reiterated", 0], [7, 7, None, "second_top", 0]]
    # the same limbs, in the same order, as limbs.json's rows (tools/limb_wood.py limbs, by logs.limb_starts)
    alive = model.tree.death[: model.tree.n] < 0
    assert [r[1] for r in rows] == logs.limb_starts(model, model.tree.n, alive).tolist()
    assert all(len(r) == len(limb_wood.LIGHT_COLUMNS) for r in rows)


def test_no_light_from_another_year_or_from_renumbered_nodes_and_no_second_top_named_by_reading():
    assert [r[2] for r in limb_wood.limb_light_rows(_made_up(year=6), 7)] == [None, None, None]
    assert [r[2] for r in limb_wood.limb_light_rows(_made_up(drop_dead=True), 7)] == [None, None, None]
    model = _made_up()
    del model._frame_second_top, model._frame_fork_of, model._limb_log
    rows = limb_wood.limb_light_rows(model, 7)
    assert [(r[2], r[3], r[4]) for r in rows] == [(None, "limb", 0), (None, "reiterated", 0), (None, "reiterated", 0)]
    assert "_frame_second_top" not in model.__dict__


def test_the_log_is_off_by_default_and_a_run_without_it_writes_nothing_new(tmp_path):
    sp, _ = load_species("betula_pendula")
    assert sp.shedding.log_limbs is False and not limb_wood.light_log_on(sp)
    del sp.shedding.log_limbs
    assert not limb_wood.light_log_on(sp)
    # runs of no years: the files each setting writes
    for sets, name in (([], "plain"), (["log.rings=true"], "rings"), (["shedding.log_limbs=true"], "limbs")):
        assert tree_table.one(1, sets, tmp_path / name, 0) == 0
    assert sorted(p.name for p in (tmp_path / "plain").iterdir()) == ["manifest.json", "stats.json", "tree.json"]
    assert sorted(p.name for p in (tmp_path / "rings").iterdir()) == ["limbs.json", "manifest.json", "stats.json", "tree.json"]
    assert sorted(p.name for p in (tmp_path / "limbs").iterdir()) == ["limb_light.json", "manifest.json", "stats.json", "tree.json"]
    # limbs.json's columns are as they were before limb_light.json
    assert json.loads((tmp_path / "rings" / "limbs.json").read_text(encoding="utf-8"))["columns"] == [
        "year", "node", "birth_year", "z_m", "base_d_cm", "stem_d_cm", "length_m", "wood_kg", "leaf_area_m2",
        "ring_replaced", "ring_more_leaf", "ring_wind", "own_carbon", "upkeep"]
    doc = json.loads((tmp_path / "limbs" / "limb_light.json").read_text(encoding="utf-8"))
    assert doc["columns"] == list(limb_wood.LIGHT_COLUMNS) and doc["rows"] == [] and doc["what"] == limb_wood.LIGHT_WHAT
