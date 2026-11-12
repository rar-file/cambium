"""Leaves that are new each spring (appearance.leaves.each_year), on made-up twigs: no tree is grown."""
from __future__ import annotations

import copy
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from treegen import appearance as ap
from treegen.params import load_species

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

FIELDS = ("node", "base", "along", "across", "length", "width", "area", "sun", "delay")
R = 0.002


@pytest.fixture(scope="module")
def look():
    return ap.load_look(load_species("betula_pendula")[1])


def _look(look, each_year, on_shoots=0.0):
    lk = copy.deepcopy(look)
    lk["leaves"]["each_year"] = each_year
    lk["leaves"]["on_shoots"]["strength"] = on_shoots
    return lk


def _twigs(age: int, n: int = 3000, seed: int = 3) -> tuple:
    """n made-up nodes: four in five are short shoots born in years 1 to 40 with 2, 2.5 or 3 leaves, the rest are this
    year's long-shoot nodes with one leaf.  The same nodes at any age; only the new nodes' birth year goes with it."""
    rng = np.random.default_rng(seed)
    pos = rng.random((n, 3)) * 5.0
    lat_dir = rng.normal(size=(n, 3)) * np.array([1.0, 1.0, 0.3])
    lat_dir /= np.linalg.norm(lat_dir, axis=1, keepdims=True)
    spur = rng.random(n) < 0.8
    birth = np.where(spur, rng.integers(1, 41, n), age).astype(float)
    size = rng.choice([0.0, 0.0015, 0.0011], n)
    leaves = np.where(spur, rng.choice([2.0, 2.5, 3.0], n), 1.0) * np.where(size > 0, size, 0.0015) / 0.0015
    snap = ap.LeafSnapshot(age, leaves, size, np.full(n, 60.0), spur, 0.0015, lat_dir=lat_dir, birth=birth)
    return snap, pos


def _leaves(lk, age: int, **kw):
    snap, pos = _twigs(age, **kw)
    return ap.leaf_instances(lk, None, snap, pos, np.full(len(pos), R), age, 0.9), snap, pos


def _same(a, b) -> bool:
    return all(np.array_equal(getattr(a, f), getattr(b, f)) for f in FIELDS)


def _slope_deg(leaves) -> np.ndarray:
    """A blade's slope from base to tip, below the horizontal."""
    return np.degrees(np.arcsin(-leaves.along[:, 2]))


def _azimuth(leaves) -> np.ndarray:
    """The compass direction a blade points in, base to tip, in radians."""
    return np.arctan2(leaves.along[:, 1], leaves.along[:, 0])


def _roll(leaves) -> np.ndarray:
    """A blade's roll about its midrib, from square to the horizon, in radians."""
    az = _azimuth(leaves)
    level = np.stack([-np.sin(az), np.cos(az), np.zeros(len(az))], 1)
    return np.arctan2((leaves.across * np.cross(leaves.along, level)).sum(1), (leaves.across * level).sum(1))


def _own_days(leaves, snap, lv: dict) -> np.ndarray:
    """A leaf's own days to turn: its delay, less what its kind of shoot and the tree's age give every leaf alike."""
    late = np.where(snap.is_spur[leaves.node], 0.0, lv["long_shoot_delay_days"])
    return leaves.delay - late + lv["old_tree_advance_days"] * min(snap.age / 100.0, 1.0)


def _shoot_end(snap, pos: np.ndarray, node: np.ndarray, cfg: dict) -> np.ndarray:
    """Where a node's stalks start with leaves on their shoots: on the bark where the bud faces, and for a short shoot at the end
    of its own axis, which is a year longer every year."""
    years = np.where(snap.is_spur[node], np.maximum(snap.age - snap.birth[node], 0.0), 0.0)
    return pos[node] + snap.lat_dir[node] * (R + np.minimum(cfg["spur_m_per_year"] * years, cfg["spur_max_m"]))[:, None]


def test_the_setting_is_on_in_the_species_file_and_in_the_unreal_target(look):
    """On since 2026-11-12, the owner's choice (DECISIONS.md row 119): trees and game exports have new leaves each spring.
    (Until then this test held it off.)"""
    import treegen.game_unreal as gu

    assert float(look["leaves"]["each_year"]) == 1.0
    assert float(gu.unreal_look(look)["leaves"]["each_year"]) == 1.0


@pytest.mark.parametrize("on_shoots", [0.0, 1.0])
def test_by_default_the_leaves_are_new_each_spring(look, on_shoots):
    """The species file's look with nothing set: the leaves the setting gives when on, and a year on none hangs as it did."""
    lk = copy.deepcopy(look)
    lk["leaves"]["on_shoots"]["strength"] = on_shoots
    now, _, _ = _leaves(lk, 60)
    assert now.key is not None and _same(now, _leaves(_look(look, 1.0, on_shoots), 60)[0])
    last, _, _ = _leaves(lk, 59)
    assert np.array_equal(now.node, last.node)
    assert (np.abs(_slope_deg(now) - _slope_deg(last)) > 1e-6).all()
    assert not _same(now, _leaves(_look(look, 0.0, on_shoots), 60)[0])


