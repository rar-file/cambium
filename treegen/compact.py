"""Drop dead nodes from a lean tree (speed.drop_dead; off by default; NOT lossless).

Most of an old tree's nodes are dead: 64-74 % at 60 for a stand tree, 87 % in a plot.  They hold memory, and every whole-array pass
walks them.  Growth reads a dead node only to learn that it's dead, so one is kept where a living node's link points at it, and
the rest go.  numpy's sums round by position in the array, so a seed could in principle make a different tree; on the runs tested,
every yearly stat stayed the same.

Only lean runs drop anything.  Meshes, timelines and the game export replay a tree at any age from its dead nodes and its yearly
radii, and a lean run keeps no radii, so it could never export anyway; a run that can export ignores this setting.  Every dead
node on living wood stays, with its position and last radius, so a live tree keeps its branch scars.  What fell is logged as it
goes (shed_dropped), so tools/tree_table.py's count of shed branches and twigs comes out the same.

If you add model state that holds node numbers, add it to compact() below: tests/test_speed.py runs with this on.
"""
from __future__ import annotations

import numpy as np


def compact(model, every: int = 3, min_share: float = 0.2) -> bool:
    """Renumber the living nodes and the dead ones they link to.  Returns whether anything was dropped."""
    T = model.tree
    if not model.lean or model.year % every != 0 or T.n < 64:
        return False
    n = T.n
    alive = T.death[:n] < 0
    par = T.parent[:n]
    keep = alive.copy()
    keep[0] = True
    dead_kid = np.nonzero(~alive & (par >= 0))[0]
    keep[dead_kid[alive[par[dead_kid]]]] = True
    m = int(keep.sum())
    if m >= (1.0 - min_share) * n:
        return False
    idx = np.nonzero(keep)[0]
    new = np.full(n, -1, np.int64)
    new[idx] = np.arange(m)

    def mapped(a):
        out = a.copy()
        ok = a >= 0
        out[ok] = new[a[ok]]
        return out

    # the shed axes among what's going, for the count of what fell (tools/tree_table.py shed_events): the year, and the axis
    # it stood on, since which axes lead the tree is only known at the end of a run
    going = np.nonzero(~keep & T.is_lateral[:n])[0]
    first = going[T.death[par[going]] != T.death[going]]
    if first.size:
        model.__dict__.setdefault("shed_dropped", []).append((T.death[first].copy(), T.axis[par[first]].copy()))
    tip = getattr(T, "stem_tip", None)
    if tip is not None:
        tip = int(tip)
        while not keep[tip] and T.parent[tip] >= 0:
            tip = int(T.parent[tip])
    cap = m + m // 4 + 16
    for name in list(T.VEC) + list(T.SCALAR):
        a = getattr(T, name)
        b = np.zeros((cap,) + a.shape[1:], dtype=a.dtype)
        b[:m] = a[idx]
        setattr(T, name, b)
    T.n, T.cap = m, cap
    for name in ("parent", "main_child", "lat_child", "scaffold"):
        a = getattr(T, name)
        a[:m] = mapped(a[:m])
    if tip is not None:
        T.stem_tip = int(new[tip])
    T.relay = {int(new[k]): int(new[v]) for k, v in T.relay.items() if keep[k] and keep[v]}

    def sliced(a):
        return a[idx[idx < len(a)]]

    for name in ("_established", "_limb_draw", "_r_last", "_r_pipe", "_psi", "_stem_pipe_prev"):
        a = getattr(model, name, None)
        if isinstance(a, np.ndarray) and len(a):
            setattr(model, name, sliced(a))
    if len(model._starving):
        s = model._starving[model._starving < n]
        s = s[keep[s]]
        model._starving = new[s]
    model.spur_rec = {int(new[k]): v for k, v in model.spur_rec.items() if keep[k]}
    model.reit = {int(new[k]): v for k, v in model.reit.items() if keep[k]}
    model._relay_buds = {int(new[k]): int(new[v]) for k, v in model._relay_buds.items() if keep[k] and keep[v]}
    model._relay_first = {a: int(new[v]) for a, v in model._relay_first.items() if keep[v]}
    # this year's working values, read by no one next year, with old numbers in them
    model._bud_q = None
    model._bud_leaf_cost = None
    model._ring = None
    model.diag = {}
    # the short-shoot log's node numbers are only for meshes, which a lean run can't make; its length is its next record's number
    model.spurs.node[:] = [0] * len(model.spurs.node)
    return True
