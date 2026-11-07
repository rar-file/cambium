"""Bud-based self-organising tree growth.

Core: the model of Palubicki et al. (2009), "Self-organizing tree models for
image synthesis", ACM TOG 28(3):58, one growth cycle per year:

1. local environment of every bud: light exposure Q and the direction of
   least shadow V, by shadow propagation on a voxel grid (``light.py``);
2. shedding of lateral branches whose light per internode Q/N is below a
   threshold (evaluated at the start of the season, so a shed branch does not
   flush first);
3. bud fate by the extended Borchert-Honda model (Borchert & Honda 1984): a
   basipetal pass accumulates Q, an acropetal pass splits v_base = alpha*Q_base
   at every node with the weight lambda;
4. shoot extension: a bud with v >= the long-shoot threshold forms
   n = floor(v) metamers of length l0 * v / n, oriented D' = D + xi*V + eta*T;
5. branch radii from the pipe model r_parent^g = sum r_child^g.

One model metamer is one real birch node (internode + leaf + axillary bud).

Extensions, each tied to a published mechanism (parameters and sources are in
the species YAML):

* lambda split into apical dominance over buds and apical control over
  established branches, the latter weakening with age (Brown et al. 1967;
  Wilson 2000);
* tropism towards a gravitropic set-point angle per branch order (Digby &
  Firn 1995);
* gravimorphism (Wareing & Nasr 1961): bud orientation weights the BH split;
* physiological ageing of meristems (Barthelemy & Caraglio 2007);
* maintenance and transport costs in the acropetal pass (Perttunen et al.
  1996; Ryan & Yoder 1997);
* hydraulic limitation of expansion with height (Koch et al. 2004);
* long vs. short shoots (Maillette 1982; Clausen & Kozlowski 1966);
* sympodial long shoots;
* branch mechanics (``mechanics.py``): every year each internode bends under
  the added load it carries, stiffness ~ r^4, and thick wood corrects back
  towards its set-point through reaction wood.  The pendulous habit of
  silver birch is the species trait "thin shoots are soft and cannot
  correct", and the hanging twigs come out of the load;
* stand mode: neighbour trees as shadow volumes, copies of the focal crown
  on a hexagonal lattice whose spacing follows a thinning schedule, in a
  periodic light grid so the stand has no edge.

Coordinates: z up, metres.  Year 0 is the seed; year t is the t-th season.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import fast, hydraulics, mechanics
from .compact import compact
from .light import SUBCANOPY_LIGHT_HEIGHTS_M, ShadowPropagation
from .reference import eriksson_1997_height
from .roots import RootSystem
from .structure import Tree, _normalize, _perpendicular

UP = np.array([0.0, 0.0, 1.0])

# lateral bud states
LAT_NONE, LAT_DORMANT, LAT_SPUR, LAT_USED, LAT_DEAD = 0, 1, 2, 3, 4

HANGING_DZ = -0.5  # an internode pointing more than 30 deg below horizontal hangs


@dataclass
class SpurLog:
    node: list
    birth: list
    death: list
    leaf_area: list = None   # m2 per leaf, last season
    lma: list = None         # g m-2, last season


class GrowthModel:
    def __init__(self, species, environment, seed: int, stand: bool = False, keyframe_step: int = 5, soil=None,
                 soil_frame=None, lean: bool = False):
        self.sp = species
        # lean: keep only what growth reads back and what the scorecard scores
        # (no radius history, no keyframes, fewer yearly stats).  The tree grows
        # the same; it can't be exported afterwards (tests/test_lean.py).
        self.lean = bool(lean)
        self.soil = soil
        self.seed = int(seed)
        self.stand = bool(stand)
        self.keyframe_step = int(keyframe_step)
        self.rng = np.random.default_rng(self.seed)
        st = species.stand
        self.light = ShadowPropagation(fast.light_environment(species, environment), species.light,
                                       float(st.shadow_horizontal_reach) if self.stand else None,
                                       (float(st.shadow_decay_length) if getattr(st, "shadow_decay_length", None) else None)
                                       if self.stand else None)
        self.gamma = float(species.pipe_model.exponent)
        self.tip_pipe = float(species.pipe_model.tip_radius) ** self.gamma
        self.spur_pipe = float(species.pipe_model.spur_radius) ** self.gamma
        self.l0 = float(species.shoot.internode_length)
        self.tree = Tree()
        self.axis_phase: list[float] = []
        self.spurs = SpurLog([], [], [], [], [])
        self.spur_rec = {}  # node -> index into spur log for the live spur
        self.year = 0
        self.radius_history: list[np.ndarray] = []
        self.keyframes: dict[int, np.ndarray] = {}
        self.stats: list[dict] = []
        self.diag: dict = {}
        self.water: dict = {}
        self._psi = None
        self._starving = np.zeros(0, np.int64)   # limbs in carbon deficit, shed next season
        self._established = np.zeros(0, bool)       # limbs that have become net carbon exporters
        self._limb_draw = np.zeros(0)               # carbon each young limb drew from the stem pool
        self.reit = {}            # reiterated limbs: first node -> (year, physiological age kept)
        self.reit_axes = set()    # axis ids of their main axes (orthotropic from then on)
        self.leader_axes = {0}    # the stem and the laterals that replaced a lost leader
        self._relay_buds = {}     # lateral bud node -> stem node whose lost leader it replaces
        self._relay_first = {}    # new replacement axis -> that stem node (relay set on its first node)
        self.leader_losses = []   # (year, height, cause)
        self._dmg_rng = np.random.default_rng([self.seed, 104729])
        self._lead_peak = 0.0     # largest yearly resource the leader's bud has received
        self.loss_of_dominance_year = None
        # the seed germinated on soil bared in this tree year (the field layer
        # grows back over it); a plot resets it, None = undisturbed ground
        self.field_layer_exposed = 0
        # soil_frame: (offset, soil seed) of this tree in a plot's shared soil
        self.roots = RootSystem(species.roots, soil, seed, self.light.vs, soil_frame) if soil is not None else None
        if self.roots is not None:
            self.roots.lean = self.lean
            self.roots.keep_soil_grids = fast.on(species, "keep_soil_grids")
        self.tree.quick_levels = fast.on(species, "quick_levels")
        if self.roots is not None:
            self.roots.tree.quick_levels = self.tree.quick_levels
        self.light.fast_rows = fast.on(species, "light_rows")
        self.light.fast_layers = fast.on(species, "light_layers") or self.light.fast_rows
        if self.stand:
            nrng = np.random.default_rng([self.seed, 7919])
            k = int(st.cell_trees)
            self._clone_angle = {(i, j): float(nrng.uniform(0, 2 * np.pi))
                                 for j in range(4 * k) for i in range(k)}
            if str(getattr(st, "layout", "lattice")) == "random":
                self._stand_map = self._random_stand_map(np.random.default_rng([self.seed, 7920]))
        self._plant_seed()

    # ------------------------------------------------------------------
    def _plant_seed(self):
        T = self.tree
        i = T.alloc(1)
        germ = getattr(self.sp, "germination", None)
        germ_on = germ is not None and bool(getattr(germ, "enabled", False))
        h0 = float(getattr(germ, "hypocotyl_height_m", 0.015)) if germ_on else 0.0
        T.pos[i] = np.array([0.0, 0.0, h0])
        T.dir[i] = UP
        T.ref[i] = np.array([1.0, 0.0, 0.0])
        T.parent[i] = -1
        T.term[i] = 1
        T.term_dir[i] = UP
        T.leaf_scale[i] = 1.0
        T.lat[i] = LAT_NONE
        T.axis[i] = 0
        self.axis_phase.append(float(self.rng.uniform(0.0, 2.0 * np.pi)))
        self._update_radii()
        if self.roots is not None:
            # the radicle: the seedling starts with a short taproot
            self.roots.step(0, float(self.sp.roots.radicle_segments))
            self._update_roots(0)
        if not self.lean:
            self.keyframes[0] = T.pos[: T.n].astype(np.float32).copy()
        self.stats.append(self.measure())

    def _scaffold_vigour(self, t: int, nodes: np.ndarray) -> np.ndarray:
        """Physiological ageing of meristems (Barthelemy & Caraglio 2007):
        buds on a first-order branch and its offshoots lose sink strength as
        that branch ages; buds on the stem age with the tree, more slowly.
        The slow decline of the stem is the loss of apical control that
        rounds off an old crown."""
        T = self.tree
        r = self.sp.resource
        born = T.scaffold_birth[nodes].astype(float)
        age = np.maximum(t - born, 0.0)
        branch_age = age / float(r.branch_aging_years)
        if bool(getattr(r, "limbs_inherit_stem_age", False)):
            # a limb's meristems start at the physiological age the stem
            # had when it made them (Barthelemy & Caraglio 2007): a limb born
            # high on an old stem is not younger than the leader
            branch_age = branch_age + np.maximum(born, 0.0) / float(r.stem_aging_years)
        if self.reit:
            # a reiterated complex is partly rejuvenated and from then on ages
            # like the trunk it reproduces
            keys = np.fromiter(self.reit.keys(), np.int64)
            sc = T.scaffold[nodes].astype(np.int64)
            hit = np.isin(sc, keys)
            if hit.any():
                ty = np.array([self.reit[k][0] for k in sc[hit]], float)
                a0 = np.array([self.reit[k][1] for k in sc[hit]], float)
                branch_age = branch_age.copy()
                branch_age[hit] = a0 + (t - ty) / float(r.stem_aging_years)
        branch = np.exp(-branch_age)
        stem = math.exp(-t / float(r.stem_aging_years))
        is_stem = (T.order[nodes] == 0) | np.isin(T.axis[nodes], np.fromiter(self.leader_axes, np.int64))
        return np.where(is_stem, stem, branch)

    def _stem_posture_target(self, n: int):
        """Posture target of the stem inside the crown: tilted towards the
        brighter side of the crown by the balance of the stem's phototropism
        and gravitropism (whole-tree phototropism, Loehle 1986), so reaction
        wood straightens it towards that, not towards vertical.  None if off."""
        cl = getattr(self, "_crown_light", None)
        has_cl = cl is not None and cl.any()
        if not has_cl and len(self.leader_axes) == 1:
            return None
        T = self.tree
        tr = self.sp.tropism
        ratio = float(tr.phototropism_per_m[0]) / float(tr.gravitropism_per_m[0])
        tgt = np.array([0.0, 0.0, 1.0]) + (ratio * cl if has_cl else 0.0)
        tgt /= np.linalg.norm(tgt)
        out = np.full((n, 3), np.nan)
        if has_cl:
            stem = T.trunk_chain(self.leader_axes)
            cb = (self.stats[-1].get("crown_base_height_m") if self.stats else None) or 0.0
            out[stem[T.pos[stem, 2] >= cb]] = tgt
        if len(self.leader_axes) > 1:
            # replacement leaders keep the stem's upright target, not the limbs' 43 deg
            la = np.isin(T.axis[:n], np.fromiter(self.leader_axes - {0}, np.int64)) & (T.order[:n] >= 1)
            out[la] = tgt
        return out

    def light_sources(self):
        """This season's leafy buds and their leaf weights (shadow sources)."""
        T = self.tree
        n0 = T.n
        alive = T.death[:n0] < 0
        term_nodes = np.nonzero(alive & (T.term[:n0] == 1))[0]
        lat_state = T.lat[:n0]
        lat_nodes = np.nonzero(alive & ((lat_state == LAT_DORMANT) | (lat_state == LAT_SPUR)))[0]
        fw = self.sp.light.foliage_weight
        # leaves per bud; leaf size shrinks with the same turgor limit that
        # shortens the internode (Koch et al. 2004)
        early = float(getattr(fw, "early_leaves", 0.0) or float(fw.spur))
        germ = getattr(self.sp, "germination", None)
        germ_on = germ is not None and bool(getattr(germ, "enabled", False))
        if n0 == 1 and germ_on:
            eff = float(getattr(germ, "first_year_effective_leaves", 0.20))
            w_term = np.full(len(term_nodes), eff) * T.leaf_scale[term_nodes] * self._size_rel(term_nodes)
        else:
            w_term = (float(fw.new_leaf) if n0 == 1 else early) * T.leaf_scale[term_nodes] * self._size_rel(term_nodes)
        ls = lat_state[lat_nodes]
        fresh = (T.lat_age[lat_nodes] == 0) & (~T.no_axil[lat_nodes]) & (T.term[lat_nodes] == 0)
        w_lat = T.leaf_scale[lat_nodes] * self._size_rel(lat_nodes) * np.where(
            ls == LAT_SPUR, float(fw.spur),
            np.where(fresh, early, float(fw.dormant)),
        )
        src = np.concatenate([T.pos[term_nodes], T.pos[lat_nodes]])
        return term_nodes, lat_nodes, w_term, w_lat, src, np.concatenate([w_term, w_lat])

    def _leaf_density_grid(self, src, src_w):
        """Exploring, M3a: this season's leaf area per m3 on a coarse grid, for a lateral-bud density control
        in the form of Sievanen et al. 2018 Eq. 11 (Ann. Bot. 122:423), whose fitted values aren't printed."""
        dc = getattr(self.sp.bud_fate, "density_control", None)
        if dc is None or not bool(dc.enabled) or len(src) == 0:
            return None
        cell = float(dc.cell_m)
        ijk = np.floor(src / cell).astype(np.int64)
        lo = ijk.min(0)
        shape = ijk.max(0) - lo + 1
        grid = np.zeros(shape)
        np.add.at(grid, tuple((ijk - lo).T), src_w * float(self.light.leaf_area) / cell ** 3)
        return grid, lo, cell

    def _density_after_growth(self, src, src_w, n_before):
        """Exploring, M3a: the same control, reckoned once the year's shoots have grown, with the
        leaves their new nodes will carry next spring counted in.  Counts the buds it removes."""
        dc = getattr(self.sp.bud_fate, "density_control", None)
        if dc is None or not bool(dc.enabled) or not bool(dc.after_growth) or self.tree.n <= n_before:
            return
        T = self.tree
        new = np.arange(n_before, T.n)
        side = new[T.term[new] == 0]
        if not len(side):
            return
        early = float(getattr(self.sp.light.foliage_weight, "early_leaves", 0.0) or 0.0)
        pos = np.concatenate([src, T.pos[side]])
        w = np.concatenate([src_w, np.full(len(side), early)])
        self._leaf_density = self._leaf_density_grid(pos, w)
        keep = self._bud_keep_chance(T.pos[side])
        drop = self.rng.random(len(side)) > keep
        T.no_axil[side[drop]] = True
        self.density_log = getattr(self, "density_log", [])
        self.density_log.append((int(self.year) + 1, len(side), int(drop.sum()), float(np.median(self._last_af)) if len(self._last_af) else 0.0))

    def _bud_keep_chance(self, pos):
        """The chance that a new node makes a lateral bud: 1 up to af_full, falling to 0 at af_zero."""
        grid, lo, cell = self._leaf_density
        dc = self.sp.bud_fate.density_control
        ijk = np.floor(pos / cell).astype(np.int64) - lo
        inside = np.all((ijk >= 0) & (ijk < np.array(grid.shape)), axis=1)
        af = np.zeros(len(pos))
        af[inside] = grid[tuple(ijk[inside].T)]
        self._last_af = af
        return np.clip((float(dc.af_zero) - af) / (float(dc.af_zero) - float(dc.af_full)), 0.0, 1.0)

    def wood_sources(self) -> tuple[np.ndarray, np.ndarray]:
        """Living woody internodes sampled along their axis and their projected area (m^2)."""
        T = self.tree
        n0 = T.n
        alive = T.death[:n0] < 0
        par = T.parent[:n0]
        seg_idx = np.nonzero(alive & (par >= 0))[0]
        if len(seg_idx) == 0:
            return np.zeros((0, 3)), np.zeros(0)
        p_idx = par[seg_idx]
        p0 = T.pos[p_idx]
        p1 = T.pos[seg_idx]
        r = T.radius[seg_idx]
        dp = p1 - p0
        lens = np.linalg.norm(dp, axis=1)
        valid = lens > 0
        if not valid.all():
            seg_idx, p0, p1, r, dp, lens = seg_idx[valid], p0[valid], p1[valid], r[valid], dp[valid], lens[valid]
        if len(seg_idx) == 0:
            return np.zeros((0, 3)), np.zeros(0)
        vs = self.light.vs
        long_mask = lens > vs
        short_mask = ~long_mask
        pts = [0.5 * (p0[short_mask] + p1[short_mask])]
        areas = [2.0 * r[short_mask] * lens[short_mask]]
        if long_mask.any():
            for p0_i, dp_i, r_i, l_i in zip(p0[long_mask], dp[long_mask], r[long_mask], lens[long_mask]):
                n_samp = max(1, int(np.ceil(l_i / vs)))
                step_l = l_i / n_samp
                t_vals = (np.arange(n_samp) + 0.5) / n_samp
                pts.append(p0_i[None, :] + t_vals[:, None] * dp_i[None, :])
                areas.append(np.full(n_samp, 2.0 * r_i * step_l))
        return np.concatenate(pts), np.concatenate(areas)

    def _shoot_base(self, nodes: np.ndarray) -> np.ndarray:
        """True for nodes of the last growth season that start a shoot (the
        first node of a lateral, or of an axis tip's extension): where a
        birch long shoot carries its early leaves."""
        T = self.tree
        par = T.parent[nodes]
        fresh = (T.lat[nodes] == LAT_DORMANT) & (T.lat_age[nodes] == 0)
        return fresh & (par >= 0) & (T.birth[np.maximum(par, 0)] < T.birth[nodes])

    def _leader_damage(self, t: int):
        """Leader loss (leader_damage in the YAML): each season, with the
        sourced yearly probability for its height, the leader's last annual
        shoot dies.  Its apex is gone; the uppermost lateral buds (or young
        laterals) just below become replacement leaders: orthotropic, with
        the stem's vigour and posture target.  Whether one wins (a crook) or
        two persist (a fork) is left to growth."""
        ld = getattr(self.sp, "leader_damage", None)
        if ld is None or not bool(ld.enabled):
            return
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        tips = np.nonzero(alive & (T.term[:n] == 1) & np.isin(T.axis[:n], np.fromiter(self.leader_axes, np.int64)))[0]
        if not tips.size:
            return
        tip = int(tips[np.argmax(T.pos[tips, 2])])
        h = float(T.pos[tip, 2])
        p_loss, cause = 0.0, None
        for ev in ld.events:
            if float(ev.min_height_m) <= h < float(ev.max_height_m):
                q = float(ev.probability_per_year)
                if self._dmg_rng.random() < q:
                    p_loss, cause = 1.0, str(ev.name)
                    break
        if not p_loss:
            return
        # Moose winter browsing clips the distal shoot down to bite_diameter_m
        # (Mathisen et al. 2017: 2.16 +- 0.15 mm on B. pendula)
        ax = int(T.axis[tip])
        shoot_nodes = []
        curr = tip
        while curr > 0 and T.axis[curr] == ax and T.birth[curr] >= t - 1:
            shoot_nodes.append(curr)
            curr = int(T.parent[curr])
        shoot_nodes = shoot_nodes[::-1]
        par_of_base = curr
        if not shoot_nodes:
            return
        bite_d = float(getattr(ld, "bite_diameter_m", 0.0) or 0.0)
        pm = self.sp.pipe_model
        d_tip = 2.0 * float(pm.tip_radius)
        if par_of_base >= 0:
            d_base = 2.0 * max(float(T.radius[par_of_base]), float(pm.tip_radius))
        else:
            d_base = d_tip
        L_shoot = sum(float(T.length[nd]) for nd in shoot_nodes)
        L_shoot = max(L_shoot, 1e-6)
        dist_from_tip = 0.0
        bite_k = shoot_nodes[0]
        for nd in reversed(shoot_nodes):
            dist_from_tip += float(T.length[nd])
            d_nd = d_tip + (d_base - d_tip) * (dist_from_tip / L_shoot)
            if bite_d > 0.0 and d_nd >= bite_d:
                bite_k = nd
                break
        k = bite_k
        base = int(T.parent[k]) if T.parent[k] >= 0 else k
        if base <= 0:
            return
        levels = T.levels(alive)
        kill = np.zeros(n, bool)
        kill[k] = True
        par = T.parent
        for seg, _, _ in levels[1:]:
            kill[seg] |= kill[par[seg]]
        T.death[np.nonzero(kill)[0]] = t
        T.main_child[base] = -1
        T.term[base] = 0
        # replacement leaders: the n uppermost lateral buds / young laterals
        cand, j = [], base
        while j > 0 and len(cand) < int(ld.replacement_leaders) and T.pos[base, 2] - T.pos[j, 2] < float(ld.replacement_zone_m):
            if (T.lat[j] in (LAT_DORMANT, LAT_SPUR) and not T.no_axil[j]) or (T.lat_child[j] >= 0 and T.death[T.lat_child[j]] < 0):
                cand.append(j)
            j = int(T.parent[j])
        for c in cand:
            lc = int(T.lat_child[c])
            if lc >= 0 and T.death[lc] < 0:
                self.leader_axes.add(int(T.axis[lc]))
                if base not in self.tree.relay:
                    self.tree.relay[base] = lc
            else:
                if T.lat[c] == LAT_SPUR:
                    self._end_spur(c, t)
                T.lat[c] = LAT_DORMANT
                T.lat_age[c] = 0
                self._relay_buds[c] = base
        self.leader_losses.append((t, round(h, 2), cause))

    def _crown_light_asymmetry(self, term_nodes, lat_nodes, Qterm, Qlat, w_term, w_lat) -> np.ndarray:
        """Where the crown catches its light, relative to the stem: the
        light-weighted mean horizontal offset of the leafy buds from the stem
        axis at their height, over the crown radius.  Its direction is the
        brighter side of the crown, its length (0-1) how lopsided the light
        is.  Fed to the leader's phototropism (lateral light inside the crown,
        not only at the apex)."""
        if not bool(getattr(self.sp.tropism, "stem_crown_phototropism", False)):
            return np.zeros(3)
        T = self.tree
        nodes = np.concatenate([term_nodes, lat_nodes])
        q = np.concatenate([Qterm[term_nodes], Qlat[lat_nodes]]) * np.concatenate([w_term, w_lat])
        if nodes.size == 0 or q.sum() <= 0:
            return np.zeros(3)
        stem = T.trunk_chain(self.leader_axes)
        zs = T.pos[stem, 2]
        P = T.pos[nodes]
        k = np.clip(np.searchsorted(zs, P[:, 2]), 0, len(stem) - 1)
        off = P[:, :2] - T.pos[stem[k], :2]
        rad = float(np.percentile(np.hypot(off[:, 0], off[:, 1]), 90)) or 1.0
        v = (q[:, None] * off).sum(0) / q.sum() / rad
        return np.array([v[0], v[1], 0.0])

    def _reiterate(self, t, term_nodes, v_term, Qterm):
        """Loss of dominance and reiteration (Barthelemy & Caraglio 2007;
        Millet, Bouchard & Edelin 1999).  Once the leader's yearly growth has
        fallen below decline_fraction of its peak (its growth units become
        short), a first-order limb attached in the upper crown, well lit and
        nearly as vigorous as the leader, becomes a reiterated complex: its
        meristems are partly rejuvenated and its own axis grows orthotropic,
        a small tree on the tree."""
        rp = getattr(self.sp.resource, "reiteration", None)
        if rp is None or not bool(rp.enabled) or not len(term_nodes):
            return
        T = self.tree
        lead = np.isin(T.axis[term_nodes], np.fromiter(self.leader_axes, np.int64))
        if not lead.any():
            return
        v_lead = float(v_term[lead].max())
        self._lead_peak = max(self._lead_peak, v_lead)
        if t < float(rp.min_age) or v_lead >= float(rp.decline_fraction) * self._lead_peak:
            return
        if self.loss_of_dominance_year is None:
            self.loss_of_dominance_year = t
        tips = np.nonzero((T.order[term_nodes] == 1) & ~lead)[0]
        if not tips.size:
            return
        nodes = term_nodes[tips]
        sc = T.scaffold[nodes].astype(np.int64)
        ok = (sc > 0) & ~np.isin(sc, np.fromiter(self.reit.keys(), np.int64)) & (T.axis[nodes] == T.axis[np.maximum(sc, 0)])
        H = float(T.pos[: T.n][T.death[: T.n] < 0, 2].max())
        cb = (self.stats[-1].get("crown_base_height_m") if self.stats else None) or 0.0
        z_att = T.pos[T.parent[np.maximum(sc, 0)], 2]
        ok &= z_att >= cb + float(rp.upper_crown_fraction) * (H - cb)
        ok &= Qterm[nodes] >= float(rp.min_light)
        ok &= v_term[tips] >= float(rp.min_relative_vigour) * v_lead
        # sequential reiteration: one complex at a time, the most vigorous
        # eligible limb, at most one per interval_years
        last = max((v[0] for v in self.reit.values()), default=-1e9)
        if not ok.any() or t - last < float(rp.interval_years):
            return
        best = np.nonzero(ok)[0]
        best = best[np.argmax(v_term[tips][best])]
        r = self.sp.resource
        for k in (best,):
            s0 = int(sc[k])
            born = float(T.scaffold_birth[s0])
            age = (t - born) / float(r.branch_aging_years)
            if bool(getattr(r, "limbs_inherit_stem_age", False)):
                age += born / float(r.stem_aging_years)
            self.reit[s0] = (t, float(rp.rejuvenation) * age)
            self.reit_axes.add(int(T.axis[s0]))

    def apical_control(self, year: int) -> float:
        r = self.sp.resource
        s = 1.0 / (1.0 + math.exp((year - r.apical_control_transition_age) / r.apical_control_transition_width))
        return r.apical_control_old + (r.apical_control_young - r.apical_control_old) * s

    # -- stand: neighbour trees as shadow volumes -----------------------
    def stand_spacing(self, height: float) -> float:
        """Hexagonal spacing (m) for the stem density at this dominant height."""
        st = self.sp.stand
        density = st.thinning[0].stems_per_ha
        for stage in st.thinning:
            if height >= stage.from_height_m:
                density = stage.stems_per_ha
        return math.sqrt(2.0 * 10000.0 / (math.sqrt(3.0) * density))

    def stems_per_ha(self, height: float) -> float:
        s = self.stand_spacing(height)
        return 2.0 * 10000.0 / (math.sqrt(3.0) * s * s)

    def _random_stand_map(self, rng) -> list:
        """Neighbours of the focal tree in one square periodic cell of
        cell_trees^2 trees, in cell units (focal tree at the centre): random
        positions with no two trees closer than min_distance x the mean
        spacing (a hard-core pattern, as thinned stands are), each with a fixed
        random turn and relative size."""
        st = self.sp.stand
        N = int(st.cell_trees) ** 2
        dmin = float(st.min_distance) / math.sqrt(N)
        pts = [np.array([0.5, 0.5])]
        tries = 0
        while len(pts) < N and tries < 100000:
            q = rng.random(2)
            d = np.abs(np.array(pts) - q)
            d = np.minimum(d, 1.0 - d)
            if (np.hypot(d[:, 0], d[:, 1]) >= dmin).all():
                pts.append(q)
            tries += 1
        cv = float(st.size_cv)
        out = []
        for q in pts[1:]:
            size = float(np.clip(rng.normal(1.0, cv), 1.0 - 2.5 * cv, 1.0 + 2.5 * cv))
            out.append((float(q[0] - 0.5), float(q[1] - 0.5), float(rng.uniform(0, 2 * np.pi)), size))
        return out

    def _stand_cell(self, pos: np.ndarray, w: np.ndarray, height: float,
                    wood_pos: np.ndarray | None = None, wood_w: np.ndarray | None = None):
        """Neighbour trees as shadow volumes: one periodic cell of the
        hexagonal stand lattice, ``cell_trees`` trees across, every lattice
        point a copy of the focal crown turned by its own fixed random angle.
        The light grid repeats the cell, so the stand has no edge."""
        st = self.sp.stand
        vs = self.light.vs
        nxt = int(st.cell_trees)
        has_w = wood_pos is not None and wood_w is not None and len(wood_pos) > 0
        if getattr(self, "_stand_map", None) is not None:
            # random layout: a square cell holding cell_trees^2 trees at the
            # stem density of this height; neighbours are scaled copies
            side = math.sqrt(len(self._stand_map) + 1) * math.sqrt(10000.0 / self.stems_per_ha(height))
            nx = max(1, int(round(side / vs)))
            side = nx * vs
            out_p, out_w = [pos], [w]
            out_wp = [wood_pos] if has_w else None
            out_ww = [wood_w] if has_w else None
            transforms = []
            for u, v, a, size in self._stand_map:
                off_x, off_y = u * side, v * side
                c, sn = math.cos(a), math.sin(a)
                p = pos.copy() * size
                p[:, 0] = size * (c * pos[:, 0] - sn * pos[:, 1]) + off_x
                p[:, 1] = size * (sn * pos[:, 0] + c * pos[:, 1]) + off_y
                transforms.append((a, off_x, off_y))
                out_p.append(p)
                out_w.append(w * size * size)
                if has_w:
                    wp = wood_pos.copy() * size
                    wp[:, 0] = size * (c * wood_pos[:, 0] - sn * wood_pos[:, 1]) + off_x
                    wp[:, 1] = size * (sn * wood_pos[:, 0] + c * wood_pos[:, 1]) + off_y
                    out_wp.append(wp)
                    out_ww.append(wood_w * size * size)
            self._stand_transforms = transforms
            c_wp = np.concatenate(out_wp) if has_w else None
            c_ww = np.concatenate(out_ww) if has_w else None
            return np.concatenate(out_p), np.concatenate(out_w), (-0.5 * side, -0.5 * side, nx, nx), c_wp, c_ww
        s = self.stand_spacing(height)
        nx = max(1, int(round(nxt * s / vs)))
        s = nx * vs / nxt                                     # snap to the voxel grid
        rows = 2 * max(1, int(round(nxt / math.sqrt(3.0))))   # even, so rows repeat
        ny = max(1, int(round(rows * s * math.sqrt(3.0) / 2.0 / vs)))
        dy = ny * vs / rows
        i0, j0 = nxt // 2, rows // 2
        out_p, out_w = [pos], [w]
        out_wp = [wood_pos] if has_w else None
        out_ww = [wood_w] if has_w else None
        transforms = []
        for j in range(rows):
            for i in range(nxt):
                if (i, j) == (i0, j0):
                    continue
                off_x = s * ((i - i0) + 0.5 * ((j % 2) - (j0 % 2)))
                off_y = dy * (j - j0)
                a = self._clone_angle[(i, j)]
                transforms.append((a, off_x, off_y))
                c, sn = math.cos(a), math.sin(a)
                p = pos.copy()
                p[:, 0] = c * pos[:, 0] - sn * pos[:, 1] + off_x
                p[:, 1] = sn * pos[:, 0] + c * pos[:, 1] + off_y
                out_p.append(p)
                out_w.append(w)
                if has_w:
                    wp = wood_pos.copy()
                    wp[:, 0] = c * wood_pos[:, 0] - sn * wood_pos[:, 1] + off_x
                    wp[:, 1] = sn * wood_pos[:, 0] + c * wood_pos[:, 1] + off_y
                    out_wp.append(wp)
                    out_ww.append(wood_w)
        x0 = -0.5 * nx * vs
        y0 = -0.5 * ny * vs
        self._stand_transforms = transforms
        c_wp = np.concatenate(out_wp) if has_w else None
        c_ww = np.concatenate(out_ww) if has_w else None
        return np.concatenate(out_p), np.concatenate(out_w), (x0, y0, nx, ny), c_wp, c_ww

    # ------------------------------------------------------------------
    def run(self, years: int, callback=None, verbose: bool = False):
        for _ in range(years):
            self.step()
            if callback is not None:
                callback(self)
            if verbose:
                s = self.stats[-1]
                dbh = s["dbh_cm"]
                print(
                    f"  year {s['year']:3d}  internodes {s['living_internodes']:7d}  "
                    f"height {s['height_m']:6.2f} m  dbh {dbh if dbh is not None else float('nan'):5.1f} cm  "
                    f"crown {s['crown_width_m']:5.2f} m  base {s['crown_base_height_m'] or 0:5.2f} m  "
                    f"hanging {s['mean_hanging_twig_length_m']:4.2f} m",
                    flush=True,
                )
        if not self.lean and self.year not in self.keyframes:
            self.keyframes[self.year] = self.tree.pos[: self.tree.n].astype(np.float32).copy()
        return self

    def _leaves_at_nodes(self, t: int) -> np.ndarray:
        """Leaves each living node carries this season: one on every new
        node, a short shoot's cluster on spurs and on non-extending tips."""
        T = self.tree
        n = T.n
        fw = self.sp.light.foliage_weight
        alive = T.death[:n] < 0
        leaves = np.where(T.birth[:n] == t, float(fw.new_leaf), 0.0)
        early = float(getattr(fw, "early_leaves", 0.0) or 0.0)
        if early:
            leaves += np.where((T.birth[:n] == t) & self._shoot_base(np.arange(n)), early, 0.0)
        leaves += np.where(T.lat[:n] == LAT_SPUR, float(fw.spur), 0.0)
        leaves += np.where((T.term[:n] == 1) & (T.birth[:n] < t), float(fw.spur), 0.0)
        return np.where(alive, leaves * T.leaf_scale[:n] * self._size_rel(np.arange(n)), 0.0)

    # days in the months of the soil-water season (May-September)
    SWB_MONTH_DAYS = (31, 30, 31, 31, 30)

    def _run_soil_water_balance(self, swb, lai: float) -> tuple[float, float]:
        """Season soil-water balance of BILJOU (Granier, Breda, Biron &
        Villette 1999, Ecol. Modell. 116:269), stepped daily as published
        (Eq. 1, dW = P - T - D, without interception and understorey terms),
        each month's rain and PET spread evenly over its days (the model has
        monthly climate only):
          REW = W / EWM            (W extractable water above the lower limit;
                                    Breda et al. 2006 Eq. 2)
          Tmax = r PET, r = 0.125 LAI for LAI <= 6, 0.75 above (Granier 1999 Eq. 2)
          T = Tmax if REW > REWc, else Tmax REW / REWc   (linear decline below
              REWc, Granier 1999 p. 271; Sopharat et al. 2015 Eqs. 9-10)
          D = W - EWM when W exceeds EWM (drainage above field capacity)
        Assumptions without a source (VERIFY): the season starts at field
        capacity on 1 May every year (Granier 1999 gives no initial state),
        and r is at its full value from 1 May (BILJOU raises r linearly over
        the 30 days after budburst, Granier 1999 p. 272; not applied here).
        Returns (lowest REW of the season, season sum T / sum Tmax)."""
        awc = float(swb.awc_mm)
        rew_c = float(swb.rew_threshold)
        r = min(float(swb.transpiration_lai_slope) * lai, float(swb.transpiration_ratio_max))
        rain = swb.dry_year_precipitation_mm if bool(getattr(swb, "drought_scenario", False)) else swb.precipitation_mm
        w = awc
        min_rew, t_sum, tmax_sum = 1.0, 0.0, 0.0
        for p, pet, days in zip(rain, swb.pet_mm, self.SWB_MONTH_DAYS):
            for _ in range(days):
                rew = w / awc
                min_rew = min(min_rew, rew)
                tmax = r * float(pet) / days
                t = tmax if rew > rew_c else tmax * rew / rew_c
                w = min(max(w + float(p) / days - t, 0.0), awc)
                t_sum += t
                tmax_sum += tmax
        return min_rew, (t_sum / tmax_sum if tmax_sum > 0 else 1.0)

    def step(self):
        t = self.year + 1
        self._leader_damage(t)
        sp, T = self.sp, self.tree
        n0 = T.n
        alive = T.death[:n0] < 0

        # 1. environment -------------------------------------------------
        term_nodes, lat_nodes, w_term, w_lat, src, src_w = self.light_sources()
        fw = sp.light.foliage_weight
        if len(src) == 0:  # no living buds left: the tree only thickens
            self.carbon = {"fixed": 0.0, "shoot": 0.0, "root": 0.0, "mean_bud_light": 0.0, "fixed_per_leaf_area": 0.0,
                           "upkeep": float(sp.resource.maintenance_per_internode) * max(int(alive.sum()) - 1, 0), "cue": 0.0}
            self._shoot_carbon = 0.0   # nothing fixed, no new wood
            self._finish_year(t)
            return
        woody_cfg = bool(getattr(getattr(sp.light, "woody_shade", None), "enabled", False))
        k_wood = float(getattr(sp.light.woody_shade, "k_wood", 0.40)) if woody_cfg else 0.40
        wpos = warea = None
        if woody_cfg:
            wpos, warea = self.wood_sources()
        all_pts = src if wpos is None or len(wpos) == 0 else np.concatenate([src, wpos])
        region = np.stack([all_pts.min(0), all_pts.max(0)])
        cell = None
        if getattr(self, "_plot_view", None) is not None:
            # in a plot: one light field shared by all trees, seen from here
            field = self._plot_view
        elif self.stand:
            height = float(T.pos[:n0][alive, 2].max())
            cpos, cw, cell, c_wpos, c_warea = self._stand_cell(src, src_w, height, wpos, warea)
            old = getattr(self, "_field", None)
            if (t - 1) % fast.light_every(sp) != 0 and old is not None and old.S.shape[:2] == (cell[2], cell[3]):
                field = old     # lossy, speed.light_every: last year's light
            else:
                field = self.light.compute(cpos, cw, region, periodic=cell, wood_pos=c_wpos, wood_area=c_warea, k_wood=k_wood,
                                           diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M)
        else:
            field = self.light.compute(src, src_w, region, wood_pos=wpos, wood_area=warea, k_wood=k_wood)
        self._field = field   # kept for diagnostics until the next season
        # output only: light at the target's measurement heights under the
        # stand canopy (a plot reports it for the whole plot, plot.py)
        self._subcanopy_light = (field.relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M)
                                 if self.stand and getattr(self, "_plot_view", None) is None else None)
        self._subcanopy_diffuse_light = (field.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M)
                                         if self.stand and getattr(self, "_plot_view", None) is None else None)
        Qterm = np.zeros(n0)
        Qlat = np.zeros(n0)
        own_t = own_l = None
        if bool(getattr(sp.light, "exclude_own_shoot", False)):
            # no shoot shades itself: the shade of the bud's own shoot (its
            # axis with its short shoots) is taken out of its light; its shade
            # on other shoots stays
            own = self.light.own_shade(src, src_w, np.concatenate([T.axis[term_nodes], T.axis[lat_nodes]]))
            own_t, own_l = own[: len(term_nodes)], own[len(term_nodes):]
        Qterm[term_nodes] = field.exposure(T.pos[term_nodes], w_term, own_t)
        Qlat[lat_nodes] = field.exposure(T.pos[lat_nodes], w_lat, own_l)
        # the herb layer (grasses, dwarf shrubs) shades buds near the ground
        Qterm[term_nodes] *= self._herb_factor(T.pos[term_nodes, 2])
        Qlat[lat_nodes] *= self._herb_factor(T.pos[lat_nodes, 2])
        # this season's leaves on short shoots and resting tips take their
        # size and LMA from their light (sun and shade leaves)
        for nodes, q in ((term_nodes, Qterm[term_nodes]), (lat_nodes, Qlat[lat_nodes])):
            T.leaf_size[nodes], T.lma[nodes] = self.leaf_traits(q)
        self._bud_q = None if fast.on(sp, "drop_dead") else (Qterm, Qlat)     # nothing in the model reads it
        self._crown_light = self._crown_light_asymmetry(term_nodes, lat_nodes, Qterm, Qlat, w_term, w_lat)

        # 2. shedding ------------------------------------------------------
        # A lateral branch is shed when its foliage no longer pays: the
        # leaf-weighted mean exposure of its buds is below the compensation
        # level, or it carries no leaves at all.  This is the paper's Q/N test
        # with the cost counted per leaf instead of per internode: at real
        # internode resolution the bare inner wood of a healthy limb grows N
        # until whole limbs cross a fixed Q/N together (Sprugel et al. 1991:
        # branches die when their own leaves stop paying).
        levels = T.levels(alive)
        Qtot = T.basipetal(levels, Qterm + Qlat)
        ones = alive.astype(float)
        ones[0] = 0.0
        Ntot = T.basipetal(levels, ones)
        leafw = np.zeros(n0)
        leafw[term_nodes] += w_term
        leafw[lat_nodes] += w_lat
        qw = np.zeros(n0)
        qw[term_nodes] += Qterm[term_nodes] * w_term
        qw[lat_nodes] += Qlat[lat_nodes] * w_lat
        Wtot = T.basipetal(levels, leafw)
        QWtot = T.basipetal(levels, qw)
        sh = sp.shedding
        # the stem, replacement leaders included, is not a branch: a lateral
        # that took over a lost leader carries the whole crown above it, and
        # the tree's fate is the tree's carbon balance (plot death rules)
        stem = np.isin(T.axis[:n0], np.fromiter(self.leader_axes, np.int64))
        cand = np.nonzero(alive & T.is_lateral[:n0] & ~stem & (T.birth[:n0] <= t - sh.min_branch_age))[0]
        ratio = QWtot[cand] / np.maximum(Wtot[cand], 1e-12)
        shed = cand[(Wtot[cand] <= 0.0) | self._falls(ratio, sh.light_per_leaf_threshold)]
        # branch autonomy: limbs that could not pay their own upkeep last year
        starving = self._starving[(self._starving < n0)]
        starving = starving[alive[starving] & ~stem[starving] & (T.birth[starving] <= t - sh.min_branch_age)]
        if starving.size:
            shed = np.union1d(shed, starving)
        self._starving = np.zeros(0, np.int64)
        if bool(getattr(sp.shoot, "stop_at_ground", False)):
            # a branch lying in the ground layer (below the contact height and
            # not climbing) dies: the axis that carries the node is shed
            gl = alive & (T.order[:n0] >= 1) & (T.pos[:n0, 2] < float(sp.shoot.ground_contact_height)) & (T.dir[:n0, 2] < 0.2)
            if gl.any():
                firsts = np.nonzero(alive & T.is_lateral[:n0])[0]
                axfirst = np.full(int(T.axis[:n0].max()) + 1, -1, np.int64)
                axfirst[T.axis[firsts]] = firsts
                g_ax = axfirst[T.axis[:n0][gl]]
                g_ax = np.unique(g_ax[g_ax >= 0])
                g_ax = g_ax[T.birth[g_ax] <= t - sh.min_branch_age]
                if g_ax.size:
                    shed = np.union1d(shed, g_ax)
        if shed.size:
            self._shed(t, shed, levels)
            alive = T.death[:n0] < 0
            Qterm[~alive] = 0.0
            Qlat[~alive] = 0.0
            keep_t, keep_l = alive[term_nodes], alive[lat_nodes]
            term_nodes, w_term = term_nodes[keep_t], w_term[keep_t]
            lat_nodes, w_lat = lat_nodes[keep_l], w_lat[keep_l]
            levels = T.levels(alive)
            Qtot = T.basipetal(levels, Qterm + Qlat)

        # 3. water: leaf water potential, stomatal opening, carbon budget ----
        bud_nodes = np.concatenate([term_nodes, lat_nodes])
        bud_q = np.concatenate([Qterm[term_nodes], Qlat[lat_nodes]])
        bud_leaf = np.concatenate([w_term, w_lat]) * self.light.leaf_area
        res = sp.resource
        if self.roots is not None:
            fine = self._fine_root_mass(bud_nodes, bud_leaf)
            if fine is not None:
                # this season's fine roots, built in spring with the leaves
                self.roots.update_uptake(t, float(sp.hydraulics.root_xylem_conductivity), fine)
            area = self.conducting_area(levels, alive, bud_nodes, np.concatenate([w_term, w_lat]))
            psi, phi, flow, collar = hydraulics.solve(T, levels, alive, bud_nodes, bud_leaf, bud_q, area,
                                                      self.roots.uptake_conductance, sp.hydraulics,
                                                      self.soil.water_potential)
            self._psi = psi
        else:
            phi = np.ones(len(bud_nodes))
            flow, collar = 0.0, 0.0
        swb = getattr(sp, "soil_water_balance", None)
        min_rew = None
        f_swb = 1.0
        if swb is not None and bool(getattr(swb, "enabled", False)):
            # leaf-area index as measure() defines it: over the ground the tree
            # holds at the stand density, or over its crown projection
            la_tot_est = float(bud_leaf.sum())
            if self.stand:
                height = float(T.pos[:n0][alive, 2].max()) if alive.any() else 0.0
                stand_lai = la_tot_est * (self.stems_per_ha(height) / 10000.0)
            else:
                d_proj = float(self.stats[-1].get("crown_projected_diameter_m") or 0.0) if self.stats else 0.0
                stand_lai = la_tot_est / (math.pi * d_proj * d_proj / 4.0) if d_proj > 0 else 0.0
            min_rew, f_swb = self._run_soil_water_balance(swb, stand_lai)
            # carbon is cut in proportion to the season's transpiration cut
            # (T / Tmax): an assumption with no opened source, on top of the
            # hydraulic stomatal limit; see KNOWN_ISSUES phase 40. VERIFY
            phi = phi * f_swb
        phi_t, phi_l = phi[: len(term_nodes)], phi[len(term_nodes):]
        # carbon is fixed by leaves: each bud's light times its leaf weight (a
        # leafless dormant bud fixes none, a short shoot's cluster 2.5 times a
        # single leaf); alpha is the carbon of one reference leaf in full light
        bud_w = np.concatenate([w_term, w_lat])
        carbon = float(res.alpha) * float((bud_q * phi * bud_w).sum())
        germ = getattr(sp, "germination", None)
        if germ is not None and bool(getattr(germ, "enabled", False)) and t == 1:
            seed_mg = float(getattr(germ, "seed_dry_mass_mg", 0.21))
            resp_frac = float(getattr(germ, "germination_respiration_fraction", 0.35))
            lc = getattr(sp.resource, "leaf_costs", None)
            c_frac = float(getattr(lc, "carbon_fraction", 0.48)) if lc else 0.48
            dens = float(getattr(lc, "wood_basic_density_kg_m3", 530.0)) if lc else 530.0
            g_per_unit = float(sp.pipe_model.wood_volume_per_carbon) * dens * 1000.0
            seed_c = (seed_mg / 1000.0) * (1.0 - resp_frac) * c_frac
            carbon += seed_c / (g_per_unit * c_frac) if (g_per_unit * c_frac) > 0 else 0.0
        stress = 1.0 - float((bud_q * phi * bud_w).sum()) / max(float((bud_q * bud_w).sum()), 1e-12)
        # functional balance (Brouwer 1963; Thornley 1972): a water-limited
        # tree sends more of its carbon below ground
        root_share = float(res.root_share_min) + (float(res.root_share_max) - float(res.root_share_min)) * stress
        if self.roots is None:
            root_share = 0.0
        shoot_budget = (1.0 - root_share) * carbon
        # respiration: maintenance of the living shoot wood (charged as the
        # resource flows out, below) and growth respiration on what is built
        # (growth_respiration_coefficient g C respired per g C in new
        # tissue); wood and roots are built from what is left
        n_int = max(int(alive.sum()) - 1, 0)
        r_maint = float(res.maintenance_per_internode) * n_int
        g_resp = 1.0 + float(getattr(res, "growth_respiration_coefficient", 0.0))
        # this season's leaves are rebuilt and respire, and so do the fine
        # roots that go with them (resource.leaf_costs)
        leaf_build, leaf_maint, root_maint, leaf_dm = self._leaf_costs(bud_nodes, bud_leaf, g_resp)
        self._bud_leaf_cost = (bud_nodes, leaf_build + leaf_maint)
        shoot_costs = r_maint + float(leaf_build.sum() + leaf_maint.sum())
        shoot_net = max(shoot_budget - shoot_costs, 0.0)
        root_net = max(carbon - shoot_budget - root_maint, 0.0)
        self._shoot_carbon = shoot_net / g_resp
        self._root_carbon = root_net
        la_tot = float(bud_leaf.sum())
        npp = float(leaf_build.sum()) / g_resp + (shoot_net + root_net) / g_resp
        self._npp_base = npp
        self.carbon = {"fixed": carbon, "shoot": shoot_budget, "root": carbon - shoot_budget,
                       "mean_bud_light": float(bud_q.mean()) if bud_q.size else 0.0,
                       "fixed_per_leaf_area": carbon / la_tot if la_tot > 0 else 0.0,
                       # what the tree must pay each year to keep going: wood,
                       # leaf and fine-root maintenance and rebuilding its
                       # leaves (the branch carbon balance applied to the whole
                       # tree, plot natural mode)
                       "upkeep": shoot_costs + root_maint,
                       "wood_maint": r_maint, "leaf_build": float(leaf_build.sum()),
                       "leaf_maint": float(leaf_maint.sum()), "fine_root_maint": root_maint, "leaf_dm_g": leaf_dm,
                       # carbon use efficiency NPP / GPP of the tree
                       "cue": npp / carbon if carbon > 0 else 0.0}
        self.water = {"transpiration_kg_s": flow, "psi_collar_mpa": collar, "stomatal_opening": 1.0 - stress,
                      "root_share": root_share,
                      "psi_top_mpa": float(psi[bud_nodes].min()) if self.roots is not None and len(bud_nodes) else 0.0}
        if min_rew is not None:
            self.water["yearly_min_rew"] = float(min_rew)
            self.water["stomatal_limitation"] = float(f_swb)

        # 4. Borchert-Honda resource allocation --------------------------
        # Gravimorphism (Wareing & Nasr 1961): a bud's pull on resources
        # depends on its orientation, upward buds pulling more.  It weights
        # the BH split; the total v_base stays alpha*Q_base.  Thin twigs of a
        # pendulous species respond weakly, as they do to gravity in general.
        g = float(sp.resource.gravimorphism)
        mp = sp.mechanics
        axis_base_r = self._axis_base_radius()
        g_term = g * np.where(T.order[term_nodes] == 0, 1.0,
                              mechanics.pendulous_factor(axis_base_r[term_nodes], mp.pendulous_radius, mp.pendulous_sharpness))
        g_lat = g * np.where(T.order[lat_nodes] == 0, 1.0,
                             mechanics.pendulous_factor(axis_base_r[lat_nodes], mp.pendulous_radius, mp.pendulous_sharpness))
        limbs = self._limb_nodes(n0)
        if limbs is not None:
            g_term = g * np.where(T.order[term_nodes] == 0, 1.0,
                                  np.where(limbs[term_nodes],
                                           mechanics.pendulous_factor(axis_base_r[term_nodes], mp.pendulous_radius_limb, mp.pendulous_sharpness),
                                           mechanics.pendulous_factor(axis_base_r[term_nodes], mp.pendulous_radius, mp.pendulous_sharpness)))
        Gterm = np.zeros(n0)
        Glat = np.zeros(n0)
        # a bud's pull also scales with its stomatal opening: water-starved
        # buds (high up, far out on long paths) fix less carbon
        bh_pub = bool(getattr(sp.bud_fate, "borchert_honda_published", False))
        if bh_pub:
            # Published Borchert-Honda (Borchert & Honda 1984; Palubicki et al. 2009):
            # Pure light capture without gravimorphism or scaffold vigour aging in the split.
            Gterm[term_nodes] = Qterm[term_nodes] * phi_t
            Glat[lat_nodes] = Qlat[lat_nodes] * phi_l
        else:
            Gterm[term_nodes] = Qterm[term_nodes] * phi_t * np.maximum(0.05, 1.0 + g_term * T.term_dir[term_nodes, 2]) * self._scaffold_vigour(t, term_nodes)
            Glat[lat_nodes] = Qlat[lat_nodes] * phi_l * np.maximum(0.05, 1.0 + g_lat * T.lat_dir[lat_nodes, 2]) * self._scaffold_vigour(t, lat_nodes)
        if bool(getattr(sp.bud_fate, "short_shoots_self_financing", False)):
            # a short shoot lives on its own leaves and draws nothing from
            # the shoot's resource: its leaves still fix carbon (Q above), but
            # it is no sink in the split (it took ~3/4 of the resource and
            # wasted it, phase 15)
            Glat[lat_nodes[T.lat[lat_nodes] == LAT_SPUR]] = 0.0
        # a node grown by less than one metamer has its leaf but no axillary
        # bud (bud_fate.axillary_buds_below_one_metamer): no sink
        Glat[lat_nodes[T.no_axil[lat_nodes]]] = 0.0
        every = getattr(sp.bud_fate, "stem_bud_every", None)
        if every:
            # only one bud in so many on the stem can start a limb; the rest stay short shoots
            on_stem = np.isin(T.axis[lat_nodes], np.fromiter(self.leader_axes, np.int64))
            Glat[lat_nodes[on_stem & (T.phyllo[lat_nodes] % int(every) != 0)]] = 0.0
        if self._frame_on():
            # the frame: only the buds it named on the stem can start a limb; the rest stay short shoots
            on_stem = np.isin(T.axis[lat_nodes], np.fromiter(self.leader_axes, np.int64))
            named = np.isin(lat_nodes, np.fromiter(self._frame_buds().keys(), np.int64))
            Glat[lat_nodes[on_stem & ~named]] = 0.0
            every = getattr(sp.crown_frame, "twig_bud_every", None)
            if every:
                # on anything finer, one bud in so many can start a long shoot, the rest stay short shoots.  Odd, so
                # they take turns on the two sides of a two-ranked shoot
                Glat[lat_nodes[~on_stem & (T.phyllo[lat_nodes] % int(every) != 0)]] = 0.0
            distal = getattr(sp.crown_frame, "twig_buds_distal", None)
            if distal:
                # acrotony: on anything finer, only the buds nearest the end of last year's shoot can start a long shoot; the rest stay short shoots.
                # The same count each year on a shoot of any length, so an axis ends in a fork, not a comb.  A bud counts from its own axis's tip
                last = int(T.axis[:n0].max()) + 1
                tip_ph = np.zeros(last, np.int64)
                np.maximum.at(tip_ph, T.axis[:n0][alive], T.phyllo[:n0][alive].astype(np.int64))
                Glat[lat_nodes[~on_stem & (tip_ph[T.axis[lat_nodes]] - T.phyllo[lat_nodes].astype(np.int64) >= int(distal))]] = 0.0
        self._hd = self._height_limit_plan(t, term_nodes, lat_nodes, Qterm, Qlat, 1.0 - stress) if self._height_limit_on() else None
        if self._hd is not None:
            self._leader_phi = float((phi_t if self._hd["is_tip"] else phi_l)[self._hd["bud"]])
        Gtot = T.basipetal(levels, Gterm + Glat)
        mc = T.main_child[:n0]
        lc = T.lat_child[:n0]
        par = T.parent
        # apical dominance over buds vs. apical control over established
        # branches (Brown et al. 1967; Wilson 2000)
        if bh_pub:
            lam = np.full(n0, float(sp.resource.apical_dominance))
        else:
            lam = np.where(lc >= 0, self.apical_control(t), float(sp.resource.apical_dominance))
        # Maintenance respiration of living wood (carbon balance, Perttunen et
        # al. 1996): the tree pays it from its pool before the split (charged
        # along the flow instead, as P09/LIGNUM do, a realistic rate drains
        # long limbs before anything reaches their tips); a branch whose own
        # carbon does not cover its share is shed (carbon_balance below).
        mu = float(res.maintenance_per_internode)
        att_len = getattr(res, "transport_attenuation_length", None)
        att = np.exp(-T.length[:n0] / float(att_len)) if att_len else np.ones(n0)

        def split(G):
            Qm = np.where(mc >= 0, G[np.maximum(mc, 0)], Gterm)
            Ql = np.where(lc >= 0, G[np.maximum(lc, 0)], Glat)
            denom = lam * Qm + (1.0 - lam) * Ql
            return np.divide(lam * Qm, denom, out=np.zeros(n0), where=denom > 0)

        fm = split(Gtot)
        # Branch autonomy (Sprugel, Hinckley & Schaap 1991): an established
        # limb lives on the carbon its own leaves fix, imports none, keeps
        # most of it and exports a fraction to the stem.  A young limb is a
        # sink: it imports from the stem pool (its Borchert-Honda share)
        # until its own carbon covers what it drew, i.e. it has become a net
        # exporter; from then on it runs on its own budget.  The stem pool
        # (the stem's own leaves plus the exports) feeds the leader, the buds
        # on the stem and the young limbs.  Water still comes from the shared
        # roots (hydraulics above), so a limb's carbon reflects its water.
        export = getattr(res, "branch_export_fraction", None)
        unit = np.zeros(n0, bool)
        inject = np.zeros(n0)
        stem_budget = shoot_budget
        limb = np.zeros(0, np.int64)
        if export is not None:
            limb = np.nonzero(alive & T.is_lateral[:n0] & (T.order[:n0] == 1))[0]
        if limb.size:
            cb = np.zeros(n0)
            cb[term_nodes] += Qterm[term_nodes] * phi_t * w_term
            cb[lat_nodes] += Qlat[lat_nodes] * phi_l * w_lat
            own = (1.0 - root_share) * float(res.alpha) * T.basipetal(levels, cb)[limb]
            if len(self._established) < n0:
                grow_by = n0 - len(self._established)
                self._established = np.concatenate([self._established, np.zeros(grow_by, bool)])
                self._limb_draw = np.concatenate([self._limb_draw, np.full(grow_by, np.inf)])
            if bool(getattr(res, "young_limbs_import", False)):
                # net exporter: its own carbon covers last year's import
                self._established[limb[own >= self._limb_draw[limb]]] = True
            else:
                self._established[limb] = True
            est_mask = self._established[limb]
            est, own_e = limb[est_mask], own[est_mask]
            if est.size:
                keep = (1.0 - float(export)) * own_e
                unit[est] = True
                inject[est] = keep
                stem_budget = shoot_budget - float(keep.sum())
                # the stem's split weights count only the sinks it feeds
                d = np.zeros(n0)
                np.add.at(d, par[est], Gtot[est])
                fm = split(Gtot - T.basipetal(levels, d))
                fm[par[est]] = 1.0          # the stem pool passes self-funded limbs by
                # an established limb whose own carbon does not cover the
                # upkeep of its wood runs a deficit and is shed before next
                # season's flush
                ones_l = alive.astype(float)
                ones_l[0] = 0.0
                upkeep = mu * T.basipetal(levels, ones_l)[est]
                self._starving = est[keep < upkeep]
        if bool(getattr(sh, "carbon_balance", False)):
            # a branch dies when the carbon its own leaves fix no longer pays
            # the upkeep of its wood (Sprugel, Hinckley & Schaap 1991); it is
            # shed before next season's flush.  Ageing only lowers vigour.
            cbal = np.zeros(n0)
            cbal[term_nodes] += Qterm[term_nodes] * phi_t * w_term
            cbal[lat_nodes] += Qlat[lat_nodes] * phi_l * w_lat
            own_c = (1.0 - root_share) * float(res.alpha) * T.basipetal(levels, cbal)
            ones_c = alive.astype(float)
            ones_c[0] = 0.0
            # its upkeep: its wood and its own leaves (rebuilt and respiring)
            leaf_c = np.zeros(n0)
            np.add.at(leaf_c, *self._bud_leaf_cost)
            upkeep_c = mu * T.basipetal(levels, ones_c) + T.basipetal(levels, leaf_c)
            br = np.nonzero(alive & T.is_lateral[:n0] & (T.birth[:n0] <= t - sh.min_branch_age))[0]
            self._starving = np.union1d(self._starving, br[self._falls(own_c[br], upkeep_c[br])])
        def flow(fm):
            vin = np.zeros(n0)
            vm = np.zeros(n0)
            vl = np.zeros(n0)
            vin[0] = max(stem_budget - shoot_costs, 0.0)
            for li, (seg, mains, lats) in enumerate(levels):
                if li > 0:
                    if mains.size:
                        vin[mains] = vm[par[mains]]
                    if lats.size:
                        vin[lats] = np.where(unit[lats], inject[lats], vl[par[lats]])
                    vin[seg] = vin[seg] * att[seg]
                vm[seg] = vin[seg] * fm[seg]
                vl[seg] = vin[seg] - vm[seg]
            return vm, vl

        vm, vl = flow(fm)
        if limb.size:
            young = limb[~unit[limb]]
            self._limb_draw[young] = vl[par[young]]     # what each young limb drew this year
        lignum = str(getattr(sp.pipe_model, "growth", "pipe")) == "lignum"
        if lignum:
            # one pool for new shoots and rings: each bud's shoot is lambda x
            # its share, lambda set so that shoots and rings use the pool
            pool = max(stem_budget - shoot_costs, 0.0)
            share_t = vm[term_nodes] / pool if pool > 0.0 else np.zeros(len(term_nodes))
            share_l = vl[lat_nodes] / pool if pool > 0.0 else np.zeros(len(lat_nodes))
            carried = float(getattr(self.sp.height_driver, "store_fraction", None) or 0.0) if self._hd is not None else 0.0
            this_year = pool if not carried else (1.0 - carried) * pool + float(getattr(self, "_carbon_store", 0.0))
            lam, self._ring = self._growth_factor(this_year, g_resp, levels, alive, term_nodes, share_t, lat_nodes, share_l,
                                                  bud_q, bud_nodes, bud_leaf)
            if carried:
                # a small store: this share of the year's pool waits for next year, with what the crown
                # couldn't use, up to twice that share; beyond it, unused carbon is lost
                self._carbon_store = min(carried * pool + float(getattr(self, "_unspent", 0.0)), 2.0 * carried * pool)
            v_term, v_lat = lam * share_t, lam * share_l
            if self._hd is not None:
                v_term, v_lat = self._height_limit_apply(v_term, v_lat)
            if bool(getattr(sp.pipe_model, "sapwood_replacement_is_upkeep", False)):
                # the rings that keep this season's foliage supplied (sapwood
                # that stopped conducting, foliage added) are part of what the
                # tree must pay to keep going, like rebuilding its leaves
                self.carbon["upkeep"] += self._ring_need
                self.carbon["sapwood_replacement"] = self._ring_need
        else:
            # what reaches a bud builds new shoot after growth respiration
            v_term = vm[term_nodes] / g_resp
            v_lat = vl[lat_nodes] / g_resp
        if bool(getattr(sp.bud_fate, "idle_buds_no_sink", False)) and not limb.size and not lignum:
            # a bud that will not grow this year (a tip below one metamer, a
            # fresh lateral below the long-shoot gate) is no sink: the split is
            # made again among the buds that grow, so their resource is not
            # lost on buds that cannot use it (phase 15)
            fresh = (T.lat[lat_nodes] == LAT_DORMANT)
            for _ in range(2):
                idle_t = v_term < 1.0
                idle_l = fresh & (v_lat < float(sp.bud_fate.long_shoot_threshold))
                if not (idle_t.any() or idle_l.any()):
                    break
                Gterm[term_nodes[idle_t]] = 0.0
                Glat[lat_nodes[idle_l]] = 0.0
                if Gterm[term_nodes].sum() + Glat[lat_nodes].sum() <= 0.0:
                    break
                vm, vl = flow(split(T.basipetal(levels, Gterm + Glat)))
                v_term = vm[term_nodes] / g_resp
                v_lat = vl[lat_nodes] / g_resp
        self._reiterate(t, term_nodes, v_term, Qterm)
        self.diag = {
            "term_nodes": term_nodes, "lat_nodes": lat_nodes, "Qterm": Qterm[term_nodes],
            "Qlat": Qlat[lat_nodes], "v_term": v_term, "v_lat": v_lat,
            "shed_candidates": cand, "shed_ratio": ratio, "n_shed": int(shed.size),
            "grid": field.S.shape,
        }

        # 5. bud fate and shoot extension ---------------------------------
        bf = sp.bud_fate
        ls = T.lat[lat_nodes]
        is_spur = ls == LAT_SPUR
        # an axis tip extends by whatever it can afford, continuously: below
        # one metamer's worth it makes a single shorter internode (shoot length
        # follows the resource, l0 * v), down to min_tip_extension; a lateral
        # bud makes a long shoot only above the long-shoot threshold, otherwise
        # it becomes a short shoot
        g_term_mask = v_term >= float(getattr(bf, "min_tip_extension", 1.0))
        lat_thr = np.where(is_spur, bf.spur_release_threshold, bf.long_shoot_threshold)
        g_lat_mask = v_lat >= lat_thr

        released_spurs = lat_nodes[g_lat_mask & is_spur]
        for nd in released_spurs.tolist():
            self._end_spur(nd, t)

        self._leaf_density = self._leaf_density_grid(src, src_w)
        _n_before = T.n
        self._grow_shoots(t, field, term_nodes[g_term_mask], v_term[g_term_mask],
                          lat_nodes[g_lat_mask], v_lat[g_lat_mask],
                          np.concatenate([Qterm[term_nodes[g_term_mask]], Qlat[lat_nodes[g_lat_mask]]]))
        self._density_after_growth(src, src_w, _n_before)
        if self._hd is not None:
            self._height_limit_log(_n_before)
        if self._frame_on():
            self._frame_name_buds(t, _n_before)
            self._frame_name_forks(t, _n_before)
        # descending shoot apices that reach the ground layer stop growing
        tips = np.nonzero((T.term[:T.n] == 1) & (T.death[:T.n] < 0))[0]
        down = (T.pos[tips, 2] < float(sp.shoot.ground_contact_height)) & (
            T.dir[tips, 2] < (0.2 if bool(getattr(sp.shoot, "stop_at_ground", False)) else 0.0))
        T.term[tips[down]] = 0

        # Short-shoot fates are local and light-driven: a short shoot is cheap
        # and pays for itself where it is lit (Maillette 1982).  Long shoots
        # above need BH resource.
        q_ss = float(bf.short_shoot_light)
        q_die = float(bf.short_shoot_survival_light)
        it = term_nodes[~g_term_mask]
        T.term[it[self._falls(Qterm[it], q_die)]] = 0

        dm = ~g_lat_mask & ~is_spur
        dn = lat_nodes[dm]
        # no axillary bud: its leaf has had its season, nothing follows
        gone = dn[T.no_axil[dn]]
        T.lat[gone] = LAT_DEAD
        dn = dn[~T.no_axil[dn]]
        lit = Qlat[dn] >= q_ss
        to_spur = dn[lit]
        T.lat[to_spur] = LAT_SPUR
        T.spur_birth[to_spur] = t
        T.own_pipe[to_spur] += self.spur_pipe
        for nd in to_spur.tolist():
            self.spur_rec[nd] = len(self.spurs.node)
            self.spurs.node.append(nd)
            self.spurs.birth.append(t)
            self.spurs.death.append(-1)
            self.spurs.leaf_area.append(0.0)
            self.spurs.lma.append(0.0)
        stay = dn[~lit]
        T.lat_age[stay] += 1
        T.lat[stay[T.lat_age[stay] > bf.dormant_bud_lifespan]] = LAT_DEAD

        sm = ~g_lat_mask & is_spur
        sn = lat_nodes[sm]
        old = (t - T.spur_birth[sn] >= bf.spur_lifespan) if bf.spur_lifespan is not None else np.zeros(sn.size, bool)
        sdie = sn[self._falls(Qlat[sn], q_die) | old]
        T.lat[sdie] = LAT_DEAD
        for nd in sdie.tolist():
            self._end_spur(nd, t + 1)  # leaves flushed this year, gone next year

        # 6. roots spend their share of the carbon ---------------------------
        if self.roots is not None:
            budget = self._root_carbon / g_resp * float(res.root_segments_per_unit)
            if getattr(self, "_plot_soil", None) is not None:
                self.roots.step(t, budget, shared=self._plot_soil)
            elif self.stand:
                self.roots.step(t, budget, self._stand_transforms, cell)
            else:
                self.roots.step(t, budget)

        self._finish_year(t)

    def conducting_area(self, levels, alive, bud_nodes, bud_leaves) -> np.ndarray:
        """Water-conducting cross-section of every internode (m2).  With
        hydraulics.huber_value set: the pipe model's additive pipes, that much
        xylem per unit leaf area beyond.  Otherwise the visible-wood pipes of
        the leaves and shoot tips merged with the branching exponent."""
        hv = getattr(self.sp.hydraulics, "huber_value", None)
        if hv is None:
            leaf_pipe = self.spur_pipe / float(self.sp.light.foliage_weight.spur)
            return hydraulics.active_pipe_area(self.tree, levels, alive, self.tip_pipe, leaf_pipe, bud_nodes,
                                               bud_leaves, self.gamma)
        return hydraulics.sapwood_area(self.tree, levels, alive, bud_nodes,
                                       np.asarray(bud_leaves, float) * self.light.leaf_area, float(hv))

    def _finish_year(self, t: int):
        """Pipe model, mechanics, keyframes and stats at the end of season t."""
        T = self.tree
        n = T.n
        self.year = t
        r_prev = np.zeros(n)
        r_prev[: len(self._r_last)] = self._r_last
        leaves_now = self._leaves_at_nodes(t)
        self._update_radii(leaves_now)
        if self.roots is not None:
            self._update_roots(t)
        alive = T.death[:n] < 0
        mp = self.sp.mechanics
        if bool(mp.enabled):
            levels = T.levels(alive)
            gsa_o = np.radians(np.asarray(self.sp.tropism.setpoint_angle_deg, dtype=float))
            setpoint = gsa_o[np.minimum(T.order[:n], len(gsa_o) - 1)]
            # a replacement leader is stem, not limb: upright set-point, and
            # stiff and posture-corrected as the stem (no pendulous trait)
            stem = np.isin(T.axis[:n], np.fromiter(self.leader_axes, np.int64))
            setpoint = np.where(stem, gsa_o[0], setpoint)
            if self._frame_on():
                own = self._frame_setpoints()[T.axis[:n]]
                setpoint = np.where(np.isfinite(own) & ~stem, own, setpoint)
            mechanics.bend_and_correct(T, levels, alive, mp, leaves_now, T.leaves[:n].astype(float),
                                       r_prev, setpoint, float(self.sp.shoot.min_height_above_ground),
                                       self._stem_posture_target(n), stem, self._limb_nodes(n),
                                       compiled=fast.on(self.sp, "compiled_mechanics"))
        T.leaves[:n] = leaves_now
        if not self.lean and self.keyframe_step > 0 and t % self.keyframe_step == 0:
            self.keyframes[t] = T.pos[:n].astype(np.float32).copy()
        self.stats.append(self.measure())
        if fast.on(self.sp, "drop_dead"):
            compact(self)

    def dbh_m(self) -> float | None:
        """Stem diameter at 1.3 m (m), None while the tree is shorter."""
        T = self.tree
        trunk = T.trunk_chain(self.leader_axes)
        z = T.pos[trunk, 2]
        r = T.radius[trunk]
        if z.max() < 1.3:
            return None
        j = max(int(np.argmax(z >= 1.3)), 1)
        f = (1.3 - z[j - 1]) / max(z[j] - z[j - 1], 1e-9)
        return 2.0 * float(r[j - 1] + f * (r[j] - r[j - 1]))

    def _pay_roots(self, t: int) -> None:
        """roots.paid: the root share's carbon goes to real things.  Out of what's left after the fine roots'
        upkeep come this year's fine roots with their growth respiration (they turn over, and they grow with
        the leaves), then root wood with its growth respiration (RootSystem.update_radii_paid).  What's left
        after that stays in the log, as the share's unresolved rest: respiration of woody roots, exudates and
        mycorrhiza, none of which is modelled.  It goes to nothing else, so the crown's carbon doesn't move."""
        res = self.sp.resource
        cfg, lc = self.sp.roots.paid, res.leaf_costs
        g_resp = 1.0 + float(getattr(res, "growth_respiration_coefficient", 0.0))
        unit_volume = float(self.sp.pipe_model.wood_volume_per_carbon)
        g_per_unit = unit_volume * float(lc.wood_basic_density_kg_m3) * 1000.0
        carbon = getattr(self, "carbon", None) or {}
        grown = t > 0 and float(carbon.get("root", 0.0)) > 0.0      # a year with no leaves has no root carbon
        net = float(getattr(self, "_root_carbon", 0.0)) if grown else 0.0
        stock = float(carbon.get("leaf_dm_g", 0.0)) * float(lc.fine_root_to_leaf_mass) if grown else 0.0
        grew = max(stock - float(getattr(self, "_fine_stock_g", 0.0)), 0.0)
        self._fine_stock_g = stock
        fine_cost = (float(cfg.fine_root_turnover_per_year) * stock + grew) / g_per_unit * g_resp
        pay_fine = min(fine_cost, net)
        wood_with_resp = net - pay_fine
        # the stump: Repola's dS = 2 + 1.25 d, over bark; his 2 cm fades under 5 cm, where he warns against the equation
        d_ob_cm = 100.0 * (self.dbh_m() or 0.0) * float(self.sp.damage.dbh_over_bark_factor)
        stump_cm = float(cfg.stump_d_per_dbh) * d_ob_cm + float(cfg.stump_d_intercept_cm) * min(d_ob_cm / 5.0, 1.0)
        stump_d = max(stump_cm / 100.0, 2.0 * float(self.tree.radius[0]) * float(self.sp.damage.dbh_over_bark_factor))
        self.roots.carbon_log = {"fine_upkeep": float(carbon.get("fine_root_maint", 0.0)), "fine_build": pay_fine, "fine_wanted": fine_cost}
        self.roots.update_radii_paid(t, stump_d, wood_with_resp / g_resp, unit_volume, float(lc.wood_basic_density_kg_m3))
        log = self.roots.carbon_log
        built = log["new_root_wood"] + log["rings"]
        log["wood_respiration"] = built * (g_resp - 1.0)
        log["rest"] = max(wood_with_resp - built * g_resp, 0.0)

    def _update_roots(self, t: int):
        rp = self.sp.roots
        if bool(getattr(getattr(rp, "paid", None), "enabled", False)):
            self._pay_roots(t)
            if self._fine_root_mass(np.zeros(0, np.int64), np.zeros(0)) is None:
                self.roots.update_uptake(t, float(self.sp.hydraulics.root_xylem_conductivity))
            return
        # zone of rapid taper: its radius scales with stem diameter [D05]
        d = self.dbh_m() or 2.0 * float(self.tree.radius[0])
        zrt = float(getattr(rp, "zrt_radius_per_dbh", 0.0)) * d * float(getattr(rp, "zrt_fade_fraction", 0.5))
        self.roots.update_radii(float(self.tree.radius[0]) ** self.gamma, self.gamma,
                                float(rp.tip_radius) ** self.gamma, zrt)
        if self._fine_root_mass(np.zeros(0, np.int64), np.zeros(0)) is None:
            # with fine-root uptake it is set at the start of each season
            self.roots.update_uptake(t, float(self.sp.hydraulics.root_xylem_conductivity))

    def _fine_root_mass(self, bud_nodes, bud_leaf):
        """Fine-root dry mass (g) that goes with this season's leaves, when
        water enters through the fine roots the tree pays for (leaf_costs and
        roots.fine_root_uptake on); None otherwise."""
        lc = getattr(self.sp.resource, "leaf_costs", None)
        fu = getattr(self.sp.roots, "fine_root_uptake", None)
        if lc is None or not bool(lc.enabled) or fu is None or not bool(fu.enabled):
            return None
        return float((bud_leaf * self.tree.lma[bud_nodes]).sum()) * float(lc.fine_root_to_leaf_mass)

    # ------------------------------------------------------------------
    def _axis_base_radius(self) -> np.ndarray:
        """Radius at the first node of each node's axis (how big the branch is)."""
        T = self.tree
        n = T.n
        first = np.nonzero(T.is_lateral[:n] | (np.arange(n) == 0))[0]
        rad_axis = np.zeros(int(T.axis[:n].max()) + 1)
        rad_axis[T.axis[first]] = T.radius[first]
        return rad_axis[T.axis[:n]]

    def _end_spur(self, node: int, year: int):
        rec = self.spur_rec.pop(node, None)
        if rec is not None:
            self.spurs.death[rec] = year
            self.spurs.leaf_area[rec], self.spurs.lma[rec] = self._leaf_traits_of(node)

    def _leaf_traits_of(self, node: int):
        T = self.tree
        size = float(T.leaf_size[node]) if T.leaf_size[node] > 0 else float(self.light.leaf_area)
        return round(size, 7), round(float(T.lma[node]), 2)

    def spur_traits(self):
        """Leaf area (m2 per leaf) and LMA (g m-2) of every short shoot in
        the log: the last season of dead ones, the current one of live ones."""
        la, lm = list(self.spurs.leaf_area), list(self.spurs.lma)
        for node, rec in self.spur_rec.items():
            la[rec], lm[rec] = self._leaf_traits_of(node)
        return la, lm

    # -- sun and shade leaves ---------------------------------------------
    def leaf_traits(self, q: np.ndarray):
        """Leaf size (m2) and LMA (g m-2) from the leaf's relative light q:
        sun leaves are thicker and smaller (see light.sun_shade in the YAML)."""
        ss = getattr(self.sp.light, "sun_shade", None)
        a_ref = float(self.light.leaf_area)
        q = np.clip(np.asarray(q, float), 0.0, 1.0)
        if ss is None or not bool(ss.enabled):
            return np.full(q.shape, a_ref), np.full(q.shape, float(getattr(ss, "lma_reference_g_m2", 60.8) if ss else 60.8))
        lma = float(ss.lma_shade_g_m2) + float(ss.lma_sun_increase_g_m2) * np.power(q, float(ss.lma_exponent))
        size = a_ref * np.power(float(ss.lma_reference_g_m2) / lma, float(ss.size_lma_exponent))
        germ = getattr(self.sp, "germination", None)
        if germ is not None and bool(getattr(germ, "enabled", False)):
            h = float(self.stats[-1]["height_m"]) if len(self.stats) else 0.015
            bh_m = float(getattr(germ, "juvenile_scale_bh_m", 1.3))
            min_s = float(getattr(germ, "min_juvenile_scale", 0.20))
            scale = min(max(min_s + (1.0 - min_s) * (h / bh_m), min_s), 1.0)
            size = size * scale
        return size, lma

    def _leaf_costs(self, bud_nodes, bud_leaf, g_resp):
        """This season's leaf and fine-root costs, in model carbon units
        (resource.leaf_costs in the YAML): rebuilding each bud's leaves
        (dry mass = leaf area x LMA, plus growth respiration), their
        maintenance respiration over the leafy season, and the maintenance
        of the fine roots that go with them (a fixed fine-root to leaf mass
        ratio).  A unit is the carbon that builds wood_volume_per_carbon of
        wood, i.e. that volume times the wood's basic density in dry
        matter.  Returns per-bud build and maintenance, the fine-root
        maintenance and the leaf dry mass (g)."""
        lc = getattr(self.sp.resource, "leaf_costs", None)
        if lc is None or not bool(lc.enabled) or not len(bud_nodes):
            z = np.zeros(len(bud_nodes))
            return z, z, 0.0, 0.0
        g_per_unit = float(self.sp.pipe_model.wood_volume_per_carbon) * float(lc.wood_basic_density_kg_m3) * 1000.0
        T = self.tree
        dm = bud_leaf * T.lma[bud_nodes]                               # g dry matter
        build = dm / g_per_unit * g_resp
        if str(getattr(self.sp.pipe_model, "growth", "pipe")) == "lignum":
            # the leaves of last season's new shoots (their tips and fresh
            # lateral buds) were built with the shoots (_growth_factor)
            last = T.birth[bud_nodes] == self.year
            paid = last & ((T.term[bud_nodes] == 1) | ((T.lat[bud_nodes] == LAT_DORMANT) & (T.lat_age[bud_nodes] == 0)))
            if bool(getattr(lc, "charge_fresh_laterals", False)):
                # exploring: only one late leaf per node and a tip's cluster were charged with the
                # shoot, so a fresh lateral's cluster next spring is still to pay
                paid = last & (T.term[bud_nodes] == 1)
            build = np.where(paid, 0.0, build)
        # g C respired per g dry matter, back to dry-matter units
        maint = dm * float(lc.leaf_maintenance_gc_per_g) / float(lc.carbon_fraction) / g_per_unit
        roots = float(dm.sum()) * float(lc.fine_root_to_leaf_mass) * float(lc.fine_root_maintenance_gc_per_g) \
            / float(lc.carbon_fraction) / g_per_unit
        return build, maint, roots, float(dm.sum())

    def _size_rel(self, nodes):
        T = self.tree
        a_ref = float(self.light.leaf_area)
        return np.where(T.leaf_size[nodes] > 0, T.leaf_size[nodes] / a_ref, 1.0)

    def _herb_factor(self, z: np.ndarray) -> np.ndarray:
        """Light left under the herb layer at height z (Beer-Lambert through
        the leaf area of the field layer above z).  Where the tree germinated
        on bared mineral soil (``field_layer_exposed``: the tree year the soil
        was bared, None for undisturbed ground) the field layer grows back
        over it with the soil's recovery half-life."""
        flc = getattr(self.sp, "field_layer_competition", None)
        if flc is not None and bool(getattr(flc, "enabled", False)):
            t = self.year + 1
            exposed = getattr(self, "field_layer_exposed", 0)
            ytm = float(getattr(flc, "years_to_mature", 4.0))
            if exposed is not None:
                a = max(t - exposed, 0)
                f = min(a / ytm, 1.0) if ytm > 0 else 1.0
            else:
                f = 1.0
            max_h = float(getattr(flc, "max_height_m", 0.45))
            h = max_h * max(f, 0.25)
            lai = float(getattr(flc, "max_lai", 3.3)) * f
            k = float(getattr(flc, "extinction", 0.45))
            above = lai * np.clip(1.0 - np.asarray(z, float) / max(h, 1e-4), 0.0, 1.0)
            return np.exp(-k * above)

        s = self.soil
        h = float(getattr(s, "herb_height", 0.0) or 0.0) if s is not None else 0.0
        if h <= 0.0:
            return np.ones(len(z))
        lai = float(s.herb_lai)
        hl = float(getattr(s, "herb_recovery_half_life", 0.0) or 0.0)
        exposed = getattr(self, "field_layer_exposed", 0)
        if hl > 0.0 and exposed is not None:
            lai *= 1.0 - 0.5 ** (max(self.year + 1 - exposed, 0) / hl)
        above = lai * np.clip(1.0 - np.asarray(z, float) / h, 0.0, 1.0)
        return np.exp(-float(s.herb_extinction) * above)

    def _falls(self, value, line) -> np.ndarray:
        """Which parts die this year, from their own light or carbon against their line.  With shedding.shade_softness
        unset, all of those under it (as it has been).  With it set, the chance rises from 0 at the line to 1 at
        (1 - softness) of it, so the crown thins in step with how far under it each part is, never by its age."""
        soft = getattr(self.sp.shedding, "shade_softness", None)
        if soft is None:
            return value < line
        rng = self.__dict__.get("_fall_rng")
        if rng is None:
            rng = self._fall_rng = np.random.default_rng([self.seed, 5501])
        under = np.maximum(line - value, 0.0)
        chance = np.divide(under, float(soft) * line, out=np.zeros_like(under, dtype=float), where=(line * np.ones_like(under)) > 0.0)
        return rng.random(len(under)) < chance

    def _shed(self, t: int, roots: np.ndarray, levels: list):
        T = self.tree
        n = T.n
        kill = np.zeros(n, dtype=bool)
        kill[roots] = True
        par = T.parent
        for seg, _, _ in levels[1:]:
            kill[seg] |= kill[par[seg]]
        p = par[roots]
        # the dead branch's pipes stay in the parent as heartwood
        np.add.at(T.own_pipe, p, T.radius[roots] ** self.gamma)
        T.lat_child[p] = -1
        T.lat[p] = LAT_DEAD
        dead = np.nonzero(kill)[0]
        T.death[dead] = t
        T.term[dead] = 0
        for nd in dead[T.lat[dead] == LAT_SPUR].tolist():
            self._end_spur(nd, t)

    def _lateral_bud_dirs(self, D, R, order, axis, phyllo):
        """Lateral bud direction (and its azimuth vector u) for new metamers."""
        A = self.sp.architecture
        m = len(D)
        ortho = order == 0
        phase = np.asarray(self.axis_phase)[axis]
        phi_o = phase + phyllo * math.radians(A.phyllotaxis_orthotropic_deg)
        side = np.cross(D, UP)
        ns = np.linalg.norm(side, axis=1)
        side = np.where((ns > 0.2)[:, None], side / np.maximum(ns, 1e-12)[:, None], R)
        jitter = self.rng.normal(0.0, math.radians(A.distichous_jitter_deg), m)
        phi_p = phyllo * math.radians(A.phyllotaxis_plagiotropic_deg) + jitter
        base = np.where(ortho[:, None], R, side)
        phi = np.where(ortho, phi_o, phi_p)
        W = np.cross(D, base)
        u = np.cos(phi)[:, None] * base + np.sin(phi)[:, None] * W
        angles = np.radians(np.asarray(A.branch_angle_deg, dtype=float))
        theta = angles[np.minimum(order, len(angles) - 1)]
        bud = np.cos(theta)[:, None] * D + np.sin(theta)[:, None] * u
        return u, _normalize(bud)

    def _expansion(self, starts: np.ndarray) -> np.ndarray:
        """Hydraulic limit on expansion (Koch et al. 2004): turgor falls with
        height, so internodes (and leaves) get smaller while nodes keep
        forming.  Share of the full internode length at each start node."""
        sp, T = self.sp, self.tree
        hmax = getattr(sp.shoot, "max_tree_height", None)
        if self._psi is not None:
            if getattr(sp.hydraulics, "expansion_water_potential", "midday") == "predawn":
                # shoots and leaves expand mostly at night and early morning,
                # when the tree has rehydrated: pre-dawn potential = soil water
                # potential minus the gravitational gradient (rho g = 0.0098
                # MPa per m of height)
                psi_x = float(self.soil.water_potential) - 0.0098 * np.maximum(T.pos[starts, 2], 0.0)
            else:
                psi_x = self._psi[starts]
            expansion = hydraulics.expansion(psi_x, sp.hydraulics, sp.shoot.min_expansion)
        else:
            expansion = np.ones(len(starts))
        if hmax:
            expansion = np.minimum(expansion, np.clip(1.0 - T.pos[starts, 2] / float(hmax), float(sp.shoot.min_expansion), 1.0))
        return expansion

    def _leaf_path_length(self, levels, alive, bud_nodes, bud_leaf) -> np.ndarray:
        """Leaf-weighted mean path length (m) from each internode's distal end
        to the leaves beyond it (0 where it carries none)."""
        T = self.tree
        n0 = len(alive)
        par = T.parent
        L = T.length[:n0]
        d = np.zeros(n0)
        for seg, _, _ in levels[1:]:
            d[seg] = d[par[seg]] + L[seg]
        w = np.zeros(n0)
        np.add.at(w, bud_nodes, bud_leaf)
        W = T.basipetal(levels, w)
        WD = T.basipetal(levels, w * d)
        return np.where(W > 0.0, WD / np.maximum(W, 1e-30) - d, 0.0)

    def _stem_theory_stage(self) -> int:
        """pipe_model.stem_theory.stage: 0 off, 1 stage a (pipe model below
        the crown base, surplus sapwood to heartwood, no distance rule), 2
        stage b (stage a plus the wind envelope, sheltered inside a taller
        canopy)."""
        st = getattr(self.sp.pipe_model, "stem_theory", None)
        return int(getattr(st, "stage", 0) or 0) if st is not None else 0

    def _wind_load_scale(self, alive: np.ndarray, laz_base: float, wl, stage_b: bool = False):
        """Force per unit leaf area (N m-2) and area coefficient (m2 / (N m)^(2/3))
        for the ForestGALES roughness-method wind load (Gardiner et al. 1997,
        2000; Raupach 1994; Hale et al. 2015), distributed over the crown's
        foliage so the base turning moment equals d * rho * G * u_*^2 * D^2 * DLF.
        Stem theory stage b switches it on with stem_theory.wind_speed_m_s at
        the canopy top; a tree below the canopy top (in a plot: the tallest
        living tree) gets the wind at its own height, u_h exp(a (h / h_c - 1))
        (exponential within-canopy profile, a =
        stem_theory.canopy_wind_attenuation)."""
        if wl is None or laz_base <= 0.0:
            return 0.0, 0.0
        if not (bool(getattr(wl, "enabled", False)) or stage_b):
            return 0.0, 0.0
        T = self.tree
        n0 = len(alive)
        pos = T.pos[:n0][alive]
        h = float(pos[:, 2].max()) if len(pos) else 0.0
        if h <= 0.2:
            return 0.0, 0.0
        xy = pos[:, :2]
        bc = max(0.5 * (float(np.ptp(xy[:, 0])) + float(np.ptp(xy[:, 1]))), 0.1) if len(xy) > 1 else 0.1
        cb = float((self.stats[-1].get("crown_base_height_m") if self.stats else None) or 0.0)
        dc = max(h - cb, 0.1)
        D = float(getattr(self, "_plot_spacing", 0.0) or (math.sqrt(10000.0 / self.stems_per_ha(h)) if self.stand else max(bc, h)))
        u_h = float(wl.wind_speed_m_s)
        if stage_b:
            st = self.sp.pipe_model.stem_theory
            u_h = float(st.wind_speed_m_s)
            h_c = float(getattr(self, "_plot_canopy_height", 0.0) or 0.0)
            if h_c > h:
                u_h *= math.exp(float(st.canopy_wind_attenuation) * (h / h_c - 1.0))
        u_s = min(max(u_h, float(wl.streamlining_min_wind_m_s)), float(wl.streamlining_max_wind_m_s))
        cd = float(wl.streamlining_c) * (u_s ** -float(wl.streamlining_n))
        lam_c = cd * bc * dc / max(D * D, 1e-6)
        ustar = u_h * min(math.sqrt(0.003 + 0.15 * lam_c), 0.3)
        rt = math.sqrt(max(7.5 * lam_c, 1e-12))
        d_zpd = h * (1.0 - (1.0 - math.exp(-rt)) / rt)
        r_dh = max(D / h, 1e-4)
        gust = max(9.0 * max(0.0, -2.1 * r_dh + 0.91) + 1.0611 * math.log(r_dh) + 4.2, 1.0)
        m_base = d_zpd * float(wl.air_density_kg_m3) * (ustar ** 2) * (D ** 2) * gust * float(wl.deflection_loading_factor)
        sigma = float(wl.wood_mor_green_mpa) * 1e6 * float(getattr(wl, "knot_factor", 1.0)) / float(wl.safety_factor)
        return m_base / laz_base, math.pi * (4.0 / (math.pi * sigma)) ** (2.0 / 3.0)

    def _growth_factor(self, pool, g_resp, levels, alive, term_nodes, share_t, lat_nodes, share_l, q_bud,
                       bud_nodes, bud_leaf):
        """The year's growth factor, as in LIGNUM (Perttunen et al. 1996):
        each bud's new shoot is lambda x its Borchert-Honda share of the pool
        (metamers), and lambda is set so that the wood of the new shoots plus
        the sapwood rings the pipe model needs equal the net carbon (pool).
        Rings: every internode keeps huber_value of sapwood per unit of
        foliage beyond it (this season's leaves plus those of the new shoots,
        late and early), after sapwood_senescence_per_year of last year's
        sapwood has stopped conducting.  The new shoots' leaves are paid when
        they are built, next season (leaf_costs).  Returns lambda and the
        ring area (m2) of each internode."""
        sp, T = self.sp, self.tree
        n0 = len(alive)
        pm, bf, fw = sp.pipe_model, sp.bud_fate, sp.light.foliage_weight
        hv = float(sp.hydraulics.huber_value)
        b = float(getattr(pm, "huber_radius_exponent", 0.0) or 0.0)
        c = float(getattr(pm, "huber_path_exponent", 0.0) or 0.0)
        # stem theory (phase 37) stage a and up: plain pipe model, no rise of
        # the Huber value with path length or radius; below the crown base
        # the sapwood is the crown base's and the surplus is retired to
        # heartwood (crown_rise_heartwood, below)
        stage = self._stem_theory_stage()
        if stage >= 1:
            b = c = 0.0
        if c:
            # wood per unit of foliage beyond rises from tip to base with the
            # path length to the leaves it supplies (leaf-weighted mean):
            # huber_value at a current-year shoot, times (l / l_ref)^c
            l_ref = float(pm.huber_path_reference_m)
            ell = self._leaf_path_length(levels, alive, bud_nodes, bud_leaf)
            hv = hv * (np.maximum(ell, l_ref) / l_ref) ** c
        elif b:
            # wood per unit of foliage beyond rises from the twigs towards the
            # stem: huber_value at a current-year shoot (tip radius), times
            # (r / r_tip)^b
            r_tip = float(pm.tip_radius)
            hv = hv * (np.maximum(T.radius[:n0], r_tip) / r_tip) ** b
        la_now = np.zeros(n0)
        np.add.at(la_now, bud_nodes, bud_leaf)
        la_now = T.basipetal(levels, la_now)
        cr_hw = bool(getattr(pm, "crown_rise_heartwood", False)) or stage >= 1
        if cr_hw and bool(getattr(pm, "sapwood", True)):
            cb = float((self.stats[-1].get("crown_base_height_m") if self.stats else None) or 0.0)
            if cb > 0.0:
                below = alive & (T.pos[:n0, 2] < cb)
                if below.any():
                    trunk = T.trunk_chain(self.leader_axes)
                    above_cb = trunk[T.pos[trunk, 2] >= cb]
                    if len(above_cb) > 0:
                        cb_node = int(above_cb[0])
                        if isinstance(hv, np.ndarray):
                            hv = hv.copy()
                            hv[below] = hv[cb_node]
                        a_su = (hv[cb_node] if isinstance(hv, np.ndarray) else hv) * la_now[cb_node]
                        if bool(getattr(pm, "heartwood_by_own_foliage", False)):
                            # each internode keeps the sapwood its own foliage beyond needs.  With the crown base's
                            # figure, a forked stem's other fork loses it every year and must rebuild it, at
                            # 28 cm2 a year (seed 3 at 45), whatever its crown does
                            a_su = hv * la_now
                        excess = below & (T.sap_area[:n0] > a_su)
                        if excess.any():
                            T.sap_area[:n0] = np.where(excess, a_su, T.sap_area[:n0])
        if bool(getattr(pm, "sapwood", True)):
            # sapwood only, after a share of last year's turned to heartwood
            keep = np.where(alive, (1.0 - self._sapwood_loss(n0)) * T.sap_area[:n0], 0.0)
        else:
            # no distinct heartwood (birch): the requirement is on the whole
            # wood cross-section, so no wood is counted twice
            keep = np.where(alive, T.wood_area[:n0], 0.0)
        z_node = T.pos[:n0, 2]
        z_base = T.pos[np.maximum(T.parent[:n0], 0), 2]
        laz_now = np.zeros(n0)
        np.add.at(laz_now, bud_nodes, bud_leaf * z_node[bud_nodes])
        laz_now = T.basipetal(levels, laz_now)
        f_wind, a_wind_coef = self._wind_load_scale(alive, float(laz_now[0]), getattr(pm, "wind_load", None),
                                                    stage_b=stage >= 2)
        wood_keep = np.where(alive, T.wood_area[:n0], 0.0)
        L = np.where(alive, T.length[:n0], 0.0)
        L[0] = 0.0
        unit = float(pm.wood_volume_per_carbon) / g_resp          # m3 of wood built per unit of carbon
        tip_area = np.pi * float(pm.tip_radius) ** 2
        starts = np.concatenate([term_nodes, lat_nodes])
        share = np.concatenate([share_t, share_l])
        thr = np.concatenate([np.full(len(term_nodes), float(getattr(bf, "min_tip_extension", 1.0))),
                              np.where(T.lat[lat_nodes] == LAT_SPUR, float(bf.spur_release_threshold),
                                       float(bf.long_shoot_threshold))])
        nmax = max(1, int(float(sp.shoot.max_shoot_length) / self.l0))
        full = self.l0 * self._expansion(starts)
        size, lma = self.leaf_traits(q_bud)                           # m2 per leaf, g m-2, at each bud's light
        per_met = float(fw.new_leaf) * size
        early = float(getattr(fw, "early_leaves", 0.0) or 0.0) * size
        lc = getattr(sp.resource, "leaf_costs", None)
        g_per_unit = float(pm.wood_volume_per_carbon) * (float(lc.wood_basic_density_kg_m3) * 1000.0 if lc else 0.0)
        # Diagnosis, off by default, no source (M3a): rings are sized for the leaves a new node
        # will carry next season, not for the single leaf it carries this year
        ahead = bool(getattr(pm, "sapwood_for_next_season", False))
        extra_per_node = (float(getattr(fw, "early_leaves", 0.0) or 0.0) - float(fw.new_leaf)) * size if ahead else 0.0

        hd = getattr(self, "_hd", None)
        lead_at = None
        caps = nmax
        ring_cap = None
        if hd is not None:
            # the leader's shoot, limited by the curve, is built first and paid first.  No side shoot may end
            # above the leader's.  Rings can't take more than ring_share_max of the pool (shoots flush first).
            lead_at = hd["bud"] if hd["is_tip"] else len(term_nodes) + hd["bud"]
            cfg = sp.height_driver
            if getattr(cfg, "ring_share_max", None) is not None:
                ring_cap = float(cfg.ring_share_max) * pool
            self._unspent = 0.0
            self._frame_earned(starts, q_bud, bud_leaf)
            caps = self._height_limit_caps(starts, len(term_nodes), full, hd, lead_at, nmax)
            hd["lead_at"] = lead_at
            hd["frame_at"], hd["frame_v"] = self._frame_plan(starts, len(term_nodes), full, hd, q_bud, nmax) if self._frame_on() else (None, None)
            if hd["frame_at"] is not None:
                caps[hd["frame_at"]] = np.minimum(self._frame_room(starts, hd, full, nmax)[hd["frame_at"]], hd["frame_v"])
                hd["frame_v"] = caps[hd["frame_at"]].copy()
                caps = self._frame_twig_caps(starts, len(term_nodes), full, caps, hd)
            hd["caps"], hd["thr"], hd["lead_at"] = caps, thr, lead_at

        def shoots(lam):
            v = lam * share
            grow = (v >= thr) & (share > 0.0)
            if lead_at is not None:
                grow = grow & (caps >= thr)
                if hd["frame_at"] is not None:
                    # the frame's limbs: paid first, like the leader, by what the frame and their own light allow
                    v[hd["frame_at"]] = hd["frame_v"]
                    grow[hd["frame_at"]] = hd["frame_v"] >= thr[hd["frame_at"]]
                v[lead_at] = hd["v"]
                grow[lead_at] = hd["v"] > 0.0
            return v, grow

        def parts(lam):
            v, grow = shoots(lam)
            vc = np.minimum(v, caps)
            shoot_vol = tip_area * float((full * vc)[grow].sum())
            # the new shoots' leaves (late, one per node, and early) are built
            # with them; next season they are not built again (_leaf_costs)
            leaf_area = np.where(grow, np.maximum(np.floor(vc), 1.0) * per_met + early, 0.0)
            leaf_units = float((leaf_area * lma).sum()) / g_per_unit * g_resp if g_per_unit > 0.0 else 0.0
            piped = leaf_area + np.where(grow, np.floor(vc) * extra_per_node, 0.0) if ahead else leaf_area
            dla = np.zeros(n0)
            np.add.at(dla, starts, piped)
            la_tot = la_now + T.basipetal(levels, dla)
            ring = np.maximum(hv * la_tot - keep, 0.0)
            if f_wind > 0.0:
                dlaz = np.zeros(n0)
                np.add.at(dlaz, starts, piped * z_node[starts])
                laz_tot = laz_now + T.basipetal(levels, dlaz)
                # the base moment comes from the canopy (_wind_load_scale), not from this year's new leaves.  With the
                # limit on it stays that moment; without, each new leaf raises it and so the whole stem's ring
                f_year = f_wind if lead_at is None else f_wind * float(laz_now[0]) / max(float(laz_tot[0]), 1e-12)
                m_wind = f_year * np.maximum(laz_tot - z_base * la_tot, 0.0)
                a_wind = a_wind_coef * np.cbrt(m_wind) ** 2
                if lead_at is not None:
                    # sapwood for the leaves comes first; the wind's thickening is what can wait
                    extra = np.maximum(a_wind - wood_keep - ring, 0.0)
                    hd["sap_units"] = float((ring * L).sum()) / unit
                    extra_units = float((extra * L).sum()) / unit
                    hd["wind_units"] = extra_units
                    if ring_cap is not None:
                        room = max(ring_cap - hd["sap_units"], 0.0)
                        if extra_units > room:
                            extra = extra * (room / extra_units)
                    ring = ring + extra
                else:
                    ring = np.maximum(ring, a_wind - wood_keep)
            return (shoot_vol + float((ring * L).sum())) / unit + leaf_units, ring

        if fast.on(sp, "compiled_carbon"):
            parts = fast.parts_function(hd, lead_at, ahead, share, thr, caps, full, per_met, early, lma, extra_per_node, starts, z_node, levels, alive, T.parent,
                                        la_now, hv, keep, L, f_wind, a_wind_coef, laz_now, z_base, wood_keep, ring_cap, tip_area, unit, g_per_unit, g_resp)
        c0, r0 = parts(0.0)
        self._ring_need = c0
        if lead_at is not None:
            hd["sap_units0"], hd["wind_units0"] = hd.get("sap_units", 0.0), hd.get("wind_units", 0.0)
            # the leader's own shoot and leaves come first; if the pool can't pay them, it builds less
            vl = float(min(hd["v"], nmax))
            lead_units = tip_area * float(full[lead_at]) * vl / unit
            if g_per_unit > 0.0:
                lead_units += float((max(math.floor(vl), 1.0) * per_met[lead_at] + early[lead_at]) * lma[lead_at]) / g_per_unit * g_resp
            hd["cost_units"], hd["pool"] = lead_units, pool
            if lead_units >= pool:
                hd["carbon_scale"] = pool / lead_units if lead_units > 0.0 else 0.0
                hd["v"] *= hd["carbon_scale"]
                hd["cost_units"] = pool
                if hd["frame_at"] is not None:
                    hd["frame_v"] = np.zeros_like(hd["frame_v"])   # nothing left for limbs: no shoot is free
                return 0.0, np.zeros(n0)
            self._ring_need = c0 - lead_units
            if c0 >= pool:
                # after the leader, the foliage's sapwood takes what's left: no side shoots
                if hd["frame_at"] is not None:
                    hd["frame_v"] = np.zeros_like(hd["frame_v"])
                return 0.0, r0 * ((pool - lead_units) / max(c0 - lead_units, 1e-12))
        if c0 >= pool:
            # the foliage's sapwood alone takes the whole pool: no new shoots,
            # and only that share of the rings
            return 0.0, r0 * (pool / c0 if c0 > 0.0 else 0.0)

        def solve_for(target):
            if fast.on(sp, "quick_solve"):
                lo, hi = fast.quick_bisect(parts, target, getattr(self, "_lam_guess", 1.0))
                self._lam_guess = lo
            else:
                lo, hi = 0.0, 1.0
                while parts(hi)[0] < target and hi < 1e7:
                    lo, hi = hi, 2.0 * hi
                for _ in range(40):
                    mid = 0.5 * (lo + hi)
                    if parts(mid)[0] < target:
                        lo = mid
                    else:
                        hi = mid
            if lead_at is not None and getattr(sp.height_driver, "leaf_growth_max", None) is not None:
                # the crown can't add more leaf area in a year than this many times what it has (sink
                # limit, standing in for nutrients and competition); what's left goes to the store or is lost
                limit = float(sp.height_driver.leaf_growth_max) * float(la_now[0])
                full_crown = False
                if self._frame_on() and getattr(sp.crown_frame, "crown_lai_max", None):
                    # nor more than the frame's crown can hold, a sink limit: without it a tree with light to spare
                    # spends everything on more leaves, and they pay for more still
                    room_la = max(float(sp.crown_frame.crown_lai_max) * math.pi * self._frame_reach_max() ** 2 - float(la_now[0]), 0.0)
                    full_crown = room_la < limit
                    limit = min(limit, room_la)

                def side_area(x):
                    v, grow = shoots(x)
                    vc = np.minimum(v, caps)
                    grow[lead_at] = False
                    return float((np.floor(vc[grow]) * next_leaves * size[grow]).sum())

                if side_area(lo) > limit:
                    a, b = 0.0, lo
                    for _ in range(40):
                        mid = 0.5 * (a + b)
                        if side_area(mid) < limit:
                            a = mid
                        else:
                            b = mid
                    lo = a
                    self._unspent = max(target - parts(lo)[0], 0.0)
                    share_stem = float(getattr(getattr(sp, "crown_frame", None), "surplus_to_stem", 0.0) or 0.0)
                    if full_crown and share_stem > 0.0 and self._unspent > 0.0:
                        # what a full crown can't use goes on the stem, as a tree in the open has it: rings by the leaf area above
                        stem = T.trunk_chain(self.leader_axes)
                        stem = stem[stem < n0]
                        w = la_now[stem] / max(float(la_now[0]), 1e-12)
                        spread = float((w * L[stem]).sum())
                        if spread > 0.0:
                            used = share_stem * self._unspent
                            ring_out = parts(lo)[1].copy()
                            ring_out[stem] += w * used * unit / spread
                            self._unspent -= used
                            return lo, ring_out
            return lo, parts(lo)[1]

        next_leaves = max(float(getattr(fw, "early_leaves", 0.0) or 0.0), float(fw.spur))
        lam, ring = solve_for(pool)
        f_late = float(getattr(fw, "late_leaf_season_fraction", 0.0) or 0.0)
        if f_late > 0.0:
            v, grow = shoots(lam)
            vc = np.minimum(v, caps)
            late_area = np.where(grow, np.floor(vc) * per_met, 0.0)
            if float(late_area.sum()) > 0.0:
                alpha = float(sp.resource.alpha)
                a_ref = float(self.light.leaf_area)
                phi_s = self.water.get("stomatal_opening", 1.0) if hasattr(self, "water") and self.water else 1.0
                root_share = self.water.get("root_share", 0.0) if hasattr(self, "water") and self.water else 0.0
                maint_per_g = (float(lc.leaf_maintenance_gc_per_g) / float(lc.carbon_fraction) / g_per_unit) if (lc and g_per_unit > 0) else 0.0
                root_maint_per_g = (float(lc.fine_root_to_leaf_mass) * float(lc.fine_root_maintenance_gc_per_g) / float(lc.carbon_fraction) / g_per_unit) if (lc and g_per_unit > 0) else 0.0
                c_late = f_late * alpha * float((q_bud * phi_s * (late_area / a_ref)).sum())
                late_dm = late_area * lma
                late_maint = f_late * float(late_dm.sum()) * maint_per_g
                late_shoot_net = max((1.0 - root_share) * c_late - late_maint, 0.0)
                late_root_maint = f_late * float(late_dm.sum()) * root_maint_per_g
                late_root_net = max(root_share * c_late - late_root_maint, 0.0)
                self._root_carbon += late_root_net
                self.carbon["fixed"] += c_late
                self.carbon["shoot"] += (1.0 - root_share) * c_late
                self.carbon["root"] += root_share * c_late
                self.carbon["leaf_maint"] += late_maint
                self.carbon["fine_root_maint"] += late_root_maint
                self.carbon["upkeep"] += late_maint + late_root_maint
                self.carbon["leaf_dm_g"] += float(late_dm.sum())
                self.carbon["late_shoot_net"] = late_shoot_net
                self.carbon["late_root_net"] = late_root_net
                if hasattr(self, "_npp_base") and self.carbon["fixed"] > 0:
                    npp = self._npp_base + (late_shoot_net + late_root_net) / g_resp
                    self.carbon["cue"] = npp / self.carbon["fixed"]
                pool = pool + late_shoot_net
                lam, ring = solve_for(pool)
        if hd is not None and self._frame_on():
            # only read, for the reports: where the year's pool went.  What's left of it is lost
            v, grow = shoots(lam)
            vc = np.minimum(v, caps)
            wood = tip_area * full * vc / unit
            leaf = np.where(grow, np.maximum(np.floor(vc), 1.0) * per_met + early, 0.0) * lma / g_per_unit * g_resp if g_per_unit > 0.0 else np.zeros(len(starts))
            cost = np.where(grow, wood + leaf, 0.0)
            is_limb = np.zeros(len(starts), bool)
            if hd["frame_at"] is not None:
                is_limb[hd["frame_at"]] = True
            hd["use"] = {"pool": float(pool), "lead": float(cost[lead_at]), "limbs": float(cost[is_limb].sum()),
                         "twigs": float(cost.sum() - cost[lead_at] - cost[is_limb].sum()), "rings": float((ring * L).sum()) / unit,
                         "twig_shoots": int((grow & ~is_limb).sum()), "at_cap": int((grow & ~is_limb & (v >= caps)).sum())}
        return lam, ring

    # -- the crown's frame (crown_frame in the species file) -------------
    def _frame_on(self) -> bool:
        cf = getattr(self.sp, "crown_frame", None)
        return cf is not None and bool(cf.enabled) and self._height_limit_on()

    def _frame_buds(self) -> dict:
        """Buds on the stem named to start a limb: node -> that limb's set-point (rad from vertical)."""
        d = self.__dict__.get("_frame_named")
        if d is None:
            d = self._frame_named = {}
            self._frame_gsa = {}       # limb's axis -> its own set-point
            self._frame_reach = {}     # named bud -> its limb's own share of the frame's reach
            self._frame_axis_reach = {}  # limb's axis -> the same
            self._frame_since = 0.0    # stem grown since the last named bud (m)
            self._frame_azimuth = 0.0
            self._frame_rng = np.random.default_rng([self.seed, 7741])
            self._frame_fork_of = {}   # fork's axis -> first node of the limb it's on
            self._frame_fork_buds = {}  # named bud for a fork -> first node of its limb
            # does this tree fork?  Drawn once, as clones differ (Zeltins et al. 2018): reiterated limbs of the others stay limbs
            self._frame_forks = bool(self._frame_rng.random() < float(self.sp.crown_frame.fork_share_of_trees))
        return d

    def _frame_setpoints(self) -> np.ndarray:
        """By axis: the limb's own set-point, NaN for anything else."""
        self._frame_buds()
        out = np.full(len(self.axis_phase), np.nan)
        if self._frame_gsa:
            out[np.fromiter(self._frame_gsa.keys(), np.int64)] = np.fromiter(self._frame_gsa.values(), float)
        if self.reit_axes and self._frame_forks:
            # a limb that has become a small tree on the tree stands up, as the rest of the model has it
            out[np.fromiter(self.reit_axes, np.int64)] = math.radians(float(self.sp.resource.reiteration.setpoint_angle_deg))
        return out

    def _frame_shares(self) -> np.ndarray:
        """By axis: the limb's own share of the frame's reach, 1 for anything else."""
        self._frame_buds()
        out = np.ones(len(self.axis_phase))
        if self._frame_axis_reach:
            out[np.fromiter(self._frame_axis_reach.keys(), np.int64)] = np.fromiter(self._frame_axis_reach.values(), float)
        return out

    def _frame_crown(self):
        """Tree height, crown base and crown length (m), as last measured."""
        s = self.stats[-1]
        h = float(s["height_m"])
        base = float(s.get("crown_base_height_m") or 0.0)
        return h, base, max(h - base, 0.05)

    def _frame_name_buds(self, t: int, n_before: int) -> None:
        """Along the stem grown this year, name a bud for a limb every so many metres, from the published number per
        length of crown: Lintunen 2013's limbs per 10 % of crown length.  New limbs stand closer than that, since the
        lower ones thin out in the shade: birth_share is the mean over the top of the crown, his Fig. 5."""
        T, cf = self.tree, self.sp.crown_frame
        named = self._frame_buds()
        # those that became something else, or whose node died
        for node in [k for k in named if T.lat[k] != LAT_DORMANT or T.death[k] >= 0]:
            named.pop(node)
            self._frame_fork_buds.pop(node, None)
        new = np.arange(n_before, T.n)
        stem = new[np.isin(T.axis[new], np.fromiter(self.leader_axes, np.int64)) & (T.birth[new] == t)]
        if not stem.size:
            return
        _, _, crown = self._frame_crown()
        gap = max(float(cf.birth_share) * crown / (10.0 * float(cf.limbs_per_10pct_crown)), float(cf.gap_min_m))
        rng = self._frame_rng
        sd, lo, hi = float(cf.angle_sd_deg), float(cf.angle_min_deg), float(cf.angle_max_deg)
        for node in stem[np.argsort(T.pos[stem, 2])].tolist():
            self._frame_since += float(T.length[node])
            if self._frame_since < gap * float(rng.uniform(1.0 - float(cf.gap_scatter), 1.0 + float(cf.gap_scatter))):
                continue
            self._frame_since = 0.0
            theta = math.radians(float(np.clip(rng.normal(float(cf.angle_mean_deg), sd), lo, hi)))
            self._frame_reach[node] = float(np.exp(rng.normal(0.0, float(cf.reach_scatter))))
            A = self.sp.architecture
            self._frame_azimuth += math.radians(float(A.phyllotaxis_orthotropic_deg) + float(rng.normal(0.0, float(A.distichous_jitter_deg))))
            d = T.dir[node] / max(float(np.linalg.norm(T.dir[node])), 1e-12)
            a = np.array([math.cos(self._frame_azimuth), math.sin(self._frame_azimuth), 0.0])
            u = a - float(a @ d) * d
            u /= max(float(np.linalg.norm(u)), 1e-12)
            T.lat_dir[node] = math.cos(theta) * d + math.sin(theta) * u
            T.lat[node] = LAT_DORMANT
            T.no_axil[node] = False
            named[node] = theta

    def _frame_name_forks(self, t: int, n_before: int) -> None:
        """A limb carrying more leaf area than its axes can hold forks: its brightest new node's bud is named for another axis, stiff like the limb and rising like it, and it
        goes on as the limb does.  So a limb that wins light gets thicker and forks, and one that loses it stays thin and single."""
        cf = self.sp.crown_frame
        per_axis = getattr(cf, "fork_leaf_area_m2", None)
        la = getattr(self, "_frame_la", None)
        if not per_axis or la is None:
            return
        T = self.tree
        self._frame_buds()
        n = T.n
        new = np.arange(n_before, n)
        new = new[(T.birth[new] == t) & (T.death[new] < 0) & (T.lat[new] == LAT_DORMANT) & (T.scaffold[new] > 0) & ~np.isin(T.axis[new], np.fromiter(self.leader_axes, np.int64))]
        if not new.size:
            return
        alive_axis = np.zeros(int(T.axis[:n].max()) + 1, bool)
        alive_axis[T.axis[:n][T.death[:n] < 0]] = True
        forks = {}
        for ax, limb in self._frame_fork_of.items():
            if alive_axis[ax]:
                forks[limb] = forks.get(limb, 0) + 1
        for limb in self._frame_fork_buds.values():
            forks[limb] = forks.get(limb, 0) + 1
        sc = T.scaffold[new].astype(np.int64)
        # only on the limb's own axis or on a fork of it
        own = np.zeros(int(T.axis[:n].max()) + 1, bool)
        own[T.axis[np.unique(sc)]] = True
        if self._frame_fork_of:
            own[np.fromiter(self._frame_fork_of.keys(), np.int64)] = True
        on_axes = own[T.axis[new]]
        new, sc = new[on_axes], sc[on_axes]
        if not new.size:
            return
        q = self._field.exposure(T.pos[new], np.zeros(len(new)))
        spread = math.radians(float(self.sp.architecture.branch_angle_deg[1]))
        for limb in np.unique(sc).tolist():
            if limb >= len(la) or la[limb] <= float(per_axis) * (1 + forks.get(limb, 0)):
                continue
            at = np.nonzero(sc == limb)[0]
            node = int(new[at[np.argmax(q[at])]])
            d = T.dir[node] / max(float(np.linalg.norm(T.dir[node])), 1e-12)
            side = np.cross(d, np.array([0.0, 0.0, 1.0]))
            side /= max(float(np.linalg.norm(side)), 1e-12)
            side *= float(self._frame_rng.choice((-1.0, 1.0)))
            T.lat_dir[node] = math.cos(spread) * d + math.sin(spread) * side
            T.lat[node] = LAT_DORMANT
            T.no_axil[node] = False
            self._frame_fork_buds[node] = limb
            self._frame_named[node] = self._frame_gsa.get(int(T.axis[limb]), math.radians(float(cf.angle_mean_deg)))

    def _frame_reach_max(self) -> float:
        """The crown's radius, from the stem and the height (m)."""
        cf = self.sp.crown_frame
        h, _, _ = self._frame_crown()
        d_wood = self.dbh_m()
        d_ob = 100.0 * float(cf.over_bark_ratio) * d_wood if d_wood is not None else 0.0
        # the crown follows the stem, and the stem follows the crown's leaves: with nothing to hold it, a tree in the open runs away.
        # So no more stem counts here than a birch of this height has at the most
        d_ob = min(d_ob, float(cf.stem_cm_per_height_m) * h)
        return 0.5 * (float(cf.crown_a) + float(cf.crown_b) * d_ob)

    def _frame_earned(self, starts, q_bud, bud_leaf) -> None:
        """With crown_frame.earned_power set: the light on each limb's leaves this year, a limb's own, to that power, and by earned_size how its leaf area
        compares with the largest limb's.  A limb's reach and its side shoots go with this, so that one that wins light grows on and thickens, and one that loses it
        stops short."""
        cf = self.sp.crown_frame
        self._frame_rel = self._frame_q = self._frame_la = None
        if getattr(cf, "earned_power", None) is None and not getattr(cf, "fork_leaf_area_m2", None):
            return
        T = self.tree
        sc = T.scaffold[starts].astype(np.int64)
        on = sc > 0
        e = np.zeros(T.n)
        la = np.zeros(T.n)
        np.add.at(e, sc[on], (q_bud * bud_leaf)[on])
        np.add.at(la, sc[on], bud_leaf[on])
        q = np.divide(e, la, out=np.ones(T.n), where=la > 0.0)
        self._frame_la = la
        if getattr(cf, "earned_power", None) is None:
            return
        self._frame_q = np.minimum(q, 1.0)
        rel = np.power(self._frame_q, float(cf.earned_power))
        size = float(getattr(cf, "earned_size", 0.0) or 0.0)
        top = float(la.max())
        if size > 0.0 and top > 0.0:
            rel = rel * np.power(la / top, size)
        self._frame_rel = rel

    def _frame_goal(self, base, first=None) -> np.ndarray:
        """How far a limb starting at these stem nodes may reach (m), before its own share.  first: the limb's first nodes, where earned_power is set."""
        T, cf = self.tree, self.sp.crown_frame
        h, _, crown = self._frame_crown()
        reach_max = self._frame_reach_max()
        overlap = getattr(cf, "spacing_overlap", None)
        if overlap:
            # neighbours: a limb that meets the next crown stops there.  The spacing here is the stand's mean, not this tree's own gap
            spacing = float(getattr(self, "_plot_spacing", 0.0) or (self.stand_spacing(h) if self.stand else 0.0))
            if spacing > 0.0:
                reach_max = min(reach_max, 0.5 * float(overlap) * spacing)
        rel = getattr(self, "_frame_rel", None)
        if rel is not None:
            # what the limb has earned sets how far it goes: no table by place in the crown
            return reach_max * np.where(first >= 0, rel[np.minimum(np.maximum(first, 0), len(rel) - 1)], 1.0)
        depth = np.clip((h - T.pos[base, 2]) / crown, 0.0, 1.0)
        peak = float(cf.peak_depth)
        top = float(cf.top_share)
        above = top + (1.0 - top) * np.power(np.minimum(depth / peak, 1.0), float(cf.profile_power))
        # below the widest point the frame falls again, to base_share at the crown base: a crown is not a cone
        below = 1.0 - (1.0 - float(cf.base_share)) * np.maximum(depth - peak, 0.0) / max(1.0 - peak, 1e-6)
        return reach_max * above * below

    def _frame_twig_caps(self, starts, n_term, full, caps, hd) -> np.ndarray:
        """Twigs stay inside the reach of the limb they stand on: free to grow down, along or inward, as light and carbon
        allow, but going outward they run out of room a little past the limb's own reach."""
        T, cf = self.tree, self.sp.crown_frame
        lim = caps.copy()
        keep = np.ones(len(starts), bool)
        if hd["frame_at"] is not None:
            keep[hd["frame_at"]] = False
        keep[hd["lead_at"]] = False
        sc = T.scaffold[starts].astype(np.int64)
        i = np.nonzero(keep & (sc > 0) & (T.order[starts] >= 1))[0]
        if not i.size:
            return lim
        node, first = starts[i], sc[i]
        base = T.parent[first]
        d = np.where((i < n_term)[:, None], T.term_dir[node], T.lat_dir[node])[:, :2]
        off = T.pos[node, :2] - T.pos[base, :2]
        r = np.maximum(np.hypot(off[:, 0], off[:, 1]), 1e-6)
        outward = (d * off).sum(1) / r
        goal = self._frame_goal(base, first) * self._frame_shares()[T.axis[first]] * float(cf.twig_overshoot)
        room = np.maximum(goal - r, 0.0) / np.maximum(outward, 0.05)
        lim[i] = np.where(outward > 0.05, np.minimum(lim[i], room / full[i]), lim[i])
        return lim

    def _frame_room(self, starts, hd, full, nmax) -> np.ndarray:
        """The most each bud may make without ending above the leader's top, in metamers."""
        T = self.tree
        lead_len = float(full[hd["lead_at"]]) * float(min(hd["v"], nmax)) if "lead_at" in hd else 0.0
        n_term = hd.get("n_term", 0)
        dz = np.concatenate([T.term_dir[starts[:n_term], 2], T.lat_dir[starts[n_term:], 2]])
        top = max(hd["z"] + lead_len * hd["dz"], float(hd["ref"]))
        room = np.maximum(top - T.pos[starts, 2], 0.0)
        return np.where(dz > 0.02, room / (np.maximum(dz, 0.02) * full), float(nmax))

    def _frame_plan(self, starts, n_term, full, hd, q_bud, nmax):
        """This year's shoot, in metamers, for each limb's tip and each named bud.  The frame gives how far the limb may
        reach; its own light and the tree's water decide how much of that it grows this year; it's paid first, from the
        pool, and it's real nodes.  Nothing is placed: a limb in the shade falls short, and the same rules as ever kill it.

        Reach: crown diameter from the stem (Hemery 2005 for an open-grown birch; a stand's crowns fall short of it in
        each other's shade), and no wider than a young tree's height allows (Klepacki 2017).  By place in the crown: from
        top_share of it at the very top to all of it at the crown base (Lintunen 2013's Fig. 5)."""
        T, cf = self.tree, self.sp.crown_frame
        hd["n_term"] = n_term
        n = T.n
        on = np.isin(T.axis[:n], np.fromiter(self.leader_axes, np.int64))
        par = np.maximum(T.parent[:n], 0)
        firsts = np.nonzero((T.death[:n] < 0) & T.is_lateral[:n] & ~on & on[par])[0]
        first_of = np.full(len(self.axis_phase), -1, np.int64)
        first_of[T.axis[firsts]] = firsts
        fork_of = self.__dict__.get("_frame_fork_of") or {}
        for ax, limb in fork_of.items():
            if ax < len(first_of):
                first_of[ax] = limb
        is_tip = np.arange(len(starts)) < n_term
        limb_tip = is_tip & (first_of[T.axis[starts]] >= 0) & ~on[starts]
        named = self._frame_buds()
        is_named = ~is_tip & np.isin(starts, np.fromiter(named.keys(), np.int64))
        at = np.nonzero(limb_tip | is_named)[0]
        if not at.size:
            return None, None
        node = starts[at]
        base = np.where(limb_tip[at], T.parent[first_of[T.axis[node]]], node)
        share = self._frame_shares()[T.axis[node]]
        for i in np.nonzero(~limb_tip[at])[0].tolist():
            share[i] = self._frame_reach.get(int(node[i]), 1.0)
        goal = self._frame_goal(base, np.where(limb_tip[at], first_of[T.axis[node]], -1)) * share
        # how long the limb's own axis has grown (a steep limb gains no reach, and mustn't climb the stem to find it)
        alive = T.death[:n] < 0
        length = np.bincount(T.axis[:n][alive], weights=T.length[:n][alive], minlength=len(self.axis_phase))
        grown = np.where(limb_tip[at], length[T.axis[node]], 0.0)
        # to the same reach, a steep limb is longer than a level one; length_per_reach is for a limb at the mean angle
        own = self._frame_setpoints()[T.axis[node]]
        for i in np.nonzero(~limb_tip[at])[0].tolist():
            own[i] = named.get(int(node[i]), np.nan)
        mean = math.radians(float(cf.angle_mean_deg))
        steep = math.sin(mean) / np.maximum(np.sin(np.where(np.isfinite(own), own, mean)), float(cf.steep_limit))
        reach = np.hypot(T.pos[node, 0] - T.pos[base, 0], T.pos[node, 1] - T.pos[base, 1])
        out = np.where(limb_tip[at], np.hypot(T.term_dir[node, 0], T.term_dir[node, 1]), np.hypot(T.lat_dir[node, 0], T.lat_dir[node, 1]))
        room = np.minimum(goal * float(cf.length_per_reach) * steep - grown, (goal - reach) / np.maximum(out, 0.5))
        # apical control: no limb's shoot longer than the leader's this year, down to a floor for an old leader's short shoots
        lead_len = float(full[hd["lead_at"]]) * float(min(hd["v"], nmax)) if "lead_at" in hd else 0.0
        longest = max(lead_len, float(cf.limb_shoot_floor_m))
        grow = np.minimum(float(cf.chase) * np.maximum(room, 0.0), longest)
        if getattr(self, "_frame_rel", None) is not None:
            # a new limb starts at the floor's length, by its light; its reach then follows what it earns
            grow = np.where(limb_tip[at], grow, float(cf.limb_shoot_floor_m))
        if self.reit_axes and self._frame_forks:
            # a reiterated limb goes up as a second top: only the room under the tree's top holds it (_frame_room)
            grow = np.where(limb_tip[at] & np.isin(T.axis[node], np.fromiter(self.reit_axes, np.int64)), longest, grow)
        light = np.minimum(q_bud[at], 1.0)      # a limb's yearly shoot goes with the light at its own tip
        # a limb loses vigour as it ages (resource.branch_aging_years, Barthelemy & Caraglio 2007), so the crown's old lower limbs fall
        # behind the younger ones above them, as a crown in the open needs, or it's a cone
        age = np.where(limb_tip[at], np.maximum(self.year + 1.0 - T.scaffold_birth[node], 0.0), 0.0)
        if getattr(self, "_frame_rel", None) is not None:
            age = 0.0 * age     # a limb grows on for as long as it earns
        limb_years = getattr(cf, "limb_ageing_years", None)
        grow = grow * light * float(hd["water"]) * np.exp(-age / float(limb_years if limb_years else self.sp.resource.branch_aging_years))
        return at, np.minimum(grow / full[at], float(nmax))

    # -- the height limit (height_driver in the species file) -----------
    def _limb_nodes(self, n: int):
        """With mechanics.pendulous_radius_limb set: which of the first n nodes belong to a limb, a side axis on the stem.  The
        pendulous trait is then a twig trait: limbs go soft only where they're thinner than that radius, near their tips.  None if unset."""
        if getattr(self.sp.mechanics, "pendulous_radius_limb", None) is None:
            return None
        T = self.tree
        on = np.isin(T.axis[:n], np.fromiter(self.leader_axes, np.int64))
        first = T.is_lateral[:n] & ~on & on[np.maximum(T.parent[:n], 0)]
        limb_axes = T.axis[:n][first]
        forks = self.__dict__.get("_frame_fork_of")
        if forks:
            limb_axes = np.concatenate([limb_axes, np.fromiter(forks.keys(), np.int64)])
        return np.isin(T.axis[:n], limb_axes)

    def _sapwood_loss(self, n: int):
        """The share of last year's sapwood that stops conducting this year, on the first n nodes.  With
        pipe_model.branch_sapwood_senescence set, side axes have their own rate; otherwise one figure for the whole tree."""
        pm = self.sp.pipe_model
        branch = getattr(pm, "branch_sapwood_senescence", None)
        if branch is None:
            return float(pm.sapwood_senescence_per_year)
        on_stem = np.isin(self.tree.axis[:n], np.fromiter(self.leader_axes, np.int64))
        return np.where(on_stem, float(pm.sapwood_senescence_per_year), float(branch))

    def _height_limit_on(self) -> bool:
        hd = getattr(self.sp, "height_driver", None)
        return hd is not None and bool(hd.enabled)

    def _curve_height(self, age: float) -> float:
        """The approved curve at this total age (Eriksson et al. 1997 as in Elfving 2010, T13 = 150 / SIS),
        for height_driver.site_index.  Below breast height the curve says nothing, so a power law from
        the seed that meets it with the same slope: no source for its shape."""
        c = getattr(self, "_hd_curve", None)
        if c is None:
            hd, ref = self.sp.height_driver, self.sp.reference.height
            si, t_ref = float(hd.site_index), float(hd.reference_age_years)

            def above(bh):
                return eriksson_1997_height(si, bh, float(ref.asi), float(ref.beta), float(ref.b2), t_ref)

            t13 = float(hd.t13_numerator) / si
            for _ in range(200):
                t13 = float(hd.t13_numerator) / above(float(hd.sis_total_age_years) - t13)
            c = self._hd_curve = (t13, (above(1.0) - 1.3) * t13 / 1.3)
        t13, p = c
        if age <= 0.0:
            return 0.0
        if age <= t13:
            return 1.3 * (age / t13) ** p
        ref = self.sp.reference.height
        hd = self.sp.height_driver
        return eriksson_1997_height(float(hd.site_index), age - t13, float(ref.asi), float(ref.beta), float(ref.b2), float(hd.reference_age_years))

    def _height_limit_plan(self, t, term_nodes, lat_nodes, Qterm, Qlat, opening):
        """This year's limit on the leader.  The curve gives the most it may grow; less light or less water
        lowers that; the shoot is then built of real nodes, paid for first from the pool (_growth_factor).
        Nothing here sets a height or moves a node.  None if the tree has no leader to limit this year."""
        T, hd = self.tree, self.sp.height_driver
        leaders = np.fromiter(self.leader_axes, np.int64)
        tips = np.nonzero(np.isin(T.axis[term_nodes], leaders))[0]
        if self.loss_of_dominance_year is not None and bool(getattr(hd, "leader_lost_in_crown", False)) and len(term_nodes):
            # once the leader has lost its dominance (resource.reiteration), whichever tip stands highest carries the height
            tips = np.arange(len(term_nodes))
        if tips.size:
            bud = int(tips[np.argmax(T.pos[term_nodes[tips], 2])])
            node, is_tip, q, dz = int(term_nodes[bud]), True, float(Qterm[term_nodes[bud]]), float(T.term_dir[term_nodes[bud], 2])
        else:
            # the leader is lost: the highest bud named to replace it takes over the limit
            relay = np.nonzero(np.isin(lat_nodes, np.fromiter(self._relay_buds.keys(), np.int64)))[0] if self._relay_buds else np.zeros(0, np.int64)
            if not relay.size:
                return None
            bud = int(relay[np.argmax(T.pos[lat_nodes[relay], 2])])
            node, is_tip, q, dz = int(lat_nodes[bud]), False, float(Qlat[lat_nodes[bud]]), float(T.lat_dir[lat_nodes[bud], 2])
        z = float(T.pos[node, 2])
        # the curve's years to breast height already hold the field layer, so its shade doesn't count twice
        herb = float(self._herb_factor(np.array([z]))[0])
        q_canopy = q / max(herb, 1e-9)
        f_light = min(1.0, q_canopy / float(hd.light_full)) ** float(hd.light_exponent)
        f_water = min(1.0, max(opening, 0.0) / float(hd.water_full))
        ref_alpha = getattr(hd, "reference_alpha", None)
        vigour = float(self.sp.resource.alpha) / float(ref_alpha) if ref_alpha else 1.0
        inc = self._curve_height(t) - self._curve_height(t - 1)
        self._hd_ref = getattr(self, "_hd_ref", 0.0) + inc * f_light * f_water * vigour
        allowed = float(np.clip(self._hd_ref - z, 0.0, float(hd.catch_up) * inc))
        v = allowed / max(dz, 0.5) / self.l0
        return {"node": node, "bud": bud, "is_tip": is_tip, "v": v, "z": z, "dz": max(dz, 0.5), "inc": inc, "allowed": allowed, "light": f_light, "water": f_water,
                "vigour": vigour, "ref": self._hd_ref, "q": q_canopy, "carbon_scale": 1.0, "cost_units": 0.0, "pool": 0.0}

    def _height_limit_caps(self, starts, n_term, full, hd, lead_at, nmax) -> np.ndarray:
        """The most each bud may make, in metamers: none ending above where the leader's shoot will end, and,
        with lateral_cap_ratio set, none longer than that share of the leader's shoot (apical control)."""
        T = self.tree
        lead_len = float(full[lead_at]) * float(min(hd["v"], nmax))
        caps = np.full(len(starts), float(nmax))
        if self._frame_on():
            # with the frame, side shoots aren't tied to the leader's: a twig's yearly shoot has its own limit in metres
            twig_m = float(self.sp.crown_frame.twig_shoot_max_m)
            lit = getattr(self, "_frame_q", None)
            if lit is not None:
                # a shaded limb's side shoots are short: it can't fork or fill
                sc = T.scaffold[starts].astype(np.int64)
                twig_m = twig_m * np.where(sc > 0, lit[np.minimum(sc, len(lit) - 1)], 1.0)
            caps = np.minimum(caps, twig_m / full)
            if bool(getattr(self.sp.crown_frame, "limp_twigs", False)):
                # gravimorphism (Wareing & Nasr 1961): a shoot heading down is a weak one, however thin, so a hanging twig lengthens slowly
                dz_cap = np.concatenate([T.term_dir[starts[:n_term], 2], T.lat_dir[starts[n_term:], 2]])
                hang = float(self.sp.crown_frame.hanging_share)
                caps = np.minimum(caps, twig_m * (1.0 + (1.0 - hang) * np.minimum(dz_cap, 0.0)) / full)
        ratio = getattr(self.sp.height_driver, "lateral_cap_ratio", None)
        twig_ratio = getattr(self.sp.height_driver, "twig_cap_ratio", None)
        if twig_ratio is not None:
            # twigs (shoots of order 2 and up) have a cap of their own, so the limbs that carry them keep the lead
            is_twig = (T.order[starts].astype(np.int64) + (np.arange(len(starts)) >= n_term)) >= 2
            caps = np.where(is_twig, np.minimum(caps, float(twig_ratio) * lead_len / full), caps)
        if ratio is not None:
            # with a floor: an old leader's short shoots don't hold the whole crown to them
            floor_m = float(getattr(self.sp.height_driver, "lateral_cap_floor_m", None) or 0.0)
            caps = np.minimum(caps, max(float(ratio) * lead_len, floor_m) / full)
            if self.reit_axes and bool(getattr(self.sp.height_driver, "leader_lost_in_crown", False)):
                # a reiterated limb is a small tree on the tree: only the top of the crown holds it back
                caps = np.where(np.isin(T.axis[starts], np.fromiter(self.reit_axes, np.int64)) & (np.arange(len(starts)) < n_term), float(nmax), caps)
        dz = np.concatenate([T.term_dir[starts[:n_term], 2], T.lat_dir[starts[n_term:], 2]])
        top = max(hd["z"] + lead_len * hd["dz"], float(hd["ref"]))
        room = np.maximum(top - T.pos[starts, 2], 0.0)
        caps = np.where(dz > 0.02, np.minimum(caps, room / (np.maximum(dz, 0.02) * full)), caps)
        caps[lead_at] = float(nmax)
        return caps

    def _height_limit_apply(self, v_term, v_lat):
        """Each bud's metamers after its cap; the leader's after the carbon check."""
        hd = self._hd
        nt = len(v_term)
        v = np.concatenate([v_term, v_lat])
        v = np.where(hd["caps"] >= hd["thr"], np.minimum(v, hd["caps"]), 0.0)
        if hd.get("frame_at") is not None:
            v[hd["frame_at"]] = np.where(hd["frame_v"] >= hd["thr"][hd["frame_at"]], hd["frame_v"], 0.0)
        v[hd["lead_at"]] = hd["v"]
        return v[:nt], v[nt:]

    def _height_limit_settle_stem(self, hd):
        """The stem is what leads to the shoot the limit paid for.  A second replacement leader stops being stem: it
        goes on as a limb, thick and upright for a while, instead of a second stem the limit knows nothing of."""
        T = self.tree
        node = hd["node"] if hd["is_tip"] else int(T.lat_child[hd["node"]])
        if node < 0:
            return
        while T.main_child[node] >= 0:
            node = int(T.main_child[node])
        T.stem_tip = node
        path = T.trunk_chain()
        self.leader_axes = set(int(a) for a in np.unique(T.axis[path]))
        if not hd["is_tip"] or self._relay_buds:
            self._relay_buds = {}
        T.relay = {int(T.parent[f]): int(f) for f in path[T.is_lateral[path]]}

    def _height_limit_log(self, n_before):
        """What the leader got this year and what held it back; only read, for the reports."""
        T, hd = self.tree, self._hd
        new = np.arange(n_before, T.n)
        chain = new[np.isin(T.axis[new], np.fromiter(self.leader_axes, np.int64))]
        tip_z = float(T.pos[chain, 2].max()) if chain.size else hd["z"]
        self._height_limit_settle_stem(hd)
        limits = {"carbon": hd["carbon_scale"], "light": hd["light"], "water": hd["water"]}
        held = min(limits, key=limits.get)
        self._driver_log = {"increment_m": round(hd["inc"], 4), "reference_m": round(hd["ref"], 4), "allowed_m": round(hd["allowed"], 4),
                            "got_m": round(max(tip_z - hd["z"], 0.0), 4), "nodes": int(chain.size), "light": round(hd["light"], 4), "light_q": round(hd["q"], 4),
                            "water": round(hd["water"], 4), "carbon": round(hd["carbon_scale"], 4), "cost_units": round(hd["cost_units"], 4),
                            "cost_share": round(hd["cost_units"] / hd["pool"], 5) if hd["pool"] > 0.0 else 1.0,
                            "held_by": held if limits[held] < 0.999 else "curve", "unspent": round(float(getattr(self, "_unspent", 0.0)), 3),
                            "sap_units": round(float(hd.get("sap_units0", 0.0)), 1), "wind_units": round(float(hd.get("wind_units0", 0.0)), 1),
                            "wood_free_m3": round(float(getattr(self, "_stress_extra", 0.0)), 6),
                            **({"use": {k: round(v, 1) for k, v in hd["use"].items()}} if "use" in hd else {})}
        self._unspent = 0.0

    def _grow_shoots(self, t, field, g_term, v_term, g_lat, v_lat, q_start=None):
        sp, T, rng = self.sp, self.tree, self.rng
        starts = np.concatenate([g_term, g_lat]).astype(np.int64)
        if q_start is None:
            q_start = np.ones(len(starts))
        leaf_size0, lma0 = self.leaf_traits(q_start)
        if starts.size == 0:
            return
        is_lat = np.concatenate([np.zeros(len(g_term), bool), np.ones(len(g_lat), bool)])
        v = np.concatenate([v_term, v_lat])
        nmax = max(1, int(float(sp.shoot.max_shoot_length) / self.l0))
        vc = np.minimum(v, nmax)
        # at least one internode (a tip below one metamer's worth makes one,
        # shorter: seg_len below)
        nmet = np.maximum(np.floor(vc), 1).astype(np.int64)
        no_axil = (vc < 1.0) & (not bool(getattr(sp.bud_fate, "axillary_buds_below_one_metamer", True)))
        expansion = self._expansion(starts)
        seg_len = self.l0 * vc / nmet * expansion
        D = np.where(is_lat[:, None], T.lat_dir[starts], T.term_dir[starts])
        D = _normalize(D)
        order = T.order[starts].astype(np.int64) + is_lat
        axis = T.axis[starts].astype(np.int64)
        li = np.nonzero(is_lat)[0]
        new_ids = np.arange(len(self.axis_phase), len(self.axis_phase) + len(li))
        axis[li] = new_ids
        self.axis_phase.extend(rng.uniform(0.0, 2.0 * np.pi, len(li)).tolist())
        phyllo = np.where(is_lat, 0, T.phyllo[starts].astype(np.int64) + 1)
        # a lateral on a leader (the stem, or a lateral that replaced a lost
        # leader) starts a scaffold of its own, with its own physiological
        # age; on a replacement leader its laterals had inherited the age of
        # the old limb, lost their vigour and left everything to the leader
        on_lead = np.isin(T.axis[starts], np.fromiter(self.leader_axes, np.int64))
        new_scaffold = is_lat & ((order == 1) | on_lead)
        scaffold = np.where(new_scaffold, t, T.scaffold_birth[starts])
        scaffold_id = T.scaffold[starts].astype(np.int64)

        R = np.where(is_lat[:, None], T.dir[starts], T.ref[starts])
        R = _perpendicular(R, D)

        # tropism rates are per metre of growth
        tr = sp.tropism
        xi_o = np.asarray(tr.phototropism_per_m, dtype=float)
        eta_o = np.asarray(tr.gravitropism_per_m, dtype=float)
        gsa_o = np.radians(np.asarray(tr.setpoint_angle_deg, dtype=float))
        xi = xi_o[np.minimum(order, len(xi_o) - 1)]
        eta = eta_o[np.minimum(order, len(eta_o) - 1)]
        gsa = gsa_o[np.minimum(order, len(gsa_o) - 1)]
        if self._frame_on():
            for i in np.nonzero(is_lat & on_lead)[0]:
                drawn = self._frame_buds().pop(int(starts[i]), None)
                if drawn is not None:
                    self._frame_gsa[int(axis[i])] = drawn
                    self._frame_axis_reach[int(axis[i])] = self._frame_reach.pop(int(starts[i]), 1.0)
            forks_named = np.zeros(len(starts), bool)
            for i in np.nonzero(is_lat & ~on_lead)[0]:
                limb = self._frame_fork_buds.pop(int(starts[i]), None)
                if limb is not None:
                    drawn = self._frame_buds().pop(int(starts[i]), None)
                    self._frame_gsa[int(axis[i])] = drawn
                    self._frame_fork_of[int(axis[i])] = limb
                    self._frame_axis_reach[int(axis[i])] = self._frame_axis_reach.get(int(T.axis[limb]), 1.0)
                    forks_named[i] = True
            own = self._frame_setpoints()[axis]
            gsa = np.where(np.isfinite(own), own, gsa)
        if self.reit_axes:
            # the main axis of a reiterated complex grows orthotropic
            rp = self.sp.resource.reiteration
            reit = ~is_lat & np.isin(axis, np.fromiter(self.reit_axes, np.int64))
            gsa = np.where(reit, math.radians(float(rp.setpoint_angle_deg)), gsa)
        # a lateral that replaces a lost leader turns upright and grows on as
        # the stem: its bud breaks into a new axis that joins the leaders
        if self._relay_buds:
            for i in np.nonzero(is_lat)[0]:
                base = self._relay_buds.pop(int(starts[i]), None)
                if base is not None:
                    self.leader_axes.add(int(axis[i]))
                    self._relay_first[int(axis[i])] = base
        lead_ax = np.isin(axis, np.fromiter(self.leader_axes, np.int64)) & (order >= 1)
        gsa = np.where(lead_ax, 0.0, gsa)
        # a replacement leader grows as the stem: the stem's tropisms
        xi = np.where(lead_ax, xi_o[0], xi)
        eta = np.where(lead_ax, eta_o[0], eta)
        # pendulous trait: shoots growing on thin twigs have a weak primary
        # gravitropic response too.  The size of the branch a shoot grows on is
        # the parent node's radius for a new lateral, the axis base radius for
        # an axis that continues.
        mp = sp.mechanics
        r_ref = np.where(is_lat, T.radius[starts], self._axis_base_radius()[starts])
        weak = mechanics.pendulous_factor(r_ref, float(mp.pendulous_radius), float(mp.pendulous_sharpness))
        limbs = self._limb_nodes(T.n)
        if limbs is not None:
            # a limb's own shoots, new or continuing, have its radius for softness, not the twigs'
            limb_start = np.where(is_lat, on_lead | (forks_named if self._frame_on() else False), limbs[starts])
            weak = np.where(limb_start, mechanics.pendulous_factor(r_ref, float(mp.pendulous_radius_limb), float(mp.pendulous_sharpness)), weak)
        if bool(getattr(tr, "twigs_keep_gravitropism", False)):
            # twigs turn towards their own set-point however thin they are; with a set-point below level, they grow down
            weak = np.where(order >= 2, 1.0, weak)
        eta = np.where((order >= 1) & ~lead_ax, eta * weak, eta)
        if self._frame_on() and bool(getattr(self.sp.crown_frame, "limp_twigs", False)):
            # a shoot too thin to hold itself up can't turn to the light either: thin twigs hang, as the pendulous trait has it
            xi = np.where((order >= 2) & ~lead_ax, xi * weak, xi)
        noise = float(sp.architecture.direction_noise_per_sqrt_m)
        corr = getattr(sp.architecture, "direction_noise_correlation_m", None)
        psm = getattr(sp.tropism, "phototropism_smoothing_m", None)
        sym_len = getattr(sp.architecture, "sympodial_bend_length_m", None)
        sym_rem = np.where(is_lat, 0.0, math.radians(sp.architecture.sympodial_deviation_deg)) if sym_len else None
        sym_side = np.where(is_lat[:, None], 0.0, T.sym_side[starts]) if sym_len else None
        v_s = np.full((len(starts), 3), np.nan) if psm else None
        xi_n = rng.normal(size=(len(starts), 3)) if corr else None
        symp = math.radians(sp.architecture.sympodial_deviation_deg)
        zmin = float(sp.shoot.min_height_above_ground)

        cur = starts.copy()
        stop_at_ground = bool(getattr(sp.shoot, "stop_at_ground", False))
        for k in range(int(nmet.max())):
            act = np.nonzero(nmet > k)[0]
            if act.size == 0:
                break
            m = len(act)
            c = cur[act]
            P = T.pos[c]
            Dk = D[act]
            L = seg_len[act]
            V = field.optimal_direction(P, Dk)
            cl = getattr(self, "_crown_light", None)
            if cl is not None and cl.any():
                lead = (order[act] == 0) & ~is_lat[act]
                if lead.any():
                    V[lead] = _normalize(V[lead] + cl[None, :])
            if psm:
                # the shoot integrates the light signal along its length, so
                # it turns smoothly instead of following every voxel
                rho_v = np.exp(-L / float(psm))[:, None]
                v_prev = np.where(np.isfinite(v_s[act, :1]), v_s[act], V)
                V = _normalize(rho_v * v_prev + (1.0 - rho_v) * V)
                v_s[act] = V
            target = mechanics.setpoint_directions(Dk, gsa[act])
            eta_n = rng.normal(size=(m, 3))
            if corr:
                # the bending noise is a smooth random curvature along the
                # shoot (Ornstein-Uhlenbeck with correlation length corr), with
                # the same wander per metre as independent kinks
                rho = np.exp(-L / float(corr))
                xi_n[act] = rho[:, None] * xi_n[act] + np.sqrt(1.0 - rho * rho)[:, None] * eta_n
                bend = (noise / np.sqrt(2.0 * float(corr)) * L)[:, None] * xi_n[act]
            else:
                bend = (noise * np.sqrt(L))[:, None] * eta_n
            Dn = Dk + (xi[act] * L)[:, None] * V + (eta[act] * L)[:, None] * target + bend
            Dn = _normalize(Dn)
            if sym_len:
                # the renewal shoot leaves beside the aborted apex: its
                # deflection is a curvature over the first sympodial_bend_length
                # of the shoot, not a kink at one node
                dlt = np.minimum(sym_rem[act], math.radians(sp.architecture.sympodial_deviation_deg) * L / float(sym_len))
                sd = sym_side[act] - (sym_side[act] * Dn).sum(1, keepdims=True) * Dn
                sn = np.linalg.norm(sd, axis=1, keepdims=True)
                Dn = np.where(sn > 1e-9, _normalize(Dn + np.tan(dlt)[:, None] * sd / np.maximum(sn, 1e-12)), Dn)
                sym_rem[act] -= dlt
            low = P[:, 2] + L * Dn[:, 2] < zmin
            if stop_at_ground:
                low &= Dn[:, 2] < 0.0          # only shoots heading into the ground
            if low.any():
                if stop_at_ground:
                    # a shoot that reaches the ground stops there; its bud is spent
                    st = act[low]
                    nmet[st] = k
                    fresh = st[cur[st] == starts[st]]
                    T.term[fresh[~is_lat[fresh]]] = 0
                    T.lat[starts[fresh[is_lat[fresh]]]] = LAT_DEAD
                    keep = ~low
                    act, c, P, Dk, L, Dn = act[keep], c[keep], P[keep], Dk[keep], L[keep], Dn[keep]
                    m = len(act)
                    if m == 0:
                        continue
                else:
                    Dn[low, 2] = np.maximum(Dn[low, 2], np.clip((zmin - P[low, 2]) / L[low], -1.0, 1.0))
                    Dn[low] = _normalize(Dn[low])
            new = T.alloc(m)
            Rn = _perpendicular(R[act], Dn)

            T.pos[new] = P + L[:, None] * Dn
            T.dir[new] = Dn
            T.ref[new] = Rn
            T.parent[new] = c
            T.birth[new] = t
            T.order[new] = order[act]
            T.axis[new] = axis[act]
            T.depth[new] = T.depth[c] + 1
            T.length[new] = L
            T.leaf_scale[new] = expansion[act]
            T.leaf_size[new] = leaf_size0[act]
            T.lma[new] = lma0[act]
            T.scaffold_birth[new] = scaffold[act]
            if k == 0:
                first = new_scaffold[act]
                scaffold_id[act[first]] = new[first]
                if self._relay_first:
                    for i_new, a_id in zip(new, axis[act]):
                        base = self._relay_first.pop(int(a_id), None)
                        if base is not None and base not in self.tree.relay:
                            self.tree.relay[base] = int(i_new)
            T.scaffold[new] = scaffold_id[act]
            T.phyllo[new] = phyllo[act] + k
            if k == 0:
                lat_first = is_lat[act]
                T.is_lateral[new] = lat_first
                T.main_child[c[~lat_first]] = new[~lat_first]
                T.term[c[~lat_first]] = 0
                T.lat_child[c[lat_first]] = new[lat_first]
                T.lat[c[lat_first]] = LAT_USED
            else:
                T.main_child[c] = new

            u, bud = self._lateral_bud_dirs(Dn, Rn, order[act], axis[act], phyllo[act] + k)
            last = nmet[act] == k + 1
            T.lat[new] = LAT_DORMANT
            # an increment below one metamer is a short-shoot year: its leaf
            # stands at the tip and no long-shoot bud forms in its axil (birch
            # short shoots carry only their terminal bud; Ishihara & Kikuzawa
            # 2009, Ann. Bot. 104:1195)
            T.no_axil[new] = no_axil[act]
            if self._leaf_density is not None and not bool(self.sp.bud_fate.density_control.after_growth):
                T.no_axil[new] |= self.rng.random(len(new)) > self._bud_keep_chance(T.pos[new])
            T.lat_dir[new] = bud
            T.term[new] = last.astype(np.int8)
            # sympodial growth: the pseudo-terminal bud sits beside the aborted
            # apex, opposite the last lateral, and deflects next year's shoot
            if sym_len:
                T.term_dir[new] = Dn
                T.sym_side[new] = -u
            else:
                T.term_dir[new] = _normalize(math.cos(symp) * Dn - math.sin(symp) * u)

            cur[act] = new
            D[act] = Dn
            R[act] = Rn

    # ------------------------------------------------------------------
    def _update_radii(self, leaves=None):
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        levels = T.levels(alive)
        own = T.own_pipe[:n] + np.where(T.main_child[:n] < 0, self.tip_pipe, 0.0)
        own = np.where(alive, own, 0.0)
        P = T.basipetal(levels, own)
        self._r_pipe = P ** (1.0 / self.gamma)      # radii of the pipes alone (conducting structure)
        pm = self.sp.pipe_model
        mode = str(getattr(pm, "growth", "pipe"))
        if mode == "lignum" and leaves is not None:
            # LIGNUM rings (Perttunen et al. 1996): the ring each internode
            # needs so that its sapwood carries the foliage beyond it, from the
            # year's single carbon pool (_growth_factor); last year's sapwood
            # loses sapwood_senescence_per_year to heartwood.  A new shoot
            # starts at the tip radius, all sapwood.
            tip = np.pi * float(pm.tip_radius) ** 2
            new = alive & (T.wood_area[:n] <= 0.0)
            T.wood_area[:n] = np.where(new, tip, T.wood_area[:n])
            T.sap_area[:n] = np.where(new, tip, T.sap_area[:n])
            ring = getattr(self, "_ring", None)
            # no heartwood (sapwood: false): sap_area stays the whole wood
            m = min(len(ring), n) if ring is not None else 0
            ss = self._sapwood_loss(m) if bool(getattr(pm, "sapwood", True)) else 0.0
            old = alive[:m] & ~new[:m]
            if m:
                T.sap_area[:m] = np.where(old, (1.0 - ss) * T.sap_area[:m] + ring[:m], T.sap_area[:m])
                T.wood_area[:m] = np.where(old, T.wood_area[:m] + ring[:m], T.wood_area[:m])
            self._ring = None
            sf = getattr(pm, "stress_floor", None)
            if sf is not None and bool(sf.enabled):
                # nor thinner than it must be to carry its load at a safe
                # bending stress (uniform-stress hypothesis); outside the pool
                need = np.where(alive, np.maximum(self._stress_area(levels, alive, leaves, sf) - T.wood_area[:n], 0.0), 0.0)
                T.wood_area[:n] += need
                T.sap_area[:n] += need
                self._stress_extra = float((need * np.where(alive, T.length[:n], 0.0)).sum())
            if T.relay:
                base = np.fromiter(T.relay.keys(), np.int64)
                first = np.fromiter(T.relay.values(), np.int64)
                ok = (first < n) & alive[np.minimum(first, n - 1)]
                T.wood_area[first[ok]] = np.maximum(T.wood_area[first[ok]], T.wood_area[base[ok]])
            r = np.sqrt(T.wood_area[:n] / np.pi)
        elif mode == "rings" and leaves is not None:
            # Annual rings: the year's wood volume (a fixed share of the
            # shoot carbon) is laid down as a ring on every living internode,
            # with ring area following the leaf area beyond it (Pressler's
            # rule: constant below the crown base), as in LIGNUM (Perttunen
            # et al. 1996).  Wood laid down for branches since shed stays
            # (disused pipes, Shinozaki et al. 1964).  A new shoot starts at
            # the tip radius.
            new = alive & (T.wood_area[:n] <= 0.0)
            T.wood_area[:n] = np.where(new, np.pi * float(pm.tip_radius) ** 2, T.wood_area[:n])
            la = T.basipetal(levels, np.where(alive, leaves, 0.0) * float(self.light.leaf_area))
            la = np.where(alive, la, 0.0)
            spread = float((la * np.where(alive, T.length[:n], 0.0)).sum())
            dv = float(pm.wood_volume_per_carbon) * float(getattr(self, "_shoot_carbon", 0.0))
            if spread > 0.0 and dv > 0.0:
                T.wood_area[:n] = T.wood_area[:n] + dv / spread * la
            # wood is never thinner than the pipes it carries (as on the stem
            # in stem_rings): without it, ring-grown limbs got the area share
            # of their leaves only, ~40 % thinner than the pipe model's, and
            # bent down under their load
            T.wood_area[:n] = np.where(alive, np.maximum(T.wood_area[:n], np.pi * self._r_pipe[:n] ** 2), T.wood_area[:n])
            sf = getattr(pm, "stress_floor", None)
            if sf is not None and bool(sf.enabled):
                # nor thinner than it must be to carry its load at a safe
                # bending stress (uniform-stress hypothesis)
                T.wood_area[:n] = np.where(alive, np.maximum(T.wood_area[:n], self._stress_area(levels, alive, leaves, sf)),
                                           T.wood_area[:n])
            if T.relay:
                # a lateral that replaced a lost leader carries the stem on: its
                # base is never thinner than the stem below it (no step)
                base = np.fromiter(T.relay.keys(), np.int64)
                first = np.fromiter(T.relay.values(), np.int64)
                ok = (first < n) & alive[np.minimum(first, n - 1)]
                T.wood_area[first[ok]] = np.maximum(T.wood_area[first[ok]], T.wood_area[base[ok]])
            r = np.sqrt(T.wood_area[:n] / np.pi)
        else:
            r = P ** (1.0 / self.gamma)
            if str(getattr(pm, "growth", "pipe")) == "stem_rings":
                r = self._stem_rings(r, alive)
        T.radius[:n] = np.where(alive, r, T.radius[:n])
        self._r_last = T.radius[:n].copy()
        # the history is for replay, export and ring widths (float32)
        if not self.lean:
            self.radius_history.append(T.radius[:n].astype(np.float32))

    def _stress_area(self, levels, alive, leaves, sf) -> np.ndarray:
        """Wood area each internode needs so that the self-weight bending
        stress at its base stays at or below the safe limit: sigma = M /
        (pi r^3 / 4) with M the moment of everything beyond it (wood and
        leaves) about its base (Metzger's uniform-stress hypothesis; McMahon
        & Kronauer 1976)."""
        T = self.tree
        n = T.n
        mp = self.sp.mechanics
        r = np.sqrt(np.maximum(T.wood_area[:n], 0.0) / np.pi)
        L = T.length[:n]
        m = np.where(alive, float(mp.wood_density) * np.pi * r ** 2 * L + float(mp.leaf_mass) * leaves, 0.0)
        c = T.pos[:n] - 0.5 * L[:, None] * T.dir[:n]
        acc = np.zeros((n, 4))
        acc[:, 0] = m
        acc[:, 1:] = m[:, None] * c
        acc = T.basipetal(levels, acc)
        arm = acc[:, 1:] - acc[:, :1] * T.pos[np.maximum(T.parent[:n], 0)]
        moment = mechanics.G * np.hypot(arm[:, 0], arm[:, 1])
        sigma = float(sf.wood_mor_green_mpa) * 1e6 / float(sf.safety_factor)
        return np.pi * np.cbrt(4.0 * moment / (np.pi * sigma)) ** 2

    # -- history on disk (long plot runs) --------------------------------
    def spill_history(self, path) -> None:
        """Move the yearly radius history and the position keyframes (the
        bulk of a tree's memory late in a run) to one .npz in ``path`` and
        drop them from memory.  restore_history reads them all back."""
        from pathlib import Path
        d = Path(path)
        d.mkdir(parents=True, exist_ok=True)
        if not self.radius_history and not self.keyframes and (self.roots is None or not self.roots.radius_history):
            return   # a second call in one year would write an empty file over the first
        rb, qb = getattr(self, "_hist_base", 0), getattr(self, "_root_hist_base", 0)
        arrays = {f"r{rb + i:04d}": a for i, a in enumerate(self.radius_history)}
        arrays.update({f"k{y:04d}": a for y, a in self.keyframes.items()})
        if self.roots is not None:
            arrays.update({f"q{qb + i:04d}": a for i, a in enumerate(self.roots.radius_history)})
        np.savez(d / f"history_{self.year:03d}.npz", **arrays)
        self._hist_base = rb + len(self.radius_history)
        self.radius_history = []
        self.keyframes = {}
        if self.roots is not None:
            self._root_hist_base = qb + len(self.roots.radius_history)
            self.roots.radius_history = []

    def restore_history(self, path) -> None:
        """Read back what spill_history wrote (all files in ``path``)."""
        from pathlib import Path
        r, k, q = {}, {}, {}
        for f in sorted(Path(path).glob("history_*.npz")):
            with np.load(f) as z:
                for key in z.files:
                    {"r": r, "k": k, "q": q}[key[0]][int(key[1:])] = z[key]
        self.radius_history = [r[i] for i in sorted(r)] + self.radius_history
        self.keyframes = {**k, **self.keyframes}
        self._hist_base = 0
        if self.roots is not None:
            self.roots.radius_history = [q[i] for i in sorted(q)] + self.roots.radius_history
            self._root_hist_base = 0

    def _stem_rings(self, r_pipe: np.ndarray, alive: np.ndarray) -> np.ndarray:
        """Annual rings on the stem (Pressler's rule): a stem internode in the
        crown adds this year's growth of its pipe area; one below the crown
        base adds the ring of the crown base, so the ring area is constant
        down the bole and the lower stem, older, carries more rings.  Wood
        is never thinner than the pipes it carries."""
        T = self.tree
        trunk = T.trunk_chain(self.leader_axes)
        a_pipe = np.pi * r_pipe[trunk] ** 2
        prev = getattr(self, "_stem_pipe_prev", np.zeros(0))
        a_prev = np.zeros(len(trunk))
        known = trunk < len(prev)
        a_prev[known] = prev[trunk[known]]
        da = np.maximum(a_pipe - a_prev, 0.0)
        cb = self.stats[-1].get("crown_base_height_m") if self.stats else None
        if cb:
            below = T.pos[trunk, 2] < cb
            if below.any() and (~below).any():
                da[below] = da[int(np.nonzero(~below)[0][0])]
        T.wood_area[trunk] += da
        store = np.zeros(T.n)
        store[trunk] = a_pipe
        self._stem_pipe_prev = store
        out = r_pipe.copy()
        out[trunk] = np.sqrt(np.maximum(T.wood_area[trunk], a_pipe) / np.pi)
        return out

    def pipe_residual(self) -> float:
        """Max relative violation of r_i^g = own_i + sum_children r_c^g over
        living nodes, for the pipes (the stem may carry more wood than its
        pipes when it grows by rings)."""
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        g = self.gamma
        P = self._r_pipe[:n] ** g
        rhs = T.own_pipe[:n] + np.where(T.main_child[:n] < 0, self.tip_pipe, 0.0)
        for ch in (T.main_child[:n], T.lat_child[:n]):
            ok = alive & (ch >= 0)
            ok[ok] &= T.death[ch[ok]] < 0
            rhs = rhs + np.where(ok, P[np.maximum(ch, 0)], 0.0)
        err = np.abs(P - rhs) / np.maximum(P, 1e-30)
        return float(err[alive].max())

    # ------------------------------------------------------------------
    def hanging_runs(self) -> np.ndarray:
        """For every living node, the length of the hanging run ending at it:
        consecutive internodes pointing more than 30 deg below horizontal."""
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        hang = alive & (T.dir[:n, 2] < HANGING_DZ)
        hang[0] = False
        run = np.where(hang, T.length[:n], 0.0)
        par = T.parent
        for seg, _, _ in T.levels(alive)[1:]:
            h = seg[hang[seg]]
            run[h] += run[par[h]]
        return run

    def scaffold(self) -> dict:
        """Scaffold diagnostics: living first-order limbs by base diameter,
        limb-to-trunk diameter ratios, how concentrated the foliage is on the
        biggest limbs, and where the leaf area sits along the trunk (by
        height decile) and across the crown (inner core vs outer shell,
        relative to the crown radius at that height)."""
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
        pos = T.pos[:n]
        H = float(pos[alive, 2].max())
        limbs = np.nonzero(alive & T.is_lateral[:n] & (T.order[:n] == 1))[0]
        tot = float(leaves.sum())
        if limbs.size == 0 or tot <= 0:
            return {}
        d_limb = 2.0 * T.radius[limbs]
        ratio = d_limb / np.maximum(2.0 * T.radius[T.parent[limbs]], 1e-9)
        sub = T.basipetal(T.levels(alive), leaves)[limbs]
        big = d_limb > 0.05
        by_size = np.argsort(-d_limb)[:5]
        li = np.nonzero(leaves > 0)[0]
        w = leaves[li]
        band = np.clip((pos[li, 2] / H * 10).astype(int), 0, 9)
        trunk = T.trunk_chain(self.leader_axes)
        j = np.clip(np.searchsorted(pos[trunk, 2], pos[li, 2]), 0, len(trunk) - 1)
        rr = np.hypot(pos[li, 0] - pos[trunk[j], 0], pos[li, 1] - pos[trunk[j], 1])
        rmax = np.array([np.percentile(rr[band == b], 98) if (band == b).any() else 0.0 for b in range(10)])
        rel = rr / np.maximum(rmax[band], 1e-6)
        return {
            "living_limbs": int(limbs.size),
            "limbs_over_5cm": int(big.sum()),
            "limbs_over_10cm": int((d_limb > 0.10).sum()),
            "five_largest_limbs_cm": [round(float(x) * 100, 1) for x in d_limb[by_size]],
            "five_largest_limbs_height_m": [round(float(pos[T.parent[limbs[i]], 2]), 2) for i in by_size],
            "five_largest_limbs_to_trunk_ratio": [round(float(x), 3) for x in ratio[by_size]],
            "largest_scaffold_limb_to_trunk_ratio": round(float(ratio[big].max()), 3) if big.any() else None,
            "leaf_share_five_biggest_limbs": round(float(np.sort(sub)[::-1][:5].sum() / tot), 3),
            "leaf_share_by_height_decile": [round(float(x), 3) for x in np.bincount(band, weights=w, minlength=10) / w.sum()],
            "leaf_share_inner_40pct_radius": round(float(w[rel < 0.4].sum() / w.sum()), 3),
            "leaf_share_outer_shell_60pct_plus": round(float(w[rel >= 0.6].sum() / w.sum()), 3),
        }

    def measure(self) -> dict:
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        pos = T.pos[:n][alive]
        height = float(pos[:, 2].max())
        dbh = self.dbh_m()
        dbh = None if dbh is None else dbh * 100.0
        xy = pos[:, :2]
        wx = float(np.ptp(xy[:, 0])) if len(xy) > 1 else 0.0
        wy = float(np.ptp(xy[:, 1])) if len(xy) > 1 else 0.0
        hull_d = 0.0
        if len(xy) >= 4 and min(wx, wy) > 1e-6:
            from scipy.spatial import ConvexHull
            try:
                hull_d = 2.0 * math.sqrt(ConvexHull(xy).volume / math.pi)
            except Exception:
                hull_d = 0.0
        idx = np.nonzero(alive)[0]
        inter = idx[idx > 0]
        axes_by_order, internodes_by_order = {}, {}
        if not self.lean:
            _, starts = np.unique(T.axis[idx], return_index=True)
            orders = T.order[idx][starts]
            axes_by_order = {str(int(o)): int(c) for o, c in zip(*np.unique(orders, return_counts=True))}
            io, ic = np.unique(T.order[inter], return_counts=True)
            internodes_by_order = {str(int(o)): int(c) for o, c in zip(io, ic)}
        # crown base: lowest living first-order limb that carries a real share
        # of the foliage (isolated near-dead twigs do not count)
        leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
        total_leaves = float(leaves.sum())
        if bool(getattr(self.sp.stats, "limbs_on_leader", False)):
            # a limb is a side axis on the stem or on a leader that replaced it; a replacement leader is stem, not a
            # limb (with order == 1 it counts as one, attached low, and the stem's own limbs don't count at all)
            on_lead = np.isin(T.axis[:n], np.fromiter(self.leader_axes, np.int64))
            limbs = np.nonzero(alive & T.is_lateral[:n] & ~on_lead & on_lead[np.maximum(T.parent[:n], 0)])[0]
        else:
            limbs = np.nonzero(alive & T.is_lateral[:n] & (T.order[:n] == 1))[0]
        crown_base = lowest_branch = None
        if limbs.size:
            lowest_branch = float(T.pos[T.parent[limbs], 2].min())
            lv = T.basipetal(T.levels(alive), leaves)[limbs]
            real = limbs[lv >= max(5.0, float(self.sp.stats.crown_base_min_leaf_share) * total_leaves)]
            if real.size:
                crown_base = float(T.pos[T.parent[real], 2].min())
        hanging = np.zeros(0)
        if not self.lean:
            run = self.hanging_runs()
            tips = alive & (T.main_child[:n] < 0)
            tips[0] = False
            hr = run[tips]
            hanging = hr[hr >= float(self.sp.stats.hanging_twig_min_length)]
        return {
            "year": int(self.year),
            "height_m": round(height, 4),
            "dbh_cm": None if dbh is None else round(dbh, 3),
            "crown_width_m": round(0.5 * (wx + wy), 4),
            "crown_width_x_m": round(wx, 4),
            "crown_width_y_m": round(wy, 4),
            "crown_projected_diameter_m": round(hull_d, 4),
            "crown_base_height_m": None if crown_base is None else round(crown_base, 4),
            "crown_ratio": None if crown_base is None or height <= 0 else round((height - crown_base) / height, 4),
            "lowest_live_branch_m": None if lowest_branch is None else round(lowest_branch, 4),
            "branches_by_order": axes_by_order,
            "internodes_by_order": internodes_by_order,
            "living_internodes": int(len(inter)),
            "living_spurs": int(np.count_nonzero(alive & (T.lat[:n] == LAT_SPUR))),
            "leaves": int(round(total_leaves)),
            "leaf_area_m2": round(total_leaves * self.light.leaf_area, 3),
            "hanging_twigs": int(hanging.size),
            "mean_hanging_twig_length_m": round(float(hanging.mean()), 4) if hanging.size else 0.0,
            "p90_hanging_twig_length_m": round(float(np.percentile(hanging, 90)), 4) if hanging.size else 0.0,
            "max_hanging_twig_length_m": round(float(hanging.max()), 4) if hanging.size else 0.0,
            "stand_spacing_m": round(self.stand_spacing(height), 3) if self.stand else None,
            # leaf area index: the tree's leaf area over the ground area it
            # holds at the current stem density (stand), or over its crown
            # projection (open-grown)
            "lai": round(total_leaves * self.light.leaf_area * self.stems_per_ha(height) / 10000.0, 3) if self.stand
            else (round(total_leaves * self.light.leaf_area / max(math.pi * hull_d * hull_d / 4.0, 1e-6), 3) if hull_d > 0 else None),
            # relative light (%) at 1.0-2.0 m under the stand canopy this
            # season (light.SUBCANOPY_LIGHT_HEIGHTS_M); stand runs only
            "subcanopy_light_pct": (round(100.0 * self._subcanopy_light, 2)
                                    if getattr(self, "_subcanopy_light", None) is not None else None),
            # the same under the sky alone (overcast), the light target's measure
            "subcanopy_diffuse_light_pct": (round(100.0 * self._subcanopy_diffuse_light, 2)
                                            if getattr(self, "_subcanopy_diffuse_light", None) is not None else None),
            "water": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in self.water.items()},
            # carbon fixed this season, in resource units (alpha x sum of bud
            # light x stomatal opening; one unit builds about one metamer)
            "carbon": {k: round(v, 4) for k, v in getattr(self, "carbon", {}).items()},
            "roots": self.roots.measure() if self.roots is not None and not self.lean else None,
            "scaffold": self.scaffold() if not self.lean and (self.year % 5 == 0 or self.year >= 50) else None,
            "apical_control": round(self.apical_control(max(self.year, 1)), 4),
            "reiterated_limbs": len(self.reit),
            "loss_of_dominance_year": self.loss_of_dominance_year,
            **({"height_limit": getattr(self, "_driver_log", None)} if self._height_limit_on() else {}),
        }
