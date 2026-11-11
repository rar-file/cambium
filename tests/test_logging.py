"""The records kept for the reports (treegen/logs.py, species block ``log``; design round 2026-11-11, step T1).

They change nothing a tree or a plot grows, with every one of them on; and each says what it claims to say.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from treegen import checkpoint, logs
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import load_environment, load_species

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bark  # noqa: E402
import independent_checks  # noqa: E402
import limb_wood  # noqa: E402
import m3_wood  # noqa: E402
import scorecard  # noqa: E402
import switch_off  # noqa: E402
import tree_list  # noqa: E402
import tree_table  # noqa: E402
from golden import hash_file  # noqa: E402
from test_forest import BEFORE_V1, make_plot, species  # noqa: E402

YEARS = 15
ARRAYS = ("pos", "dir", "radius", "length", "parent", "axis", "birth", "death", "wood_area", "sap_area", "leaves", "leaf_size", "lma")


def _model(*sets, seed: int = 4):
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, list(sets))
    env, _ = load_environment("sweden_open_field")
    return GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)


@pytest.fixture(scope="module")
def pair():
    """One stand tree grown twice: as it is, and with the ring and limb logs on and measured every year."""
    plain, logged = _model(), _model("log.rings=true", "shedding.log_limbs=true")
    years, limb_rows, snaps = [], [], {}
    for year in range(1, YEARS + 1):
        before = float(logged.light_sources()[5].sum()) * float(logged.light.leaf_area)
        plain.step()
        logged.step()
        use = (logged.stats[-1].get("height_limit") or {}).get("use")
        years.append({"year": year, "ring": logged._ring_log, "must_log": logged._must_log, "use": use, "lit_before": before,
                      **limb_wood.year_record(logged, year)})
        limb_rows += limb_wood.limb_rows(logged, year)
        if year % 5 == 0:
            snaps[year] = tree_table.snapshot(logged, year)
    return plain, logged, years, limb_rows, snaps


# -- the switches ------------------------------------------------------------
def test_the_logs_are_off_by_default_and_a_file_without_them_reads_as_off():
    sp, _ = load_species("betula_pendula")
    assert sp.log.rings is False and sp.log.stand is False
    assert not logs.on(sp, "rings") and not logs.on(sp, "stand")
    del sp.log
    assert not logs.on(sp, "rings") and not logs.on(sp, "stand")


def test_a_log_that_is_on_leaves_the_golden_hash_alone(tmp_path):
    a, b, c = (tmp_path / f"{n}.json" for n in "abc")
    a.write_text(json.dumps({"x": 1.5, "options": {"old": True}}))
    b.write_text(json.dumps({"x": 1.5, "options": {"old": True, "log.rings": True, "log.stand": True}}))
    c.write_text(json.dumps({"x": 1.5, "options": {"old": True, "shedding.other": True}}))
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)      # any other option that is on still counts


# -- a tree -------------------------------------------------------------------
@pytest.mark.slow
def test_a_tree_grows_the_same_with_the_ring_and_limb_logs_on_and_measured(pair):
    plain, logged, years, _, _ = pair
    assert json.dumps(plain.stats, sort_keys=True) == json.dumps(logged.stats, sort_keys=True)
    n = plain.tree.n
    assert n == logged.tree.n and n > 500
    for name in ARRAYS:
        assert np.array_equal(getattr(plain.tree, name)[:n], getattr(logged.tree, name)[:n]), name
    assert getattr(plain, "_ring_log", None) is None and getattr(plain, "_limb_carbon", None) is None
    # what is kept without a switch is the same on both
    assert plain._must_log == logged._must_log and plain._lit_leaf_m2 == logged._lit_leaf_m2
    assert getattr(plain, "sapwood_short_years", 0) == getattr(logged, "sapwood_short_years", 0)


@pytest.mark.slow
def test_the_years_rings_add_up_to_what_the_model_laid(pair):
    _, logged, years, _, _ = pair
    checked = 0
    for y in years:
        ring = y["ring"]
        assert ring["year"] == y["year"]
        stem, branch = sum(ring["stem"].values()), sum(ring["branch"].values())
        assert all(v >= 0.0 for part in (ring["stem"], ring["branch"]) for v in part.values())
        on_limbs = float(ring["limb_replaced"].sum() + ring["limb_more_leaf"].sum() + ring["limb_wind"].sum())
        assert on_limbs <= branch * (1.0 + 1e-9) + 1e-9
        assert len(ring["limb_node"]) == len(ring["limb_z"]) == len(ring["limb_birth"]) == len(ring["limb_wind"])
        if y["use"]:        # the model's own figures for the year, to 0.1 of a unit
            assert stem + branch == pytest.approx(y["use"]["rings"], abs=0.051 + 1e-9 * y["use"]["rings"])
            assert stem == pytest.approx(y["use"]["stem_rings"], abs=0.051 + 1e-9 * y["use"]["stem_rings"])
            checked += 1
        assert y["rings"] == {"stem": ring["stem"], "branch": ring["branch"]}
    assert checked >= 5
    last = years[-1]["ring"]
    assert sum(last["stem"].values()) > 0.0 and sum(last["branch"].values()) > 0.0 and len(last["limb_node"]) > 3
    assert last["stem"]["more_leaf"] > 0.0 and last["branch"]["replaced"] > 0.0


@pytest.mark.slow
def test_a_short_years_rings_split_by_the_share_paid_and_the_winds_extra_is_what_is_left(pair):
    _, logged, _, _, _ = pair
    T = logged.tree
    n = T.n
    alive = T.death[:n] < 0
    levels = T.levels(alive)
    rng = np.random.default_rng(1)
    sap = np.where(alive, rng.uniform(1e-6, 1e-4, n), 0.0)
    keep = 0.7 * sap
    need = np.where(alive, sap * rng.uniform(0.5, 1.5, n), 0.0)
    length = np.where(alive, T.length[:n], 0.0)
    full = np.maximum(need - keep, 0.0)
    held = logged._ring_log
    try:
        logs.note_rings(logged, 99, 0.25 * full, need, keep, sap, length, 2.0, levels, alive, 0.25)
        short = logged._ring_log
        logs.note_rings(logged, 99, full + np.where(alive, 3e-6, 0.0), need, keep, sap, length, 2.0, levels, alive)
        windy = logged._ring_log
    finally:
        logged._ring_log = held
    total = lambda log, k: log["stem"][k] + log["branch"][k]
    more = np.minimum(np.maximum(need - sap, 0.0) * 0.25, 0.25 * full)
    assert short["year"] == 99
    assert total(short, "wind") == pytest.approx(0.0, abs=1e-12)
    assert total(short, "more_leaf") == pytest.approx(float((more * length).sum()) / 2.0)
    assert total(short, "replaced") + total(short, "more_leaf") == pytest.approx(float((0.25 * full * length).sum()) / 2.0)
    assert total(windy, "wind") == pytest.approx(float((3e-6 * length).sum()) / 2.0)
    assert total(windy, "replaced") + total(windy, "more_leaf") == pytest.approx(float((full * length).sum()) / 2.0)


@pytest.mark.slow
def test_what_a_year_had_to_pay_is_kept_and_the_short_years_are_counted(pair):
    _, logged, years, _, _ = pair
    short = 0
    for y in years:
        must = y["must_log"]
        assert must["year"] == y["year"] and must["pool"] >= 0.0 and must["must"] >= 0.0 and 0.0 <= must["paid"] <= 1.0
        assert (must["paid"] < 1.0) == (must["must"] >= must["pool"] or (must["lead"] is not None and must["lead"] >= must["pool"]))
        assert y["must"] == must
        short += must["paid"] < 1.0
    assert getattr(logged, "sapwood_short_years", 0) == short
    assert logs.tree_record(logged)["sapwood_short_years"] == short


@pytest.mark.slow
def test_leaf_area_is_each_leaf_at_its_own_size_and_the_count_is_beside_it(pair):
    """The reported leaf area and the leaf area that shades both count a leaf at its own size (review of 2026-11-11, validation
    challenge P1): the size-weighted figure is the reported one, and the count at the reference size is the other."""
    _, logged, years, _, _ = pair
    T = logged.tree
    n = T.n
    a_ref = float(logged.light.leaf_area)
    got = logs.leaf_areas(logged)
    assert got["leaf_area_sized_m2"] == pytest.approx(logged.stats[-1]["leaf_area_m2"], abs=6e-4)
    assert years[-1]["leaf_area_sized_m2"] == got["leaf_area_sized_m2"] and years[-1]["leaf_area_counted_m2"] == got["leaf_area_counted_m2"]
    # the model's own count of leaves, with every leaf made the reference size and unshrunk
    size, scale = T.leaf_size[:n].copy(), T.leaf_scale[:n].copy()
    try:
        T.leaf_size[:n], T.leaf_scale[:n] = 0.0, 1.0
        count = logged._leaves_at_nodes(logged.year)
    finally:
        T.leaf_size[:n], T.leaf_scale[:n] = size, scale
    assert got["leaf_area_counted_m2"] == pytest.approx(float(count.sum()) * a_ref, rel=1e-5)
    own = np.where(size > 0.0, size, a_ref)
    assert got["leaf_area_sized_m2"] == pytest.approx(float((count * scale * own).sum()), rel=1e-5)
    assert got["leaf_area_counted_m2"] != pytest.approx(got["leaf_area_sized_m2"], rel=1e-3)       # sun and shade leaves differ in size
    # what the year's light was worked out from: the buds' leaf weights as the year began (a year with damage first takes its toll before)
    same = sum(1 for y in years if y["leaf_area_lit_m2"] == y["lit_before"])
    assert same >= YEARS // 2 and years[-1]["leaf_area_lit_m2"] > 0.0


@pytest.mark.slow
def test_branch_wood_splits_three_ways_that_each_add_up(pair):
    _, logged, _, _, snaps = pair
    assert sorted(snaps) == [5, 10, 15]
    for age, snap in snaps.items():
        bw = snap["branch_wood"]
        assert bw["branch_kg"] == pytest.approx(snap["branch_kg"], rel=1e-9, abs=1e-12)
        assert sum(bw["by_order"].values()) == pytest.approx(bw["branch_kg"], rel=1e-9, abs=1e-12)
        assert sum(bw["by_limb_age"].values()) == pytest.approx(bw["branch_kg"], rel=1e-9, abs=1e-12)
        assert bw["by_limb_age"]["over_20"] == 0.0 and bw["by_limb_age"]["on_no_limb"] >= -1e-9
        if snap["crown_base_stem_m"] is not None:
            assert sum(bw["by_crown_quarter"].values()) == pytest.approx(bw["branch_kg"], rel=1e-9, abs=1e-12)
        scan = bw["scan"]
        assert bw["limbs"] >= scan["limbs_over_2cm"] >= scan["limbs_over_5cm"] >= scan["limbs_over_10cm"] >= 0
        assert scan["limbs_over_2cm"] >= scan["low_limbs_over_2cm"] >= scan["low_limbs_ascending"] >= 0
        assert 0.0 <= scan["branch_kg_over_1cm"] <= bw["branch_kg"] + 1e-9 and scan["branch_m_over_1cm"] >= 0.0
        if scan["limb_over_stem_max"] is not None:
            assert 0.0 < scan["limb_over_stem_p90"] <= scan["limb_over_stem_max"]
    last = snaps[15]["branch_wood"]
    assert last["limbs"] > 3 and last["by_order"]["1"] > 0.0 and last["by_order"]["2"] > 0.0 and last["by_limb_age"]["under_10"] > 0.0
    # a tree list's wood (treegen/logs.py) is tools/tree_table.py's
    stem, branch = logs.wood_volumes(logged)
    assert stem == pytest.approx(snaps[15]["stem_m3"], rel=1e-12) and stem * tree_list.DENSITY == pytest.approx(snaps[15]["stem_kg"], rel=1e-12)
    assert branch * tree_list.DENSITY == pytest.approx(snaps[15]["branch_kg"], rel=1e-12)
    record = logs.tree_record(logged)
    assert record["stem_m3"] == stem and record["branch_m3"] == branch and record["leaf_area_lit_m2"] == logged._lit_leaf_m2
    hl = logged.stats[-1]["height_limit"]
    assert (record["leader_light"], record["light_factor"], record["water_factor"], record["carbon_factor"]) == (hl["light_q"], hl["light"], hl["water"], hl["carbon"])


@pytest.mark.slow
def test_every_limb_every_year_and_the_wood_shed(pair):
    _, logged, years, limb_rows, snaps = pair
    cols = {name: i for i, name in enumerate(limb_wood.LIMB_COLUMNS)}
    assert all(len(r) == len(cols) for r in limb_rows)
    final = [r for r in limb_rows if r[cols["year"]] == YEARS]
    assert len(final) == snaps[15]["branch_wood"]["limbs"] == len(limb_wood.limbs(logged)["node"])
    # everything on the limbs is branch wood, and no more than all of it
    assert sum(r[cols["wood_kg"]] for r in final) <= snaps[15]["branch_kg"] * (1.0 + 1e-4)
    assert all(r[cols["birth_year"]] <= YEARS and r[cols["z_m"]] >= 0.0 and r[cols["base_d_cm"]] > 0.0 for r in final)
    # the limbs that stood when the year's rings were worked out have their rings; those old enough for the shedding test, their carbon
    ringed = [r for r in final if r[cols["ring_replaced"]] is not None]
    earning = [r for r in final if r[cols["own_carbon"]] is not None]
    assert len(ringed) >= len(final) // 2 and earning
    ring = years[-1]["ring"]
    by_node = {int(k): float(a + b + c) for k, a, b, c in zip(ring["limb_node"], ring["limb_replaced"], ring["limb_more_leaf"], ring["limb_wind"])}
    for r in ringed:
        assert r[cols["ring_replaced"]] + r[cols["ring_more_leaf"]] + r[cols["ring_wind"]] == pytest.approx(by_node[r[cols["node"]]], rel=1e-3, abs=1e-6)
    # wood shed: over the run, the wood on every dead node, as thick as it was when it died
    T = logged.tree
    n = T.n
    dead = T.death[:n] >= 1
    shed = sum(y["shed_wood"]["branch_kg"] + y["shed_wood"]["stem_kg"] for y in years)
    assert shed == pytest.approx(float((math.pi * T.radius[:n] ** 2 * T.length[:n])[dead].sum()) * limb_wood.DENSITY, rel=1e-9)
    assert shed > 0.0 and all(y["shed_wood"]["branch_kg"] >= 0.0 for y in years)


def test_tree_table_writes_the_new_records_and_the_same_stats(tmp_path, monkeypatch, capsys):
    a, b = tmp_path / "plain" / "1_stand", tmp_path / "logged" / "1_stand"
    assert tree_table.one(1, [], a, 5) == 0
    assert tree_table.one(1, ["log.rings=true", "shedding.log_limbs=true"], b, 5) == 0
    stats = [json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"] for d in (a, b)]
    assert stats[0] == stats[1]
    # the switch-off rule's own comparison (tools/switch_off.py), on the files as written: the two settings are the only options apart
    same, lines = switch_off.compare(tmp_path / "plain", tmp_path / "logged", switched=("shedding.log_limbs",))
    assert same, lines
    assert any("options allowed to differ: log.rings: false against true; shedding.log_limbs: false against true" in x for x in lines)
    assert any(x.startswith("  tree.json: identical in all ") for x in lines) and any("yearly.rings" in x for x in lines)
    assert not switch_off.compare(tmp_path / "plain", tmp_path / "logged")[0]       # a setting nobody named still counts
    plain, logged = (json.loads((d / "tree.json").read_text(encoding="utf-8")) for d in (a, b))
    for doc in (plain, logged):
        assert {"shed_wood", "must", "leaf_area_counted_m2", "leaf_area_sized_m2", "leaf_area_lit_m2"} <= set(doc["yearly"][-1])
        assert doc["sapwood_short_years"] == sum(1 for y in doc["yearly"] if y["must"] and y["must"]["paid"] < 1.0)
        assert {"by_order", "by_limb_age", "by_crown_quarter", "scan", "branch_kg", "limbs"} == set(doc["snapshots"][0]["branch_wood"])
    assert "rings" not in plain["yearly"][-1] and not (a / "limbs.json").exists()
    assert set(logged["yearly"][-1]["rings"]) == {"stem", "branch"} and set(logged["yearly"][-1]["rings"]["stem"]) == set(logs.RING_PARTS)
    limbs = json.loads((b / "limbs.json").read_text(encoding="utf-8"))
    assert limbs["columns"] == list(limb_wood.LIMB_COLUMNS) and isinstance(limbs["rows"], list)
    # the two readers take the saved files as they are
    monkeypatch.setattr(limb_wood, "E", tmp_path)
    limb_wood.scans(["logged"])
    limb_wood.wood(["logged", "plain"], ages=(5,))
    said = capsys.readouterr().out
    assert "| `logged` | at the scans' height | 1 |" in said and "| `logged` | 5 | 1 |" in said and "| `plain` | 5 | 1 |" in said


def test_a_yearly_log_gives_no_top_height_where_the_curve_cant_be_fitted():
    assert logs.fitted_top_height([5.0, 5.0, 5.0], [3.0, 3.5, 4.0], 1000.0) == (None, 3.0, 3.5)      # three trees, one diameter
    assert logs.fitted_top_height([5.0, 6.0], [3.0, 3.5], 1000.0) == (None, 0.0, None)               # too few trees
    d, h = [4.0, 8.0, 12.0, 16.0], [5.0, 9.0, 12.0, 14.0]
    assert logs.fitted_top_height(d, h, 1000.0) == logs.naslund_top_height(d, h, 1000.0)


# -- a plot -------------------------------------------------------------------
@pytest.mark.slow
def test_a_plot_grows_the_same_with_the_stand_log_on_and_the_log_counts_what_went():
    def grow(*more):
        # as tests/test_forest.py's tree list test: under birch v1's defaults none of these trees dies in 5 years
        sp = species(*BEFORE_V1, "plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=9000", "plot.natural_start.area_m2=20",
                     "mortality.enabled=true", "plot.stand_measures=true", *more)
        plot = make_plot(sp, lean=True)
        for _ in range(5):
            plot.step()
        return plot

    plain, logged = grow(), grow("log.stand=true")
    assert plain.stats == logged.stats and plain.info == logged.info and plain.alive == logged.alive
    assert getattr(plain, "stand_log", None) is None and getattr(plain, "tree_log", None) is None
    log = logged.stand_log
    assert [r["year"] for r in log] == [1, 2, 3, 4, 5]
    dead = [i for i in logged.info if i.get("removed") is not None]
    assert dead and sum(r["dead_trees"] for r in log) == len(dead) == len(logged.tree_log)
    for r in log:
        went = [i for i in dead if i["removed"] == r["year"]]
        assert r["dead_trees"] == len(went)
        assert r["dead_stem_m3"] == pytest.approx(sum(logged.tree_log[i["id"]]["stem_m3"] for i in went), abs=1e-15)
        assert r["dead_stem_m3_ha"] == pytest.approx(r["dead_stem_m3"] / logged.area * 1e4)
        assert sum(r["dead_stem_m3_by_cause"].values()) == pytest.approx(r["dead_stem_m3"], abs=1e-15)
        assert set(r["dead_stem_m3_by_cause"]) == {i["cause"] for i in went}
        s = logged.stats[r["year"] - 1]
        assert r["trees"] == s["trees"] and r["lai"] == pytest.approx(s["lai"], abs=6e-4)
        assert r["trees_grew"] >= r["leaders"] >= max(r["light_slowed"], r["water_slowed"], r["carbon_cut"]) >= 0
        assert 0 <= r["short_of_sapwood"] <= r["trees_grew"] and r["lai_lit"] is not None
        assert set(r) == set(logs.STAND_LOG_WHAT)
    assert log[-1]["trees_grew"] > 0
    json.dumps(log)       # plain numbers: it can be written as it is

    # the tree lists: a living tree's new columns, with or without the log; a dead one's only with it
    doc, doc_plain = tree_list.tree_list(logged), tree_list.tree_list(plain)
    json.dumps(doc)
    living = {t["id"]: t for t in doc["trees"] if t["alive"]}
    assert [t for t in doc_plain["trees"] if t["alive"]] == list(living.values())
    gone, gone_plain = [t for t in doc["trees"] if not t["alive"]], [t for t in doc_plain["trees"] if not t["alive"]]
    assert gone and len(gone) == len(gone_plain)
    assert all(t["stem_kg"] is not None and t["stem_m3"] is not None and t["leaf_area_counted_m2"] is not None for t in gone)
    assert all(t["stem_kg"] is None and t["germination_year"] is not None and t["vigour"] is not None for t in gone_plain)
    k = logged.alive[0]
    m, row = logged.trees[k], living[k]
    stem, branch = logs.wood_volumes(m)
    assert stem > 0.0 and row["stem_m3"] == pytest.approx(stem, rel=1e-5)
    assert row["stem_kg"] == pytest.approx(stem * tree_list.DENSITY, rel=1e-5) and row["branch_kg"] == pytest.approx(branch * tree_list.DENSITY, rel=1e-5, abs=1e-12)
    assert row["germination_year"] == logged.info[k]["germination"] and row["vigour"] == logged.info[k]["vigour"]
    assert row["age_years"] == doc["plot_year"] - row["germination_year"]
    assert row["leaf_area_sized_m2"] == pytest.approx(row["leaf_area_m2"], abs=2e-3) and row["leaf_area_lit_m2"] == pytest.approx(m._lit_leaf_m2, rel=1e-5)
    assert set(tree_list.MORE) <= set(row)

    # a windthrow after the year is done goes into that year's row
    before = dict(log[-1])
    took = logged.open_gap(0.0, 0.0, 1.5)
    assert took >= 1 and len(logged.stand_log) == 5
    assert log[-1]["dead_trees"] == before["dead_trees"] + took and log[-1]["dead_stem_m3_by_cause"]["windthrow"] > 0.0

    # top height on the approved definition is read off what a tree list holds: give the trees sizes that have one
    for j, k in enumerate(logged.alive):
        logged.trees[k].stats[-1]["dbh_cm"], logged.trees[k].stats[-1]["height_m"] = 3.0 + 0.7 * j, 4.0 + 0.5 * j - 0.01 * j * j
    assert len(logged.alive) >= 3
    logged._log_year()
    trees = [t for t in tree_list.tree_list(logged)["trees"] if t["alive"]]
    recs = [{"dbh_cm": t["dbh_cm"], "height_m": t["height_m"]} for t in trees]
    top, counted, simple = scorecard.naslund_top_height(recs, logged.area)
    assert trees[0]["dbh_cm"] == pytest.approx(float(bark.dbh_over_bark(3.0)), abs=0.006)        # over bark, once
    assert log[-1]["top_height_approved_m"] == pytest.approx(top, abs=6e-5) and log[-1]["top_height_mean_m"] == pytest.approx(simple, abs=6e-5)
    assert log[-1]["top_height_trees"] == pytest.approx(counted, abs=6e-4)


@pytest.mark.slow
def test_the_stand_log_and_the_tree_list_say_what_held_each_leader():
    sp = species("plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=6000", "plot.natural_start.area_m2=20",
                 "mortality.enabled=true", "plot.stand_measures=true", "log.stand=true")
    plot = make_plot(sp, lean=True)
    for _ in range(3):
        plot.step()
    active = [k for k in plot.alive if 4 > plot.info[k]["germination"]]
    lit = sum(float(plot.trees[k].light_sources()[5].sum()) for k in active) * float(plot.light.leaf_area)
    plot.step()
    row = plot.stand_log[-1]
    assert row["year"] == 4 and row["lai_lit"] == pytest.approx(lit / plot.area, abs=6e-5)
    assert 1 <= row["leaders"] <= row["trees_grew"] <= len(active)
    doc = tree_list.tree_list(plot)
    seen = 0
    for t in doc["trees"]:
        if not t["alive"]:
            continue
        m = plot.trees[t["id"]]
        if logs.grew_this_year(m) and getattr(m, "_hd", None) is not None:
            hl = m.stats[-1]["height_limit"]
            assert (t["leader_light"], t["light_factor"], t["water_factor"], t["carbon_factor"]) == (hl["light_q"], hl["light"], hl["water"], hl["carbon"])
            assert 0.0 <= t["light_factor"] <= 1.0 and 0.0 <= t["water_factor"] <= 1.0
            seen += 1
        else:
            assert t["leader_light"] is None and t["light_factor"] is None
    assert seen >= 1
    if row["dead_trees"] == 0:      # every tree that grew is still there to be counted again
        grew = [plot.trees[k] for k in active if logs.grew_this_year(plot.trees[k])]
        led = [m._hd for m in grew if getattr(m, "_hd", None) is not None]
        assert row["trees_grew"] == len(grew) and row["leaders"] == len(led)
        assert row["light_slowed"] == sum(1 for hd in led if hd["light"] < 1.0)
        assert row["water_slowed"] == sum(1 for hd in led if hd["water"] < 1.0)
        assert row["carbon_cut"] == sum(1 for hd in led if hd["carbon_scale"] < 1.0)
        assert row["short_of_sapwood"] == sum(1 for m in grew if m._must_log["paid"] < 1.0)


def test_top_height_on_the_approved_definition_is_the_scorecards():
    rng = np.random.default_rng(3)
    d = rng.uniform(4.0, 30.0, 40)
    h = 1.3 + 2.2 * d ** 0.7 + rng.normal(0.0, 0.5, 40)
    recs = [{"dbh_cm": float(a), "height_m": float(b)} for a, b in zip(d, h)]
    for area in (150.0, 1000.0, 2500.0, 10000.0):       # 1.5 trees, 10, 25, and more than there are
        assert logs.naslund_top_height(d, h, area) == scorecard.naslund_top_height(recs, area)
    # a tree below breast height has no diameter: it counts in neither
    with_small = [{"dbh_cm": None, "height_m": 0.9}] + recs
    assert logs.naslund_top_height([0.0] + list(d), [0.9] + list(h), 1000.0) == scorecard.naslund_top_height(with_small, 1000.0)
    assert math.isnan(logs.naslund_top_height([5.0, 6.0], [3.0, 4.0], 1000.0)[0])


# -- Repola's rows, side by side --------------------------------------------------
def test_repolas_branch_equation_with_crown_length():
    # ln y = -5.067 + 14.614 dS/(dS + 12) - 5.074 h/(h + 12) + 0.092 cl, dS = 2 + 1.25 d, with exp((0.01508 + 0.05663)/2): 20 cm, 18 m, 9 m of crown
    assert m3_wood.repola_a3(20.0, 18.0, 9.0) == pytest.approx(17.6342, abs=5e-4)
    assert m3_wood.repola(20.0, 18.0)[1] == pytest.approx(20.7864, abs=5e-4)
    eq = independent_checks.branch_equations(20.0, 18.0, 9.0)
    assert eq == {"eq9": m3_wood.repola(20.0, 18.0)[1], "a3_own": m3_wood.repola_a3(20.0, 18.0, 9.0), "a3_mean": m3_wood.repola_a3(20.0, 18.0, 0.58 * 18.0)}
    assert independent_checks.branch_equations(20.0, 18.0, None)["a3_own"] is None
    assert m3_wood.repola_a3(20.0, 18.0, 10.0) / m3_wood.repola_a3(20.0, 18.0, 9.0) == pytest.approx(math.exp(0.092))
    assert independent_checks.in_range(2.5) and independent_checks.in_range(38.0) and not independent_checks.in_range(38.01) and not independent_checks.in_range(2.49)


def _stand_tree(folder: Path, seed: int, wood_dbh: float):
    d = folder / f"{seed}_stand"
    d.mkdir(parents=True)
    snaps = [{"age": a, "stem_kg": 100.0 + a, "branch_kg": 20.0 + seed, "stem_m3": 0.3} for a in (30, 50, 60)]
    years = [{"year": a, "dbh_cm": wood_dbh, "height_m": 18.0 + 0.1 * a, "crown_base_height_m": 9.0, "lai": 4.0, "leaf_area_m2": 80.0} for a in (30, 50, 60)]
    (d / "tree.json").write_text(json.dumps({"snapshots": snaps}), encoding="utf-8")
    (d / "stats.json").write_text(json.dumps({"per_year": years}), encoding="utf-8")


def test_the_three_branch_rows_stand_side_by_side_for_stand_trees(tmp_path):
    for seed in (1, 2, 3):
        _stand_tree(tmp_path, seed, 18.0)
    rows = independent_checks.tree_rows(tmp_path, ages=(30, 50, 60))
    for age in (30, 50, 60):
        at = [r for r in rows if r["age"] == age]
        names = [r["what"] for r in at]
        i = next(j for j, name in enumerate(names) if "Eq. 9" in name)
        assert "branch wood over" in names[i] and "Eq. A3, at the tree's own crown length" in names[i + 1] and "mean crown ratio, 0.58" in names[i + 2]
        h, d_ob = 18.0 + 0.1 * age, float(bark.dbh_over_bark(18.0))      # the yearly row's diameter is wood: bark goes on once
        want = {"eq9": m3_wood.repola(d_ob, h)[1], "a3_own": m3_wood.repola_a3(d_ob, h, h - 9.0), "a3_mean": m3_wood.repola_a3(d_ob, h, 0.58 * h)}
        for row, key in zip(at[i:i + 3], ("eq9", "a3_own", "a3_mean")):
            ratios = [(20.0 + seed) / want[key] for seed in (1, 2, 3)]
            gmean = math.exp(sum(math.log(x) for x in ratios) / 3.0)
            assert row["model"].startswith(f"{gmean:.3g} ") and "n 3" in row["model"]
            assert row["inside"] == 1.0 and row["inside_text"] == "3 of 3" and row["reads"] is None
            assert row["kind"] == independent_checks.branch_kind()[0]
    text = independent_checks.table(rows)
    assert "3 of 3" in text and "INFO" not in text.split("Reported rows")[0]
    # the kind is read off the species file's own label of the value that sets branch wood
    kind, why = independent_checks.branch_kind()
    assert kind == independent_checks.TUNED and "Repola" in why


def test_a_branch_row_reads_info_when_under_two_thirds_of_its_stems_are_inside_the_equations_diameters(tmp_path):
    _stand_tree(tmp_path, 1, 18.0)
    _stand_tree(tmp_path, 2, 36.5)       # 39.8 cm over bark: outside 2.5-38.0
    _stand_tree(tmp_path, 3, 37.0)
    assert float(bark.dbh_over_bark(36.5)) > 38.0
    rows = [r for r in independent_checks.tree_rows(tmp_path, ages=(50,)) if "branch wood over" in r["what"]]
    assert len(rows) == 3 and all(r["inside"] == pytest.approx(1.0 / 3.0) and r["reads"] == "INFO" for r in rows)
    assert independent_checks.table(rows).count("**INFO**: under two thirds") == 3
    # two of three inside is two thirds: not under it
    row = independent_checks._row("x", 50, "1", "1", "kind", "note", (2, 3))
    assert row["reads"] is None and independent_checks._row("x", 50, "1", "1", "kind", "note", (1, 3))["reads"] == "INFO"
    assert independent_checks._row("x", 50, "1", "1", "kind", "note")["inside"] is None


def test_plot_branch_wood_takes_the_tree_lists_diameter_as_it_is(tmp_path):
    """A tree list's DBH is over bark already (tools/tree_list.py): adding bark again read plot branch wood about 1.3 times too well."""
    trees = [{"alive": True, "dbh_cm": 12.0 + 2.0 * i, "height_m": 15.0 + i, "crown_base_m": 7.0 + 0.5 * i, "branch_kg": 5.0 + i} for i in range(6)]
    trees += [{"alive": True, "dbh_cm": None, "height_m": 1.0, "crown_base_m": None, "branch_kg": 0.01},      # below 1.3 m: not a stem
              {"alive": False, "dbh_cm": 20.0, "height_m": 19.0, "crown_base_m": 9.0, "branch_kg": 9.0}]       # dead: not standing
    got = independent_checks.plot_branch_wood(trees, 100.0)
    stems = trees[:6]
    assert got["stems"] == 6 and got["inside"] == 6
    assert got["repola"]["eq9"] == pytest.approx(sum(m3_wood.repola(t["dbh_cm"], t["height_m"])[1] for t in stems) / 100.0 * 10.0)
    assert got["repola"]["a3_own"] == pytest.approx(sum(m3_wood.repola_a3(t["dbh_cm"], t["height_m"], t["height_m"] - t["crown_base_m"]) for t in stems) / 100.0 * 10.0)
    assert got["repola"]["a3_mean"] == pytest.approx(sum(m3_wood.repola_a3(t["dbh_cm"], t["height_m"], 0.58 * t["height_m"]) for t in stems) / 100.0 * 10.0)
    twice = sum(m3_wood.repola(float(bark.dbh_over_bark(t["dbh_cm"])), t["height_m"])[1] for t in stems) / 100.0 * 10.0
    assert twice > 1.15 * got["repola"]["eq9"]
    assert got["model_t_ha"] == pytest.approx(sum(t["branch_kg"] for t in stems) / 100.0 * 10.0) and got["model"]["eq9"] == got["model_t_ha"]
    # a list from before the wood columns: Repola's side still, no model figure
    old = [{k: v for k, v in t.items() if k != "branch_kg"} for t in trees]
    assert independent_checks.plot_branch_wood(old, 100.0)["model_t_ha"] is None
    assert independent_checks.plot_branch_wood(old, 100.0)["repola"] == got["repola"]

    for name, rows_ in (("new", trees), ("old", old)):
        plot = tmp_path / name / "plot_1"
        plot.mkdir(parents=True)
        (plot / "plot.json").write_text(json.dumps({"stats": [{"year": 50, "basal_area_ob_m2_ha": 20.0, "subcanopy_diffuse_light_pct": 18.0}]}), encoding="utf-8")
        (plot / "trees_050.json").write_text(json.dumps({"area_m2": 100.0, "trees": rows_}), encoding="utf-8")
    new = [r for r in independent_checks.plot_rows(tmp_path / "new", ages=(50,)) if "plot branch wood over" in r["what"]]
    assert len(new) == 3 and all(r["inside_text"] == "6 of 6" and r["reads"] is None for r in new)
    ratio = got["model"]["eq9"] / got["repola"]["eq9"]
    assert new[0]["model"].startswith(f"{ratio:.3g} ") and f"{got['repola']['eq9']:.3g} t/ha" in new[0]["reference"]
    before = [r for r in independent_checks.plot_rows(tmp_path / "old", ages=(50,)) if "plot branch wood" in r["what"]]
    assert len(before) == 3 and all("saved no wood" in r["model"] and "t/ha" in r["reference"] for r in before)
