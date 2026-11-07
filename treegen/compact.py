"""Drop dead nodes from a lean tree (speed.drop_dead; off by default; NOT lossless).

Most of an old tree's nodes are dead: 64-74 % at 60 for a stand tree, 87 % in a plot.  They hold memory, and every whole-array pass
walks them.  Growth reads a dead node only to learn that it's dead, so one is kept where a living node's link points at it, and
the rest go.  The maths is the same, but numpy's sums round by position in the array, so a seed makes a different tree, as it does
on another machine.  Only for lean runs: what a tree's history or mesh needs from dead nodes goes too.  tools/tree_table.py's
count of shed branches misses the ones dropped.

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