@pytest.mark.parametrize("on_shoots", [0.0, 1.0])
def test_the_timelapse_look_gives_the_leaves_the_setting_gave_when_off(look, on_shoots):
    """A film of one frame a year keeps the old leaves: byte for byte the arrays the setting gives at 0, and those it gave before
    it was in the file at all; and the game target's own draws on top of them are the same too."""
    import treegen.game_unreal as gu

    lk = copy.deepcopy(look)
    lk["leaves"]["on_shoots"]["strength"] = on_shoots
    assert float(lk["leaves"]["each_year"]) > 0.0
    lapse = ap.timelapse_look(lk)
    assert lapse is lk and float(lapse["leaves"]["each_year"]) == 0.0 and float(look["leaves"]["each_year"]) == 1.0
    assert float(gu.unreal_look(lapse)["leaves"]["each_year"]) == 0.0     # the game target's look is made from it
    absent = _look(look, 0.0, on_shoots)
    del absent["leaves"]["each_year"]
    cfg = look["game"]["unreal"]["leaf"]
    by_age = {}
    for age in (59, 60):
        got, _, pos = _leaves(lapse, age)
        by_age[age] = got
        assert got.key is None
        z = np.clip(pos[got.node, 2] / 5.0, 0.0, 1.0)
        for other in (_leaves(_look(look, 0.0, on_shoots), age)[0], _leaves(absent, age)[0]):
            for f in FIELDS:
                x, y = getattr(got, f), getattr(other, f)
                assert x.dtype == y.dtype and x.shape == y.shape and x.tobytes() == y.tobytes(), f
            hung, hung_other = gu.hang_leaves(got, z, cfg), gu.hang_leaves(other, z, cfg)
            assert hung.along.tobytes() == hung_other.along.tobytes() and hung.across.tobytes() == hung_other.across.tobytes()
    # which is what a film wants: last year's leaves come back as they were
    for f in ("node", "along", "across", "area"):
        assert np.array_equal(getattr(by_age[59], f), getattr(by_age[60], f)), f


@pytest.mark.parametrize("on_shoots", [0.0, 1.0])
def test_off_or_absent_the_leaves_are_todays(look, on_shoots):
    off, snap, pos = _leaves(_look(look, 0.0, on_shoots), 60)
    absent = _look(look, 0.0, on_shoots)
    del absent["leaves"]["each_year"]
    assert _same(off, _leaves(absent, 60)[0]) and off.key is None
    # today's fault: the year has no say, so last year's leaves come back exactly
    last, _, _ = _leaves(_look(look, 0.0, on_shoots), 59)
    assert np.array_equal(off.along, last.along) and np.array_equal(off.across, last.across) and np.array_equal(off.area, last.area)
    # and today's rule, written out: every draw by the node and the leaf's number alone
    lv = look["leaves"]
    k = np.arange(len(off.node)) - np.searchsorted(off.node, off.node)
    key = off.node * 64 + k
    lo, hi = np.radians(lv["inclination_deg"])
    assert np.allclose(np.radians(_slope_deg(off)), lo + (hi - lo) * ap.hash01(key, 2), atol=1e-12)
    late = np.where(snap.is_spur[off.node], 0.0, lv["long_shoot_delay_days"]) - lv["old_tree_advance_days"] * 0.6
    assert np.allclose(off.delay, (ap.hash01(key, 4) - 0.5) * 2.0 * lv["turn_spread_days"] + late, atol=1e-12)
    az = np.arctan2(off.along[:, 1], off.along[:, 0])
    if on_shoots:
        d = snap.lat_dir[off.node]
        want = np.arctan2(d[:, 1], d[:, 0]) + k * np.radians(lv["on_shoots"]["divergence_deg"])
    else:
        want = 2.0 * np.pi * ap.hash01(key, 1)
    assert np.allclose(np.angle(np.exp(1j * (az - want))), 0.0, atol=1e-9)


@pytest.mark.parametrize("on_shoots", [0.0, 1.0])
def test_on_each_node_keeps_its_leaves_and_the_tree_its_leaf_area(look, on_shoots):
    off, _, _ = _leaves(_look(look, 0.0, on_shoots), 60)
    on, _, _ = _leaves(_look(look, 1.0, on_shoots), 60)
    assert np.array_equal(on.node, off.node)                    # the same count, node by node
    assert np.array_equal(on.sun, off.sun)
    assert abs(float(on.area.sum()) - float(off.area.sum())) < 1e-12
    if on_shoots:
        # each leaf's size share is this year's, inside the same limits and as spread as before
        assert not np.allclose(on.area, off.area)
        assert on.area.min() > 0.9 * off.area.min() and on.area.max() < 1.1 * off.area.max()
        assert on.area.std() / on.area.mean() == pytest.approx(off.area.std() / off.area.mean(), rel=0.05)
    else:
        assert np.array_equal(on.area, off.area)                # the model's own sizes, leaf by leaf


