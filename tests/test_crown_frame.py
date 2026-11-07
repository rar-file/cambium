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


# -- crown_frame.earned: limbs and twigs go by what they earn -------------------------------------------------------------
EARNED = ON + ["crown_frame.earned=true", "mechanics.pendulous_radius=0.012", "mechanics.pendulous_radius_limb=0.0025", "crown_frame.reach_scatter=0.2", "crown_frame.limb_shoot_floor_m=0.15",
               "crown_frame.twig_shoot_max_m=0.5", "crown_frame.spacing_overlap=1.0", "bud_fate.long_shoot_threshold=5", "bud_fate.density_control.enabled=true", "bud_fate.density_control.after_growth=true"]


def test_earned_off_by_default():
    sp, _ = load_species("betula_pendula")
    assert sp.crown_frame.earned is False
    model = grow(6, ON)
    assert not model._frame_earns()


def test_earned_only_a_shoots_end_bud_starts_a_long_shoot():
    """Off the stem, a new axis leaves the last node its parent axis had when it started: no combs."""
    model = grow(20, EARNED, stand=False)
    T = model.tree
    n = T.n
    on = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    side = np.nonzero(T.is_lateral[:n] & ~on & ~on[np.maximum(T.parent[:n], 0)] & (T.death[:n] < 0))[0]
    assert side.size > 20
    fork_buds = set(model._frame_fork_of)
    checked = 0
    for f in side.tolist():
        if int(T.axis[f]) in fork_buds:
            continue
        p = int(T.parent[f])
        same = (T.axis[:n] == T.axis[p]) & (T.birth[:n] < T.birth[f])
        assert T.phyllo[p] == T.phyllo[:n][same].max()
        checked += 1
    assert checked > 10


def test_earned_no_limb_goes_past_the_published_crown():
    model = grow(22, EARNED, stand=False)
    T = model.tree
    alive = T.death[: T.n] < 0
    assert all(s <= 1.0 for s in model._frame_axis_reach.values())
    longest = 0.0
    for start in limbs_of(model).tolist():
        tip = T.pos[: T.n][alive & (T.axis[: T.n] == T.axis[start])][-1]
        longest = max(longest, float(np.hypot(*(tip[:2] - T.pos[T.parent[start], :2]))))
    assert longest <= 1.25 * model._frame_reach_max()     # the crown it was aiming at a few years ago was smaller, but a limb bends as it loads


def test_earned_limbs_fork_by_leaf_area_and_the_forks_are_limbs():
    model = grow(25, EARNED + ["crown_frame.fork_leaf_area_m2=0.4"], stand=False)
    T = model.tree
    assert len(model._frame_fork_of) > 3
    first = np.fromiter(model._frame_fork_of.values(), np.int64)
    # each is on the limb it's filed under, and stiff as that limb is, at its own set-point
    limbs = model._limb_nodes(T.n)
    for ax, limb in model._frame_fork_of.items():
        nodes = np.nonzero(T.axis[: T.n] == ax)[0]
        assert nodes.size and int(T.scaffold[nodes[0]]) == limb
        assert limbs[nodes].all()
        assert np.isfinite(model._frame_setpoints()[ax])
    # no forks at all if the limit is out of reach
    assert not grow(16, EARNED + ["crown_frame.fork_leaf_area_m2=1000"], stand=False)._frame_fork_of


def test_earned_a_limb_behind_its_neighbours_has_less_supply():
    model = grow(18, EARNED, stand=False)
    la, vig = model._frame_la, model._frame_vig
    limbs = np.nonzero(la > 0.0)[0]
    assert vig[limbs].max() <= 2.0
    k = int(model.sp.crown_frame.limb_rivals)
    by_z = limbs[np.argsort(model.tree.pos[model.tree.parent[limbs], 2])]
    for i in range(k, len(by_z) - k, 5):
        med = float(np.median(la[by_z[i - k: i + k + 1]]))
        assert (vig[by_z[i]] >= 1.0) == (la[by_z[i]] >= med)


def test_earned_a_full_crown_sheds_its_oldest_short_shoots():
    cap = ["crown_frame.crown_lai_max=2.0", "crown_frame.full_crown_spur_years=3"]
    model = grow(20, EARNED + cap, stand=False)
    T = model.tree
    assert model._frame_crown_full
    spurs = np.nonzero((T.lat[: T.n] == 2) & (T.death[: T.n] < 0))[0]     # LAT_SPUR
    assert spurs.size == 0 or (model.year - T.spur_birth[spurs]).max() <= 4


