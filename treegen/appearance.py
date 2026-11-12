"""How each part of a tree looks at a given age, from the ``appearance`` block of the species file.

This module only reads a finished tree: nothing here feeds back into growth.  Nothing is
birch-specific either.  A species is a list of bark stages with ramps on a part's own age and size,
a bark thickness rule, a leaf colour ramp and a season, all data.

    part_state(...)      bark stage weights, thickness, peeling, along any part
    leaf_instances(...)  one blade per model leaf, at the model's own count and size
    peel_strips(...)     the free strips of bark standing off stems and limbs
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def load_look(species_raw: dict) -> dict:
    """The ``appearance`` block of a species file (the dict from ``params.load_species``)."""
    look = species_raw.get("appearance")
    if look is None:
        raise KeyError("this species file has no appearance block")
    return look


def timelapse_look(look: dict) -> dict:
    """The look for a time-lapse, a film of one frame a year: ``leaves.each_year`` off, the leaves every export
    had before that setting.  New leaves each spring are the default and true to the tree, but new leaves in
    every frame read as shimmer.  Off, a leaf placed here hangs as it did the year before; the game target's
    own draws then go by a leaf's place in the tree's list, so there its droop still shifts a little.
    Changes ``look`` and returns it."""
    look["leaves"]["each_year"] = 0.0
    return look


def srgb_to_linear(c) -> np.ndarray:
    """sRGB 0-255 to linear 0-1."""
    a = np.asarray(c, float) / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(a) -> np.ndarray:
    """Linear 0-1 to sRGB 0-1."""
    a = np.clip(np.asarray(a, float), 0.0, 1.0)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * a ** (1.0 / 2.4) - 0.055)


def smooth(lo, hi, x):
    """C1 ramp from 0 at lo to 1 at hi."""
    t = np.clip((np.asarray(x, float) - lo) / np.maximum(np.asarray(hi, float) - lo, 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def hash01(ids, salt: int = 0) -> np.ndarray:
    """A number in [0, 1) for each integer id, the same on every run and machine (SplitMix64), so a
    leaf or a bark strip keeps its place from one age to the next."""
    z = (np.asarray(ids, np.uint64) + np.uint64((salt * 0x9E3779B97F4A7C15 + 0x9E3779B97F4A7C15) % 2**64))
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    z = z ^ (z >> np.uint64(31))
    return (z >> np.uint64(11)).astype(np.float64) / float(2**53)


# -- bark ---------------------------------------------------------------------------------------
def over_bark_dbh_cm(look: dict, dbh_wood_cm: float | None) -> float:
    """DBH over bark from the model's DBH, which is wood.  0 for a tree under breast height."""
    if not dbh_wood_cm:
        return 0.0
    th = look["bark"]["thickness"]
    b0, b1, b2 = th["hansen_double_mm"]
    c = float(th["calibration"])
    # at breast height d = DBH: wood = DBH - c (b0 + (b1 + b2) DBH) / 10
    dbh = (float(dbh_wood_cm) + c * b0 / 10.0) / (1.0 - c * (b1 + b2) / 10.0)
    return float(max(dbh, float(dbh_wood_cm) / (1.0 - 2.0 * float(th["min_fraction_of_diameter"]))))


def bark_wall_m(look: dict, d_wood_m, dbh_ob_cm: float, rough=0.0) -> np.ndarray:
    """Bark thickness (one wall, m) over wood of diameter d_wood_m: Hansen's birch equation scaled to
    Vihera-Aarnio's silver birch, thicker by ``rough_ratio`` where the rough stage has taken over."""
    th = look["bark"]["thickness"]
    b0, b1, b2 = th["hansen_double_mm"]
    c = float(th["calibration"])
    rel = float(th["min_fraction_of_diameter"])
    d_ub = np.asarray(d_wood_m, float) * 100.0
    # d_ob = d_ub + c (b0 + b1 DBH + b2 d_ob) / 10, linear in d_ob
    d_ob = (d_ub + c * (b0 + b1 * dbh_ob_cm) / 10.0) / (1.0 - c * b2 / 10.0)
    wall_cm = np.maximum(0.5 * (d_ob - d_ub), rel * d_ub / (1.0 - 2.0 * rel))
    return wall_cm / 100.0 * (1.0 + (float(th["rough_ratio"]) - 1.0) * np.asarray(rough, float))


