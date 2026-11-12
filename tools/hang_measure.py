"""How much of a tree hangs, as numbers, from its geometry at one age.  It only reads; it changes no number.

The one rule, kept fixed.  An internode HANGS when it points more than 30 degrees below level: it drops by more
than half its own length from its near end to its far end.  The stem never counts.  This is the engine's own rule
(treegen/growth.py, HANGING_DZ = -0.5); tests/test_hang_measure.py holds the two together.

The measures are the seven of reports/reviews/2026-11-11_audit_look.md, "How to measure hanginess":

H1  share of branch length that hangs, by wood diameter: under 5, 5-10, 10-20 and over 20 mm
H2  share of the leaves that sit on hanging internodes
H3  hanging run over tree height: mean, 90th percentile, longest.  A run is the unbroken hanging length from where a
    branch first passes 30 degrees below level to an end beyond which nothing hangs.  Runs under 0.2 m aren't counted
H4  ends per hanging spray: a spray is all the hanging wood below one such start, so 1 end is a single strand.  Given
    for all sprays, and for those that start on wood under 5 mm (a hanging limb is one spray with all its twigs)
H5  is read from a picture (tools/hang_photo.py).  Its twin here, straight from the geometry: the share of branch
    length within 20 degrees of vertical in a level side view, and how much of that points down.  H5 alone can't tell
    hanging wood from wood that stands upright, so it is never ranked alone: closer_on_h5()
H6  the first age at which H2 passes 10 %
H7  crown width over tree height, and the height of the widest point over tree height, in a level side view

A tree is a Geometry: plain arrays, one row per node.  Node i is the far end of the internode parent[i] -> i, z is
metres above the ground, and the base has parent -1.  from_model() makes one from a grown model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

HANG_BELOW_LEVEL_DEG = 30.0
HANG_DZ = -0.5                       # the sine of 30 degrees, downward: the one rule
MIN_RUN_M = 0.2                      # shorter hanging runs aren't counted in H3 and H4
CLASS_EDGES_MM = (5.0, 10.0, 20.0)   # wood diameter
CLASSES = ("under_5mm", "5_10mm", "10_20mm", "over_20mm")
NEAR_VERTICAL_DEG = 20.0
H6_SHARE = 0.10
BANDS = 10                           # H7 reads the crown in tenths of tree height
BAND_MIN_NODES = 5


@dataclass
class Geometry:
    pos: np.ndarray      # (n, 3) metres, z up from the ground
    parent: np.ndarray   # (n,) the node an internode starts from; -1 for the base
    vec: np.ndarray      # (n, 3) the internode parent -> node as the wood runs: its direction times its length (m)
    radius: np.ndarray   # (n,) metres, of the internode
    leaves: np.ndarray   # (n,) leaves carried at the node
    stem: np.ndarray     # (n,) True on the stem
    alive: np.ndarray    # (n,) False for shed wood, which is never read


def geometry(pos, parent, radius=None, leaves=None, stem=None, alive=None) -> Geometry:
    """A Geometry from plain lists; what isn't given is 1 mm wood, no leaves, no stem, all alive.  Each internode runs
    straight from its parent's place to its own."""
    pos = np.asarray(pos, dtype=float).reshape(-1, 3)
    n = len(pos)
    parent = np.asarray(parent, dtype=np.int64)
    if len(parent) != n or (parent >= n).any() or int((parent < 0).sum()) != 1:
        raise ValueError("parent must name one node per row, with exactly one base (-1)")
    vec = np.where((parent >= 0)[:, None], pos - pos[np.maximum(parent, 0)], 0.0)
    return Geometry(pos, parent, vec,
                    np.full(n, 0.001) if radius is None else np.asarray(radius, dtype=float),
                    np.zeros(n) if leaves is None else np.asarray(leaves, dtype=float),
                    np.zeros(n, bool) if stem is None else np.asarray(stem, dtype=bool),
                    np.ones(n, bool) if alive is None else np.asarray(alive, dtype=bool))


def from_model(model) -> Geometry:
    """The living tree of a grown model (treegen.growth.GrowthModel), as it stands now.  An internode's direction and
    length are the engine's own (its `dir` and `length`), the ones its own rule reads.  They differ from the step between
    two nodes' places only where the engine holds a strand at the ground (mechanics.py, "keeping nodes above the ground")."""
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    stem = np.zeros(n, bool)
    stem[np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)] = True
    return Geometry(T.pos[:n], T.parent[:n].astype(np.int64), T.dir[:n] * T.length[:n, None], T.radius[:n],
                    np.where(alive, T.leaves[:n], 0.0).astype(float), stem, alive)


