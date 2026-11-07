"""The crown's frame (crown_frame in the species file): published data set the main limbs; light and carbon decide the rest.

The maintainer's limits: limbs are real nodes that cost carbon, grow year by year and can fall short or die.  No finished shape is
placed and no node is moved.
"""
from __future__ import annotations

import numpy as np

from treegen import checkpoint
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import load_environment, load_species

ON = ["height_driver.enabled=true", "stats.limbs_on_leader=true", "crown_frame.enabled=true", "mechanics.pendulous_radius_limb=0.002",
      "leader_damage.enabled=false"]


def grow(years: int, sets: list, seed: int = 3, stand: bool = True):
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, sets)
    env, _ = load_environment("sweden_open_field")
    model = GrowthModel(sp, make_environment(env), seed, stand=stand, soil=make_soil(env), lean=True)
    for _ in range(years):
        model.step()
    return model


def limbs_of(model):
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    on = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    return np.nonzero(alive & T.is_lateral[:n] & ~on & on[np.maximum(T.parent[:n], 0)])[0]


def test_off_by_default():
    sp, _ = load_species("betula_pendula")
    assert sp.crown_frame.enabled is False
    assert sp.crown_frame.surplus_to_stem < 1.0     # the rest of a full crown's surplus is lost; all on the stem ran to 114 cm
    # and with the height limit off it stays off, whatever its own switch says
    model = grow(3, ["crown_frame.enabled=true"])
    assert not model._frame_on()
    assert "_frame_named" not in model.__dict__


def test_only_named_buds_start_limbs_and_their_angles_are_the_drawn_ones():
    model = grow(18, ON)
    T = model.tree
    limbs = limbs_of(model)
    assert limbs.size > 5
    gsa = model._frame_setpoints()[T.axis[limbs]]
    assert np.isfinite(gsa).all()
    cf = model.sp.crown_frame
    assert (np.degrees(gsa) >= float(cf.angle_min_deg)).all() and (np.degrees(gsa) <= float(cf.angle_max_deg)).all()


def test_fewer_limbs_than_without_the_frame():
    sets = [s for s in ON if not s.startswith("crown_frame")]
    assert limbs_of(grow(18, ON)).size < limbs_of(grow(18, sets)).size


def test_limbs_grow_year_by_year_as_real_nodes():
    """Length comes from new nodes each year, none placed at their final length and none moved along the limb."""
    model = grow(14, ON)
    T = model.tree
    limb = limbs_of(model)
    ages = {int(a): set(T.birth[: T.n][T.axis[: T.n] == a].tolist()) for a in T.axis[limb][:10].tolist()}
    assert max(len(v) for v in ages.values()) >= 3     # at least one limb has nodes of three different years
    # a limb's shoot is never longer than a year's limit allows
    longest = float(model.sp.shoot.max_shoot_length)
    for a, years in ages.items():
        for y in years:
            mask = (T.axis[: T.n] == a) & (T.birth[: T.n] == y)
            assert float(T.length[: T.n][mask].sum()) <= longest + 1e-9


def test_a_shaded_limb_falls_short():
    """The plan: less light at a limb's tip, a shorter shoot.  It's a limit met by light, not a length handed out."""
    model = grow(14, ON)
    T = model.tree
    tips = np.nonzero((T.term[: T.n] == 1) & (T.death[: T.n] < 0))[0]
    starts = tips
    full = np.full(len(starts), float(model.sp.shoot.internode_length))
    hd = {"water": 1.0}
    bright = model._frame_plan(starts, len(starts), full, hd, np.ones(len(starts)), 48)
    dark = model._frame_plan(starts, len(starts), full, hd, np.full(len(starts), 0.1), 48)
    assert (bright[0] == dark[0]).all()
    assert (dark[1] <= bright[1] + 1e-12).all() and (dark[1] < bright[1]).any()


def test_limbs_cost_carbon():
    """They're paid from the pool: a starved tree makes less limb, because it has less to pay with, whatever the frame allows."""
    fed = grow(16, ON + ["height_driver.reference_alpha=null"])
    starved = grow(16, ON + ["height_driver.reference_alpha=null", "resource.alpha=0.6"])

    def limb_metres(model):
        T = model.tree
        n = T.n
        alive = T.death[:n] < 0
        return float(T.length[:n][alive & np.isin(T.axis[:n], T.axis[limbs_of(model)])].sum())

    assert limb_metres(starved) < 0.5 * limb_metres(fed)


def test_steep_limb_does_not_climb_the_stem():
    """A limb's length has a limit whatever its direction: a steep one gains no reach, and can't run up beside the stem."""
    model = grow(25, ON + ["crown_frame.angle_mean_deg=25", "crown_frame.angle_sd_deg=0.1", "crown_frame.reach_scatter=0.01"])
    T = model.tree
    limb = limbs_of(model)
    alive = T.death[: T.n] < 0
    length = np.bincount(T.axis[: T.n][alive], weights=T.length[: T.n][alive])
    assert float(length[T.axis[limb]].max()) < 0.5 * float(model.stats[-1]["height_m"])


def test_a_full_crown_stops_making_leaves_and_its_surplus_is_paid_for():
    """In the open, leaf area stays near the frame's limit, and the stem's extra rings come out of carbon the crown couldn't use."""
    model = grow(22, ON, stand=False)
    cf = model.sp.crown_frame
    room = float(cf.crown_lai_max) * np.pi * model._frame_reach_max() ** 2
    # new shoots' leaves count from next spring, and a year's shoots can overshoot a little
    assert float(model.stats[-1]["leaf_area_m2"]) < 1.6 * room


def test_whether_a_tree_forks_is_drawn_once_per_tree():
    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, ON)
    env, _ = load_environment("sweden_open_field")
    drawn = []
    for seed in range(1, 41):
        model = GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)
        model._frame_buds()
        first = model._frame_forks
        model._frame_buds()
        assert model._frame_forks == first
        drawn.append(first)
    assert 0.15 < sum(drawn) / len(drawn) < 0.6      # about 0.349


def test_limbs_keep_their_distance_on_the_stem():
    model = grow(14, ON)
    T = model.tree
    z = np.sort(T.pos[T.parent[limbs_of(model)], 2])
    cf = model.sp.crown_frame
    gaps = np.diff(z)
    # the floor, less its scatter, along the stem; a little under for a leaning stem
    assert float(np.median(gaps)) >= 0.9 * float(cf.gap_min_m) * (1.0 - float(cf.gap_scatter))
