"""The stem's own top beside the height, and a thinning that stays (reports/design/2026-11-12_height_faults.md, the build).

A tree's height_m is its highest living point, which can be a limb's second top or fork above the stem; the height curve
sets the stem's top.  log.stem_tops records the stem's top beside the height and changes nothing else.  Two switches
correct the bookkeeping of a stand tree's thinning schedule: stand.thinning_stays (a row once reached is kept) and
stand.thinning_on_stem_top (the schedule is read at the stem's top).  All three are off by default, and off is today's.

No tree is grown here: the trees are made up by hand, a few nodes each, and the model's own functions are called on them.
"""
from __future__ import annotations

import ast
import json
import math
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from treegen import checkpoint, damage, logs, names
from treegen.growth import GrowthModel
from treegen.params import load_species
from treegen.plot import Plot
from treegen.structure import Tree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import switch_off  # noqa: E402
import tree_list  # noqa: E402
from golden import hash_file  # noqa: E402

# the Finnish schedule of the control arm S1 (reports/design/2026-11-12_t2_control_report.md, section 11): its last row is near the final height
S1 = 'stand.thinning=[{"from_height_m":0.0,"stems_per_ha":1600},{"from_height_m":14.0,"stems_per_ha":700},{"from_height_m":20.5,"stems_per_ha":375}]'
STAYS, ON_STEM = "stand.thinning_stays=true", "stand.thinning_on_stem_top=true"
STEM_Z = (0.0, 5.0, 10.0, 16.0, 20.0)
LIMB_TIP_Z = 21.2


def species(*sets):
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, list(sets))
    return sp


def made_up_tree(stem_z=STEM_Z, limb_tip_z=LIMB_TIP_Z) -> Tree:
    """A stem of five nodes, and one limb that leaves it at the fourth and whose tip stands at limb_tip_z: with the values
    above a 20.0 m stem with a limb's tip at 21.2 m, 1.2 m over it."""
    T = Tree(16)
    stem = T.alloc(len(stem_z))
    T.pos[stem, 2] = stem_z
    T.parent[stem] = [-1] + list(stem[:-1])
    T.main_child[stem[:-1]] = stem[1:]
    T.radius[stem] = np.linspace(0.15, 0.01, len(stem))
    T.length[stem[1:]] = np.diff(np.asarray(stem_z, float))
    T.depth[stem] = np.arange(len(stem))
    at = int(stem[-2])
    limb = T.alloc(2)
    T.pos[limb] = [[1.0, 0.0, 0.5 * (stem_z[-2] + limb_tip_z)], [1.5, 0.0, limb_tip_z]]
    T.parent[limb] = [at, limb[0]]
    T.lat_child[at] = limb[0]
    T.main_child[limb[0]] = limb[1]
    T.is_lateral[limb[0]] = True
    T.axis[limb] = 1
    T.order[limb] = 1
    T.radius[limb] = [0.02, 0.005]
    T.length[limb] = [3.0, 2.3]
    T.depth[limb] = [T.depth[at] + 1, T.depth[at] + 2]
    T.leaves[limb[1]] = 40.0
    T.leaves[stem[-1]] = 60.0
    return T


def model(sp, tree=None, year=45) -> GrowthModel:
    """A stand tree that was never grown: only what the functions under test read."""
    m = GrowthModel.__new__(GrowthModel)
    m.sp, m.tree, m.leader_axes, m.stand, m.lean, m.year = sp, made_up_tree() if tree is None else tree, {0}, True, True, year
    m.light, m.water, m.roots, m.reit, m.loss_of_dominance_year, m.stats = SimpleNamespace(leaf_area=0.0015), {}, None, {}, None, []
    return m


def row_of(m, height: float, measured: bool = False) -> int:
    """Stems a hectare of the schedule row the model reads for a tree whose highest living point is `height`."""
    return round(m.stems_per_ha(m._schedule_height(height, measured)))