def _ramp(spec, name, x):
    pair = spec.get(name)
    return 1.0 if pair is None else smooth(pair[0], pair[1], x)


def stem_stub_share(look: dict) -> float:
    """What the mesher should take as the lost leader's last thread: nothing, unless the bark's look is on."""
    edge = look["bark"].get("uneven_top")
    return float(edge["stem_stub_share"]) if edge and float(edge["strength"]) > 0.0 else 0.0


def limb_level_step(look: dict) -> float:
    """How finely a limb's bark follows its own share of white, or 0: one atlas column to a circumference."""
    edge = look["bark"].get("uneven_top")
    return float(edge["limbs"]["level_step"]) if edge and float(edge["strength"]) > 0.0 else 0.0


def climb_top(climb: dict, part_age) -> np.ndarray:
    """How high a stage that climbs has reached on a part this old, in metres."""
    return float(climb["height_max_m"]) * (1.0 - np.exp(-np.maximum(np.asarray(part_age, float) - float(climb["onset_age"]), 0.0) / float(climb["time_constant_years"])))


def part_state(look: dict, part_age, d_wood_m, height_m, tree_height_m: float, dbh_ob_cm: float) -> dict:
    """The look of parts with these ages, wood diameters and heights.

    Returns arrays: ``weights`` (stages x parts; stage 0 is always 1, each later stage covers those
    before it), ``peel`` (share of the surface lifted), ``grime``, ``wall_m`` (bark thickness),
    ``fissure_m`` (depth of the deepest cracks), and ``diameter_m`` (over bark)."""
    bark = look["bark"]
    part_age = np.asarray(part_age, float)
    d_wood = np.asarray(d_wood_m, float)
    z = np.asarray(height_m, float)
    d0 = d_wood + 2.0 * bark_wall_m(look, d_wood, dbh_ob_cm)
    stages = bark["stages"]
    ramps = bark.get("stage_ramps", {})
    look2 = bark.get("uneven_top")
    if look2 and float(look2["strength"]) > 0.0 and look2.get("stage_ramps"):
        # the same setting: how thick a limb has to be before it's white
        ramps = {name: {**spec, **look2["stage_ramps"].get(name, {})} for name, spec in ramps.items()}
    weights = [np.ones_like(d0)]
    rough = np.zeros_like(d0)
    for st in stages[1:]:
        spec = ramps.get(st["name"], {})
        w = _ramp(spec, "part_age_years", part_age) * _ramp(spec, "diameter_m", d0) * np.ones_like(d0)
        climb = spec.get("climbs")
        if climb is not None:
            top = climb_top(climb, part_age)
            band = float(climb["band_m"])
            w = w * (1.0 - smooth(top - band, top + band, z)) * np.clip(top / band, 0.0, 1.0)
            rough = w
        weights.append(w)
    weights = np.stack(weights)
    wall = bark_wall_m(look, d_wood, dbh_ob_cm, rough)
    peel = np.zeros_like(d0)
    peel_cfg = bark.get("peel")
    if peel_cfg:                 # a species whose bark doesn't peel just has no peel block
        names = [st["name"] for st in stages]
        k = names.index(peel_cfg["on_stage"])
        shown = weights[k] * np.prod(1.0 - weights[k + 1:], axis=0) if k + 1 < len(names) else weights[k]
        peel = float(peel_cfg["coverage_max"]) * _ramp(peel_cfg, "part_age_years", part_age) * _ramp(peel_cfg, "diameter_m", d0) * shown
    marks = bark.get("marks") or {}
    low = 1.0 - 0.6 * np.clip(z / max(0.5 * tree_height_m, 1.0), 0.0, 1.0)
    grime = float(marks.get("grime_strength", 0.0)) * np.clip(part_age / float(marks.get("grime_age_years", 1.0)), 0.0, 1.0) * low
    return {
        "weights": weights,
        "peel": peel,
        "grime": grime,
        "wall_m": wall,
        # cracks are deep as soon as they open
        "fissure_m": float(bark["thickness"]["fissure_depth_fraction"]) * wall * np.sqrt(rough),
        "diameter_m": d_wood + 2.0 * wall,
    }