@pytest.mark.parametrize("on_shoots", [0.0, 1.0])
def test_the_same_tree_at_the_same_age_has_the_same_leaves(look, on_shoots):
    lk = _look(look, 1.0, on_shoots)
    a, _, _ = _leaves(lk, 60)
    b, _, _ = _leaves(lk, 60)
    assert _same(a, b) and np.array_equal(a.key, b.key)
    assert len(np.unique(a.key)) == len(a.key)


def test_a_year_on_a_short_shoots_leaves_are_new_where_the_wood_has_them(look):
    lk = _look(look, 1.0, 1.0)
    cfg = lk["leaves"]["on_shoots"]
    petiole = lk["leaves"]["petiole_m"]
    (a, snap_a, pos), (b, snap_b, _) = _leaves(lk, 59), _leaves(lk, 60)
    assert np.array_equal(a.node, b.node)
    spur = snap_a.is_spur[a.node]
    # none hangs the way last year's did, and none has last year's days to turn
    assert (np.abs(_slope_deg(a) - _slope_deg(b))[spur] > 1e-6).all()
    assert (np.linalg.norm(a.along[spur] - b.along[spur], axis=1) > 1e-3).mean() > 0.99
    assert (np.abs(_own_days(a, snap_a, lk["leaves"]) - _own_days(b, snap_b, lk["leaves"]))[spur] > 1e-6).mean() > 0.999
    # the cluster goes on round the shoot's spiral: this year's leaves follow last year's and the bud's three scale leaves
    per_node = np.bincount(a.node, minlength=len(pos))[a.node]
    turned = np.arctan2(b.along[:, 1], b.along[:, 0]) - np.arctan2(a.along[:, 1], a.along[:, 0])
    assert cfg["bud_scale_leaves"] == 3 and cfg["divergence_deg"] == 144.0
    want = np.radians(cfg["divergence_deg"]) * (per_node + cfg["bud_scale_leaves"])
    assert np.allclose(np.angle(np.exp(1j * (turned - want)))[spur], 0.0, atol=1e-6)
    # so on this 2/5 spiral three leaves a year turn 144 degrees, and two a year stand the same ways round as last year's
    three, two = spur & (per_node == 3), spur & (per_node == 2)
    assert three.any() and two.any() and (three | two)[spur].all()
    assert np.allclose(np.abs(np.angle(np.exp(1j * turned)))[three], np.radians(144.0), atol=1e-6)
    assert np.allclose(np.angle(np.exp(1j * turned))[two], 0.0, atol=1e-6)
    # the same place on the wood: every stalk starts at the end of the shoot's own axis, which is a year longer
    d = snap_a.lat_dir[a.node]
    tips = []
    for leaves, snap in ((a, snap_a), (b, snap_b)):
        years = np.where(spur, snap.age - snap.birth[leaves.node], 0.0)
        tip = pos[leaves.node] + d * (R + np.minimum(cfg["spur_m_per_year"] * years, cfg["spur_max_m"]))[:, None]
        assert np.allclose(np.linalg.norm(leaves.base - tip, axis=1), petiole, atol=1e-9)
        tips.append(tip)
    assert np.linalg.norm(tips[1] - tips[0], axis=1).max() <= cfg["spur_m_per_year"] + 1e-9
    # a new long-shoot node's lone leaf still leaves on the side its bud faces
    lone = ~spur
    assert ((b.base[lone] - pos[b.node[lone]]) * d[lone]).sum(1).min() > 0.0


