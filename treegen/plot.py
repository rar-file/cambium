"""A plot of trees that each grow as their own simulation, sharing one light
field and one soil.

Every year the plot gathers the leafy buds of all living trees, computes one
periodic light field over the plot (shade from each tree's real leaf area),
and steps each tree, which reads that field through its own offset.  The
soil is one too (roots.SharedSoil): stones and rootable depth are laid out
once with the plot seed, and every year the absorbing roots of all trees are
blurred into one soil-water field that each tree reads at its offset (root
competition).  Trees differ by seed (architecture), germination year and a
heritable growth factor on their carbon gain.

Two modes: "managed" follows the species' thinning programme, thinning from
below (the smallest stems go); "natural" never thins, and a tree dies when
its own carbon no longer pays the upkeep of its living wood (the branch
carbon balance of Sprugel, Hinckley & Schaap 1991 applied to the whole
tree), as in an unmanaged stand.  ``on_finish(k, cause)`` is called for
each tree the year it is removed or dies, before it is freed; ``checkpoint``
moves every tree's history to disk and pickles the plot, so a long run can
resume and keeps only the trees' current state in memory.
"""
from __future__ import annotations

import copy
import math
import os
import pickle
from pathlib import Path

import numpy as np

from .growth import GrowthModel
from .roots import SharedSoil


class OffsetField:
    """The plot's light field as seen from one tree (in its own coordinates)."""

    def __init__(self, field, offset):
        self.f = field
        self.off = np.asarray(offset, float)
        self.p, self.S, self.lo, self.periodic = field.p, field.S, field.lo, field.periodic

    def shadow_at_voxel(self, pos):
        return self.f.shadow_at_voxel(pos + self.off)

    def exposure(self, pos, self_weight, own_shade=None):
        return self.f.exposure(pos + self.off, self_weight, own_shade)

    def sample(self, pts):
        return self.f.sample(pts + self.off)

    def optimal_direction(self, pos, heading):
        return self.f.optimal_direction(pos + self.off, heading)


