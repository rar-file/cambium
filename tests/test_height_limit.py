"""The height limit (height_driver in the species file) limits the leader; it doesn't script it.

The maintainer's rule: the curve only limits the leader, which grows by making real new nodes that cost carbon, and falls
short of the curve when light, water or carbon are short.  No height is set directly and no node is moved.
"""
from __future__ import annotations

import numpy as np
import pytest

from treegen import checkpoint
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import load_environment, load_species

ON = ["height_driver.enabled=true"]


def grow(years: int, sets: list, seed: int = 3, keep=None):
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, sets)
    env, _ = load_environment("sweden_open_field")
    model = GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)
    for _ in range(years):
        if keep is not None:
            keep(model)
        model.step()
    return model


def test_off_by_default():
    sp, _ = load_species("betula_pendula")
    assert sp.height_driver.enabled is False
    assert sp.stats.limbs_on_leader is False
    assert sp.pipe_model.heartwood_by_own_foliage is False
    assert sp.pipe_model.branch_sapwood_senescence is None
    assert sp.shedding.shade_softness is None
    assert sp.mechanics.pendulous_radius_limb is None


def test_limbs_are_soft_only_below_their_own_radius():
    """With the limb radius set, a limb of a given thickness is stiffer than a twig of that thickness."""
    from treegen import mechanics

    model = grow(6, ON + ["mechanics.pendulous_radius_limb=0.002", "mechanics.pendulous_radius=0.01", "leader_damage.enabled=false"])
    limbs = model._limb_nodes(model.tree.n)
    assert limbs is not None and limbs.any()
    T = model.tree
    assert not limbs[T.order[: T.n] == 0].any()
    limb = mechanics.pendulous_factor(np.array([0.004]), 0.002, 4.0)
    twig = mechanics.pendulous_factor(np.array([0.004]), 0.01, 4.0)
    assert limb[0] > 0.9 > twig[0]
    plain = grow(1, ON)
    assert plain._limb_nodes(plain.tree.n) is None


def test_it_follows_the_curve_when_nothing_is_short():
    model = grow(14, ON + ["leader_damage.enabled=false"])
    for s in model.stats[1:]:
        assert s["height_m"] == pytest.approx(model._curve_height(s["year"]), abs=0.08)


def test_every_metre_of_height_is_real_new_nodes_that_cost_carbon():
    model = grow(12, ON + ["leader_damage.enabled=false"])
    T = model.tree
    log = [s["height_limit"] for s in model.stats[1:]]
    assert all(row["nodes"] >= 1 and row["cost_units"] > 0.0 for row in log)
    # the stem is a chain of internodes, each born in its year, and its height is that chain's own geometry
    chain = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
    assert T.birth[chain[1:]].min() >= 1
    tip_from_chain = float(T.pos[chain, 2].max())
    assert model.stats[-1]["height_m"] == pytest.approx(tip_from_chain, abs=0.02)
    # no year's growth is longer than the nodes built that year
    for year in range(2, 13):
        built = T.length[chain][T.birth[chain] == year].sum()
        assert log[year - 1]["got_m"] <= built + 1e-6


def test_no_node_is_moved():
    """With the bending of wood off, nothing else may shift a node, so every node stays where it was built."""
    frames = []
    model = grow(12, ON + ["mechanics.enabled=false", "leader_damage.enabled=false"], keep=lambda m: frames.append(m.tree.pos[: m.tree.n].copy()))
    final = model.tree.pos
    for pos in frames:
        assert np.array_equal(final[: len(pos)], pos)


def test_short_of_carbon_it_falls_short():
    """The same tree with a small fraction of its carbon stays under the curve."""
    model = grow(14, ON + ["leader_damage.enabled=false", "resource.alpha=0.45", "height_driver.reference_alpha=null"])
    last = model.stats[-1]
    assert last["height_m"] < 0.6 * model._curve_height(14)
    assert any(s["height_limit"]["held_by"] == "carbon" for s in model.stats[1:])


def test_short_of_water_it_falls_short():
    """Water short enough to starve the tree: it can't build what the curve allows."""
    model = grow(14, ON + ["leader_damage.enabled=false", "hydraulics.xylem_conductivity=0.03", "hydraulics.root_xylem_conductivity=0.03"])
    assert model.stats[-1]["height_m"] < 0.2 * model._curve_height(14)


