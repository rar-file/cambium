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

Settings, all off by default: ``mortality.enabled`` adds mortality that answers
to crowding and vigour in natural mode (treegen/thinning.py);
``plot.natural_start.enabled`` starts at a chosen density on a chosen rectangle
of ground, the first trees optionally on one part of it; ``plot.stand_measures``
adds basal area, top height, gap fraction and new trees to the yearly stats.
``lean=True`` (a way of running, for plots with no tree files) keeps only what
growth reads back, and shares what trees needn't each hold.
"""
from __future__ import annotations

import copy
import math
import os
import pickle
from pathlib import Path

import numpy as np

from .growth import GrowthModel
from .light import SUBCANOPY_LIGHT_HEIGHTS_M
from .regeneration import Regeneration, SpreadRegeneration
from .roots import SharedSoil
from .thinning import Mortality, gap_fraction, over_bark_cm, top_height_m

# a tree that dies of no carbon within this many years of its own age is
# logged as "failed to establish" (a label, not a parameter of the model)
ESTABLISHMENT_YEARS = 5


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


def sweep_after_stop(out_dir, tree_years: dict) -> list:
    """Resuming from a checkpoint: remove what a stopped run left that the checkpoint doesn't
    know about.  A half-written pickle; history from a later checkpoint that never finished,
    which would otherwise be read back as extra years; and the history of trees the checkpoint
    counts as dead.  Returns what it removed.  tree_years: each tree the checkpoint counts as
    alive -> its own age there.  History files are named by a tree's own age, which runs behind
    the plot's year for a tree that germinated late.  A tree that died after the checkpoint
    still counts as alive here, and keeps its history: it has to die again."""
    out = Path(out_dir)
    removed = []
    tmp = out / "checkpoint.pkl.tmp"
    if tmp.exists():
        tmp.unlink()
        removed.append(tmp)
    for folder in out.glob("tree_*/history"):
        k = int(folder.parent.name.split("_")[1])
        for f in folder.glob("history_*"):
            digits = f.name[len("history_"):].split(".")[0]
            if k not in tree_years or not digits.isdigit() or int(digits) > tree_years[k]:
                f.unlink()
                removed.append(f)
    return removed


class Plot:
    def __init__(self, species, environment, make_soil, n_final: int = 25, seed: int = 1, mode: str = "managed", lean: bool = False):
        pp = species.plot
        st = species.stand
        stages = sorted(st.thinning, key=lambda s: float(s.from_height_m))
        self.stages = [(float(s.from_height_m), float(s.stems_per_ha)) for s in stages]
        self.lean = bool(lean)
        rng = np.random.default_rng([seed, 31337])
        start = getattr(pp, "natural_start", None)
        if start is not None and bool(getattr(start, "enabled", False)):
            pts, n0, L, Lx, Ly = self._natural_start(start, rng, float(st.min_distance))
        else:
            self.area = n_final / self.stages[-1][1] * 1e4
            n0 = int(round(self.stages[0][1] * self.area / 1e4))
            L = math.sqrt(self.area)
            Lx = Ly = None
            dmin = float(st.min_distance) * math.sqrt(1e4 / self.stages[0][1])
            pts = []
            while len(pts) < n0:
                q = rng.uniform(-L / 2, L / 2, 2)
                d = np.abs(np.array(pts) - q) if pts else np.zeros((0, 2))
                d = np.minimum(d, L - d)
                if not len(d) or (np.hypot(d[:, 0], d[:, 1]) >= dmin).all():
                    pts.append(q)
        self.trees, self.info = [], []
        shared_soil = make_soil() if self.lean else None
        for k in range(n0):
            sp_k = self._tree_species(species)
            vigour = float(math.exp(rng.normal(0.0, float(pp.vigour_sd))))
            sp_k.resource.alpha = float(sp_k.resource.alpha) * vigour
            g = int(rng.choice(np.asarray(pp.germination_years, int), p=np.asarray(pp.germination_weights, float)))
            m = GrowthModel(sp_k, environment, seed * 1000 + k, stand=True, soil=shared_soil or make_soil(),
                            soil_frame=(np.array([pts[k][0], pts[k][1], 0.0]), seed), lean=self.lean)
            if self.lean:
                self._lighten(m, self.trees[0].light if self.trees else m.light)
            # the stand grows up on ground bared by the disturbance at plot
            # year 0 (tree year -g); the field layer grows back over it
            m.field_layer_exposed = -g
            self.trees.append(m)
            self.info.append({"id": k, "x": float(pts[k][0]), "y": float(pts[k][1]), "germination": g,
                              "vigour": round(vigour, 4), "seed": seed * 1000 + k, "removed": None})
        self.alive = list(range(n0))
        self.light = self.trees[0].light
        vs = self.light.vs
        if Lx is None:
            nx = max(1, int(round(L / vs)))
            self.L = nx * vs
            self.cell = (-0.5 * self.L, -0.5 * self.L, nx, nx)
        else:
            # a rectangle of ground, whole voxels each way
            nx, ny = max(1, int(round(Lx / vs))), max(1, int(round(Ly / vs)))
            self.Lx, self.Ly = nx * vs, ny * vs
            self.L = self.Lx
            self.cell = (-0.5 * self.Lx, -0.5 * self.Ly, nx, ny)
        self.seed = int(seed)
        self.soil = None
        self._make_soil()
        self.year = 0
        self.stats = []
        self.mode = mode
        self.on_finish = None
        # the template and environment new trees are made from (regeneration)
        self.species, self.environment = species, environment
        self.regen = None
        self.measures = bool(getattr(pp, "stand_measures", False))
        self.mort = None
        mp = getattr(species, "mortality", None)
        if mp is not None and bool(getattr(mp, "enabled", False)):
            lx, ly = self._sides()
            self.mort = Mortality(mp, lx, ly, self.cell[0], self.cell[1])
            self.mort_rng = np.random.default_rng([seed, 5381])
            self.rings = {}

    def _sides(self):
        """The plot's two sides (m)."""
        return (self.Lx, self.Ly) if getattr(self, "Lx", None) is not None else (self.L, self.L)

    def _natural_start(self, start, rng, min_distance):
        """Trees at a natural density on a rectangle of ground, repeating at
        its edges; with ``patch_x_m``, only in the first stretch of x, the rest
        being open ground to spread over."""
        lx = float(getattr(start, "side_x_m", None) or math.sqrt(float(start.area_m2)))
        ly = float(getattr(start, "side_y_m", None) or lx)
        self.area = lx * ly
        patch = float(getattr(start, "patch_x_m", None) or lx)
        density = float(start.stems_per_ha)
        n0 = max(1, int(round(density * patch * ly / 1e4)))
        dmin = min_distance * math.sqrt(1e4 / density)
        pts = []
        while len(pts) < n0:
            q = np.array([rng.uniform(-lx / 2, -lx / 2 + patch), rng.uniform(-ly / 2, ly / 2)])
            d = np.abs(np.array(pts) - q) if pts else np.zeros((0, 2))
            d = np.minimum(d, np.array([lx, ly]) - d)
            if not len(d) or (np.hypot(d[:, 0], d[:, 1]) >= dmin).all():
                pts.append(q)
        return pts, n0, math.sqrt(self.area), lx, ly

    def _tree_species(self, species):
        """A tree's own copy of the species: all of it, or (lean) only the part
        that differs between trees."""
        if not getattr(self, "lean", False):
            return copy.deepcopy(species)
        sp = copy.copy(species)
        sp.resource = copy.copy(species.resource)
        return sp

    @staticmethod
    def _lighten(m, light):
        """What a lean plot's trees needn't hold each: one light model for all,
        no neighbour tables, since a plot's neighbours are real, and no room for
        4096 nodes in a seedling that may die at three (2 MB a tree at the start)."""
        m.light = light
        m._clone_angle = {}
        m._stand_map = None
        m.tree.trim()
        if m.roots is not None:
            m.roots.tree.trim()

    def _offset(self, k):
        return np.array([self.info[k]["x"], self.info[k]["y"], 0.0])

    def _make_soil(self):
        """The plot's one soil (stones, rootable depth, moisture), laid out
        once with the plot seed; each tree reads it at its own offset."""
        m0 = self.trees[self.alive[0]]
        if m0.roots is None:
            return
        self.seed = seed = getattr(self, "seed", self.info[0]["seed"] // 1000)   # plots pickled before the shared soil
        self.soil = SharedSoil(m0.soil, m0.sp.roots, m0.light.vs, self.cell, seed)
        for k in self.alive:
            self.trees[k].roots.frame = (self._offset(k), seed)

    def enable_regeneration(self, species=None, environment=None):
        """Natural regeneration from now on (treegen/regeneration.py).  Plots
        pickled before regeneration existed take the species template and
        environment here."""
        if species is not None:
            self.species = species
        if environment is not None:
            self.environment = environment
        if getattr(self, "soil", None) is None:
            self._make_soil()
        spread = getattr(self.species.regeneration, "spread", None)
        if spread is not None and bool(getattr(spread, "enabled", False)):
            self.regen = SpreadRegeneration(self.species.regeneration, self.species.bud_fate.short_shoot_survival_light,
                                            self.trees[self.alive[0]].soil, *self._sides(), self.seed)
        else:
            self.regen = Regeneration(self.species.regeneration, self.species.bud_fate.short_shoot_survival_light,
                                      self.trees[self.alive[0]].soil, self.L, self.seed)
        if self.year > 0:
            # switched on in a grown stand: the exposed mineral soil of a stand
            # long past its disturbance (new exposure = cover each year)
            self.regen.mineral[:] = self.regen.equilibrium_mineral()

    def _regenerate(self, field):
        """Seed rain from the living trees onto the ground grid, germination
        where the light and seedbed allow, and this year's recruits."""
        R = self.regen
        xy, seeds = [], []
        for k in self.alive:
            f = R.fecundity(self._dbh(k), self.trees[k].year)
            if f > 0.0:
                xy.append(self._offset(k)[:2])
                seeds.append(f)
        pts = np.stack([R.cx.ravel(), R.cy.ravel(), np.full(R.cx.size, 0.1)], 1)
        light = np.ones(len(pts))
        if field is not None:
            # the light grid ends at the lowest leaves; below them the shade
            # carries on unchanged to the ground (stand: no fading with depth)
            q = pts.copy()
            q[:, 2] = np.maximum(q[:, 2], (field.lo[2] + 0.5) * self.light.vs)
            light = np.exp(-field.sample(q) / self.light.C)
        # what a full field layer leaves at 0.1 m (bared mineral soil has none)
        s = self.trees[self.alive[0]].soil
        h = float(getattr(s, "herb_height", 0.0) or 0.0)
        field_layer = math.exp(-float(s.herb_extinction) * float(s.herb_lai) * max(1.0 - 0.1 / h, 0.0)) if h > 0.0 else 1.0
        occupied = np.zeros(R.cx.shape, bool)
        i, j = R._cell(np.array([[self.info[k]["x"], self.info[k]["y"]] for k in self.alive]))
        occupied[i, j] = True
        spreading = isinstance(R, SpreadRegeneration)
        if spreading:
            # what a seed's way out depends on: the big trees around its source
            big = [self._offset(k)[:2] for k in self.alive if self._dbh(k) * 100.0 >= float(R.p.spread.tree_dbh_cm)]
            R.count_trees(np.array(big).reshape(-1, 2))
        ground = light.reshape(R.cx.shape)
        for x, y, mineral in R.step(np.array(xy).reshape(-1, 2), np.array(seeds), ground, field_layer, occupied):
            self._recruit(float(x), float(y), mineral)
            if spreading:
                i, j = R._cell(np.array([[x, y]]))
                self.info[-1]["light_at_birth"] = round(float(ground[i[0], j[0]]), 3)

    def _recruit(self, x, y, mineral=True):
        """A new tree from this year's seed; it germinates next spring, on
        bared mineral soil (the field layer then grows back over it) or on
        the undisturbed organic layer under a full field layer."""
        k = len(self.trees)
        sp_k = self._tree_species(self.species)
        vigour = float(math.exp(self.regen.rng.normal(0.0, float(self.species.plot.vigour_sd))))
        sp_k.resource.alpha = float(sp_k.resource.alpha) * vigour
        s = self.seed * 1_000_000 + k
        lean = getattr(self, "lean", False)
        m = GrowthModel(sp_k, self.environment, s, stand=True, soil=self.trees[self.alive[0]].soil,
                        soil_frame=(np.array([x, y, 0.0]), self.seed), lean=lean)
        if lean:
            self._lighten(m, self.light)
        m.field_layer_exposed = 0 if mineral else None
        self.trees.append(m)
        self.info.append({"id": k, "x": x, "y": y, "germination": self.year, "vigour": round(vigour, 4), "seed": s,
                          "removed": None, "recruit": True, "on_mineral_soil": bool(mineral)})
        self.alive.append(k)

    def step(self):
        t = self.year + 1
        self._lost_this_year = 0.0
        if getattr(self, "soil", None) is None:
            self._make_soil()
        active = [k for k in self.alive if t > self.info[k]["germination"]]
        srcs, ws = [], []
        for k in active:
            _, _, _, _, src, w = self.trees[k].light_sources()
            if len(src):
                srcs.append(src + self._offset(k))
                ws.append(w)
        woody_cfg = bool(getattr(getattr(self.species.light, "woody_shade", None), "enabled", False))
        k_wood = float(getattr(self.species.light.woody_shade, "k_wood", 0.40)) if woody_cfg else 0.40
        wood_pts, wood_areas = [], []
        if woody_cfg:
            for k in active:
                wpos, warea = self.trees[k].wood_sources()
                if len(wpos):
                    wood_pts.append(wpos + self._offset(k))
                    wood_areas.append(warea)
        all_wpos = np.concatenate(wood_pts) if wood_pts else None
        all_warea = np.concatenate(wood_areas) if wood_areas else None
        field = None
        if srcs:
            allp = np.concatenate(srcs)
            pts_for_region = allp if all_wpos is None or len(all_wpos) == 0 else np.concatenate([allp, all_wpos])
            field = self.light.compute(allp, np.concatenate(ws), np.stack([pts_for_region.min(0), pts_for_region.max(0)]),
                                       periodic=self.cell, wood_pos=all_wpos, wood_area=all_warea, k_wood=k_wood,
                                       diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M)
        if getattr(self, "measures", False):
            lx, ly = self._sides()
            cfg = self.species.plot
            self._gap_fraction = gap_fraction(np.concatenate(srcs) if srcs else None, self.cell[0], self.cell[1], lx, ly,
                                              float(getattr(cfg, "gap_cell_m", 2.0)), float(getattr(cfg, "gap_above_m", 2.0)))
        # output only: light at the target's measurement heights under the canopy
        self._subcanopy_light = field.relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) if field is not None else None
        self._subcanopy_diffuse_light = field.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) if field is not None else None
        if self.soil is not None:
            # every tree's absorbing roots at the start of its season, in one field
            pts, ls = [], []
            for k in active:
                q, lq = self.trees[k].roots.absorbing(self.trees[k].year + 1)
                pts.append(q + self._offset(k))
                ls.append(lq)
            self.soil.update(np.concatenate(pts) if pts else np.zeros((0, 3)), np.concatenate(ls) if ls else np.zeros(0))
        h_canopy = max((self.trees[k].stats[-1]["height_m"] for k in active if self.trees[k].stats), default=0.0)
        for k in active:
            m = self.trees[k]
            m._plot_view = OffsetField(field, self._offset(k)) if field is not None else None
            m._plot_soil = self.soil
            m._plot_spacing = math.sqrt(self.area / max(len(self.alive), 1))
            # canopy top for the within-canopy wind profile (stem theory stage b)
            m._plot_canopy_height = h_canopy
            m.step()
            m._plot_view = m._plot_soil = None
        self.year = t
        self._starve(active)
        if self.mode == "natural":
            self._die([k for k in active if k in self.alive])
            if getattr(self, "mort", None) is not None:
                self._self_thin(active)
        else:
            self._thin()
        if getattr(self, "regen", None) is not None and self.alive:
            self._regenerate(field)
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

    def _starve(self, active):
        """Either mode: a tree that fixes no carbon two years running is dead
        (a seedling that never rooted has neither carbon nor upkeep, so the
        upkeep rule below never catches it).  In its first years
        (ESTABLISHMENT_YEARS of its own age, a label only) it failed to
        establish."""
        for k in active:
            c = getattr(self.trees[k], "carbon", None) or {}
            n = self.info[k].get("years_without_carbon", 0) + 1 if c.get("fixed", 0.0) <= 0.0 else 0
            self.info[k]["years_without_carbon"] = n
            if n >= 2:
                young = self.trees[k].year <= ESTABLISHMENT_YEARS
                self._finish(k, "failed to establish" if young else "no carbon")

    def _die(self, active):
        """Natural mode: a tree whose carbon no longer pays its upkeep (wood,
        leaf and fine-root maintenance and rebuilding its leaves) two years
        running dies.  After the first year it sheds the branches that ran
        their own deficit (before the next flush), so it dies only if what is
        left still cannot pay."""
        for k in active:
            c = getattr(self.trees[k], "carbon", None) or {}
            n = self.info[k].get("years_in_deficit", 0) + 1 if c and c.get("fixed", 0.0) < c.get("upkeep", 0.0) else 0
            self.info[k]["years_in_deficit"] = n
            if n >= 2:
                self._finish(k, "died")

    def _self_thin(self, active):
        """Natural mode, with ``mortality`` on: the hazards of treegen/thinning.py,
        drawn tree by tree.  Each tree's recent wood DBHs give its ring width."""
        M = self.mort
        alive = set(self.alive)
        now = [k for k in active if k in alive]
        if not now:
            return
        window = int(M.p.vigour.window_years)
        d = np.array([self._dbh(k) * 100.0 for k in now])
        rings = np.zeros(len(now))
        for n, k in enumerate(now):
            h = self.rings.setdefault(k, [0.0])
            if d[n] <= 0.0:
                h[:] = [0.0]
            else:
                h.append(float(d[n]))
                del h[:-(window + 1)]
            rings[n] = M.ring_mm(h)
        xy = np.array([self._offset(k)[:2] for k in now])
        age = np.array([self.trees[k].year for k in now], float)
        hz = M.hazards(xy, d, rings, age, float(self.year))
        self._rd_mean = float(hz["rd"].mean())
        for n, cause in M.draw(hz, self.mort_rng):
            self._finish(now[n], cause)

    def open_gap(self, x: float, y: float, radius: float) -> int:
        """A windthrow: every tree within radius of (x, y) goes this year, across the plot's
        repeat, and uprooting bares soil there.  Returns how many went."""
        lx, ly = self._sides()
        gone = 0
        for k in list(self.alive):
            dx, dy = abs(self.info[k]["x"] - x), abs(self.info[k]["y"] - y)
            if math.hypot(min(dx, lx - dx), min(dy, ly - dy)) <= radius:
                self._finish(k, "windthrow")
                gone += 1
        if isinstance(getattr(self, "regen", None), SpreadRegeneration):
            self.regen.bare_circle(x, y, radius, float(self.species.regeneration.spread.windthrow_mineral))
        return gone

    def _finish(self, k, cause):
        if getattr(self, "measures", False):
            ob = float(over_bark_cm(self._dbh(k) * 100.0, self.species.mortality.bark_double_mm))
            self._lost_this_year = getattr(self, "_lost_this_year", 0.0) + math.pi / 4.0 * (ob / 100.0) ** 2
        self.alive.remove(k)
        if getattr(self, "mort", None) is not None:
            self.rings.pop(k, None)
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
        """Carry on from a stopped run in this folder.  This deletes what the stopped run left
        after its last checkpoint, so never call it on the folder of a run that's still going."""
        with open(Path(out_dir) / "checkpoint.pkl", "rb") as f:
            plot = pickle.load(f)
        sweep_after_stop(out_dir, {k: plot.trees[k].year for k in plot.alive})
        return plot

    def _stand_row(self, d, h):
        """The stand as a forester reads it: basal area over bark, quadratic
        mean diameter, top height (the 100 thickest stems a hectare), gap
        fraction, what came and went this year, and for ground with a seed
        source at one end, stems and seedlings along it."""
        ob = over_bark_cm(d, self.species.mortality.bark_double_mm)
        stems = ob[ob > 0.0]    # past breast height, as a forester counts them
        row = {"basal_area_ob_m2_ha": round(float(np.sum(np.pi / 4.0 * (ob / 100.0) ** 2)) / self.area * 1e4, 2),
               "stems_bh_per_ha": round(len(stems) / self.area * 1e4),
               "dg_ob_cm": round(100.0 * math.sqrt(float(np.mean((stems / 100.0) ** 2))), 2) if len(stems) else 0.0,
               "top_height_m": round(top_height_m(ob, h, self.area), 2),
               "gap_fraction": round(getattr(self, "_gap_fraction", 1.0), 3),
               "new_trees": sum(1 for i in self.info if i.get("recruit") and i["germination"] == self.year),
               "basal_area_lost_m2_ha": round(getattr(self, "_lost_this_year", 0.0) / self.area * 1e4, 3),
               "dead_this_year": {}}
        for i in self.info:
            if i.get("removed") == self.year:
                row["dead_this_year"][i["cause"]] = row["dead_this_year"].get(i["cause"], 0) + 1
        if getattr(self, "mort", None) is not None:
            row["relative_density"] = round(getattr(self, "_rd_mean", 0.0), 3)
            rings = [self.mort.ring_mm(self.rings[k]) for k in self.alive if k in self.rings and self.rings[k][-1] > 0.0]
            # the share of stems that have all but stopped laying wood
            row["stopped_share"] = round(sum(1 for r in rings if r < 0.1) / len(rings), 3) if rings else 0.0
        start = getattr(self.species.plot, "natural_start", None)
        if start is not None and getattr(start, "patch_x_m", None):
            # 10 m slices along x, from the source end
            lx, _ = self._sides()
            xs = np.array([self.info[k]["x"] for k in self.alive]) + 0.5 * lx
            bins = np.arange(0.0, lx + 10.0, 10.0)
            row["stems_along_x"] = np.histogram(xs[h >= 2.0], bins=bins)[0].tolist()
            row["seedlings_along_x"] = np.histogram(xs[h < 2.0], bins=bins)[0].tolist()
        return row

    def measure(self):
        if not self.alive:
            return {"year": self.year, "trees": 0, "stems_per_ha": 0,
                    "died_total": sum(1 for i in self.info if i.get("cause") not in (None, "thinned"))}
        d = np.array([self._dbh(k) * 100 for k in self.alive])
        h = np.array([self.trees[k].stats[-1]["height_m"] for k in self.alive])
        la = sum(self.trees[k].stats[-1]["leaf_area_m2"] for k in self.alive)
        dead = sum(1 for i in self.info if i.get("cause") not in (None, "thinned"))
        row = {"year": self.year, "trees": len(self.alive), "stems_per_ha": round(len(self.alive) / self.area * 1e4),
               "died_total": dead,
               "dbh_mean_cm": round(float(d.mean()), 2), "dbh_sd_cm": round(float(d.std()), 2),
               "dbh_min_cm": round(float(d.min()), 2), "dbh_max_cm": round(float(d.max()), 2),
               "height_mean_m": round(float(h.mean()), 2), "height_max_m": round(float(h.max()), 2),
               "lai": round(la / self.area, 3),
               # relative light (%) at 1.0-2.0 m under the canopy this season
               # (light.SUBCANOPY_LIGHT_HEIGHTS_M)
               "subcanopy_light_pct": (round(100.0 * self._subcanopy_light, 2)
                                       if getattr(self, "_subcanopy_light", None) is not None else None),
               # the same under the sky alone (overcast), the light target's measure
               "subcanopy_diffuse_light_pct": (round(100.0 * self._subcanopy_diffuse_light, 2)
                                               if getattr(self, "_subcanopy_diffuse_light", None) is not None else None)}
        if getattr(self, "measures", False):
            row.update(self._stand_row(d, h))
        if getattr(self, "regen", None) is not None:
            # everything above counts the recruits too
            row["recruits_alive"] = sum(1 for k in self.alive if self.info[k].get("recruit"))
            row.update({k: round(v, 4) if isinstance(v, float) else v for k, v in self.regen.last.items()})
        return row
