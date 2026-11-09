"""roots.paid: root wood and fine roots cost carbon, and the books close.  On by default since birch v1 (2026-11-08)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import root_measure  # noqa: E402

from treegen import checkpoint  # noqa: E402
from treegen.environment import make_environment, make_soil  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402
from treegen.params import load_environment, load_species  # noqa: E402


def _model(paid: bool, seed: int = 4, sets: tuple = ()):
    sp, _ = load_species("betula_pendula")
    # said both ways: it's on by default since birch v1
    checkpoint.set_values(sp, [f"roots.paid.enabled={'true' if paid else 'false'}", *(sets if paid else ())])
    env, _ = load_environment("sweden_open_field")
    return GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)


def test_it_is_off_by_default():
    """Named when it was off by default; on since birch v1 (2026-11-08).  Switched off, it books nothing."""
    sp, _ = load_species("betula_pendula")
    assert sp.roots.paid.enabled is True
    model = _model(False)
    for _ in range(3):
        model.step()
    assert model.roots.carbon_log == {}


def test_the_root_carbon_goes_where_the_log_says():
    model = _model(True)
    g_resp = 1.0 + float(model.sp.resource.growth_respiration_coefficient)
    for _ in range(14):
        model.step()
        log = model.roots.carbon_log
        net = float(model._root_carbon)
        # everything left after the fine roots' upkeep is fine roots, wood with its respiration, or the logged rest
        spent = log["fine_build"] + (log["new_root_wood"] + log["rings"]) * g_resp + log["rest"]
        assert math.isclose(spent, net, rel_tol=1e-9, abs_tol=1e-9) or log["new_root_wood"] * g_resp > net - log["fine_build"]
        assert log["rings"] <= log["rings_wanted"] + 1e-12


def test_the_wood_gained_is_the_wood_paid_for():
    model = _model(True)
    unit_g = root_measure.unit_grams(model)
    for _ in range(12):
        before = root_measure.wood_kg(model)
        n_before = model.roots.tree.n
        model.step()
        R = model.roots.tree
        # roots shed this year take their wood with them, so add it back
        shed = (R.death[: n_before] == model.year)
        lost = float((math.pi * R.radius[: n_before][shed] ** 2 * R.length[: n_before][shed]).sum()) * root_measure.root_density(model)
        gain = root_measure.wood_kg(model) + lost - before
        paid = (model.roots.carbon_log["new_root_wood"] + model.roots.carbon_log["rings"]) * unit_g / 1000.0
        assert abs(gain - paid) < 1e-4 + 0.02 * paid


def test_root_radii_never_shrink():
    model = _model(True)
    last = None
    for _ in range(14):
        model.step()
        R = model.roots.tree
        now = R.radius[: R.n].copy()
        if last is not None:
            alive = R.death[: len(last)] < 0
            assert np.all(now[: len(last)][alive] >= last[alive] - 1e-12)
        last = now


def test_with_carbon_to_spare_the_collar_sums_to_the_stump():
    # at the size this test was written for: on the height curve (on by default since birch v1) the 14-year tree has a
    # 5.3 cm stump and its collar sums to 0.69, just under the floor here (node_fb_dg_collar); off, 12.6 cm and 0.94
    model = _model(True, sets=("height_driver.enabled=false",))
    for _ in range(14):
        model.step()
    log = model.roots.carbon_log
    assert log["rings"] >= log["rings_wanted"] * (1.0 - 1e-9)
    a = root_measure.architecture(model)
    assert a["rel_sum_stump"] <= float(model.sp.roots.paid.rel_sum_d2) * 1.02
    assert a["rel_sum_stump"] >= float(model.sp.roots.paid.rel_sum_d2) * 0.6


def test_on_the_v1_defaults_the_collar_sums_to_the_stump():
    """The same rule on the model as shipped (height curve on).  Fails on birch v1: the collar sums to 0.69, under
    the floor, because young trees get room for too few collar roots (DECISIONS 98; fixed after v1 with the young-roots
    floor).  Kept failing on purpose, not skipped."""
    model = _model(True)
    for _ in range(14):
        model.step()
    a = root_measure.architecture(model)
    assert a["rel_sum_stump"] <= float(model.sp.roots.paid.rel_sum_d2) * 1.02
    assert a["rel_sum_stump"] >= float(model.sp.roots.paid.rel_sum_d2) * 0.6


def test_no_carbon_no_rings():
    """A root system that can't pay is thinner, and gets no free wood."""
    model = _model(True)
    for _ in range(8):
        model.step()
    R = model.roots
    T = R.tree
    before = T.radius[: T.n].copy()
    R.carbon_log = {}
    R.update_radii_paid(9, R.stump_d_m * 1.2, 0.0, float(model.sp.pipe_model.wood_volume_per_carbon), 530.0)
    assert R.carbon_log["rings"] == 0.0
    assert R.carbon_log["rings_wanted"] > 0.0
    alive = T.death[: T.n] < 0
    assert np.allclose(T.radius[: T.n][alive], before[alive])