def test_a_shoot_whose_number_of_leaves_changes_keeps_its_place_but_not_its_spiral(look):
    """The spiral counts every earlier year at this year's number of leaves.  That's right for a steady shoot, whose leaves follow
    on from last year's; a shoot that gains a leaf has its leaves where the wood has them, but starts somewhere else round its axis."""
    lk = _look(look, 1.0, 1.0)
    cfg = lk["leaves"]["on_shoots"]
    (snap_a, pos), (snap_b, _) = _twigs(59), _twigs(60)
    every = np.arange(len(pos))
    gains = snap_b.is_spur & (snap_b.leaves == 2.0) & (snap_b.size == 0.0) & (every % 2 == 0)
    assert gains.sum() > 50
    snap_b.leaves = np.where(gains, 3.0, snap_b.leaves)
    radius = np.full(len(pos), R)
    a, b = ap.leaf_instances(lk, None, snap_a, pos, radius, 59, 0.9), ap.leaf_instances(lk, None, snap_b, pos, radius, 60, 0.9)
    per_a, per_b = np.bincount(a.node, minlength=len(pos)), np.bincount(b.node, minlength=len(pos))
    assert (per_a[gains] == 2).all() and (per_b[gains] == 3).all() and np.array_equal(per_a[~gains], per_b[~gains])
    # where the wood has them: every stalk starts at the end of the shoot's own axis
    years = np.where(snap_b.is_spur[b.node], 60 - snap_b.birth[b.node], 0.0)
    tip = pos[b.node] + snap_b.lat_dir[b.node] * (R + np.minimum(cfg["spur_m_per_year"] * years, cfg["spur_max_m"]))[:, None]
    assert np.allclose(np.linalg.norm(b.base - tip, axis=1), lk["leaves"]["petiole_m"], atol=1e-9)
    # each short shoot's first leaf, a year on
    has = snap_a.is_spur & (per_a > 0) & (per_b > 0)
    first_a, first_b = np.searchsorted(a.node, every[has]), np.searchsorted(b.node, every[has])
    turned = np.arctan2(b.along[first_b, 1], b.along[first_b, 0]) - np.arctan2(a.along[first_a, 1], a.along[first_a, 0])
    step = np.radians(cfg["divergence_deg"])
    off_by = np.abs(np.angle(np.exp(1j * (turned - step * (per_a[has] + cfg["bud_scale_leaves"])))))
    steady = ~gains[has]
    assert np.allclose(off_by[steady], 0.0, atol=1e-6)          # follows on from last year's leaves and the bud's three
    counted = (per_b[has] + cfg["bud_scale_leaves"]) * (60 - snap_b.birth[has]) - (per_a[has] + cfg["bud_scale_leaves"]) * (59 - snap_a.birth[has])
    assert np.allclose(np.angle(np.exp(1j * (turned - step * counted))), 0.0, atol=1e-6)
    assert (off_by[~steady] > 0.1).mean() > 0.5                 # and most of the changed ones don't


def test_a_year_on_with_leaves_on_no_shoot_they_are_new_on_the_same_side_of_the_node(look):
    """The plain export.  The side of its node a leaf sits on is the wood's, so a blade's base stays where it was; how steeply
    the blade hangs, its roll and its days to turn are the leaf's, and new."""
    lk = _look(look, 1.0, 0.0)
    lv = lk["leaves"]
    (a, snap_a, pos), (b, snap_b, _) = _leaves(lk, 59), _leaves(lk, 60)
    off, _, _ = _leaves(_look(look, 0.0, 0.0), 60)
    assert np.array_equal(a.node, b.node)
    # a blade's base moves no further than a short shoot grows in a year.  Here not at all: this export gives a shoot no axis,
    # and these made-up twigs neither move nor thicken.  It's where the leaf has it with the setting off
    moved = np.linalg.norm(b.base - a.base, axis=1)
    assert moved.max() <= lv["on_shoots"]["spur_m_per_year"]
    assert moved.max() == 0.0 and np.array_equal(b.base, off.base)
    for leaves in (a, b):
        assert np.allclose(np.linalg.norm(leaves.base - pos[leaves.node], axis=1), R + lv["petiole_m"], atol=1e-9)
    # the side is drawn by the node and the leaf's number alone, in any year: the draw the setting must leave to the wood
    k = np.arange(len(a.node)) - np.searchsorted(a.node, a.node)
    side = 2.0 * np.pi * ap.hash01(a.node * 64 + k, 1)
    for leaves in (a, b, off):
        assert np.allclose(np.angle(np.exp(1j * (_azimuth(leaves) - side))), 0.0, atol=1e-9)
    # and each leaf hangs anew: none has last year's slope, roll or days to turn
    assert (np.abs(_slope_deg(a) - _slope_deg(b)) > 1e-6).all()
    assert (np.abs(_roll(a) - _roll(b)) > 1e-6).all()
    assert (np.abs(_own_days(a, snap_a, lv) - _own_days(b, snap_b, lv)) > 1e-6).all()
    assert (np.linalg.norm(a.along - b.along, axis=1) > 1e-6).all()
    # those three are drawn by the node, the leaf's number and the year
    lo, hi = np.radians(lv["inclination_deg"])
    for leaves, snap in ((a, snap_a), (b, snap_b)):
        key = leaves.node * 64 + k + snap.age * 2 ** 40
        assert np.allclose(np.radians(_slope_deg(leaves)), lo + (hi - lo) * ap.hash01(key, 2), atol=1e-9)
        assert np.allclose(_roll(leaves), (ap.hash01(key, 3) - 0.5) * 0.9, atol=1e-9)
        assert np.allclose(_own_days(leaves, snap, lv), (ap.hash01(key, 4) - 0.5) * 2.0 * lv["turn_spread_days"], atol=1e-9)