def todays_row(sp, height: float) -> int:
    """The rule as it has been, written out again: the last row whose height the tree's highest living point has passed."""
    row = sp.stand.thinning[0]
    for r in sp.stand.thinning:
        if height >= r.from_height_m:
            row = r
    return round(row.stems_per_ha)


# -- names and defaults --------------------------------------------------------
def test_the_record_and_both_switches_are_named_and_off_by_default():
    sp = species()
    assert sp.log.stem_tops is False and sp.stand.thinning_stays is False and sp.stand.thinning_on_stem_top is False
    assert {"log.stem_tops", "stand.thinning_stays", "stand.thinning_on_stem_top"} <= names.SPECIES
    assert not logs.on(sp, "stem_tops")
    del sp.log
    assert not logs.on(sp, "stem_tops")      # a species from before the record reads as off


def test_a_record_that_is_on_leaves_the_golden_hash_alone_and_a_switch_that_is_on_does_not(tmp_path):
    a, b, c, d = (tmp_path / f"{n}.json" for n in "abcd")
    a.write_text(json.dumps({"x": 1.5, "options": {"old": True}}))
    b.write_text(json.dumps({"x": 1.5, "options": {"old": True, "log.stem_tops": True, "stand.thinning_stays": False, "stand.thinning_on_stem_top": False}}))
    c.write_text(json.dumps({"x": 1.5, "options": {"old": True, "stand.thinning_stays": True}}))
    d.write_text(json.dumps({"x": 1.5, "options": {"old": True, "stand.thinning_on_stem_top": True}}))
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c) and hash_file(a) != hash_file(d)
    # the switch-off rule: the record may differ, a switch that is on may not
    assert switch_off.options_apart({"old": True}, {"old": True, "log.stem_tops": True, "stand.thinning_stays": False}) == (
        ["log.stem_tops: absent against true", "stand.thinning_stays: absent against false"], [])
    assert switch_off.options_apart({"old": True}, {"old": True, "stand.thinning_stays": True})[1] == ["stand.thinning_stays: absent against true"]


# -- the stem's top -------------------------------------------------------------
def test_the_stem_top_is_the_stems_last_node_and_not_the_highest_living_point():
    m = model(species())
    T = m.tree
    alive = T.death[:T.n] < 0
    assert float(T.pos[:T.n][alive, 2].max()) == LIMB_TIP_Z      # what the model reports as height_m
    assert m.stem_top_m() == 20.0
    assert m.stem_top_measured() == 20.0                          # none kept: as it is now
    m._stem_top_m = 19.5
    assert m.stem_top_measured() == 19.5 and m.stem_top_m() == 20.0


def test_a_stem_that_lost_its_top_ends_at_its_last_living_node():
    m = model(species())
    m.tree.death[4] = 44
    assert m.stem_top_m() == 16.0
    # with the height limit on, the stem is what leads to the shoot the limit paid for (Tree.stem_tip)
    paid = model(species())
    paid.tree.stem_tip = 4
    assert paid.stem_top_m() == 20.0
    paid.tree.death[4] = 44
    assert paid.stem_top_m() == 16.0


def test_the_yearly_row_keeps_the_stem_top_beside_it_only_with_the_record_on_and_is_the_same_row():
    plain, logged = model(species(S1)), model(species(S1, "log.stem_tops=true"))
    a, b = plain.measure(), logged.measure()
    assert a["height_m"] == LIMB_TIP_Z                             # the limb's tip
    assert "_stem_top_m" not in vars(plain) and logged._stem_top_m == 20.0
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)      # nothing in the row: stats.json is the same
    assert not any("stem_top" in k for k in a)
    assert "_schedule_reached" not in vars(plain) and "_schedule_reached" not in vars(logged)


# -- the schedule row ----------------------------------------------------------
HEIGHTS = (3.0, 13.99, 14.0, 14.2, 13.9, 20.49, 20.5, 20.6, 19.33, 19.9, 20.7, 10.99, 11.0, 16.0, 15.99, 25.0, 0.0)