def _internodes(g: Geometry):
    """Per node, its internode: whether there is one, its vector, its length (m) and how steeply it points
    (-1 straight down, 0 level, +1 straight up)."""
    has = g.alive & (g.parent >= 0)
    vec = np.where(has[:, None], g.vec, 0.0)
    length = np.linalg.norm(vec, axis=1)
    dz = np.divide(vec[:, 2], length, out=np.zeros(len(length)), where=length > 0.0)
    return has, vec, length, dz


def held_at_ground_m(g: Geometry) -> float:
    """Length of hanging wood whose far end the ground holds up: its step between places is shorter than the wood itself."""
    has, _, length, _ = _internodes(g)
    step = np.linalg.norm(g.pos - g.pos[np.maximum(g.parent, 0)], axis=1)
    return float(length[hangs(g) & (step < 0.99 * length)].sum())


def hangs(g: Geometry) -> np.ndarray:
    """The one rule: which internodes hang."""
    has, _, _, dz = _internodes(g)
    return has & ~g.stem & (dz < HANG_DZ)


def _levels(g: Geometry) -> list:
    """Living nodes by their number of internodes from the base, nearest first, so a parent always comes before its children."""
    depth = (g.parent >= 0).astype(np.int64)
    up = g.parent.copy()
    while True:                       # pointer jumping: each pass doubles how far up every node has looked
        on = np.nonzero(up >= 0)[0]
        if not on.size:
            break
        above = up[on]
        depth[on] += depth[above]
        up[on] = up[above]
    idx = np.nonzero(g.alive)[0]
    idx = idx[np.argsort(depth[idx], kind="stable")]
    d = depth[idx]
    bounds = np.searchsorted(d, np.arange(int(d.max()) + 2)) if idx.size else np.zeros(1, np.int64)
    return [idx[bounds[k]:bounds[k + 1]] for k in range(len(bounds) - 1)]


def runs(g: Geometry):
    """Per node: the hanging run ending there (m; 0 where the internode doesn't hang), and the node where its spray starts (-1 where none)."""
    hang = hangs(g)
    _, _, length, _ = _internodes(g)
    run = np.zeros(len(length))
    start = np.full(len(length), -1, np.int64)
    for idx in _levels(g)[1:]:
        h = idx[hang[idx]]
        if not h.size:
            continue
        p = g.parent[h]
        on = hang[p]
        run[h] = length[h] + np.where(on, run[p], 0.0)
        start[h] = np.where(on, start[p], h)
    return run, start


def leaf_share(g: Geometry) -> float:
    """H2 alone, cheap enough for every year: the share of the leaves on hanging internodes."""
    total = float(g.leaves[g.alive].sum())
    return float(g.leaves[hangs(g)].sum()) / total if total > 0.0 else 0.0


def first_age_over(by_age: dict, share: float = H6_SHARE):
    """H6: the first age at which the share of leaves on hanging internodes reaches `share`; None if it never does."""
    for age in sorted(by_age, key=int):
        if by_age[age] >= share:
            return int(age)
    return None


def first_age_staying_over(by_age: dict, share: float = H6_SHARE):
    """H6, read strictly: the first age from which that share is reached every year to the end of the record.  A seedling
    with a dozen leaves can pass the line for one year and drop back; this is the age the habit sets in.  None if the
    last year is under the line."""
    ages = sorted(by_age, key=int)
    first = None
    for age in reversed(ages):
        if by_age[age] < share:
            break
        first = int(age)
    return first


def foot_and_top(g: Geometry):
    """Where the stem meets the ground and the tree's highest living node (m)."""
    foot = g.pos[int(np.nonzero(g.parent < 0)[0][0])].astype(float)
    alive = np.nonzero(g.alive)[0]
    return foot, g.pos[alive[int(np.argmax(g.pos[alive, 2]))]].astype(float)