@pytest.mark.parametrize("ages, still_growing", [((12, 13), True), ((59, 60), False)])
def test_a_year_on_in_the_unreal_target_a_blades_base_is_within_reach_of_where_the_wood_has_it(look, ages, still_growing):
    """The game target, as its export makes its leaves: placed on their shoots, then hung.  Its own bound: the end of the shoot's
    axis, where the stalks start, moves a year's growth at most, and a blade's base is one stalk's length from it.  So a base moves
    at most that growth and two stalks' lengths, as the cluster turns; where the cluster stands the same ways round (two leaves a
    year, or a lone leaf, whose stalk goes straight out), the year's growth alone.  At 12 the short shoots' axes are still
    lengthening; by 59 each is as long as it gets."""
    import treegen.game_unreal as gu

    lk = gu.unreal_look(look)
    lk["leaves"]["each_year"] = 1.0
    lv, cfg = lk["leaves"], lk["leaves"]["on_shoots"]
    assert cfg["strength"] > 0.0
    grow, petiole = cfg["spur_m_per_year"], lv["petiole_m"]
    hung = []
    for age in ages:
        snap, pos = _twigs(age)
        leaves = ap.leaf_instances(lk, None, snap, pos, np.full(len(pos), R), age, 0.9)
        hung.append((gu.hang_leaves(leaves, np.clip(pos[leaves.node, 2] / 5.0, 0.0, 1.0), lk["game"]["unreal"]["leaf"]), snap))
    (a, snap_a), (b, snap_b) = hung
    assert np.array_equal(a.node, b.node)
    # where the stalks start: the wood's, a year's growth further out at most
    ends = [_shoot_end(snap, pos, leaves.node, cfg) for leaves, snap in hung]
    for (leaves, _), end in zip(hung, ends):
        assert np.allclose(np.linalg.norm(leaves.base - end, axis=1), petiole, atol=1e-9)
    end_moved = np.linalg.norm(ends[1] - ends[0], axis=1)
    assert end_moved.max() <= grow + 1e-9 and (end_moved.max() > 0.99 * grow) == still_growing
    # the blade's base
    moved = np.linalg.norm(b.base - a.base, axis=1)
    assert moved.max() <= grow + 2.0 * petiole + 1e-9
    per_node = np.bincount(a.node, minlength=len(pos))[a.node]
    assert set(np.unique(per_node)) <= {1, 2, 3}
    # a short shoot with three leaves a year turns 144 degrees, once it has a year behind it
    turns = snap_b.is_spur[b.node] & (snap_b.birth[b.node] < snap_b.age) & (per_node == 3)
    assert turns.any() and (~turns).any()
    assert moved[~turns].max() <= grow + 1e-9
    assert np.median(moved[turns]) > 3.0 * grow
    # and each leaf hangs anew: its slope, its roll and its days to turn are this year's
    assert (np.abs(_slope_deg(a) - _slope_deg(b)) > 1e-6).mean() > 0.999
    assert (np.abs(_roll(a) - _roll(b)) > 1e-6).mean() > 0.999
    assert (np.abs(_own_days(a, snap_a, lv) - _own_days(b, snap_b, lv)) > 1e-6).mean() > 0.999


def test_the_leaves_hang_as_steeply_as_before(look):
    """Over many leaves, the slopes and the tilt of the blades' planes are spread as with the setting off."""
    q = (5, 25, 50, 75, 95)
    lo, hi = look["leaves"]["inclination_deg"]
    for on_shoots in (0.0, 1.0):
        off, _, _ = _leaves(_look(look, 0.0, on_shoots), 60, n=20000)
        on, _, _ = _leaves(_look(look, 1.0, on_shoots), 60, n=20000)
        tilt = lambda v: np.degrees(np.arccos(np.abs(np.cross(v.along, v.across)[:, 2])))  # noqa: E731
        for angle in (_slope_deg, tilt):
            assert np.allclose(np.percentile(angle(on), q), np.percentile(angle(off), q), atol=0.7)
            assert abs(angle(on).mean() - angle(off).mean()) < 0.3
        assert _slope_deg(on).min() >= lo - 1e-9 and _slope_deg(on).max() <= hi + 1e-9


def test_the_unreal_targets_own_draws_go_by_the_year_too(look):
    import treegen.game_unreal as gu

    cfg = look["game"]["unreal"]["leaf"]
    hung = {}
    for name, each_year in (("off", 0.0), ("on", 1.0)):
        for age in (59, 60):
            leaves, _, pos = _leaves(_look(look, each_year, 1.0), age, n=20000)
            hung[name, age] = gu.hang_leaves(leaves, np.clip(pos[leaves.node, 2] / 5.0, 0.0, 1.0), cfg)
    # off: by a leaf's place in the list, as it was; here the list is the same at both ages, so the leaves are too
    assert np.array_equal(hung["off", 59].along, hung["off", 60].along)
    assert (np.abs(_slope_deg(hung["on", 59]) - _slope_deg(hung["on", 60])) > 1e-6).mean() > 0.999
    q = (5, 25, 50, 75, 95)
    assert np.allclose(np.percentile(_slope_deg(hung["on", 60]), q), np.percentile(_slope_deg(hung["off", 60]), q), atol=0.7)