def add_bark_radius(look: dict, rad_wood: np.ndarray, part_age: np.ndarray, z: np.ndarray, is_root: np.ndarray,
                    tree_height_m: float, dbh_wood_cm: float | None) -> np.ndarray:
    """Radii over bark for meshing: the model's radii are wood.  Roots are left alone."""
    dbh_ob = over_bark_dbh_cm(look, dbh_wood_cm)
    st = part_state(look, part_age, 2.0 * rad_wood, z, tree_height_m, dbh_ob)
    return np.where(is_root, rad_wood, rad_wood + st["wall_m"])


# -- stem and branch colour ---------------------------------------------------------------------
def state_colour(stage_means: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Mean surface colour of parts: each stage laid over the last by its weight.
    stage_means (stages x 3); weights (stages x parts); returns (parts x 3)."""
    c = np.broadcast_to(stage_means[0], weights.shape[1:] + (3,)).copy()
    for i in range(1, len(stage_means)):
        c = c + (stage_means[i] - c) * weights[i][..., None]
    return c


# -- leaves -------------------------------------------------------------------------------------
@dataclass
class LeafSnapshot:
    """What the model's leaves are in one year, read from the tree at the end of that year."""
    age: int
    leaves: np.ndarray       # reference-leaf units per node, as stats["leaves"] sums them
    size: np.ndarray         # m2 a leaf, 0 for the species' reference size
    lma: np.ndarray          # g m-2
    is_spur: np.ndarray      # a short shoot, not a long-shoot node
    reference_area: float    # m2
    lat_dir: np.ndarray | None = None   # which way each node's bud and leaf face, as the wood has carried them
    birth: np.ndarray | None = None     # the year each node was made


def leaf_snapshot(model, age: int | None = None) -> LeafSnapshot:
    """Read the leaves of the tree as it stands now (call between years; it changes nothing)."""
    from .growth import LAT_SPUR
    T = model.tree
    n = T.n
    return LeafSnapshot(age=int(model.year if age is None else age), leaves=np.asarray(T.leaves[:n], np.float64).copy(),
                        size=np.asarray(T.leaf_size[:n], np.float64).copy(), lma=np.asarray(T.lma[:n], np.float64).copy(),
                        is_spur=np.asarray(T.lat[:n] == LAT_SPUR).copy(), reference_area=float(model.light.leaf_area),
                        lat_dir=np.asarray(T.lat_dir[:n], np.float64).copy(), birth=np.asarray(T.birth[:n], np.float64).copy())


def chlorophyll_at(look: dict, day: float, sun: np.ndarray, delay: np.ndarray) -> np.ndarray:
    """Chlorophyll fraction of leaves on a day of the year; ``delay`` days move a leaf later in
    autumn, and ``sun`` (0 shade, 1 full sun) makes it paler."""
    lv = look["leaves"]
    table = np.asarray(lv["season"]["chlorophyll_by_day"], float)
    last_full = table[np.nonzero(table[:, 1] == table[:, 1].max())[0][-1], 0]
    d = float(day) - np.asarray(delay, float) if float(day) > last_full else np.full(np.shape(delay), float(day))
    f = np.interp(d, table[:, 0], table[:, 1])
    return f * (1.0 + (float(lv["light_effect"]["sun_chlorophyll_factor"]) - 1.0) * sun)


def leaf_colours(look: dict, chlorophyll: np.ndarray) -> tuple:
    """(diffuse reflectance, transmittance), both linear RGB, by chlorophyll fraction: the measured
    ramp, with the shine a PBR material adds itself taken off the reflectance."""
    lv = look["leaves"]
    ramp = sorted(lv["chlorophyll_ramp"], key=lambda r: r["chlorophyll_fraction"])
    f = [r["chlorophyll_fraction"] for r in ramp]
    R = np.stack([np.interp(chlorophyll, f, [r["reflectance_linear"][c] for r in ramp]) for c in range(3)], -1)
    T = np.stack([np.interp(chlorophyll, f, [r["transmittance_linear"][c] for r in ramp]) for c in range(3)], -1)
    lift = lv.get("yellow_lift")
    if lift:
        w = (1.0 - smooth(0.0, float(lift["below_chlorophyll"]), chlorophyll))[..., None]
        factor = 1.0 + (np.asarray(lift["factor"], float) - 1.0) * w
        R, T = R * factor, np.minimum(T * factor, 1.0)
    return np.maximum(R - float(lv["specular_f0"]), 0.002), T


def leaf_sun(look: dict, sp, lma: np.ndarray) -> np.ndarray:
    """A leaf's light from its LMA, the inverse of the model's sun-leaf rule (0 shade, 1 sun).
    Where a species has no such rule, leaves count as half lit."""
    ss = getattr(getattr(sp, "light", None), "sun_shade", None)
    if ss is None or not bool(getattr(ss, "enabled", False)):
        return np.full(np.shape(lma), 0.5)
    q = np.clip((np.asarray(lma, float) - float(ss.lma_shade_g_m2)) / float(ss.lma_sun_increase_g_m2), 0.0, 1.0)
    return q ** (1.0 / float(ss.lma_exponent))


@dataclass
class LeafInstances:
    node: np.ndarray         # node carrying the leaf
    base: np.ndarray         # petiole end on the blade (n x 3), z-up metres
    along: np.ndarray        # unit, base to tip
    across: np.ndarray       # unit, across the blade
    length: np.ndarray       # m, blade length of the leaf's outline
    width: np.ndarray        # m
    area: np.ndarray         # m2, one-sided, as the model has it
    sun: np.ndarray          # 0 shade, 1 sun
    delay: np.ndarray        # days later than the tree's average to turn
    key: np.ndarray | None = None   # with leaves.each_year: each leaf's number this year, for an exporter's own draws


def _on_shoot(cfg: dict, snap: LeafSnapshot, pos: np.ndarray, r: np.ndarray, node: np.ndarray, k: np.ndarray, in_node: np.ndarray, tree_age: int) -> tuple:
    """Where each leaf leaves its shoot, which way its stalk goes, and which way it hangs.  A node's leaves
    leave on the side its bud faces.  On a short shoot that's at the end of the shoot's own short axis, a few
    millimetres a year long, and a cluster's leaves go the shoot's divergence apart, so they fan out."""
    turn = 2.0 * np.pi * hash01(node, 5)
    away = np.stack([np.cos(turn), np.sin(turn), np.zeros(len(turn))], 1)
    d = np.asarray(snap.lat_dir, float)[node]
    ln = np.linalg.norm(d, axis=1, keepdims=True)
    d = np.where(ln > 0.5, d / np.maximum(ln, 1e-9), away)
    years = np.where(snap.is_spur[node], np.maximum(float(tree_age) - np.asarray(snap.birth, float)[node], 0.0), 0.0)
    axis_m = np.minimum(float(cfg["spur_m_per_year"]) * years, float(cfg["spur_max_m"]))
    tip = pos[node] + d * (r + axis_m)[:, None]
    level = np.hypot(d[:, 0], d[:, 1])
    az = np.where(level > 0.05, np.arctan2(d[:, 1], d[:, 0]), turn) + k * np.radians(float(cfg["divergence_deg"]))
    splay = np.where(in_node > 1, np.radians(float(cfg["splay_deg"])), 0.0)
    stalk = d * np.cos(splay)[:, None] + np.stack([np.cos(az), np.sin(az), np.zeros(len(az))], 1) * np.sin(splay)[:, None]
    return tip, stalk / np.maximum(np.linalg.norm(stalk, axis=1, keepdims=True), 1e-9), az


def _size_spread(cfg: dict, key: np.ndarray, area: np.ndarray) -> np.ndarray:
    """Leaves of one kind differ in size.  Each leaf's own share, the same every year unless its key is the
    year's (``leaves.each_year``), with the tree's total leaf area held: the model's sizes and their mean stay
    as they are."""
    sigma = np.sqrt(np.log(1.0 + float(cfg["size_cv"]) ** 2))
    z = np.sqrt(-2.0 * np.log(np.maximum(hash01(key, 6), 1e-9))) * np.cos(2.0 * np.pi * hash01(key, 7))
    low, high = cfg["size_limits_sd"]
    share = np.exp(sigma * np.clip(z, float(low), float(high)))
    return area * share * (area.sum() / max(float((area * share).sum()), 1e-12))


def leaf_instances(look: dict, sp, snap: LeafSnapshot, pos: np.ndarray, radius: np.ndarray, tree_age: int, fill: float = 1.0) -> LeafInstances:
    """One blade for each leaf the model has: its count (a node's leaves over its size share) and its
    size, placed by a hash of the node, so a leaf keeps its place from age to age.  ``fill`` is the
    share of a blade's diamond its outline fills; the diamond is enlarged so the visible area is the
    model's.  With ``leaves.on_shoots`` asked for, each leaf leaves its shoot as a birch's does and has
    a size of its own round the model's; the leaves, and the tree's total leaf area, are the same.
    With ``leaves.each_year`` asked for, the leaves are this year's, not last year's: a leaf's own draws (how
    steeply it hangs, its roll, its days to turn, its size share) go by its node, its number and the year, and
    a short shoot's cluster goes on round the shoot's spiral from last year's, past the bud's scale leaves.
    What the wood has stays: how many leaves a node has, and where they leave it, which with leaves on no
    shoot is the side of the node each one sits on.  The tree's total leaf area is the same."""
    lv = look["leaves"]
    a_ref = snap.reference_area
    size = np.where(snap.size > 0, snap.size, a_ref)
    count = np.where(snap.leaves > 0, snap.leaves * a_ref / size, 0.0)
    whole = np.floor(count)
    extra = hash01(np.arange(len(count)), 11) < (count - whole)
    n_leaf = (whole + extra).astype(np.int64)
    node = np.repeat(np.arange(len(count)), n_leaf)
    k = np.arange(len(node)) - np.repeat(np.r_[0, np.cumsum(n_leaf)[:-1]], n_leaf)
    key = node * 64 + k
    # the wood's: the side of its node a leaf sits on when leaves are on no shoot, by the node and the leaf's number in any year
    side = key
    each_year = float(lv.get("each_year", 0.0)) > 0.0
    if each_year:
        # this spring's leaves: the same numbers for the same tree at the same age, others the year after
        key = key + int(tree_age) * 2 ** 40
    az = 2.0 * np.pi * hash01(side, 1)
    lo, hi = np.radians(lv["inclination_deg"])
    inc = lo + (hi - lo) * hash01(key, 2)
    place = lv.get("on_shoots")
    on_shoots = place is not None and float(place["strength"]) > 0.0 and snap.lat_dir is not None
    r = radius[np.minimum(node, len(radius) - 1)]
    if on_shoots:
        turn = k
        if each_year:
            # a shoot that has leaves again numbers them on round its spiral, past the scale leaves of the bud in between.
            # Every earlier year is counted at this year's number of leaves: a shoot whose number changed has its leaves
            # where the wood has them, but doesn't follow on from last year's round its axis
            years = np.maximum(float(tree_age) - np.asarray(snap.birth, float)[node], 0.0)
            turn = k + (n_leaf[node] + float(place.get("bud_scale_leaves", 0.0))) * years
        tip, stalk, az = _on_shoot(place, snap, pos, r, node, turn, n_leaf[node], tree_age)
    outward = np.stack([np.cos(az), np.sin(az), np.zeros(len(az))], 1)
    along = outward * np.cos(inc)[:, None] + np.array([0.0, 0.0, -1.0]) * np.sin(inc)[:, None]
    across = np.stack([-np.sin(az), np.cos(az), np.zeros(len(az))], 1)
    # a little roll, so the blades don't all sit square to the horizon
    roll = (hash01(key, 3) - 0.5) * 0.9
    n0 = np.cross(along, across)
    across = across * np.cos(roll)[:, None] + n0 * np.sin(roll)[:, None]
    aspect = float(lv["shape"]["aspect"])
    area = size[node]
    if on_shoots and len(area):
        area = _size_spread(place, key, area)
    diamond = area / max(fill, 1e-3)
    L = np.sqrt(2.0 * diamond * aspect)
    # the petiole leaves the bark, not the centre of the wood
    base = tip + stalk * float(lv["petiole_m"]) if on_shoots else pos[node] + outward * (r + float(lv["petiole_m"]))[:, None]
    sun = leaf_sun(look, sp, snap.lma[node])
    spread = (hash01(key, 4) - 0.5) * 2.0 * float(lv["turn_spread_days"])
    late = np.where(snap.is_spur[node], 0.0, float(lv["long_shoot_delay_days"]))
    old = -float(lv["old_tree_advance_days"]) * min(tree_age / 100.0, 1.0)
    return LeafInstances(node=node, base=base, along=along, across=across, length=L, width=L / aspect, area=area, sun=sun, delay=spread + late + old,
                         key=key if each_year else None)


# -- free bark strips ---------------------------------------------------------------------------
@dataclass
class PeelStrips:
    vertices: np.ndarray
    normals: np.ndarray
    uv: np.ndarray
    colour: np.ndarray       # linear RGBA, A is the strip's opacity
    faces: np.ndarray
    count: int
    node: np.ndarray = None   # node each vertex's strip sits on
    opacity: np.ndarray = None  # each vertex's strip's opacity


def peel_strips(look: dict, pos: np.ndarray, parent: np.ndarray, radius_wood: np.ndarray, birth: np.ndarray, select: np.ndarray,
                tree_age: int, tree_height_m: float, dbh_ob_cm: float) -> PeelStrips | None:
    """Curled strips of outer bark standing off the stem and limbs.  Each internode draws its own
    candidates from a hash of its node id; a strip shows for a few years of its node's life, so
    from one age to the next most strips stay where they are.  Two faces each: the white outside
    and the orange inside (two sheets back to back, so no two-sided lighting is needed)."""
    cfg = look["bark"].get("peel")
    if not cfg or not float(cfg.get("strips_per_m2", 0.0)):
        return None
    idx = np.nonzero(select & (radius_wood >= 0.5 * float(cfg["diameter_m"][0])))[0]
    idx = idx[idx > 0]
    if idx.size == 0:
        return None
    p0, p1 = pos[parent[idx]], pos[idx]
    seg = p1 - p0
    length = np.linalg.norm(seg, axis=1)
    part_age = tree_age - birth[idx]
    st = part_state(look, part_age, 2.0 * radius_wood[idx], 0.5 * (p0[:, 2] + p1[:, 2]), tree_height_m, dbh_ob_cm)
    rel = st["peel"] / max(float(cfg["coverage_max"]), 1e-6)
    r_ob = 0.5 * st["diameter_m"]
    # strips are drawn per 3 years of a node's life and live several years
    expected = 2.0 * np.pi * r_ob * length * float(cfg["strips_per_m2"]) * rel
    per_slot = 4
    keep_node, keep_slot = [], []
    for slot in range(per_slot):
        keep = hash01(idx * 8 + slot, 21) < expected / per_slot
        keep_node.append(idx[keep])
        keep_slot.append(np.full(int(keep.sum()), slot))
    node = np.concatenate(keep_node)
    if node.size == 0:
        return None
    slot = np.concatenate(keep_slot)
    key = node * 8 + slot
    # born in a window of the node's life; the window slides with age so the count holds steady
    lo, hi = cfg["life_years"]
    life = lo + (hi - lo) * hash01(key, 22)
    phase = hash01(key, 23) * life
    t_in_life = ((tree_age + phase) % life) / life
    which = np.searchsorted(idx, node)
    az0 = 2.0 * np.pi * hash01(key + np.floor((tree_age + phase) / life).astype(np.int64) * 1000, 24)
    frac = hash01(key, 25)
    # local frame
    t = seg[which] / np.maximum(length[which], 1e-9)[:, None]
    ref = np.where((np.abs(t[:, 2]) > 0.9)[:, None], np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]))
    e1 = np.cross(ref, t)
    e1 /= np.maximum(np.linalg.norm(e1, axis=1), 1e-9)[:, None]
    e2 = np.cross(t, e1)
    centre = p0[which] + seg[which] * frac[:, None]
    R = r_ob[which]
    sl, sh = cfg["strip_length_m"], cfg["strip_height_m"]
    strip_len = np.minimum(sl[0] + (sl[1] - sl[0]) * hash01(key, 26) ** 2, 1.4 * np.pi * R)
    strip_h = sh[0] + (sh[1] - sh[0]) * hash01(key, 27)
    curl = float(cfg["curl_m"]) * (0.4 + 1.2 * hash01(key, 28)) * (0.4 + 0.6 * t_in_life)
    # one end stays on the bark; the free end lifts and rolls back
    NA, NB = 9, 3
    a = np.linspace(0.0, 1.0, NA)[:, None]
    b = np.linspace(-0.5, 0.5, NB)[:, None]
    sign = np.where(hash01(key, 29) < 0.5, -1.0, 1.0)
    n = len(node)
    grid_a = np.repeat(a.T, n, axis=0)                           # n x NA
    theta = az0[:, None] + sign[:, None] * grid_a * (strip_len / R)[:, None]
    lift = (grid_a ** 2.6) * curl[:, None] + 0.001
    # the roll: past two thirds of the way the sheet turns back on itself
    turn = np.clip((grid_a - 0.66) / 0.34, 0.0, 1.0)
    theta = theta - sign[:, None] * turn * turn * (0.3 * strip_len / R)[:, None]
    rad = R[:, None] + lift
    wob = (hash01(key, 30) - 0.5)[:, None] * 0.6 * strip_h[:, None] * grid_a
    verts = np.zeros((n, NA, NB, 3))
    nrm = np.zeros((n, NA, NB, 3))
    for j in range(NB):
        o = np.cos(theta)[..., None] * e1[:, None, :] + np.sin(theta)[..., None] * e2[:, None, :]
        verts[:, :, j, :] = centre[:, None, :] + rad[..., None] * o + t[:, None, :] * ((b[j, 0] * strip_h)[:, None, None] + wob[..., None])
        nrm[:, :, j, :] = o
    # normals from the sheet's own curve, so the roll catches the light
    da = np.gradient(verts, axis=1)
    db = np.gradient(verts, axis=2)
    nrm = np.cross(da, db) * sign[:, None, None, None]
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-12)
    uv_a = np.repeat(grid_a[:, :, None], NB, axis=2)
    uv_b = np.broadcast_to((b.T + 0.5)[None, :, :], (n, NA, NB))
    variant = np.floor(hash01(key, 31) * 4.0)
    # strip texture: four strips in rows, the left half the outside, the right half the inside
    U_out = 0.002 + 0.496 * uv_a
    V = (variant[:, None, None] + 0.02 + 0.96 * uv_b) / 4.0
    v_all = np.concatenate([verts, verts]).reshape(-1, 3)
    n_all = np.concatenate([nrm, -nrm]).reshape(-1, 3)
    uv_all = np.concatenate([np.stack([U_out, V], -1), np.stack([0.5 + U_out, V], -1)]).reshape(-1, 2)
    # faces, the outside turned out and the inside turned in
    q0 = (np.arange(NA - 1)[:, None] * NB + np.arange(NB - 1)[None, :]).ravel()
    tri = np.concatenate([np.stack([q0, q0 + NB, q0 + NB + 1], 1), np.stack([q0, q0 + NB + 1, q0 + 1], 1)])
    per = NA * NB
    F_out = np.arange(n)[:, None, None] * per + tri[None]
    flip = sign < 0                      # a strip turning the other way flips its sheet's winding
    F_out[flip] = F_out[flip][:, :, ::-1]
    F_in = F_out[:, :, ::-1] + n * per
    faces = np.concatenate([F_out.reshape(-1, 3), F_in.reshape(-1, 3)])
    op = float(cfg["opacity_young"]) + (float(cfg["opacity_old"]) - float(cfg["opacity_young"])) * t_in_life
    col = np.ones((2 * n * per, 4))
    col[:, 3] = np.tile(np.repeat(op, per), 2)
    # darker where the sheet is still on the bark, in the shade of its own roll
    col[:, :3] = np.tile((0.72 + 0.28 * smooth(0.0, 0.8, uv_a)).ravel(), 2)[:, None]
    return PeelStrips(v_all, n_all, uv_all, col, faces.astype(np.int64), int(n), np.tile(np.repeat(node, per), 2), col[:, 3].copy())