class Plot:
    def __init__(self, species, environment, make_soil, n_final: int = 25, seed: int = 1, mode: str = "managed"):
        pp = species.plot
        st = species.stand
        stages = sorted(st.thinning, key=lambda s: float(s.from_height_m))
        self.stages = [(float(s.from_height_m), float(s.stems_per_ha)) for s in stages]
        self.area = n_final / self.stages[-1][1] * 1e4
        rng = np.random.default_rng([seed, 31337])
        n0 = int(round(self.stages[0][1] * self.area / 1e4))
        L = math.sqrt(self.area)
        dmin = float(st.min_distance) * math.sqrt(1e4 / self.stages[0][1])
        pts = []
        while len(pts) < n0:
            q = rng.uniform(-L / 2, L / 2, 2)
            d = np.abs(np.array(pts) - q) if pts else np.zeros((0, 2))
            d = np.minimum(d, L - d)
            if not len(d) or (np.hypot(d[:, 0], d[:, 1]) >= dmin).all():
                pts.append(q)
        self.trees, self.info = [], []
        for k in range(n0):
            sp_k = copy.deepcopy(species)
            vigour = float(math.exp(rng.normal(0.0, float(pp.vigour_sd))))
            sp_k.resource.alpha = float(sp_k.resource.alpha) * vigour
            g = int(rng.choice(np.asarray(pp.germination_years, int), p=np.asarray(pp.germination_weights, float)))
            m = GrowthModel(sp_k, environment, seed * 1000 + k, stand=True, soil=make_soil(),
                            soil_frame=(np.array([pts[k][0], pts[k][1], 0.0]), seed))
            self.trees.append(m)
            self.info.append({"id": k, "x": float(pts[k][0]), "y": float(pts[k][1]), "germination": g,
                              "vigour": round(vigour, 4), "seed": seed * 1000 + k, "removed": None})
        self.alive = list(range(n0))
        self.light = self.trees[0].light
        vs = self.light.vs
        nx = max(1, int(round(L / vs)))
        self.L = nx * vs
        self.cell = (-0.5 * self.L, -0.5 * self.L, nx, nx)
        self.seed = int(seed)
        self.soil = None
        self._make_soil()
        self.year = 0
        self.stats = []
        self.mode = mode
        self.on_finish = None

    def _offset(self, k):
        return np.array([self.info[k]["x"], self.info[k]["y"], 0.0])

    def _make_soil(self):
        """The plot's one soil (stones, rootable depth, moisture), laid out
        once with the plot seed; each tree reads it at its own offset."""
        m0 = self.trees[self.alive[0]]
        if m0.roots is None:
            return
        seed = getattr(self, "seed", self.info[0]["seed"] // 1000)   # plots pickled before the shared soil
        self.soil = SharedSoil(m0.soil, m0.sp.roots, m0.light.vs, self.cell, seed)
        for k in self.alive:
            self.trees[k].roots.frame = (self._offset(k), seed)

    def step(self):
        t = self.year + 1
        if getattr(self, "soil", None) is None:
            self._make_soil()
        active = [k for k in self.alive if t > self.info[k]["germination"]]
        srcs, ws = [], []
        for k in active:
            _, _, _, _, src, w = self.trees[k].light_sources()
            if len(src):
                srcs.append(src + self._offset(k))
                ws.append(w)
        field = None
        if srcs:
            allp = np.concatenate(srcs)
            field = self.light.compute(allp, np.concatenate(ws), np.stack([allp.min(0), allp.max(0)]), periodic=self.cell)
        if self.soil is not None:
            # every tree's absorbing roots at the start of its season, in one field
            pts, ls = [], []
            for k in active:
                q, lq = self.trees[k].roots.absorbing(self.trees[k].year + 1)
                pts.append(q + self._offset(k))
                ls.append(lq)
            self.soil.update(np.concatenate(pts) if pts else np.zeros((0, 3)), np.concatenate(ls) if ls else np.zeros(0))
        for k in active:
            m = self.trees[k]
            m._plot_view = OffsetField(field, self._offset(k)) if field is not None else None
            m._plot_soil = self.soil
            m.step()
            m._plot_view = m._plot_soil = None
        self.year = t
        if self.mode == "natural":
            self._die(active)
        else:
            self._thin()
        self.stats.append(self.measure())

    def _dbh(self, k):
        d = self.trees[k].dbh_m()
        return 0.0 if d is None else d

    def _thin(self):
        """Thinning from below to the stem density of the programme stage
        reached by the dominant height (mean of the 100 largest per ha)."""
        if not self.alive:
            return
        n_dom = max(1, int(round(100 * self.area / 1e4)))
        h = sorted((self.trees[k].stats[-1]["height_m"] for k in self.alive), reverse=True)[:n_dom]
        hdom = float(np.mean(h))
        target = None
        for h0, dens in self.stages:
            if hdom >= h0:
                target = int(round(dens * self.area / 1e4))
        if target is None or len(self.alive) <= target:
            return
        order = sorted(self.alive, key=self._dbh)
        for k in order[: len(self.alive) - target]:
            self._finish(k, "thinned")

    def _die(self, active):
        """Natural mode: a tree whose carbon no longer pays its upkeep dies."""
        for k in active:
            c = getattr(self.trees[k], "carbon", None)
            if c and c.get("shoot", 0.0) < c.get("upkeep", 0.0):
                self._finish(k, "died")

    def _finish(self, k, cause):
        self.alive.remove(k)
        self.info[k]["removed"] = self.year
        self.info[k]["cause"] = cause
        if self.on_finish is not None:
            self.on_finish(k, cause)
        self.trees[k] = None              # free its memory

    # -- checkpoints ------------------------------------------------------
    def checkpoint(self, out_dir) -> None:
        """Move every living tree's history to out_dir/tree_XXX/ and pickle
        the plot to out_dir/checkpoint.pkl (written atomically)."""
        out = Path(out_dir)
        for k in self.alive:
            m = self.trees[k]
            m._plot_view = None
            m._field = None
            m.spill_history(out / f"tree_{k:03d}" / "history")
            m.tree.trim()
            if m.roots is not None:
                m.roots.tree.trim()
        hook, self.on_finish = self.on_finish, None
        tmp = out / "checkpoint.pkl.tmp"
        with open(tmp, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, out / "checkpoint.pkl")
        self.on_finish = hook

    @staticmethod
    def resume(out_dir) -> "Plot":
        with open(Path(out_dir) / "checkpoint.pkl", "rb") as f:
            return pickle.load(f)

    def measure(self):
        d = np.array([self._dbh(k) * 100 for k in self.alive])
        h = np.array([self.trees[k].stats[-1]["height_m"] for k in self.alive])
        la = sum(self.trees[k].stats[-1]["leaf_area_m2"] for k in self.alive)
        dead = sum(1 for i in self.info if i.get("cause") == "died")
        return {"year": self.year, "trees": len(self.alive), "stems_per_ha": round(len(self.alive) / self.area * 1e4),
                "died_total": dead,
                "dbh_mean_cm": round(float(d.mean()), 2), "dbh_sd_cm": round(float(d.std()), 2),
                "dbh_min_cm": round(float(d.min()), 2), "dbh_max_cm": round(float(d.max()), 2),
                "height_mean_m": round(float(h.mean()), 2), "height_max_m": round(float(h.max()), 2),
                "lai": round(la / self.area, 3)}