def test_the_picture_tool_reads_a_blades_slope_and_tilt_from_a_files_own_points():
    """tools/leaves_each_year.py measures the game target's leaves in the files it wrote: made-up blades, flat and curled."""
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import leaves_each_year as ley

    rng = np.random.default_rng(1)
    n = 400
    az, inc = rng.random(n) * 2.0 * np.pi, np.radians(20.0 + 40.0 * rng.random(n))
    outward = np.stack([np.cos(az), np.sin(az), np.zeros(n)], 1)
    along = outward * np.cos(inc)[:, None] - np.array([0.0, 0.0, 1.0]) * np.sin(inc)[:, None]
    across = np.stack([-np.sin(az), np.cos(az), np.zeros(n)], 1)
    normal = np.cross(along, across)
    base = rng.random((n, 3)) * 20.0
    t = np.linspace(0.0, 1.0, 6)
    for curl in (np.zeros(n), 0.05 + 0.23 * rng.random(n)):
        # six points down the midrib, four out on each side, then the stalk's six, as the game's mesh has them
        mid = base[:, None] + 0.05 * (t[None, :, None] * along[:, None] - (curl[:, None] * t ** 2)[..., None] * normal[:, None])
        sides = [mid[:, 1:5] + side * 0.015 * across[:, None] for side in (1.0, -1.0)]
        stalk = base[:, None] + rng.random((n, 6, 3)) * 0.02
        slope, tilt = ley.file_angles(SimpleNamespace(V=np.concatenate([mid] + sides + [stalk], 1).reshape(-1, 3).astype(np.float32)), n, 5, 6)
        # the midrib's ends: its slope is the blade's start and the droop its curl adds
        assert np.allclose(slope, np.degrees(inc + np.arctan(curl)), atol=0.05)
        # the plane the blade lies nearest to: the blade's own when it's flat, about the midrib's when it curls
        assert np.allclose(tilt, np.degrees(inc + np.arctan(curl)), atol=0.05 if not curl.any() else 1.5)
    # the frame a placed leaf has, as the papers' angle: rolled about its midrib, a blade's plane is steeper than its midrib
    rolled = SimpleNamespace(along=along, across=across * np.cos(0.4) + normal * np.sin(0.4))
    assert np.allclose(ley.plane_tilt(SimpleNamespace(along=along, across=across)), np.degrees(inc), atol=1e-9)
    assert np.allclose(np.cos(np.radians(ley.plane_tilt(rolled))), np.cos(inc) * np.cos(0.4), atol=1e-12)


# -- the time-lapse option of the exports, and the tool that tells leaves from wood ---------------------------------------
def test_each_export_command_has_the_one_option_and_says_why(monkeypatch, capsys):
    import game_export
    from cambium.cli import parser

    monkeypatch.setattr(sys, "argv", ["game_export.py", "export", "--help"])
    with pytest.raises(SystemExit):
        game_export.main()
    with pytest.raises(SystemExit):
        parser().parse_args(["export", "--help"])
    helps = capsys.readouterr().out
    assert helps.count("--timelapse") >= 2 and " ".join(helps.split()).count("new leaves in every frame read as shimmer") == 2
    # off unless asked for
    assert parser().parse_args(["export", "--out", "x"]).timelapse is False
    assert parser().parse_args(["export", "--out", "x", "--timelapse"]).timelapse is True


def test_the_timelapse_option_and_a_look_value_for_the_same_thing_are_refused_before_anything_is_written(tmp_path):
    from types import SimpleNamespace

    from cambium._tree import Tree

    grown = SimpleNamespace(stats=[{"year": 0, "height_m": 0.1}], lean=False, year=3)      # no tree: the check comes first
    tree = Tree(grown, None, species_file=Path("betula_pendula.yaml"), environment_file=Path("sweden_open_field.yaml"), seed=1, stand=True, settings=[])
    with pytest.raises(ValueError, match="timelapse sets leaves.each_year itself"):
        tree.export(tmp_path / "x", timelapse=True, look={"leaves.each_year": 1.0})
    assert not (tmp_path / "x").exists()


