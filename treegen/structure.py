"""Node store shared by the crown and the root system.

Node i is the distal end of internode parent[i] -> i; node 0 is the base.
Passes over the tree are vectorised level by level (depth from the base);
subtree sums run compiled, node by node in the same order (kernels.py).
"""
from __future__ import annotations

import numpy as np

from . import kernels


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def _perpendicular(ref: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Component of ``ref`` orthogonal to unit ``d``, normalised, with a fallback."""
    r = ref - (ref * d).sum(-1, keepdims=True) * d
    n = np.linalg.norm(r, axis=-1)
    bad = n < 1e-6
    if bad.any():
        alt = np.where(np.abs(d[bad, 0:1]) < 0.9, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
        r[bad] = alt - (alt * d[bad]).sum(-1, keepdims=True) * d[bad]
        n[bad] = np.linalg.norm(r[bad], axis=-1)
    return r / n[:, None]


class Levels(list):
    """``Tree.levels``: per depth (all nodes, main children, laterals), with
    the flattened node order the compiled passes walk (kernels.py)."""

    @property
    def down(self) -> np.ndarray:
        """Nodes below the base, level by level (parents before children)."""
        d = getattr(self, "_down", None)
        if d is None:
            d = self._down = np.concatenate([seg for seg, _, _ in self[1:]]) if len(self) > 1 else np.zeros(0, np.intp)
        return d

    @property
    def up(self) -> np.ndarray:
        """Nodes below the base, deepest level first, each level's main
        children before its laterals (the order of the level-wise sums)."""
        u = getattr(self, "_up", None)
        if u is None:
            parts = [a for _, mains, lats in reversed(self[1:]) for a in (mains, lats)]
            u = self._up = np.concatenate(parts) if parts else np.zeros(0, np.intp)
        return u


class Tree:
    """Struct-of-arrays node store.  Node i is the distal end of internode
    parent[i] -> i; node 0 is the root at ground level."""

    VEC = ("pos", "dir", "ref", "term_dir", "lat_dir", "sym_side")
    SCALAR = {
        "parent": np.int32, "main_child": np.int32, "lat_child": np.int32,
        "is_lateral": np.bool_, "birth": np.int16, "death": np.int16,
        "order": np.int16, "axis": np.int32, "depth": np.int32,
        "length": np.float64, "phyllo": np.int32,
        "term": np.int8,
        "lat": np.int8, "lat_age": np.int16, "spur_birth": np.int16,
        "own_pipe": np.float64, "radius": np.float64, "scaffold_birth": np.int16, "scaffold": np.int32,
        "leaf_scale": np.float64, "leaves": np.float32,
        "leaf_size": np.float64, "lma": np.float32, "wood_area": np.float64, "sap_area": np.float64,
        "no_axil": np.bool_,
    }

    def __setstate__(self, state):
        # trees pickled before an array existed get it (zeros; sap_area: all wood)
        self.__dict__.update(state)
        for name, dt in self.SCALAR.items():
            if name not in state:
                setattr(self, name, state["wood_area"].copy() if name == "sap_area" else np.zeros(self.cap, dtype=dt))

    def __init__(self, capacity: int = 4096):
        self.n = 0
        self.relay = {}   # stem node -> first node of the lateral that replaced its lost leader
        self.cap = capacity
        for k in self.VEC:
            setattr(self, k, np.zeros((capacity, 3)))
        for k, dt in self.SCALAR.items():
            setattr(self, k, np.zeros(capacity, dtype=dt))

    def alloc(self, k: int) -> np.ndarray:
        need = self.n + k
        if need > self.cap:
            new_cap = max(need, 2 * self.cap)
            for name in list(self.VEC) + list(self.SCALAR):
                a = getattr(self, name)
                b = np.zeros((new_cap,) + a.shape[1:], dtype=a.dtype)
                b[: self.n] = a[: self.n]
                setattr(self, name, b)
            self.cap = new_cap
        idx = np.arange(self.n, need)
        self.n = need
        self.main_child[idx] = -1
        self.lat_child[idx] = -1
        self.death[idx] = -1
        self.spur_birth[idx] = -1
        return idx

    def trim(self, spare: float = 0.1) -> None:
        """Shrink the arrays to the nodes in use plus a margin: growth by
        doubling can leave up to half of them unused (plot checkpoints)."""
        cap = int(self.n * (1.0 + spare)) + 16
        if cap >= self.cap:
            return
        for name in list(self.VEC) + list(self.SCALAR):
            setattr(self, name, getattr(self, name)[:cap].copy())
        self.cap = cap

    # -- tree passes, vectorised level by level --------------------------
    def levels(self, mask: np.ndarray) -> Levels:
        idx = np.nonzero(mask)[0]
        d = self.depth[idx]
        order = np.argsort(d, kind="stable")
        idx, d = idx[order], d[order]
        bounds = np.searchsorted(d, np.arange(int(d.max()) + 2))
        lat = self.is_lateral[idx]
        out = Levels()
        for k in range(len(bounds) - 1):
            a, b = bounds[k], bounds[k + 1]
            seg = idx[a:b]
            sl = lat[a:b]
            out.append((seg, seg[~sl], seg[sl]))
        return out

    def basipetal(self, levels: list, values: np.ndarray) -> np.ndarray:
        """Subtree sums: acc[i] = values[i] + sum over descendants."""
        acc = values.copy()
        up = levels.up if isinstance(levels, Levels) else Levels(levels).up
        kernels.basipetal(up, self.parent, acc.reshape(acc.shape[0], int(np.prod(acc.shape[1:]))))
        return acc

    def trunk_chain(self, leaders=None) -> np.ndarray:
        """The stem from the base to its tip: the main child, unless a living
        replacement leader (a lateral on one of the ``leaders`` axes, or the
        shoot that replaced a lost leader, ``relay``: node -> its first node)
        is thicker, as the stem is found in the field.  After browsing the
        first replacement to grow is not always the one that wins; following
        it measured DBH on a suppressed side stem (3.7 cm against 20 cm, phase
        26).  Ordinary limbs never take over: without ``leaders`` only the
        relay shoot can."""
        chain = [0]
        mc, lc = self.main_child, self.lat_child
        relay = getattr(self, "relay", {})
        lead = set() if leaders is None else set(int(a) for a in leaders)
        while True:
            k = chain[-1]
            nxt, best = -1, -1.0
            lat = int(lc[k]) if lc[k] >= 0 and int(self.axis[lc[k]]) in lead else -1
            for c in (int(mc[k]), lat, int(relay.get(k, -1))):
                if c >= 0 and self.death[c] < 0 and self.radius[c] > best:
                    nxt, best = c, float(self.radius[c])
            if mc[k] >= 0 and self.death[mc[k]] < 0 and self.radius[mc[k]] >= best:
                nxt = int(mc[k])
            if nxt < 0:
                break
            chain.append(nxt)
        return np.array(chain)