def in_window(g: Geometry, window: dict, axis: int, mirror: bool = False) -> np.ndarray:
    """Which internodes have their middle inside a photo's window (tools/hang_photo.py, window_of), in the level side
    view whose sideways axis is `axis`: the same boxes, in tree heights along the tree's own stem line, that
    window_mask lays on a picture."""
    foot, top = foot_and_top(g)
    tall = float(top[2] - foot[2])
    if tall <= 0.0:
        return np.zeros(len(g.parent), bool)
    mid = 0.5 * (g.pos + g.pos[np.maximum(g.parent, 0)])
    v = (mid[:, 2] - foot[2]) / tall
    u = (mid[:, axis] - foot[axis] - (top[axis] - foot[axis]) * v) / tall
    a = (-u if mirror else u) + window["lean"] * v
    m = np.zeros(len(g.parent), bool)
    for a0, v0, a1, v1 in window["include"]:
        m |= (a >= a0) & (a < a1) & (v > v0) & (v <= v1)
    for a0, v0, a1, v1 in window["exclude"]:
        m &= ~((a >= a0) & (a < a1) & (v > v0) & (v <= v1))
    return m


def side_view(g: Geometry, min_diameter_m: float = 0.0, window: dict | None = None) -> dict:
    """H5's twin: of the branch length seen in a level side view, the share within 20 degrees of vertical, and how much
    of that points down.  Mean of the two views, east and north.  min_diameter_m leaves out wood too thin to show.
    It reads the step from each node's place to the next, which is what a picture is drawn from.
    window: read only the part of the tree inside a photo's window, laid on either side of the tree in turn (the mean
    of the four)."""
    has = g.alive & (g.parent >= 0)
    vec = np.where(has[:, None], g.pos - g.pos[np.maximum(g.parent, 0)], 0.0)
    keep = has & ~g.stem & (2.0 * g.radius >= min_diameter_m)
    near, down, length = [], [], []
    for axis in (0, 1):
        for mirror in ((False,) if window is None else (False, True)):
            part = keep if window is None else keep & in_window(g, window, axis, mirror)
            across, rise = np.abs(vec[part, axis]), vec[part, 2]
            seen = np.hypot(across, rise)
            upright = np.degrees(np.arctan2(across, np.abs(rise))) <= NEAR_VERTICAL_DEG
            total = float(seen.sum())
            if total <= 0.0:
                return {"near_vertical_share": None, "of_which_down": None, "seen_m": 0.0}
            near.append(float(seen[upright].sum()) / total)
            down.append(float(seen[upright & (rise < 0.0)].sum()) / max(float(seen[upright].sum()), 1e-12))
            length.append(total)
    return {"near_vertical_share": float(np.mean(near)), "of_which_down": float(np.mean(down)), "seen_m": float(np.mean(length))}


def closer_on_h5(before: dict, after: dict, photos: tuple) -> dict:
    """The rule for ranking on H5.  The picture's near-vertical share can't tell hanging wood from wood that stands
    upright: a setting that turned hanging twigs upright would read as well as one that let them spread.  So a change
    counts as closer to the photos only if all four hold:

      the near-vertical share, read in the photo's window, ends nearer the photos' range (lowest, highest) than it began;
      H1, the share of branch length that hangs, falls;
      the near-vertical wood that points down falls (the twin's share times its 'of_which_down');
      the near-vertical wood that points up doesn't rise (the twin's share times the rest).  It counts as risen only
      if it rose both as a share of the wood seen and in metres: when hanging cords shorten, what stands upright is a
      larger share of less wood without one twig having turned.

    before, after: {"near_vertical": the picture's share in the window, "twin": the geometry's share in the same window,
    "of_which_down": the twin's, "seen_m": the length the twin saw, "hanging_share": H1}.  Returns each test, the
    figures behind them, and `closer`, true only if all four pass."""
    lo, hi = photos

    def gap(x: float) -> float:
        return max(lo - x, 0.0, x - hi)

    def down(m: dict) -> float:
        return m["twin"] * m["of_which_down"]

    def up(m: dict) -> float:
        return m["twin"] * (1.0 - m["of_which_down"])

    tests = {"nearer_the_photos": gap(after["near_vertical"]) < gap(before["near_vertical"]),
             "less_wood_hangs": after["hanging_share"] < before["hanging_share"],
             "less_upright_wood_points_down": down(after) < down(before),
             "no_more_upright_wood_points_up": up(after) <= up(before) or up(after) * after["seen_m"] <= up(before) * before["seen_m"]}
    figures = {"gap_to_photos": [gap(before["near_vertical"]), gap(after["near_vertical"])], "hanging_share": [before["hanging_share"], after["hanging_share"]],
               "upright_pointing_down_share": [down(before), down(after)], "upright_pointing_up_share": [up(before), up(after)],
               "upright_pointing_up_m": [up(before) * before["seen_m"], up(after) * after["seen_m"]]}
    return {**tests, "closer": all(tests.values()), "figures": figures}