def _made_up_export(folder: Path, leaf_tip: float = 0.05, stem_top: float = 2.0, bark_grey: int = 200, leaf_grey: int = 90, leaves: int = 1, roots: bool = True) -> Path:
    """A folder laid out as an export, by hand: one .glb with a stem and its bark map, leaves and theirs; a second file; a manifest."""
    from PIL import Image

    from treegen.export import GameGLB

    def png(grey):
        buf = io.BytesIO()
        Image.fromarray(np.full((4, 4, 3), grey, np.uint8)).save(buf, "PNG")
        return buf.getvalue(), "image/png"

    folder.mkdir(parents=True)
    glb = GameGLB(folder / "tree_age008_summer_lod0.glb", "tree", {"seed": 1, "run_manifest": {"written_to": str(folder)}})
    bark = glb.add_material({"name": "bark_stem", "pbrMetallicRoughness": {"baseColorTexture": {"index": glb.add_texture(*png(bark_grey), name="bark_stem_base")}}})
    blade = glb.add_material({"name": "leaf_blade", "pbrMetallicRoughness": {"baseColorTexture": {"index": glb.add_texture(*png(leaf_grey), name="leaf_blade_base")}}})
    up = np.array([[0.0, 0.0, 1.0]] * 3)
    glb.add_mesh("stem", bark, np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [0.0, 0.0, stem_top]]), up, np.array([[0, 1, 2]]), attributes={"NODE_ID": np.arange(3.0)})
    glb.add_mesh("leaves", blade, np.array([[0.0, 0.0, 1.0], [leaf_tip, 0.0, 1.0], [0.0, 0.05, 1.0]]), up, np.array([[0, 1, 2]]))
    info = glb.write()
    if roots:
        (folder / "roots.bin").write_bytes(b"roots")
    level = {"triangles": info["triangles"], "file_mb": 0.01 + leaf_tip, "parts": {"wood": 1, "leaves": 1}}
    manifest = {"run_manifest": {"written_to": str(folder)}, "stages": [{"age": 8, "height_m": stem_top, "exported_leaves": leaves, "exported_leaf_area_m2": 0.001,
                                                                         "model_leaf_area_m2": 0.001, "seasons": {"summer": {"lod0": level}}}]}
    (folder / "game_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


def test_the_comparison_tells_leaves_from_wood(tmp_path):
    """tools/leaves_only.py, which the proof of the new default rests on: on made-up exports, each with one thing changed."""
    import leaves_only as lo

    a = _made_up_export(tmp_path / "a")
    file = "tree_age008_summer_lod0.glb"
    # run metadata differs between the two (each names its folder) and isn't a difference
    same = lo.compare(a, _made_up_export(tmp_path / "same"))
    assert same["identical"] and same["leaves_only"] and same["parts_compared"] == 8 and not same["values_that_differ"]
    # a leaf that hangs differently, and a leaf map a shade off: leaves only.  The file's megabytes are a whole file's number
    moved = lo.compare(a, _made_up_export(tmp_path / "leaf", leaf_tip=0.06, leaf_grey=91))
    assert moved["leaves_only"] and not moved["identical"]
    assert [r["part"] for r in moved["differ"]] == [f"{file}: map leaf_blade_base", f"{file}: mesh leaves"] and all(r["leaf"] for r in moved["differ"])
    assert [(v["path"], v["whose"]) for v in moved["values_that_differ"]] == [("stages.0.seasons.summer.lod0.file_mb", "whole file")]
    # wood that moved, in the mesh and in the manifest
    wood = lo.compare(a, _made_up_export(tmp_path / "wood", stem_top=2.5))
    assert not wood["leaves_only"] and wood["not_the_leaves"] == [f"{file}: mesh stem", "game_manifest.json: stages.0.height_m"]
    # a bark map one grey level off
    bark = lo.compare(a, _made_up_export(tmp_path / "bark", bark_grey=201))
    assert not bark["leaves_only"] and bark["not_the_leaves"] == [f"{file}: map bark_stem_base"]
    # one leaf more or fewer is not "leaves only": the count is the model's
    count = lo.compare(a, _made_up_export(tmp_path / "count", leaves=2))
    assert not count["leaves_only"] and "game_manifest.json: stages.0.exported_leaves" in count["not_the_leaves"]
    # a file that is missing
    gone = lo.compare(a, _made_up_export(tmp_path / "gone", roots=False))
    assert not gone["leaves_only"] and gone["not_the_leaves"] == ["roots.bin: bytes"]
    # nothing to compare proves nothing
    (tmp_path / "empty").mkdir()
    assert not lo.compare(tmp_path / "empty", tmp_path / "empty")["leaves_only"]


# small maps and budgets, so a whole export takes seconds (as tests/test_game_export.py)
SMALL = {"bark.tile_px": 256, "bark.stem_texture_px": [128, 512], "bark.atlas_px": [512, 256], "game.leaf_card.texture_px": 256,
         "game.lods": [{"name": "lod0", "kind": "full", "budget": None, "stem_texture_scale": 1.0, "atlas_scale": 1.0, "leaf_kind": "blades", "peel_strips": 1},
                       {"name": "lod1", "kind": "reduced", "budget": 4000, "wood_share": 0.4, "stem_texture_scale": 0.5, "atlas_scale": 0.5, "leaf_kind": "cards", "peel_strips": 0},
                       {"name": "lod2", "kind": "far", "budget": 12, "cards": 3, "texture_px": 128}]}


@pytest.fixture(scope="module")
def small_exports(tmp_path_factory):
    """One small stand tree, grown once to eight years, through tools/game_export.py in summer and winter, for the plain target and
    the game's: as it is by default, with the time-lapse option, and with the setting turned off by --look."""
    from argparse import Namespace

    import game_export as ge

    root = tmp_path_factory.mktemp("each_year")
    small = [f"{key}={json.dumps(value)}" for key, value in SMALL.items()]
    out = {}
    for target in ("generic", "unreal"):
        for how, timelapse, more in (("default", False, []), ("timelapse", True, []), ("off", False, ["leaves.each_year=0"])):
            out[target, how] = root / f"{target}_{how}"
            ge.main_export(Namespace(ages="8", seasons="summer,winter", out=str(out[target, how]), state=str(root / "tree.pkl"), species="betula_pendula", seed=1,
                                     environment="sweden_open_field", stand=True, set=[], budget=[], look=small + more, levels="", target=target, timelapse=timelapse))
    return out


@pytest.mark.parametrize("target", ["generic", "unreal"])
def test_the_timelapse_option_writes_the_export_the_setting_gave_when_off(small_exports, target):
    """File by file as tools/golden.py hashes them, and part by part with every map's pixels."""
    import golden
    import leaves_only as lo

    lapse, off = small_exports[target, "timelapse"], small_exports[target, "off"]
    files = golden.hash_tree(lapse)
    assert len(files) >= 4 and files == golden.hash_tree(off)
    assert lo.compare(off, lapse)["identical"]


@pytest.mark.parametrize("target", ["generic", "unreal"])
def test_by_default_an_export_differs_from_a_timelapse_one_in_its_leaves_alone(small_exports, target):
    import leaves_only as lo

    c = lo.compare(small_exports[target, "timelapse"], small_exports[target, "default"])
    assert c["leaves_only"] and not c["identical"] and not c["in_one_only"] and not c["not_the_leaves"]
    differ = [row["part"] for row in c["differ"]]
    # the summer leaves are new: as many blades, with as many points and triangles
    blades = [row for row in c["differ"] if row["part"].endswith(": mesh leaves")]
    assert blades and all(row["vertices"][0] == row["vertices"][1] and row["triangles"][0] == row["triangles"][1] for row in blades)
    assert all(row["leaf"] for row in c["differ"])
    # winter has no leaves, so nothing of a winter file differs, its far level's picture of the bare tree neither
    assert not any("winter" in part for part in differ) and not any(".winter." in v["path"] for v in c["values_that_differ"])
    # the wood is there to be compared, and none of it is among what differs
    wood = [part for part in c_same(c, small_exports[target, "default"]) if part.split(": ")[-1] in ("mesh stem", "mesh branches")]
    assert len(wood) >= 4 and not set(wood) & set(differ)
    # the model's leaves: the same count and area, and each level's wood the same triangles
    counted = [n for n in c["numbers_old_new"] if "exported_leaves" in n]
    assert counted and all(n[key][0] == n[key][1] for n in counted for key in ("exported_leaves", "exported_leaf_area_m2", "model_leaf_area_m2"))
    assert all(n["exported_leaves"][0] > 0 and n["exported_leaf_area_m2"][0] == pytest.approx(n["model_leaf_area_m2"][0], rel=0.03) for n in counted)
    levels = [n for n in c["numbers_old_new"] if "wood_triangles" in n]
    assert len(levels) >= 4 and all(n["wood_triangles"][0] == n["wood_triangles"][1] and n["triangles_not_leaves"][0] == n["triangles_not_leaves"][1] for n in levels)


def c_same(c: dict, folder: Path) -> list:
    """The parts of an export that a comparison found the same: all its parts less those that differ."""
    import leaves_only as lo

    return sorted(set(lo.parts(folder)[0]) - {row["part"] for row in c["differ"]})


def test_cambiums_export_takes_the_option_too(tmp_path):
    """Tree.export(timelapse=True), which `cambium export --timelapse` calls: the export the setting gave when off, and the
    default differs from it in its leaves alone."""
    import cambium
    import golden
    import leaves_only as lo

    tree = cambium.grow(seed=1, years=6, stand=True)
    default = tree.export(tmp_path / "default", lod="lod0", look=SMALL)
    lapse = tree.export(tmp_path / "lapse", lod="lod0", look=SMALL, timelapse=True)
    tree.export(tmp_path / "off", lod="lod0", look={**SMALL, "leaves.each_year": 0.0})
    assert [p.name for p in default] == [p.name for p in lapse]
    assert golden.hash_tree(tmp_path / "lapse") == golden.hash_tree(tmp_path / "off")
    c = lo.compare(tmp_path / "lapse", tmp_path / "default")
    assert c["leaves_only"] and not c["identical"] and [row["part"].split(": ")[-1] for row in c["differ"]] == ["mesh leaves"]