def test_anchorage_and_the_root_plate_still_read_the_roots():
    from treegen import damage

    model = _model(True)
    for _ in range(25):
        model.step()
    a = damage.anchorage_of(model)
    assert a["plate_radius_m"] > 0.0 and a["plate_depth_m"] > 0.0
    assert len(a["main_roots"]) >= 3
    assert a["overturning_resistance_mean_knm"] > 0.0
    state = damage.state_from_model(model)
    state.anchorage = a
    assert damage.uprooting_moment_knm(state, 90.0, model.sp) > 0.0
    plate = damage.root_plate(state, 90.0, model.sp)
    assert plate["plate_radius_m"] == round(a["plate_radius_m"], 3)
    assert plate["plate_depth_m"] == round(a["plate_depth_m"], 3)


def test_trees_in_a_plot_pay_for_their_roots_too():
    import cli
    from treegen.plot import Plot

    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, ["roots.paid.enabled=true"])
    env_p, _ = cli.load_environment("sweden_open_field")
    plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), 1, 3, "natural", lean=True)
    for _ in range(5):
        plot.step()
    logs = [plot.trees[k].roots.carbon_log for k in plot.alive]
    assert logs and all("rings" in log for log in logs)


def test_measuring_the_roots_changes_nothing():
    import json

    for paid in (False, True):
        plain, read = _model(paid), _model(paid)
        for year in range(1, 13):
            plain.step()
            wood = root_measure.wood_kg(read)
            read.step()
            root_measure.ledger_year(read, year, wood)
            root_measure.architecture(read)
        assert json.dumps(plain.stats, sort_keys=True) == json.dumps(read.stats, sort_keys=True)


def test_the_taproot_stops_at_its_length_whichever_way_stones_turn_it():
    """Seed 16's taproot never got below taproot_max_depth, and ran on sideways as a thick log, 1.5 m long and 88 kg at 60."""
    model = _model(True, seed=16)
    for _ in range(25):
        model.step()
    limit = float(model.sp.roots.paid.taproot_length_per_depth) * float(model.sp.roots.taproot_max_depth)
    R = model.roots.tree
    on = (model.roots.kind[R.axis[: R.n]] == 0) & (R.death[: R.n] < 0)
    assert float(R.length[: R.n][on].sum()) <= limit + 1e-6


def test_a_radicle_over_a_stone_at_the_surface_goes_round_it():
    """Seed 12 has a stone at the surface under the stand tree's origin.  The collar's short steps once went straight down
    onto it, so the tree never rooted and stood at height 0 for its whole run: 8 of 500 seeds, against none with the setting off."""
    env, _ = load_environment("sweden_open_field")
    assert make_soil(env).is_stone(np.array([[0.0, 0.0, -0.01]]), 12)[0]
    model = _model(True, seed=12)
    assert model.roots.tree.n > 1
    for _ in range(3):
        model.step()
    assert model.stats[-1]["height_m"] > 0.0


def test_the_tables_leave_out_a_seed_that_never_grew_and_say_so(monkeypatch, capsys):
    import tree_table

    runs = {1: {"per_year": {60: {"height_m": 23.0}}}, 2: {"per_year": {60: {"height_m": 0.0}}}}
    monkeypatch.setattr(tree_table, "load", lambda label: runs)
    root_measure._SAID.discard("x")
    assert list(root_measure._load("x")) == [1]
    assert "seed 2" in capsys.readouterr().out