@pytest.mark.parametrize("schedule", [(), (S1,)], ids=["default", "S1"])
def test_with_both_switches_off_the_row_is_todays_at_every_reading_and_nothing_is_kept(schedule):
    sp = species(*schedule)
    m = model(sp)
    for h in HEIGHTS:
        assert m._schedule_height(h) is h and m._schedule_height(h, measured=True) is h      # the caller's own number, untouched
        assert row_of(m, h) == todays_row(sp, h)
        assert m.stems_per_ha(m._schedule_height(h)) == m.stems_per_ha(h) and m.stand_spacing(m._schedule_height(h)) == m.stand_spacing(h)
    assert "_schedule_reached" not in vars(m) and "_stem_top_m" not in vars(m)


def test_a_tree_that_loses_height_gets_its_neighbours_back_today_and_keeps_its_row_with_thinning_stays():
    """Seed 10 on the schedule S1: 20.6 m at the end of year 44, 19.33 m after the snap at the start of year 45."""
    readings = (13.0, 14.2, 13.9, 20.6, 19.33, 19.9, 20.4, 20.7)
    off, stays = model(species(S1)), model(species(S1, STAYS))
    assert [row_of(off, h) for h in readings] == [1600, 700, 1600, 375, 700, 700, 700, 375]        # the removed trees come back, twice
    assert [row_of(stays, h) for h in readings] == [1600, 700, 700, 375, 375, 375, 375, 375]
    assert stays._schedule_reached == 20.7 and "_schedule_reached" not in vars(off)
    # it only ever holds a row that was reached: a tree that never passes a row's height never gets it
    low = model(species(S1, STAYS))
    assert [row_of(low, h) for h in (13.0, 13.9, 12.0)] == [1600, 1600, 1600]


def test_a_tree_whose_highest_point_is_over_its_stem_reads_the_limb_today_and_the_stem_with_thinning_on_stem_top():
    """The made-up tree: stem top 20.0 m, a limb's tip at 21.2 m.  S1's last row starts at 20.5 m."""
    off, stem = model(species(S1)), model(species(S1, ON_STEM))
    assert row_of(off, LIMB_TIP_Z) == 375            # the limb brings the thinning forward
    assert row_of(stem, LIMB_TIP_Z) == 700           # the stem hasn't reached it
    assert stem._schedule_height(LIMB_TIP_Z) == 20.0
    # a place that reads the height from the last yearly row reads the stem top that row measured
    stem._stem_top_m = 20.55
    assert row_of(stem, LIMB_TIP_Z, measured=True) == 375 and row_of(stem, LIMB_TIP_Z) == 700
    assert "_schedule_reached" not in vars(stem)
    # the stem grows past the row: both then agree
    stem.tree.pos[4, 2] = 20.6
    assert row_of(stem, 21.3) == 375


def test_both_switches_together_follow_the_stem_and_keep_what_it_reached():
    m = model(species(S1, STAYS, ON_STEM))
    T = m.tree
    assert row_of(m, LIMB_TIP_Z) == 700              # stem 20.0 m, limb 21.2 m
    T.pos[4, 2] = 20.6
    assert row_of(m, 21.4) == 375                    # the stem reaches the row
    T.death[4] = 45                                  # a storm takes the top: stem 16.0 m, the limb's tip is now the highest point
    assert m.stem_top_m() == 16.0
    assert row_of(m, LIMB_TIP_Z) == 375              # the thinning stays
    assert m._schedule_reached == 20.6
    # each switch alone on the same story
    stays, stem = model(species(S1, STAYS)), model(species(S1, ON_STEM))
    stem.tree.pos[4, 2] = 20.6
    assert row_of(stays, LIMB_TIP_Z) == 375 and row_of(stem, 21.4) == 375
    stem.tree.death[4] = 45
    assert row_of(stays, 19.0) == 375 and row_of(stem, LIMB_TIP_Z) == 700