def test_earned_on_a_tree_that_forks_one_limb_goes_up_as_a_second_top():
    model = grow(40, EARNED, seed=8, stand=False)      # seed 8 draws a fork
    assert model._frame_forks and model.loss_of_dominance_year is not None
    tops = model._frame_tops()
    assert tops.size == 1
    T = model.tree
    nodes = np.nonzero((T.axis[: T.n] == tops[0]) & (T.death[: T.n] < 0))[0]
    assert np.degrees(model._frame_setpoints()[tops[0]]) == float(model.sp.resource.reiteration.setpoint_angle_deg)
    assert float(T.pos[nodes, 2].max()) > float(T.pos[T.parent[nodes[0]], 2]) + 1.0


def test_earned_a_browsed_stem_has_no_sharp_crook():
    """A replacement leader leaves the wound from a bud, nearly in line: seed 3 lost its leader at 1.4 m, and the old way left 44 degrees in the wood for good."""
    model = grow(12, [s for s in EARNED if not s.startswith("leader_damage")], seed=3)
    assert model.leader_losses
    T = model.tree
    stem = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
    d = np.diff(T.pos[stem], axis=0)
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    assert float(np.degrees(np.arccos(np.clip((d[1:] * d[:-1]).sum(1), -1.0, 1.0))).max()) < 20.0


def test_thick_limbs_sapwood_turns_over_more_slowly():
    sets = ON + ["pipe_model.branch_sapwood_senescence=0.3", "pipe_model.branch_sapwood_thick_m=0.01"]
    model = grow(16, sets, stand=False)
    T = model.tree
    n = T.n
    on = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    loss = model._sapwood_loss(n)
    thin = ~on & (T.radius[:n] <= 0.01) & (T.death[:n] < 0)
    thick = ~on & (T.radius[:n] > 0.01) & (T.death[:n] < 0)
    assert thin.any() and thick.any()
    assert np.allclose(loss[thin], 0.3) and (loss[thick] < 0.3).all()
    assert np.allclose(loss[on], float(model.sp.pipe_model.sapwood_senescence_per_year))


def test_open_grown_share_leaves_a_stand_tree_bit_identical():
    """It's for trees with no neighbours: a stand tree grown with it is the same tree, node for node."""
    off = grow(14, EARNED)
    on = grow(14, EARNED + ["height_driver.open_grown_share=0.8"])
    assert off.tree.n == on.tree.n
    assert (off.tree.pos[: off.tree.n] == on.tree.pos[: on.tree.n]).all()
    assert (off.tree.radius[: off.tree.n] == on.tree.radius[: on.tree.n]).all()
    # and an open tree comes out shorter, by about that share of the curve's height
    open_off = float(grow(20, EARNED, stand=False).stats[-1]["height_m"])
    open_on = float(grow(20, EARNED + ["height_driver.open_grown_share=0.8"], stand=False).stats[-1]["height_m"])
    assert 0.75 * open_off < open_on < 0.9 * open_off


def test_earned_surplus_goes_on_the_stem_only_with_no_neighbours():
    a = grow(18, EARNED + ["crown_frame.surplus_to_stem=0.0", "crown_frame.crown_lai_max=2.0"])
    b = grow(18, EARNED + ["crown_frame.surplus_to_stem=0.5", "crown_frame.crown_lai_max=2.0"])
    assert (a.tree.radius[: a.tree.n] == b.tree.radius[: b.tree.n]).all()
    c = grow(18, EARNED + ["crown_frame.surplus_to_stem=0.0", "crown_frame.crown_lai_max=2.0"], stand=False)
    d = grow(18, EARNED + ["crown_frame.surplus_to_stem=0.5", "crown_frame.crown_lai_max=2.0"], stand=False)
    assert float(d.stats[-1]["dbh_cm"]) > 1.05 * float(c.stats[-1]["dbh_cm"])