def _plan_at(q_leader: float, opening: float):
    """The limit a leader gets this year, at this canopy light and this stomatal opening of the crown."""
    model = grow(6, ON + ["leader_damage.enabled=false"])
    T = model.tree
    term = np.nonzero((T.term[: T.n] == 1) & (T.axis[: T.n] == 0) & (T.death[: T.n] < 0))[0]
    q = np.zeros(T.n)
    bright = q.copy()
    bright[term] = q_leader
    ref0 = model._hd_ref
    plan = model._height_limit_plan(7, term, np.zeros(0, np.int64), bright, q, opening)
    return plan, plan["ref"] - ref0, model.sp.height_driver


def test_less_light_lowers_the_limit_in_proportion():
    full, gained_full, cfg = _plan_at(1.0, 1.0)
    shaded, gained_shaded, _ = _plan_at(0.15, 1.0)
    assert shaded["light"] == pytest.approx(0.15 / float(cfg.light_full))
    assert gained_shaded == pytest.approx(gained_full * shaded["light"])
    assert shaded["allowed"] < full["allowed"]


def test_less_water_lowers_the_limit_in_proportion():
    full, gained_full, cfg = _plan_at(1.0, 1.0)
    dry, gained_dry, _ = _plan_at(1.0, 0.2)
    assert dry["water"] == pytest.approx(0.2 / float(cfg.water_full))
    assert gained_dry == pytest.approx(gained_full * dry["water"])
    assert dry["allowed"] < full["allowed"]


def test_a_side_shoot_never_ends_above_the_leader():
    model = grow(20, ON + ["leader_damage.enabled=false"])
    for s in model.stats[5:]:
        assert s["height_m"] <= model._curve_height(s["year"]) + 0.08


def _first_browsed_seed(years: int = 12) -> GrowthModel:
    for seed in range(1, 30):
        model = grow(years, ON, seed=seed)
        if model.leader_losses:
            return model
    raise AssertionError("no seed lost its leader in 29 tries")


def test_a_lost_leader_is_replaced_and_gets_back_to_the_curve():
    model = _first_browsed_seed()
    for _ in range(14):
        model.step()
    assert model.stats[-1]["height_m"] == pytest.approx(model._curve_height(model.year), abs=0.25)


def test_the_stem_is_the_path_to_the_shoot_the_limit_paid_for():
    model = _first_browsed_seed()
    T = model.tree
    chain = T.trunk_chain(model.leader_axes)
    assert chain[0] == 0
    assert all(T.parent[b] == a for a, b in zip(chain, chain[1:]))
    assert float(T.pos[chain[-1], 2]) == pytest.approx(model.stats[-1]["height_m"], abs=0.1)
    assert model.leader_axes == set(int(a) for a in np.unique(T.axis[chain]))


def test_limbs_on_the_stem_read_the_crown_base_from_the_stem():
    """With a replaced leader, order == 1 finds only that leader, low down, and none of the limbs above it."""
    model = _first_browsed_seed()
    assert model.leader_losses
    old = model.measure()["crown_base_height_m"]
    model.sp.stats.limbs_on_leader = True
    new = model.measure()["crown_base_height_m"]
    assert new is not None
    assert old is None or new >= old - 1e-9


def test_falling_under_the_line_is_the_old_rule_until_softened():
    model = grow(1, ON)
    value = np.array([0.0, 0.1, 0.2, 0.3])
    assert model._falls(value, 0.2).tolist() == [True, True, False, False]
    model.sp.shedding.shade_softness = 0.5
    n = 20000
    many = lambda q: float(model._falls(np.full(n, q), 0.2).mean())
    assert many(0.3) == 0.0
    assert many(0.2) == 0.0
    assert many(0.1) == 1.0
    assert many(0.15) == pytest.approx(0.5, abs=0.02)
    upkeep = np.array([0.0, 2.0, 2.0])
    falls = model._falls(np.array([1.0, 3.0, 0.0]), upkeep)
    assert falls.tolist() == [False, False, True]