def test_the_default_schedule_reads_the_same_row_either_way_once_the_tree_is_past_its_last_height():
    """On the default schedule the last row starts at 16 m: a snap that leaves 18.95 m changes no row (the control's seed 10)."""
    for sets in ((), (STAYS,), (ON_STEM,), (STAYS, ON_STEM)):
        m = model(species(*sets))
        assert [row_of(m, h) for h in (LIMB_TIP_Z, 18.95, 21.0)] == [450, 450, 450]


# -- every place that reads the schedule --------------------------------------
def _calls(path: str):
    """(the function a call is in, the name called, its arguments) for every call in a source file."""
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    yield fn.name, node.func.attr, node.args


def _through_the_schedule_height(arg) -> bool:
    return isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "_schedule_height"


def test_every_reader_of_the_schedule_goes_through_one_function():
    """Light, soil water, wind load, a limb's reach, damage and the yearly stats: each hands its height to _schedule_height before
    the schedule is read.  A new reader that doesn't fails here, so the two switches can't be on in one place and off in another."""
    readers = []
    for path in ("treegen/growth.py", "treegen/damage.py"):
        for where, name, args in _calls(path):
            if name in ("stand_spacing", "stems_per_ha"):
                arg = args[0]
                if where in ("stems_per_ha", "_stand_cell") and isinstance(arg, ast.Name) and arg.id == "height":
                    continue        # the two functions that are handed the height: stems_per_ha itself, and the light's cell
                if where == "measure" and isinstance(arg, ast.Name) and arg.id == "at":
                    readers.append(where)
                    continue
                assert _through_the_schedule_height(arg), f"{path} {where}: {name} is read at a height that didn't go through _schedule_height"
                readers.append(where)
            if name == "_stand_cell":
                assert _through_the_schedule_height(args[2]), f"{path} {where}: the light's cell is built at a height that didn't go through _schedule_height"
                readers.append(where)
    assert sorted(readers) == ["_frame_goal", "_wind_load_scale", "measure", "measure", "state_from_model", "step", "step"]
    # measure's `at` is that function's result
    src = (ROOT / "treegen" / "growth.py").read_text(encoding="utf-8")
    assert "at = self._schedule_height(height, measured=True) if self.stand else height" in src


def test_the_yearly_row_the_winds_load_a_limbs_reach_and_damage_all_read_the_same_row():
    """Each place on the made-up tree (stem 20.0 m, limb 21.2 m, schedule S1) reads 375/ha today and 700/ha on the stem's top; a
    place reads 700/ha exactly as it does on a schedule that holds 700/ha at every height."""
    flat_700 = 'stand.thinning=[{"from_height_m":0.0,"stems_per_ha":700}]'
    flat_375 = 'stand.thinning=[{"from_height_m":0.0,"stems_per_ha":375}]'

    def places(*sets):
        m = model(species(*sets))
        row = m.measure()
        m.stats.append(row)
        alive = m.tree.death[:m.tree.n] < 0
        wind = m._wind_load_scale(alive, 1.0, m.sp.pipe_model.wind_load, stage_b=True)
        reach = m._frame_goal(np.array([3])).tolist()
        state = damage.state_from_model(m)
        return {"spacing": row["stand_spacing_m"], "lai": row["lai"], "wind": wind, "reach": reach, "damage": round(state.stems_per_ha)}

    today, on_stem = places(S1), places(S1, ON_STEM)
    assert today == places(flat_375) and today["damage"] == 375
    assert on_stem == places(flat_700) and on_stem["damage"] == 700
    assert all(today[k] != on_stem[k] for k in today)      # every one of them moved with the row
    # thinning_stays alone: the limb's row, as today, and kept
    assert places(S1, STAYS) == today