def test_earned_no_limb_tip_near_the_leader_and_new_limbs_still_start():
    model = grow(24, EARNED)
    T = model.tree
    alive = T.death[: T.n] < 0
    on = np.isin(T.axis[: T.n], np.fromiter(model.leader_axes, np.int64))
    H = float(T.pos[: T.n][alive & on, 2].max())
    assert float(T.pos[: T.n][alive & ~on, 2].max()) < H
    assert limbs_of(model).size > 20
    assert float(T.pos[T.parent[limbs_of(model)], 2].max()) > 0.85 * H


def test_open_lai_max_leaves_a_stand_tree_bit_identical():
    """A leaf limit only for a tree on its own: a stand tree grown with it is the same tree, and a lone tree carries less."""
    off = grow(14, EARNED)
    on = grow(14, EARNED + ["crown_frame.open_lai_max=2.0"])
    assert off.tree.n == on.tree.n
    assert (off.tree.pos[: off.tree.n] == on.tree.pos[: on.tree.n]).all()
    la_off = float(grow(20, EARNED, stand=False).stats[-1]["leaf_area_m2"])
    la_on = float(grow(20, EARNED + ["crown_frame.open_lai_max=2.0"], stand=False).stats[-1]["leaf_area_m2"])
    assert la_on < 0.9 * la_off


def test_earned_limb_sag_makes_a_limb_low_at_the_stem_and_rising_at_its_end():
    """A limb's posture target rises in young wood and falls with the wood's age, so a limb's old wood stands lower than its young wood, more so than without the sag."""
    def lean_of_old_and_young(model):
        T = model.tree
        n = T.n
        alive = T.death[:n] < 0
        out_old, out_young = [], []
        for first in limbs_of(model):
            nodes = np.nonzero((T.axis[:n] == T.axis[first]) & alive)[0]
            if nodes.size < 8:
                continue
            lean = np.degrees(np.arccos(np.clip(T.dir[nodes, 2], -1.0, 1.0)))
            out_old.append(lean[: nodes.size // 4].mean())
            out_young.append(lean[nodes.size // 2: 3 * nodes.size // 4].mean())
        return float(np.mean(out_old)), float(np.mean(out_young))

    straight_old, straight_young = lean_of_old_and_young(grow(30, EARNED))
    sag_old, sag_young = lean_of_old_and_young(grow(30, EARNED + ["crown_frame.limb_sag_deg=45"]))
    assert sag_old - sag_young > straight_old - straight_young


def test_earned_browsing_only_on_a_lone_tree_and_only_within_reach():
    """Axes with a thin shoot within a moose's reach go at the leader's yearly chance.  A stand tree grown with the switch is the same tree, and a lone tree's crown above the reach is not touched."""
    off = grow(14, EARNED)
    on = grow(14, EARNED + ["crown_frame.twigs_browsed=true"])
    assert off.tree.n == on.tree.n
    assert (off.tree.pos[: off.tree.n] == on.tree.pos[: on.tree.n]).all()
    model = grow(24, EARNED + ["crown_frame.twigs_browsed=true"], stand=False)
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    stem = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    gone = np.zeros(0, np.int64)
    for _ in range(12):
        gone = np.union1d(gone, model._browsed_twigs(model.year, alive, stem))
    assert gone.size > 0
    assert (T.is_lateral[gone] & (T.order[gone] >= 1) & ~stem[gone]).all()
    reach = T.radius[:n] <= 0.5 * float(model.sp.leader_damage.bite_diameter_m)
    ev = model.sp.leader_damage.events[0]
    reach &= (T.pos[:n, 2] >= float(ev.min_height_m)) & (T.pos[:n, 2] <= float(ev.max_height_m))
    for k in gone[:200]:
        assert reach[T.axis[:n] == T.axis[k]].any()


def test_earned_surplus_stops_at_the_most_stem_for_the_height():
    """A lone tree thickens on what its crown can't use only up to crown_frame.stem_cm_per_height_m."""
    free = grow(26, EARNED + ["crown_frame.surplus_to_stem=0.8", "crown_frame.stem_cm_per_height_m=9"], stand=False)
    capped = grow(26, EARNED + ["crown_frame.surplus_to_stem=0.8", "crown_frame.stem_cm_per_height_m=1.0"], stand=False)
    assert float(capped.stats[-1]["dbh_cm"]) < float(free.stats[-1]["dbh_cm"])
    assert capped._surplus_share() == 0.0
    assert grow(6, EARNED + ["crown_frame.surplus_to_stem=0.8"])._surplus_share() == 0.0