def outline(g: Geometry) -> dict:
    """H7: the crown's width over tree height and where it is widest, in a level side view.  Width of a tenth of height:
    from the 2nd to the 98th percentile of its branch nodes, sideways.  Mean of the two views."""
    height = float(g.pos[g.alive, 2].max()) if g.alive.any() else 0.0
    nodes = g.alive & ~g.stem & (g.parent >= 0)
    if height <= 0.0 or not nodes.any():
        return {"width_over_height": None, "widest_at": None}
    band = np.clip((g.pos[nodes, 2] / height * BANDS).astype(int), 0, BANDS - 1)
    widths = np.zeros(BANDS)
    for b in range(BANDS):
        hit = band == b
        if int(hit.sum()) >= BAND_MIN_NODES:
            xy = g.pos[nodes][hit]
            widths[b] = np.mean([np.percentile(xy[:, a], 98) - np.percentile(xy[:, a], 2) for a in (0, 1)])
    if widths.max() <= 0.0:
        return {"width_over_height": None, "widest_at": None}
    return {"width_over_height": float(widths.max()) / height, "widest_at": (int(np.argmax(widths)) + 0.5) / BANDS}


def measures(g: Geometry, min_seen_diameter_m: float = 0.0) -> dict:
    """Every hang measure of one tree at one age (H6 needs the yearly series: first_age_over)."""
    has, _, length, _ = _internodes(g)
    hang = hangs(g)
    branch = has & ~g.stem
    height = float(g.pos[g.alive, 2].max()) if g.alive.any() else 0.0
    # H1
    mm = 2000.0 * g.radius
    cls = np.searchsorted(np.asarray(CLASS_EDGES_MM), mm, side="right")
    by_class = {}
    for k, name in enumerate(CLASSES):
        total = float(length[branch & (cls == k)].sum())
        by_class[name] = {"length_m": total, "share": float(length[hang & (cls == k)].sum()) / total if total > 0.0 else None}
    branch_m, hang_m = float(length[branch].sum()), float(length[hang].sum())
    # H3 and H4
    run, start = runs(g)
    continues = np.zeros(len(length), bool)
    continues[g.parent[hang]] = True
    ends = hang & ~continues                       # nothing beyond it hangs
    n = len(length)
    spray_m = np.bincount(start[hang], weights=length[hang], minlength=n)
    spray_ends = np.bincount(start[ends], minlength=n)
    longest = np.zeros(n)
    np.maximum.at(longest, start[ends], run[ends])
    counted = np.nonzero(longest >= MIN_RUN_M)[0]
    r = run[ends]
    r = r[r >= MIN_RUN_M]
    over = r / height if height > 0.0 else r
    h3 = {"runs": int(r.size),
          "mean_m": float(r.mean()) if r.size else None, "p90_m": float(np.percentile(r, 90)) if r.size else None, "longest_m": float(r.max()) if r.size else None,
          "mean_over_height": float(over.mean()) if r.size else None, "p90_over_height": float(np.percentile(over, 90)) if r.size else None,
          "longest_over_height": float(over.max()) if r.size else None}
    def sprays(which: np.ndarray) -> dict:
        return {"sprays": int(which.size),
                "ends_per_spray": float(spray_ends[which].mean()) if which.size else None,
                "single_strand_share": float((spray_ends[which] == 1).mean()) if which.size else None,
                # 1.0: every spray is one cord; lower: the hanging wood is shared out over side twigs
                "longest_path_share_of_spray_length": float(longest[which].sum() / spray_m[which].sum()) if which.size else None}

    # a whole limb that hangs is one spray with all its twigs; the sprays that start on wood under 5 mm are the twigs' own
    h4 = {**sprays(counted), "starting_under_5mm": sprays(counted[mm[counted] < CLASS_EDGES_MM[0]])}
    return {"height_m": height, "branch_length_m": branch_m, "hanging_length_m": hang_m, "hanging_held_at_ground_m": held_at_ground_m(g),
            "H1_hanging_share_of_branch_length": {"all": hang_m / branch_m if branch_m > 0.0 else None, **by_class},
            "H2_leaves_on_hanging_share": leaf_share(g),
            "H3_hanging_run": h3, "H4_sprays": h4,
            "H5_side_view": {"all_wood": side_view(g), "wood_wide_enough_to_show": side_view(g, min_seen_diameter_m)},
            "H7_outline": outline(g)}