def test_a_managed_plots_thinning_reads_stem_tops_only_with_the_switch():
    """60 trees on 1,000 m2: the ten tallest reach 16.4 m at their highest points, and 15.2 m at their stems' tops.  The default
    programme's last row (450/ha: 45 trees) starts at 16 m."""
    def thinned(*sets):
        p = Plot.__new__(Plot)
        p.species, p.area, p.alive = species(*sets), 1000.0, list(range(60))
        p.stages = [(float(s.from_height_m), float(s.stems_per_ha)) for s in p.species.stand.thinning]
        p.trees = [SimpleNamespace(stats=[{"height_m": 16.4 if k < 10 else 14.0}], dbh_m=lambda k=k: 0.10 + 0.001 * k,
                                   stem_top_measured=lambda k=k: 15.2 if k < 10 else 14.0) for k in range(60)]
        gone = []
        p._finish = lambda k, cause: gone.append((k, cause))
        p._thin()
        return gone

    today = thinned()
    assert today == [(k, "thinned") for k in range(15)]              # today: the limbs' tips bring the last thinning on, and the 15 thinnest go
    assert thinned(STAYS) == today
    assert thinned(ON_STEM) == [] and thinned(STAYS, ON_STEM) == []      # the stems haven't reached 16 m


# -- the records ---------------------------------------------------------------
def test_a_plot_years_row_reads_top_height_and_spread_on_highest_points_and_on_stem_tops():
    rng = np.random.default_rng(7)
    d = np.round(rng.uniform(6.0, 24.0, 40), 2).tolist() + [0.0, 0.0]
    stem = np.round(8.0 + 0.5 * np.array(d[:40]) + rng.normal(0.0, 0.4, 40), 3).tolist() + [1.1, 0.6]
    h = list(stem)
    for i, lift in ((3, 1.2), (11, 0.31), (17, 0.3), (25, 2.05)):       # four trees with a limb over the stem; one of them by exactly 0.3 m
        h[i] = round(stem[i] + lift, 3)
    area = 400.0
    row = logs.stem_top_row(45, d, h, stem, area)
    top, counted, simple = logs.fitted_top_height(d, h, area)
    top_stem, _, simple_stem = logs.fitted_top_height(d, stem, area)
    assert row["year"] == 45 and row["trees"] == 42 and row["top_height_trees"] == round(counted, 3) == 4.0
    assert row["top_height_approved_m"] == round(top, 4) and row["top_height_approved_stem_m"] == round(top_stem, 4)
    assert row["top_height_mean_m"] == round(simple, 4) and row["top_height_mean_stem_m"] == round(simple_stem, 4)
    assert row["top_height_approved_m"] != row["top_height_approved_stem_m"]
    # the spread as tools/independent_checks.py reads it: the sample SD over the trees with a DBH
    assert row["height_sd_trees"] == 40
    assert row["height_sd_m"] == round(statistics.stdev(h[:40]), 4) and row["height_sd_stem_m"] == round(statistics.stdev(stem[:40]), 4)
    assert row["trees_over"] == 3 and row["over_most_m"] == 2.05          # more than 0.3 m, on heights to 0.001 m: the one at 0.300 doesn't count
    assert set(row) == set(logs.STEM_LOG_WHAT)
    # where no tree stands over its stem the two readings are one
    same = logs.stem_top_row(45, d, stem, stem, area)
    assert same["top_height_approved_m"] == same["top_height_approved_stem_m"] and same["height_sd_m"] == same["height_sd_stem_m"]
    assert same["trees_over"] == 0 and same["over_most_m"] == 0.0
    # too few trees: no spread, no top height, and no error
    few = logs.stem_top_row(3, [0.0, 2.0], [1.0, 3.0], [1.0, 3.0], area)
    assert few["top_height_approved_m"] is None and few["top_height_approved_stem_m"] is None and few["height_sd_m"] is None
    empty = logs.stem_top_row(3, [], [], [], area)
    assert empty["trees"] == 0 and empty["over_most_m"] is None and empty["trees_over"] == 0


