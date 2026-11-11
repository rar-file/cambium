"""tools/switch_off.py: the switch-off rule's comparison says IDENTICAL only when every number the runs share is the same.

No model is grown here: the folders are made by hand, in the shape tools/forest.py and tools/tree_table.py write.
tests/test_logging.py runs it on what tools/tree_table.py really wrote.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import golden  # noqa: E402
import switch_off  # noqa: E402


def _plot_doc() -> dict:
    return {"area_m2": 1000.0, "year": 2, "seed": 1, "trees_ever": 3, "runtime_s": 100, "peak_mb": 600,
            "run_manifest": {"git_commit": "aaaaaaa", "overrides": ["plot.stand_measures=true"]},
            "options": {"mortality.enabled": True, "shedding.log_limbs": False, "height_driver.enabled": True, "speed.quick_solve": True},
            "stats": [{"year": 1, "trees": 3, "lai": 0.006}, {"year": 2, "trees": 2, "lai": 0.011}],
            # year, seconds, peak MB, trees, crown nodes, root nodes, crown nodes alive
            "year_log": [[1, 5.4, 571, 3, 40, 170, 40], [2, 6.0, 580, 2, 95, 310, 90]],
            "damage_log": {"years": [{"year": 1, "storm": False}], "events": []}}


def _list_doc(year: int) -> dict:
    return {"plot_year": year, "area_m2": 1000.0, "seed": 1, "run": {"git_commit": "aaaaaaa", "overrides": []}, "trees_alive": 2,
            "trees": [{"id": 0, "x_m": 1.5, "height_m": 3.25, "dbh_cm": 2.1, "alive": True},
                      {"id": 2, "x_m": -4.0, "height_m": 2.75, "dbh_cm": None, "alive": True},
                      {"id": 1, "x_m": 0.5, "height_m": 1.0, "dbh_cm": None, "alive": False, "died_year": year, "cause": "self-thinned"}]}


def _stats_doc() -> dict:
    return {"format": "treegen.stats/1", "mode": "stand", "seed": 1, "run_manifest": {"git_commit": "aaaaaaa", "scenario": []},
            "options": {"mortality.enabled": False, "shedding.log_limbs": False},
            "per_year": [{"year": 0, "height_m": 0.0, "dbh_cm": None}, {"year": 1, "height_m": 0.1309, "dbh_cm": None, "carbon": {"fixed": 3.5}}],
            "anchorage": {"plate_radius_m": 0.2}}


def _tree_doc() -> dict:
    return {"yearly": [{"year": 1, "new_m": 0.13093284506026995, "pool": 1.7727999999999997}],
            "snapshots": [{"age": 5, "stem_m3": 0.001, "shape": {"widest_at": 0.35}}], "shed": {"4": {"branches": 1, "twigs": 0}}}


def _write(folder: Path, name: str, doc) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(doc), encoding="utf-8")


def _plot(label: Path, seed: int = 1, plot=None, lists=None, done: bool = True, more=None) -> Path:
    folder = label / f"plot_{seed}"
    _write(folder, "plot.json", _plot_doc() if plot is None else plot)
    for year, doc in ({1: _list_doc(1), 2: _list_doc(2)} if lists is None else lists).items():
        _write(folder, f"trees_{year:03d}.json", doc)
    for name, doc in (more or {}).items():
        _write(folder, name, doc)
    if done:
        (folder / "done.txt").write_text("done\n")
    return folder


def _tree(label: Path, seed: int = 1, stats=None, tree=None, done: bool = True, more=None) -> Path:
    folder = label / f"{seed}_stand"
    _write(folder, "stats.json", _stats_doc() if stats is None else stats)
    _write(folder, "tree.json", _tree_doc() if tree is None else tree)
    for name, doc in (more or {}).items():
        _write(folder, name, doc)
    if done:
        _write(folder, "manifest.json", {"run_manifest": {"git_commit": "aaaaaaa"}})
    return folder


def _same(a: Path, b: Path, **kw) -> bool:
    same, lines = switch_off.compare(a, b, **kw)
    assert lines[-1] == ("IDENTICAL" if same else "DIFFERENT") or (not same and lines[-1].startswith("DIFFERENT"))
    return same


def _said(a: Path, b: Path, **kw) -> str:
    return "\n".join(switch_off.compare(a, b, **kw)[1])


def test_its_metadata_keys_are_the_golden_runs():
    assert switch_off.METADATA_KEYS == golden.METADATA_KEYS


# -- plots --------------------------------------------------------------------
def test_two_plots_that_differ_only_in_what_a_run_says_about_itself_are_identical(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _plot(a)
    doc = _plot_doc()
    doc.update(runtime_s=250, peak_mb=700, run_manifest={"git_commit": "bbbbbbb", "overrides": ["plot.stand_measures=true", "log.stand=true"]})
    doc["year_log"] = [[1, 9.9, 999, 3, 40, 170, 40], [2, 8.8, 888, 2, 95, 310, 90]]      # slower and bigger, the same trees and nodes
    doc["options"]["log.stand"] = True
    doc["options"]["log.rings"] = False
    lists = {y: _list_doc(y) for y in (1, 2)}
    for d in lists.values():
        d["run"] = {"git_commit": "bbbbbbb", "overrides": ["log.stand=true"]}
    _plot(b, plot=doc, lists=lists)
    assert _same(a, b)
    said = _said(a, b)
    assert "plot.json: identical, sha256 " in said and "log.stand: absent against true" in said and "log.rings: absent against false" in said
    assert "tree lists: identical in all " in said and "6 tree rows over 2 years (1, 2)" in said


def test_one_last_digit_in_a_plots_yearly_measures_is_a_difference(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _plot(a)
    doc = _plot_doc()
    doc["stats"][1]["lai"] = math.nextafter(0.011, 1.0)        # the next number a computer can hold
    _plot(b, plot=doc)
    assert not _same(a, b)
    assert "plot.json: DIFFERS" in _said(a, b) and f"/stats[1]/lai: 0.011 against {math.nextafter(0.011, 1.0)!r}" in _said(a, b)


def test_a_whole_number_is_not_the_same_as_its_decimal(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _plot(a)
    doc = _plot_doc()
    doc["stats"][0]["trees"] = 3.0
    _plot(b, plot=doc)
    assert not _same(a, b)


def test_a_plot_years_node_count_is_compared_and_its_seconds_are_not(tmp_path):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _plot(a)
    slower = _plot_doc()
    slower["year_log"][1][1], slower["year_log"][1][2] = 60.0, 9000
    _plot(b, plot=slower)
    one_node = _plot_doc()
    one_node["year_log"][1][4] = 96
    _plot(c, plot=one_node)
    assert _same(a, b)
    assert not _same(a, c)
    assert "/year_log[1][2]: 95 against 96" in _said(a, c)      # the row as compared: year, trees, crown nodes, ...


def test_an_item_only_one_plot_json_has_is_a_difference(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _plot(a)
    doc = _plot_doc()
    doc["trees"] = [{"id": 0}]
    _plot(b, plot=doc)
    assert not _same(a, b)
    assert "/trees: only in the second" in _said(a, b)


def test_only_log_options_and_named_switches_may_differ(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _plot(a)
    doc = _plot_doc()
    doc["options"]["shedding.log_limbs"] = True
    _plot(b, plot=doc)
    assert not _same(a, b)
    assert "options that DIFFER: shedding.log_limbs: false against true" in _said(a, b)
    assert _same(a, b, switched=("shedding.log_limbs",))
    assert "options allowed to differ: shedding.log_limbs: false against true" in _said(a, b, switched=("shedding.log_limbs",))
    # a way of running is not a record: speed.* counts here, unlike in the golden hashes
    doc = _plot_doc()
    doc["options"]["speed.quick_solve"] = False
    _plot(b, plot=doc)
    assert not _same(a, b)


def test_a_switch_added_since_counts_only_when_it_is_on(tmp_path):
    a, off, null, on, value, zero = (tmp_path / n for n in ("a", "off", "null", "on", "value", "zero"))
    _plot(a)
    for folder, v in ((off, False), (null, None), (on, True), (value, 0.5), (zero, 0)):
        doc = _plot_doc()
        doc["options"]["height_status.enabled"] = v
        _plot(folder, plot=doc)
    assert _same(a, off) and _same(off, a) and _same(a, null)
    assert "height_status.enabled: absent against false" in _said(a, off)
    assert not _same(a, on) and not _same(on, a) and not _same(a, value)
    assert not _same(a, zero)       # 0 is a value, not off


def test_tree_lists_are_compared_in_the_columns_both_sides_have(tmp_path):
    a, b, c, d = (tmp_path / n for n in "abcd")
    _plot(a)
    more = {y: _list_doc(y) for y in (1, 2)}
    for doc in more.values():
        doc["wood"] = "stem_kg: dry wood"
        for row in doc["trees"]:
            row["stem_kg"] = 1.25
    _plot(b, lists=more)
    assert _same(a, b)
    assert "only one side has, not compared: trees.stem_kg, wood" in _said(a, b)
    moved = copy.deepcopy(more)
    moved[2]["trees"][1]["height_m"] = 2.751
    _plot(c, lists=moved)
    assert not _same(a, c)
    assert "trees_002.json: trees 2: height_m" in _said(a, c)
    fewer = copy.deepcopy(more)
    del fewer[2]["trees"][2]
    _plot(d, lists=fewer)
    assert not _same(a, d)
    assert "trees_002.json: trees: 3 rows against 2" in _said(a, d)


def test_a_tree_lists_order_and_its_header_count(tmp_path):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _plot(a)
    turned = {1: _list_doc(1), 2: _list_doc(2)}
    turned[1]["trees"][0], turned[1]["trees"][1] = turned[1]["trees"][1], turned[1]["trees"][0]
    _plot(b, lists=turned)
    assert not _same(a, b)
    header = {1: _list_doc(1), 2: _list_doc(2)}
    header[2]["trees_alive"] = 3
    _plot(c, lists=header)
    assert not _same(a, c)
    assert "trees_002.json: trees_alive: 2 against 3" in _said(a, c)


def test_a_year_only_one_side_listed_is_named_and_the_rest_still_compared(tmp_path):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _plot(a)
    _plot(b, lists={1: _list_doc(1), 2: _list_doc(2), 3: _list_doc(3)})
    assert _same(a, b)
    assert "trees_003.json: only in the second, not compared" in _said(a, b)
    wrong = _list_doc(1)
    wrong["trees"][0]["dbh_cm"] = 2.2
    _plot(c, lists={1: wrong, 3: _list_doc(3)})
    assert not _same(a, c)


def test_another_file_is_compared_where_both_have_it_and_named_where_one_has(tmp_path):
    a, b, c, d = (tmp_path / n for n in "abcd")
    _plot(a)
    _plot(b, more={"stand_log.json": {"rows": [{"year": 1, "dead_stem_m3": 0.5}]}})
    _plot(c, more={"stand_log.json": {"rows": [{"year": 1, "dead_stem_m3": 0.5}]}})
    _plot(d, more={"stand_log.json": {"rows": [{"year": 1, "dead_stem_m3": 0.6}]}})
    assert _same(a, b) and "stand_log.json: only in the second, not compared" in _said(a, b)
    assert _same(b, c) and "stand_log.json: identical, sha256 " in _said(b, c)
    assert not _same(b, d) and "/rows[0]/dead_stem_m3: 0.5 against 0.6" in _said(b, d)


# -- single trees -------------------------------------------------------------
def test_two_trees_that_differ_only_in_logs_and_metadata_are_identical(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _tree(a)
    stats = _stats_doc()
    stats["run_manifest"] = {"git_commit": "bbbbbbb", "scenario": ["log.rings=true"]}
    stats["options"]["log.rings"] = True
    tree = _tree_doc()
    tree["yearly"][0]["rings"] = {"stem": {"wind": 0.5}}
    tree["snapshots"][0]["branch_wood"] = {"limbs": 5}
    tree["sapwood_short_years"] = 0
    _tree(b, stats=stats, tree=tree, more={"limbs.json": {"rows": []}})
    assert _same(a, b)
    said = _said(a, b)
    assert "stats.json: identical, sha256 " in said and "log.rings: absent against true" in said
    assert "tree.json: identical in all 7 values both sides have" in said      # 3 in the year, 3 in the snapshot besides its new key, and shed
    assert "only one side has, not compared: sapwood_short_years, snapshots.branch_wood, yearly.rings" in said
    assert "limbs.json: only in the second, not compared" in said


def test_one_last_digit_in_a_trees_yearly_row_is_a_difference(tmp_path):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _tree(a)
    stats = _stats_doc()
    stats["per_year"][1]["carbon"]["fixed"] = math.nextafter(3.5, 10.0)
    _tree(b, stats=stats)
    assert not _same(a, b)
    assert f"/per_year[1]/carbon/fixed: 3.5 against {math.nextafter(3.5, 10.0)!r}" in _said(a, b)
    tree = _tree_doc()
    tree["yearly"][0]["new_m"] = math.nextafter(tree["yearly"][0]["new_m"], 1.0)
    _tree(c, tree=tree)
    assert not _same(a, c)
    assert "tree.json: DIFFERS" in _said(a, c) and "yearly 1: new_m" in _said(a, c)


def test_a_nan_is_the_same_as_a_nan(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    tree = _tree_doc()
    tree["yearly"][0]["stomata_leader"] = float("nan")
    _tree(a, tree=tree)
    _tree(b, tree=copy.deepcopy(tree))
    assert _same(a, b)


# -- the set of runs ----------------------------------------------------------
def test_every_run_must_be_on_both_sides_and_finished(tmp_path):
    a, b, c, empty = (tmp_path / n for n in ("a", "b", "c", "empty"))
    for folder in (a, b):
        _plot(folder, 1)
        _plot(folder, 2)
        _tree(folder, 1)
    assert _same(a, b)
    assert "3 runs: 3 identical, 0 differ, 0 on one side only, 0 not finished" in _said(a, b)
    _tree(a, 2)
    assert not _same(a, b) and "2_stand\n  only in the first" in _said(a, b)
    assert _same(a, b, seeds=[1])                       # asked for seed 1 alone: both of its runs are there
    assert not _same(a, b, seeds=[1, 3]) and "seed 3: on neither side" in _said(a, b, seeds=[1, 3])
    _plot(c, 1, done=False)
    _plot(c, 2)
    _tree(c, 1, done=False)
    assert not _same(b, c)
    assert "plot_1\n  not finished in the second (no done.txt)" in _said(b, c) and "1_stand\n  not finished in the second (no manifest.json)" in _said(b, c)
    empty.mkdir()
    assert not _same(empty, empty) and _said(empty, empty).endswith("DIFFERENT: no runs found")


def test_the_command_line_ends_with_the_verdict_and_its_exit_code(tmp_path, monkeypatch, capsys):
    a, b = tmp_path / "a", tmp_path / "b"
    _plot(a)
    doc = _plot_doc()
    doc["options"]["shedding.log_limbs"] = True
    _plot(b, plot=doc)
    for argv, code, word in ((["--switched", "shedding.log_limbs"], 0, "IDENTICAL"), ([], 1, "DIFFERENT"), (["--seeds", "1,2"], 1, "DIFFERENT")):
        monkeypatch.setattr(sys, "argv", ["switch_off.py", str(a), str(b), *argv])
        with pytest.raises(SystemExit) as stop:
            switch_off.main()
        assert stop.value.code == code
        assert capsys.readouterr().out.rstrip().endswith(word)