def _made_up_plot(*sets):
    """Three living trees and one that went, never grown: the made-up tree at three sizes."""
    sp = species(*sets)
    p = Plot.__new__(Plot)
    p.species, p.area, p.year, p.seed, p.mode, p.L, p.measures, p.on_finish = sp, 100.0, 45, 1, "natural", 10.0, True, None
    p.trees, p.info = [], []
    for k, scale in enumerate((1.0, 0.9, 0.8, 0.7)):
        m = model(sp, made_up_tree(tuple(z * scale for z in STEM_Z), LIMB_TIP_Z * scale if k != 1 else 17.0), year=45 - k)
        m.stats.append(m.measure())
        p.trees.append(m)
        p.info.append({"id": k, "x": float(k), "y": 0.5 * k, "germination": k, "vigour": 1.0, "seed": 1000 + k, "removed": None})
    p.alive = [0, 1, 2, 3]
    return p


def test_a_plot_keeps_a_row_a_year_and_the_stem_top_of_a_tree_that_went_only_with_the_record_on(monkeypatch):
    monkeypatch.setattr(logs, "tree_record", lambda m: {"stem_m3": 0.1, "branch_m3": 0.01})
    lists = {}
    for name, sets in (("plain", ()), ("logged", ("log.stem_tops=true",))):
        p = _made_up_plot(*sets)
        p._finish(3, "self-thinned")
        p._log_year()
        if logs.on(p.species, "stem_tops"):
            p._log_stem_tops()
        lists[name] = (p, tree_list.tree_list(p))
    plain, a = lists["plain"]
    logged, b = lists["logged"]
    assert "stem_log" not in vars(plain) and "stem_tops_gone" not in vars(plain)
    assert logged.stem_tops_gone == {3: pytest.approx(14.0)} and "stem_top_m" not in logged.info[3]["last"]
    assert plain.info == logged.info                                    # a plot.json that holds info is the same
    # the year's row: three living trees; the first and third stand over their stems, the second doesn't
    row = logged.stem_log[-1]
    assert row["trees"] == 3 and row["trees_over"] == 2 and row["over_most_m"] == 1.2
    assert row["top_height_approved_m"] == logged.stand_log[-1]["top_height_approved_m"]       # log.stand's own figure
    assert row["top_height_mean_stem_m"] < row["top_height_mean_m"]
    assert plain.stand_log == logged.stand_log                          # stand_log.json is the same with the record on
    # the lists: a column beside height_m and a header line with the record on, and not a byte more without it
    assert "stem_top" not in a and all("stem_top_m" not in t for t in a["trees"])
    assert [t["stem_top_m"] for t in b["trees"]] == [20.0, 18.0, 16.0, 14.0]
    assert [t["height_m"] for t in b["trees"]] == [21.2, 18.0, 16.96, 14.84]
    assert [k for k in b["trees"][0]][5:7] == ["height_m", "stem_top_m"]
    without = dict(b, trees=[{k: v for k, v in t.items() if k != "stem_top_m"} for t in b["trees"]])
    del without["stem_top"]
    assert json.dumps(without) == json.dumps(a)


def test_the_table_tool_reads_a_plots_lists_as_its_yearly_rows_do(tmp_path, monkeypatch, capsys):
    import stem_top_table

    monkeypatch.setattr(logs, "tree_record", lambda m: {"stem_m3": 0.1, "branch_m3": 0.01})
    p = _made_up_plot("log.stem_tops=true")
    p._finish(3, "self-thinned")
    p._log_stem_tops()
    folder = tmp_path / "plot_1"
    tree_list.write(p, folder / "trees_045.json")
    (folder / "stem_log.json").write_text(json.dumps({"rows": p.stem_log}), encoding="utf-8")
    assert stem_top_table.from_list(json.loads((folder / "trees_045.json").read_text(encoding="utf-8"))) == p.stem_log[-1]
    assert stem_top_table.plots(tmp_path, [30, 45]) == 0
    out = capsys.readouterr().out
    assert "| 1 | 45 | 3 |" in out and "| 2, 66.7 % (1.20 m) | yes |" in out
    # a list that doesn't give the year's row is said, and fails
    doc = json.loads((folder / "trees_045.json").read_text(encoding="utf-8"))
    doc["trees"][0]["stem_top_m"] -= 0.5
    (folder / "trees_045.json").write_text(json.dumps(doc), encoding="utf-8")
    assert stem_top_table.plots(tmp_path, [45]) == 1 and "| NO |" in capsys.readouterr().out


def test_the_table_tool_finds_the_first_year_two_runs_part_and_tells_the_schedules_own_figures_from_the_trees(tmp_path, capsys):
    import stem_top_table

    a = [{"year": y, "height_m": 10.0 + y, "dbh_cm": 9.0, "stand_spacing_m": 4.061, "lai": 3.0, "carbon": {"fixed": 1.0}} for y in range(1, 8)]
    assert stem_top_table.first_change(a, json.loads(json.dumps(a))) == (None, [], None, [])
    b = json.loads(json.dumps(a))
    b[3]["stand_spacing_m"], b[3]["lai"] = 5.549, 2.0          # year 4: only the schedule's own two figures
    b[5]["height_m"] += 0.01                                   # year 6: the tree
    b[5]["carbon"]["fixed"] = 1.1
    assert stem_top_table.first_change(a, b) == (4, ["lai", "stand_spacing_m"], 6, ["carbon", "height_m"])
    assert [stem_top_table.stems_of(s) for s in (5.549, 4.061, 2.686, 5.066, 3.398, 2.533, None)] == [375, 700, 1600, 450, 1000, 1800, None]
    for name, rows in (("control", a), ("arm", b)):
        for seed, per_year in ((1, a), (2, rows)):
            d = tmp_path / name / f"{seed}_stand"
            d.mkdir(parents=True)
            (d / "stats.json").write_text(json.dumps({"per_year": per_year}), encoding="utf-8")
    (tmp_path / "arm" / "2_stand" / "tree.json").write_text(json.dumps({"yearly": [{"year": y, "stem_top_m": 9.5 + y} for y in range(1, 8)]}), encoding="utf-8")
    assert stem_top_table.changed(tmp_path / "control", tmp_path / "arm", [4, 6]) == 0
    out = capsys.readouterr().out
    assert "| 1 | the same in all 7 years | the same | none |" in out
    assert "| 2 | from year 4: lai, stand_spacing_m | from year 6: carbon, height_m | 4: 700; 375 |" in out
    b[4]["stand_spacing_m"] = b[6]["stand_spacing_m"] = 5.549
    assert stem_top_table.row_years(a, b) == "4-5: 700; 375, 7: 700; 375" and stem_top_table.row_years(a, a) == "none"
    assert "2 seeds on both sides, 1 changed: 2" in out
    assert "| 2 | 4 | 14.00; 14.00 | 13.50 | 9.00; 9.00 | 700; 375 | 3.00; 2.00 |" in out
    assert "| 2 | 6 | 16.00; 16.01 | 15.50 |" in out


def test_a_dead_trees_row_has_no_stem_top_where_none_was_kept(monkeypatch):
    """A list written from a plot whose record was switched on after the tree went: null, not a guess."""
    monkeypatch.setattr(logs, "tree_record", lambda m: {"stem_m3": 0.1, "branch_m3": 0.01})
    p = _made_up_plot()
    p._finish(3, "self-thinned")
    p.species.log.stem_tops = True
    got = tree_list.tree_list(p)
    assert [t["stem_top_m"] for t in got["trees"]] == [20.0, 18.0, 16.0, None]
