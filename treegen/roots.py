"""Root system: bud-based self-organising growth in soil.

The same scheme as the crown (Palubicki et al. 2009), with soil in place of
light: root tips compete for available soil water on a soil voxel grid, a
Borchert-Honda split shares out the year's root budget, and tropisms steer
each tip.

* Availability of a soil voxel = relative moisture at its depth x (no stone)
  x exp(-k * RLD), where RLD is the tree's own absorbing root-length density
  blurred over the depletion zone around each root: a root draws down the
  water near it, as a leaf casts shade.  In stand mode the neighbours' roots
  deplete the same cells.  In a plot all trees read one soil (SharedSoil):
  the same stones and rootable depth, and every tree's roots in one field.
* Root classes follow silver birch (Laitakari 1935): a seedling taproot that
  is soon overtaken, near-horizontal main laterals in the top soil that
  spread beyond the crown, and sinker roots that drop from the laterals near
  the stem towards the compact subsoil.
* The root collar (the taproot zone) forms the main laterals: its
  primordia sit at a fixed divergence, stay viable for years and share the
  budget without favouring the deeper ones, so the main laterals radiate
  around the stem instead of one taking over.
* Water uptake: young roots (the zone carrying fine roots) take up water in
  proportion to their length and the availability around them, in series
  with the axial resistance of the woody path back to the stem.
* Radii: the shoot's pipes continue into the roots (pipe model), shared out
  over root branches in proportion to their own tip counts, so the root
  collar matches the stem base.

Coordinates as the crown: z up, ground at z = 0, roots at z < 0.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.spatial import cKDTree

from .mechanics import setpoint_directions
from .structure import Tree, _normalize, _perpendicular

LAT_NONE, LAT_DORMANT, LAT_DEAD, LAT_USED = 0, 1, 4, 3
DOWN = np.array([0.0, 0.0, -1.0])


def _clamp_z(D: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
    """Unit directions with the vertical component clamped to [lo, hi]; the
    horizontal part is rescaled so the vector stays unit length."""
    dz = np.clip(D[:, 2], np.clip(lo, -1.0, 1.0), np.clip(hi, -1.0, 1.0))
    h = D[:, :2]
    hn = np.linalg.norm(h, axis=1, keepdims=True)
    h = np.where(hn > 1e-9, h / np.maximum(hn, 1e-12), np.array([1.0, 0.0]))
    out = np.empty_like(D)
    out[:, :2] = h * np.sqrt(np.maximum(1.0 - dz ** 2, 0.0))[:, None]
    out[:, 2] = dz
    return out


def _limit_turn(D0: np.ndarray, D1: np.ndarray, max_angle: float) -> np.ndarray:
    """D1 turned back towards D0 where it turns by more than max_angle."""
    c = np.clip((D0 * D1).sum(1), -1.0, 1.0)
    over = c < math.cos(max_angle)
    if not over.any():
        return D1
    perp = D1[over] - c[over, None] * D0[over]
    pn = np.linalg.norm(perp, axis=1, keepdims=True)
    perp = np.where(pn > 1e-9, perp / np.maximum(pn, 1e-12), _perpendicular(np.tile([1.0, 0.0, 0.0], (int(over.sum()), 1)), D0[over]))
    out = D1.copy()
    out[over] = math.cos(max_angle) * D0[over] + math.sin(max_angle) * perp
    return out


def _fib(n: int) -> np.ndarray:
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)


def _soil_grids(soil, seed: int, lo, nx: int, ny: int, nz: int, vs: float):
    """The parts of availability that do not change: relative moisture by
    depth x no stone x within the local rootable depth, on the voxel grid
    starting at voxel ``lo``; and the stone grid."""
    zc = (np.arange(nz) + lo[2] + 0.5) * vs
    moist = soil.moisture(-zc).astype(np.float32)
    # stones: evaluate the stone field at voxel centres
    gx = (np.arange(nx) + lo[0] + 0.5) * vs
    gy = (np.arange(ny) + lo[1] + 0.5) * vs
    X, Y, Z = np.meshgrid(gx, gy, zc, indexing="ij")
    stone = soil.is_stone(np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1), seed).reshape(nx, ny, nz)
    # below the local rootable depth the soil holds no available water
    local = soil.depth_at(np.stack(np.meshgrid(gx, gy, indexing="ij"), -1), seed)
    rootable = (-zc)[None, None, :] <= local[:, :, None]
    return moist[None, None, :] * (~stone) * rootable, stone


def _root_density(pts, ls, lo, shape, vs: float, p, periodic: bool):
    """Absorbing root length per m^3, blurred over the depletion zone."""
    nx, ny, nz = shape
    rld = np.zeros((nx, ny, nz), dtype=np.float32)
    if len(pts):
        idx = np.floor(pts / vs).astype(int) - lo
        if periodic:
            idx[:, 0] %= nx
            idx[:, 1] %= ny
        ok = np.all((idx >= 0) & (idx < np.array([nx, ny, nz])), axis=1)
        np.add.at(rld, tuple(idx[ok].T), ls[ok].astype(np.float32))
        sig = float(p.depletion_radius) / vs
        mode = ("wrap", "wrap", "constant") if periodic else "constant"
        rld = gaussian_filter(rld, sig, mode=mode, truncate=3.0) / vs ** 3   # m root per m^3
    return rld


class SharedSoil:
    """One soil for a plot of trees, in plot coordinates with one seed:
    moisture, stones and rootable depth are laid out once, and each year the
    absorbing roots of all trees are blurred once into one root-length
    density.  Every tree reads the same availability, stones and depth
    through its own offset (``RootSystem.frame``)."""

    def __init__(self, soil, rp, vs: float, cell, seed: int):
        self.p, self.vs, self.seed, self.cell = rp, float(vs), int(seed), cell
        x0, y0, nx, ny = cell
        zlo = -int(math.ceil(soil.max_depth / vs)) - 1
        self.lo = np.array([int(round(x0 / vs)), int(round(y0 / vs)), zlo])
        self.shape = (int(nx), int(ny), -zlo + 1)
        self.static, self.stone = _soil_grids(soil, self.seed, self.lo, *self.shape, self.vs)
        self.field = None

    def update(self, pts: np.ndarray, ls: np.ndarray) -> None:
        """This year's field from all absorbing roots (midpoints in plot coordinates)."""
        rld = _root_density(pts, ls, self.lo, self.shape, self.vs, self.p, periodic=True)
        A = self.static * np.exp(-float(self.p.depletion_coefficient) * rld)
        self.field = (A.astype(np.float32), self.lo, self.stone, self.cell)


class RootSystem:
    def __init__(self, rp, soil, seed: int, vs: float, frame=None):
        self.p = rp
        self.soil = soil
        self.seed = int(seed)
        # in a plot: (offset of this tree in plot coordinates, the plot's soil
        # seed); stones, rootable depth and availability are read there
        self.frame = None if frame is None else (np.asarray(frame[0], float), int(frame[1]))
        self.rng = np.random.default_rng([int(seed), 104729])
        self.vs = float(vs)
        self.tree = Tree()
        self.gsa = np.zeros(0)        # per-axis set-point (rad from vertical up)
        self.eta = np.zeros(0)        # per-axis gravitropism (1/m)
        self.kind = np.zeros(0, int)  # per-axis: 0 taproot, 1 lateral, 2 sinker
        self.radius_history: list[np.ndarray] = []
        self.probe = _fib(48)
        self.rhizo_phase = float(self.rng.uniform(0.0, 2.0 * np.pi))
        T = self.tree
        i = T.alloc(1)
        T.pos[i] = 0.0
        T.dir[i] = DOWN
        T.ref[i] = np.array([1.0, 0.0, 0.0])
        T.parent[i] = -1
        T.term[i] = 1
        T.term_dir[i] = DOWN
        T.axis[i] = 0
        self._new_axes(np.array([0]), np.array([0]))
        self.uptake_conductance = 0.0
        self.field = None
        self.P = np.zeros(1)
        self.diag = {}

    # -- per-axis traits ----------------------------------------------------
    def _new_axes(self, ids: np.ndarray, kind: np.ndarray):
        p = self.p
        n = int(ids.max()) + 1
        if len(self.gsa) < n:
            grow = n - len(self.gsa)
            self.gsa = np.concatenate([self.gsa, np.zeros(grow)])
            self.eta = np.concatenate([self.eta, np.zeros(grow)])
            self.kind = np.concatenate([self.kind, np.zeros(grow, int)])
        ang = np.radians(np.where(kind == 0, p.taproot_setpoint_deg,
                                  np.where(kind == 2, p.sinker_setpoint_deg, p.lateral_setpoint_deg)))
        ang = ang + np.where(kind == 1, np.radians(p.lateral_setpoint_spread_deg) * self.rng.standard_normal(len(ids)), 0.0)
        self.gsa[ids] = ang
        self.eta[ids] = np.where(kind == 0, p.taproot_gravitropism_per_m,
                                 np.where(kind == 2, p.sinker_gravitropism_per_m, p.lateral_gravitropism_per_m))
        self.kind[ids] = kind

    # -- soil availability ---------------------------------------------------
    def _frame(self):
        """(offset, soil seed) of the soil this tree reads: in a plot the
        plot's shared soil, otherwise its own (no offset, its own seed)."""
        fr = getattr(self, "frame", None)
        return (None, self.seed) if fr is None else fr

    def availability_field(self, t: int, clones=None, cell=None):
        """Availability grid for this year.  ``clones``: list of (angle, dx, dy)
        neighbour transforms; ``cell``: periodic (x0, y0, nx, ny) at self.vs.
        A tree in a plot reads the plot's SharedSoil instead (``step``); this
        is then only its first season, in plot coordinates."""
        T, p, vs = self.tree, self.p, self.vs
        n = T.n
        alive = T.death[:n] < 0
        off, sseed = self._frame()
        absorbing = alive & ((T.birth[:n] >= t - int(p.absorbing_years)) | (T.term[:n] == 1)) & (np.arange(n) > 0)
        mid = T.pos[:n][absorbing] - 0.5 * T.length[:n][absorbing, None] * T.dir[:n][absorbing]
        own = T.pos[:n][alive]
        if off is not None:
            mid, own = mid + off, own + off
        L = T.length[:n][absorbing]
        pts, ls = [mid], [L]
        for a, dx, dy in (clones or []):
            c, s = math.cos(a), math.sin(a)
            q = mid.copy()
            q[:, 0] = c * mid[:, 0] - s * mid[:, 1] + dx
            q[:, 1] = s * mid[:, 0] + c * mid[:, 1] + dy
            pts.append(q)
            ls.append(L)
        pts = np.concatenate(pts) if pts else np.zeros((0, 3))
        ls = np.concatenate(ls) if ls else np.zeros(0)
        zlo = -int(math.ceil(self.soil.max_depth / vs)) - 1
        if cell is not None:
            x0, y0, nx, ny = cell
            lo = np.array([int(round(x0 / vs)), int(round(y0 / vs)), zlo])
        else:
            allp = np.concatenate([own, pts]) if len(pts) else own
            m = int(math.ceil(float(p.field_margin) / vs))
            lo = np.array([int(math.floor(allp[:, 0].min() / vs)) - m, int(math.floor(allp[:, 1].min() / vs)) - m, zlo])
            hi = np.array([int(math.floor(allp[:, 0].max() / vs)) + m, int(math.floor(allp[:, 1].max() / vs)) + m])
            nx, ny = int(hi[0] - lo[0] + 1), int(hi[1] - lo[1] + 1)
        nz = -zlo + 1
        rld = _root_density(pts, ls, lo, (nx, ny, nz), vs, p, cell is not None)
        static, stone = _soil_grids(self.soil, sseed, lo, nx, ny, nz, vs)
        A = static * np.exp(-float(p.depletion_coefficient) * rld)
        self.field = (A.astype(np.float32), lo, stone, cell)
        return self.field

    def _sample(self, pts: np.ndarray) -> np.ndarray:
        A, lo, _, cell = self.field
        off, _ = self._frame()
        if off is not None:
            pts = pts + off
        c = pts / self.vs - lo - 0.5
        if cell is None:
            return map_coordinates(A, c.T, order=1, mode="constant", cval=0.0)
        out = map_coordinates(A, c.T, order=1, mode="grid-wrap")
        return np.where((c[:, 2] < -0.5) | (c[:, 2] > A.shape[2] - 0.5), 0.0, out)

    def _stone_at(self, pts: np.ndarray) -> np.ndarray:
        off, sseed = self._frame()
        return self.soil.is_stone(pts if off is None else pts + off, sseed)

    def _depth_at(self, xy: np.ndarray) -> np.ndarray:
        """Rootable depth under horizontal positions xy (this tree's frame)."""
        off, sseed = self._frame()
        return self.soil.depth_at(xy if off is None else xy + off[:2], sseed)

    # -- one season ----------------------------------------------------------
    def absorbing(self, t: int):
        """Midpoints and lengths of this year's absorbing roots."""
        T, p = self.tree, self.p
        n = T.n
        alive = T.death[:n] < 0
        ab = alive & ((T.birth[:n] >= t - int(p.absorbing_years)) | (T.term[:n] == 1)) & (np.arange(n) > 0)
        return T.pos[:n][ab] - 0.5 * T.length[:n][ab, None] * T.dir[:n][ab], T.length[:n][ab]

    def step(self, t: int, budget: float, clones=None, cell=None, shared=None):
        T, p, rng = self.tree, self.p, self.rng
        n0 = T.n
        alive = T.death[:n0] < 0
        if shared is not None:
            self.field = shared.field      # the plot's soil, built once for all trees
        else:
            self.availability_field(t, clones, cell)
        tips = np.nonzero(alive & (T.term[:n0] == 1))[0]
        prim = np.nonzero(alive & (T.lat[:n0] == LAT_DORMANT))[0]
        q_tip = np.zeros(n0)
        q_prim = np.zeros(n0)
        if tips.size:
            q_tip[tips] = self._sample(T.pos[tips])
        if prim.size:
            q_prim[prim] = self._sample(T.pos[prim])

        # shedding: a lateral root whose tips and primordia no longer find water
        levels = T.levels(alive)
        cnt = np.zeros(n0)
        cnt[tips] += 1.0
        cnt[prim] += 1.0
        Csum = T.basipetal(levels, cnt)
        Qsum = T.basipetal(levels, q_tip + q_prim)
        cand = np.nonzero(alive & T.is_lateral[:n0] & (T.birth[:n0] <= t - 2))[0]
        mean_q = Qsum[cand] / np.maximum(Csum[cand], 1e-12)
        shed = cand[(Csum[cand] <= 0) | (mean_q < float(p.shed_availability))]
        if shed.size:
            self._shed(t, shed, levels)
            alive = T.death[:n0] < 0
            tips = tips[alive[tips]]
            prim = prim[alive[prim]]
            q_tip[~alive] = 0.0
            q_prim[~alive] = 0.0
            levels = T.levels(alive)

        # Borchert-Honda split of the root budget
        ax = T.axis[:n0]
        tap_age = t
        tap_fade = math.exp(-tap_age / float(p.taproot_fade_years))
        wt = np.zeros(n0)
        wt[tips] = q_tip[tips] * np.where(self.kind[ax[tips]] == 0, tap_fade, 1.0)
        collar = self.kind[ax] == 0                # nodes on the taproot / root collar
        wt[prim] = q_prim[prim] * np.where(collar[prim], float(p.collar_primordium_weight), float(p.primordium_weight))
        Wtot = T.basipetal(levels, wt)
        mc, lc = T.main_child[:n0], T.lat_child[:n0]
        Qm = np.where(mc >= 0, Wtot[np.maximum(mc, 0)], np.where(T.term[:n0] == 1, wt, 0.0))
        Ql = np.where(lc >= 0, Wtot[np.maximum(lc, 0)], np.where(T.lat[:n0] == LAT_DORMANT, wt, 0.0))
        lam = np.where(lc >= 0, float(p.apical_control), float(p.apical_dominance))
        # once the taproot has stopped, the collar is no apex: its main
        # laterals share without a bias towards the deeper ones
        lam = np.where(collar, float(p.collar_apical_control), lam)
        den = lam * Qm + (1 - lam) * Ql
        fm = np.divide(lam * Qm, den, out=np.zeros(n0), where=den > 0)
        vin = np.zeros(n0)
        vm = np.zeros(n0)
        vl = np.zeros(n0)
        vin[0] = budget
        par = T.parent
        for li, (seg, mains, lats) in enumerate(levels):
            if li > 0:
                if mains.size:
                    vin[mains] = vm[par[mains]]
                if lats.size:
                    vin[lats] = vl[par[lats]]
            vm[seg] = vin[seg] * fm[seg]
            vl[seg] = vin[seg] - vm[seg]
        v_tip = vm[tips]
        v_prim = vl[prim]
        thr = np.where(collar[prim], float(p.collar_lateral_threshold), float(p.lateral_threshold))
        g_tip = tips[v_tip >= 1.0]
        g_prim = prim[v_prim >= thr]
        self._grow(t, g_tip, v_tip[v_tip >= 1.0], g_prim, v_prim[v_prim >= thr])

        # tips that find no water die; unused primordia age and die; the
        # taproot stops where it turns horizontal or is overtaken [L35]
        it = tips[v_tip < 1.0]
        T.term[it[q_tip[it] < float(p.tip_survival_availability)]] = 0
        tap = np.nonzero((T.term[:T.n] == 1) & (T.death[:T.n] < 0) & (self.kind[T.axis[:T.n]] == 0))[0]
        T.term[tap[-T.pos[tap, 2] > float(p.taproot_max_depth)]] = 0
        stay = prim[v_prim < thr]
        T.lat_age[stay] += 1
        # the root collar keeps forming main laterals for years; primordia
        # elsewhere die unused
        life = np.where(collar[stay], int(p.collar_primordium_lifespan), int(p.primordium_lifespan))
        T.lat[stay[T.lat_age[stay] > life]] = LAT_DEAD
        self.diag = {"tips": int(tips.size), "grown_tips": int(g_tip.size), "new_laterals": int(g_prim.size), "shed": int(shed.size)}
        if bool(getattr(p, "trim_taproot", False)):
            self._trim_taproot(t)

    def _trim_taproot(self, t: int):
        """Silver birch keeps no taproot [L35]: once the seedling taproot has
        stopped, the bare part below the deepest living main lateral decays.
        Its pipes stay in the collar zone as heartwood, so radii never shrink."""
        T = self.tree
        chain = [0]
        while T.main_child[chain[-1]] >= 0 and T.death[T.main_child[chain[-1]]] < 0:
            chain.append(int(T.main_child[chain[-1]]))
        chain = np.array(chain)
        if len(chain) < 2 or T.term[chain[-1]] == 1:
            return
        lc = T.lat_child[chain]
        has = (lc >= 0) & (T.death[np.maximum(lc, 0)] < 0)
        if not has.any():
            return
        j = int(np.nonzero(has)[0].max())
        stub = chain[j + 1:]
        if stub.size == 0:
            return
        if len(self.P) > stub[0]:
            T.own_pipe[chain[j]] += self.P[stub[0]]
        T.main_child[chain[j]] = -1
        T.death[stub] = t
        T.term[stub] = 0

    def _shed(self, t, roots, levels):
        T = self.tree
        kill = np.zeros(T.n, bool)
        kill[roots] = True
        for seg, _, _ in levels[1:]:
            kill[seg] |= kill[T.parent[seg]]
        p = T.parent[roots]
        # a dead root's pipes stay in its parent as heartwood (tip-pipe units)
        np.add.at(T.own_pipe, p, self.P[roots] if len(self.P) > roots.max() else 0.0)
        T.lat_child[p] = -1
        T.lat[p] = LAT_DEAD
        dead = np.nonzero(kill)[0]
        T.death[dead] = t
        T.term[dead] = 0

    def _avoidance(self):
        """Near the collar, growing roots keep clear of the stem column and of
        other roots (root-stem and root-root avoidance): living root nodes
        within the avoidance zone, in a KD-tree, with each axis' parent axis."""
        T, p = self.tree, self.p
        c = getattr(p, "avoid_clearance_m", None)
        if c is None:
            return None
        n = T.n
        ids = np.nonzero(T.death[:n] < 0)[0]
        ids = ids[ids > 0]
        zone = float(p.avoid_zone_radius_m)
        ids = ids[np.hypot(T.pos[ids, 0], T.pos[ids, 1]) < zone + 0.3]
        first = np.nonzero(T.is_lateral[:n])[0]
        par_axis = np.full(int(T.axis[:n].max()) + 1 + 4096, -1, np.int64)
        par_axis[T.axis[first]] = T.axis[T.parent[first]]
        kd = cKDTree(T.pos[ids]) if ids.size else None
        return {"kd": kd, "ids": ids, "par_axis": par_axis, "c": float(c), "zone": zone,
                "w": float(p.avoid_weight), "r_stem": float(T.radius[0])}

    def _avoid(self, av, P, Dn, axis_now, parent_axis, r_self):
        """Add a push away from the stem column and from nearby roots."""
        T = self.tree
        h = np.hypot(P[:, 0], P[:, 1])
        ii = np.nonzero(h < av["zone"])[0]
        if ii.size == 0:
            return Dn
        push = np.zeros((ii.size, 3))
        c = av["c"]
        # root-stem: the stem column below ground has the collar radius
        lim = av["r_stem"] + 2.0 * c
        s_ = np.clip((lim - h[ii]) / (2.0 * c), 0.0, 1.0)
        push[:, :2] += s_[:, None] * P[ii, :2] / np.maximum(h[ii], 1e-6)[:, None]
        # root-root: other roots closer than their radii plus the clearance
        if av["kd"] is not None:
            reach = c + r_self[ii].max() + float(T.radius[av["ids"]].max())
            tips = cKDTree(P[ii])
            pairs = tips.sparse_distance_matrix(av["kd"], reach, output_type="ndarray")
            if len(pairs):
                a, j, d = pairs["i"], pairs["j"], pairs["v"]
                node = av["ids"][j]
                ax = T.axis[node]
                ok = (ax != axis_now[ii][a]) & (ax != parent_axis[ii][a]) & (d > 1e-6)
                a, node, d = a[ok], node[ok], d[ok]
                lim2 = r_self[ii][a] + T.radius[node] + c
                close = d < lim2
                a, node, d, lim2 = a[close], node[close], d[close], lim2[close]
                if a.size:
                    v = (P[ii][a] - T.pos[node]) / d[:, None] * (1.0 - d / lim2)[:, None]
                    np.add.at(push, a, v)
        out = Dn.copy()
        out[ii] = _normalize(Dn[ii] + av["w"] * push)
        return out

    def _grow(self, t, g_tip, v_tip, g_prim, v_prim):
        T, p, rng = self.tree, self.p, self.rng
        starts = np.concatenate([g_tip, g_prim]).astype(np.int64)
        if starts.size == 0:
            return
        av = self._avoidance()
        is_lat = np.concatenate([np.zeros(len(g_tip), bool), np.ones(len(g_prim), bool)])
        v = np.concatenate([v_tip, v_prim])
        l0 = float(p.segment_length)
        nmax = max(1, int(float(p.max_extension_per_year) / l0))
        vc = np.minimum(v, nmax)
        nmet = np.floor(vc).astype(np.int64)
        seg_len = l0 * vc / nmet
        D = _normalize(np.where(is_lat[:, None], T.lat_dir[starts], T.term_dir[starts]))
        axis = T.axis[starts].astype(np.int64)
        order = T.order[starts].astype(np.int64) + is_lat
        li = np.nonzero(is_lat)[0]
        if li.size:
            new_ids = np.arange(len(self.gsa), len(self.gsa) + li.size)
            axis[li] = new_ids
            # main laterals from the taproot; sinkers drop from main laterals near the stem
            parent_kind = self.kind[T.axis[starts[li]]]
            horiz = np.hypot(T.pos[starts[li], 0], T.pos[starts[li], 1])
            sinker = (parent_kind == 1) & (horiz <= float(p.sinker_zone_radius)) & (rng.random(li.size) < float(p.sinker_probability))
            kind = np.where(parent_kind == 0, 1, np.where(sinker, 2, 1))
            self._new_axes(new_ids, kind)
        R = _perpendicular(np.where(is_lat[:, None], T.dir[starts], T.ref[starts]), D)
        gsa = self.gsa[axis]
        eta = self.eta[axis]
        xi = float(p.hydrotropism_per_m)
        noise = float(p.direction_noise_per_sqrt_m)
        ztop = -float(p.min_depth)
        alive_tip = np.ones(len(starts), bool)
        cur = starts.copy()
        for k in range(int(nmet.max())):
            act = np.nonzero((nmet > k) & alive_tip)[0]
            if act.size == 0:
                break
            m = act.size
            c = cur[act]
            P = T.pos[c]
            Dk = D[act]
            L = seg_len[act]
            zbot = -self._depth_at(P[:, :2]) + 0.02
            # hydrotropism: towards the wettest probe point in the forward cone
            probes = P[:, None, :] + float(p.probe_radius) * self.probe[None]
            a = self._sample(probes.reshape(-1, 3)).reshape(m, -1)
            cosang = Dk @ self.probe.T
            a = np.where(cosang > 0.0, a, -np.inf)
            best = self.probe[np.argmax(a, axis=1)]
            target = setpoint_directions(Dk, gsa[act])
            Dn = _normalize(Dk + (xi * L)[:, None] * best + (eta[act] * L)[:, None] * target
                            + (noise * np.sqrt(L))[:, None] * rng.standard_normal((m, 3)))
            if av is not None:
                # a lateral started this season still has its parent's axis
                # at its base; a continuing tip's parent axis is looked up
                own_ax = axis[act]
                pa = np.where(is_lat[act], T.axis[starts[act]], av["par_axis"][np.minimum(own_ax, len(av["par_axis"]) - 1)])
                Dn = self._avoid(av, P, Dn, own_ax, pa, np.maximum(T.radius[c], float(p.tip_radius)))
            mt = getattr(p, "max_turn_deg_per_segment", None)
            if mt:
                Dn = _limit_turn(Dk, Dn, math.radians(float(mt)))
            # stay in the soil: below the surface, above the compact subsoil
            Dn = _clamp_z(Dn, (zbot - P[:, 2]) / L, (ztop - P[:, 2]) / L)
            # stones: a tip that meets a stone turns sideways along it (a root
            # tip touching a barrier bends and grows along its surface: Massa
            # & Gilroy 2003, Plant J. 33:435), by the smallest turn of 30, 60
            # or 90 deg towards any of 8 sides that clears it; a tip boxed in
            # on every side stops
            newp = P + L[:, None] * Dn
            blocked = self._stone_at(newp)
            if blocked.any():
                bi = np.nonzero(blocked)[0]
                Db = Dn[bi]
                e1 = _perpendicular(np.tile([1.0, 0.0, 0.0], (bi.size, 1)), Db)
                e2 = np.cross(Db, e1)
                phase = rng.uniform(0.0, 2.0 * np.pi, bi.size)
                for ang in np.radians([30.0, 60.0, 90.0]):
                    for j in range(8):
                        still = blocked[bi]
                        if not still.any():
                            break
                        phi = phase + j * np.pi / 4.0
                        alt = math.cos(ang) * Db + math.sin(ang) * (np.cos(phi)[:, None] * e1 + np.sin(phi)[:, None] * e2)
                        alt = _clamp_z(alt, (zbot[bi] - P[bi, 2]) / L[bi], (ztop - P[bi, 2]) / L[bi])
                        ok = still & ~self._stone_at(P[bi] + L[bi, None] * alt)
                        Dn[bi[ok]] = alt[ok]
                        blocked[bi[ok]] = False
            if blocked.any():
                alive_tip[act[blocked]] = False
                keep = ~blocked
                act, c, P, Dn, L = act[keep], c[keep], P[keep], Dn[keep], L[keep]
                if act.size == 0:
                    continue
            m = act.size
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
            first = (cur[act] == starts[act])
            lat_first = first & is_lat[act]
            main_first = first & ~is_lat[act]
            T.is_lateral[new] = lat_first
            T.main_child[c[main_first]] = new[main_first]
            T.term[c[main_first]] = 0
            T.lat_child[c[lat_first]] = new[lat_first]
            T.lat[c[lat_first]] = LAT_USED
            later = ~first
            T.main_child[c[later]] = new[later]
            # a lateral-root primordium at every new node, pointing out at
            # the branching angle on a random side; on the taproot the
            # primordia follow a fixed divergence (rhizotaxy), so the main
            # laterals spread evenly around the collar
            phi = rng.uniform(0.0, 2.0 * np.pi, m)
            on_tap = self.kind[axis[act]] == 0
            if on_tap.any():
                phi[on_tap] = self.rhizo_phase + math.radians(float(p.collar_divergence_deg)) * T.depth[new[on_tap]]
            W = np.cross(Dn, Rn)
            u = np.cos(phi)[:, None] * Rn + np.sin(phi)[:, None] * W
            th = math.radians(float(p.branch_angle_deg))
            T.lat[new] = LAT_DORMANT
            T.lat_age[new] = 0
            T.lat_dir[new] = _normalize(math.cos(th) * Dn + math.sin(th) * u)
            T.term[new] = 0
            cur[act] = new
            D[act] = Dn
            R[act] = Rn
        ends = cur[cur != starts]
        T.term[ends] = 1
        T.term_dir[ends] = D[np.nonzero(cur != starts)[0]]

    # -- radii, uptake, measures ---------------------------------------------
    def update_radii(self, collar_pipe: float, gamma: float, tip_pipe: float, zrt_length: float = 0.0):
        """Root radii.  At the collar the shoot's pipes (``collar_pipe`` =
        r_stem_base^gamma) are shared out over the root branches in
        proportion to their own tip pipes, so the collar matches the stem
        base.  Away from the stem, roots follow their own pipe model (their
        tips' pipes alone, much thinner): the extra wood near the stem is
        the zone of rapid taper (Eis 1974; Danjon et al. 2005), laid on for
        anchorage, and fades as exp(-distance / ``zrt_length``)."""
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        levels = T.levels(alive)
        own = np.where(alive & (T.main_child[:n] < 0) & (np.arange(n) > 0), tip_pipe, 0.0)
        own = own + np.where(alive, T.own_pipe[:n], 0.0)
        P = T.basipetal(levels, own)
        self.P = P
        scale = collar_pipe / max(P[0], 1e-30)
        r = (P * scale) ** (1.0 / gamma)
        if zrt_length > 0.0:
            r_far = np.minimum(P ** (1.0 / gamma), r)
            # distance from the collar along the root, so a root never
            # thickens towards its tip where it curves back to the stem
            d = np.where(alive, T.length[:n], 0.0)
            d[0] = 0.0
            for seg, _, _ in levels[1:]:
                d[seg] += d[T.parent[seg]]
            r = r_far + (r - r_far) * np.exp(-d / zrt_length)
            self.path_dist = d
        self.zrt_length = float(zrt_length)
        T.radius[:n] = np.where(alive, r, T.radius[:n])
        if not getattr(self, "lean", False):
            self.radius_history.append(T.radius[:n].astype(np.float16))

    def update_uptake(self, t: int, k_axial: float, fine_root_mass: float | None = None):
        """Root uptake conductance (kg s^-1 MPa^-1): absorbing roots in series
        with the woody path back to the stem.  With ``fine_root_mass`` (g, the
        fine roots the tree pays for) and roots.fine_root_uptake on, water
        enters through those fine roots: their length (mass x specific root
        length) is spread over this year's absorbing roots in proportion to
        their length, at a conductance per metre from the measured root-system
        conductance of young silver birch; otherwise at
        uptake_conductance_per_m of absorbing structural root."""
        T, p = self.tree, self.p
        n = T.n
        alive = T.death[:n] < 0
        absorbing = alive & ((T.birth[:n] >= t - int(p.absorbing_years)) | (T.term[:n] == 1)) & (np.arange(n) > 0)
        if not absorbing.any():
            self.uptake_conductance = 0.0     # no absorbing root: no water in
            return
        mid = T.pos[:n] - 0.5 * T.length[:n, None] * T.dir[:n]
        a = np.zeros(n)
        a[absorbing] = self._sample(mid[absorbing])
        fu = getattr(p, "fine_root_uptake", None)
        if fine_root_mass is not None and fu is not None and bool(fu.enabled):
            srl = float(fu.specific_root_length_m_per_g)
            # conductance per metre of fine root: root-system conductance per
            # leaf area over the fine-root length per leaf area of the same trees
            k_len = float(fu.root_conductance_per_leaf_area) / (
                float(fu.fine_root_per_leaf_mass) * float(fu.leaf_mass_per_area_g_m2) * srl)
            self.fine_root_length = float(fine_root_mass) * srl
            L_abs = np.where(absorbing, T.length[:n], 0.0)
            g = k_len * self.fine_root_length * L_abs / max(float(L_abs.sum()), 1e-12) * a
        else:
            g = float(p.uptake_conductance_per_m) * T.length[:n] * a * absorbing
        area = np.pi * np.maximum(T.radius[:n], 1e-5) ** 2
        r_seg = np.where(alive, T.length[:n] / (k_axial * area), 0.0)
        levels = T.levels(alive)
        path = r_seg.copy()
        for seg, _, _ in levels[1:]:
            path[seg] += path[T.parent[seg]]
        geff = np.where(g > 0, 1.0 / (1.0 / np.maximum(g, 1e-30) + path), 0.0)
        self.uptake_conductance = float(geff.sum())

    def critical_turning_moment(self, ap, stem_volume_m3: float, roots: list) -> dict | None:
        """Critical turning moment for uprooting, the ForestGALES way: an
        empirical regression of tree-pulling moments on stem size (here
        Krisans et al. 2022, silver birch, through the origin on stem
        volume), adjusted for the simulated rooting depth and, by wind
        direction, for the asymmetry of the main structural roots."""
        creg = getattr(ap, "critical_moment_per_stem_volume_knm_per_m3", None)
        if not creg or stem_volume_m3 <= 0.0 or not roots:
            return None
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        alive[0] = False
        near = alive & (np.hypot(T.pos[:n, 0], T.pos[:n, 1]) <= float(ap.rooting_depth_radius_m))
        d_root = float(-T.pos[:n][near, 2].min()) if near.any() else 0.0
        d_root = min(d_root, float(self._depth_at(np.zeros((1, 2)))[0]))
        f_depth = float(np.clip(d_root / float(ap.reference_rooting_depth_m), float(ap.depth_factor_min), float(ap.depth_factor_max)))
        st = [r for r in roots if r.get("structural")] or roots
        az = np.radians([r["azimuth_deg"] for r in st])
        area = np.array([r["base_diameter_m"] ** 2 for r in st])
        dirs = np.radians(np.arange(0, 360, 45))
        tens = np.array([(area * np.maximum(0.0, np.cos(az - w))).sum() for w in dirs])
        share = float(ap.root_tension_share)
        f_asym = (1.0 - share) + share * tens / max(float(tens.mean()), 1e-12)
        m = float(creg) * stem_volume_m3 * f_depth * f_asym
        return {
            "method": "C_reg x stem volume (Krisans et al. 2022, silver birch) x rooting-depth factor x root asymmetry",
            "mean_knm": round(float(m.mean()), 2),
            "min_knm": round(float(m.min()), 2),
            "by_wind_dir_knm": {f"{int(np.degrees(w))}": round(float(v), 2) for w, v in zip(dirs, m)},
            "stem_volume_m3": round(stem_volume_m3, 4),
            "rooting_depth_m": round(d_root, 3),
            "depth_factor": round(f_depth, 3),
            "asymmetry_factor_range": [round(float(f_asym.min()), 3), round(float(f_asym.max()), 3)],
        }

    def anchorage(self, ap, height_m: float, dbh_cm: float | None, stem_mass_kg: float,
                  stem_volume_m3: float = 0.0) -> dict:
        """Overturning resistance and main-root strengths, for later storm
        modelling (numbers only).

        Root-soil plate (Coutts 1986): each first-order root counts out to
        where it thins below ``plate_root_diameter``; the plate radius is the
        median of those distances and its depth the 90th percentile depth of
        root length inside it.  Resistance to overturning about the leeward
        hinge = plate weight x radius + tension of the windward roots at the
        plate edge x their lever (root strength: power law in diameter).
        The empirical cross-check scales with H * DBH^2 (Peltola et al. 2000).
        """
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        main = np.nonzero(alive & T.is_lateral[:n] & (T.order[:n] == 1))[0]
        d_plate = float(ap.plate_root_diameter)
        s1, beta = float(ap.tensile_strength_1mm_mpa), float(ap.tensile_strength_exponent)

        def strength_kn(d):
            sig = s1 * np.power(np.maximum(d * 1000.0, 1e-3), -beta) * 1e6  # Pa
            return sig * np.pi * d * d / 4.0 / 1000.0                      # kN

        roots = []
        for s in main.tolist():
            chain = [s]
            while T.main_child[chain[-1]] >= 0 and T.death[T.main_child[chain[-1]]] < 0:
                chain.append(int(T.main_child[chain[-1]]))
            chain = np.array(chain)
            d = 2.0 * T.radius[chain]
            inside = np.nonzero(d >= d_plate)[0]
            edge = chain[inside[-1]] if inside.size else chain[0]
            p0 = T.pos[T.parent[s]]
            pe = T.pos[edge]
            base_d = float(2.0 * T.radius[s])
            # end of the taper zone along this root: where the extra wood
            # near the stem has faded to 5 % (path distance ln(20) x length)
            tz = chain[-1]
            if getattr(self, "zrt_length", 0.0) > 0.0 and getattr(self, "path_dist", None) is not None:
                past = np.nonzero(self.path_dist[chain] >= math.log(20.0) * self.zrt_length)[0]
                tz = chain[past[0]] if past.size else chain[-1]
            pt = T.pos[tz]
            q = np.nonzero(d >= 0.25 * d[0])[0]
            pq = T.pos[chain[q[-1]] if q.size else chain[0]]
            roots.append({
                "quarter_base_distance_m": round(float(np.hypot(pq[0], pq[1])), 3),
                "taper_end_distance_m": round(float(np.hypot(pt[0], pt[1])), 3),
                "taper_end_diameter_m": round(float(2.0 * T.radius[tz]), 4),
                "breaking_force_taper_end_kn": round(float(strength_kn(2.0 * T.radius[tz])), 3),
                "node": int(s),
                "azimuth_deg": round(float(np.degrees(np.arctan2(pe[1] - p0[1], pe[0] - p0[0]))) % 360.0, 1),
                "depth_m": round(float(-p0[2]), 3),
                "base_diameter_m": round(base_d, 4),
                "plate_edge_distance_m": round(float(np.hypot(pe[0], pe[1])), 3),
                "edge_diameter_m": round(float(2.0 * T.radius[edge]), 4),
                "breaking_force_base_kn": round(float(strength_kn(base_d)), 3),
                "breaking_force_edge_kn": round(float(strength_kn(2.0 * T.radius[edge])), 3),
            })
        if not roots:
            return {"plate_radius_m": 0.0, "main_roots": []}
        # The plate is held by the main structural roots: the fewest main
        # roots that carry ``plate_structural_share`` of the cross-section of
        # all main roots at their base; its radius is their plate-edge
        # distance weighted by cross-section (small first-order roots that
        # thin out at the collar do not shrink it).
        area = np.array([r["base_diameter_m"] ** 2 for r in roots])
        edge = np.array([r["plate_edge_distance_m"] for r in roots])
        o = np.argsort(-area)
        k = int(np.searchsorted(np.cumsum(area[o]) / area.sum(), float(getattr(ap, "plate_structural_share", 0.8)))) + 1
        sel = o[:k]
        tend = np.array([r["taper_end_distance_m"] for r in roots])
        rules = {
            "median_all_main_roots_2cm": float(np.median(edge)),
            "structural_roots_2cm": float((area[sel] * edge[sel]).sum() / area[sel].sum()),
            "taper_zone_end": float((area[sel] * tend[sel]).sum() / area[sel].sum()),
            "structural_roots_quarter_base": float((area[sel] * np.array([r["quarter_base_distance_m"] for r in roots])[sel]).sum()
                                                   / area[sel].sum()),
        }
        rule = str(getattr(ap, "plate_radius_rule", "taper_zone_end"))
        Rp = rules[rule]
        for i, r in enumerate(roots):
            r["structural"] = bool(i in set(sel.tolist()))
        mid = T.pos[:n] - 0.5 * T.length[:n, None] * T.dir[:n]
        inplate = alive & (np.hypot(mid[:, 0], mid[:, 1]) <= Rp) & (np.arange(n) > 0)
        if inplate.any():
            dep = -mid[inplate, 2]
            o = np.argsort(dep)
            cum = np.cumsum(T.length[:n][inplate][o]) / T.length[:n][inplate].sum()
            Dp = float(dep[o][min(np.searchsorted(cum, 0.9), len(o) - 1)])
            Dmax = float(dep.max())
        else:
            Dp = Dmax = 0.0
        g = 9.81
        plate_mass = self.soil.bulk_density * np.pi * Rp * Rp * Dp / 2.0
        m_soil = plate_mass * g * Rp / 1000.0                                    # kN m
        az = np.radians([r["azimuth_deg"] for r in roots])
        fe = np.array([r["breaking_force_taper_end_kn" if rule == "taper_zone_end" else "breaking_force_edge_kn"]
                       for r in roots])
        # resistance under every rule, for comparison (soil weight + tension)
        def resist(R, edge_key):
            dep = -mid[alive & (np.hypot(mid[:, 0], mid[:, 1]) <= R) & (np.arange(n) > 0), 2]
            if dep.size == 0:
                return 0.0
            D = float(np.percentile(dep, 90))
            m_s = self.soil.bulk_density * np.pi * R * R * D / 2.0 * 9.81 * R / 1000.0
            az_ = np.radians([r["azimuth_deg"] for r in roots])
            f_ = np.array([r[edge_key] for r in roots])
            return float(np.mean([m_s + float(ap.root_strength_mobilised) * float((f_ * R * (1 + np.cos(az_ - w)) * (np.cos(az_ - w) > 0)).sum())
                                  for w in np.radians(np.arange(0, 360, 45))]))
        by_rule = {k_: round(resist(v, "breaking_force_taper_end_kn" if k_ == "taper_zone_end" else "breaking_force_edge_kn"), 2)
                   for k_, v in rules.items()}
        per_dir = []
        for wind in np.radians(np.arange(0, 360, 45)):
            c = np.cos(az - wind)                                               # +1: root points upwind
            lever = Rp * (1.0 + c)
            per_dir.append(m_soil + float(ap.root_strength_mobilised) * float((fe * lever * (c > 0)).sum()))
        emp = emp_range = None
        if dbh_cm:
            hd2 = height_m * (dbh_cm / 100.0) ** 2
            emp = float(ap.h_dbh2_coefficient_knm_per_m3) * hd2
            rng_c = getattr(ap, "h_dbh2_coefficient_range", None)
            if rng_c:
                emp_range = [round(float(rng_c[0]) * hd2, 2), round(float(rng_c[1]) * hd2, 2)]
        return {
            "plate_radius_m": round(Rp, 3),
            "plate_radius_rule": rule,
            "plate_radius_by_rule_m": {k_: round(v, 3) for k_, v in rules.items()},
            "overturning_resistance_mean_by_rule_knm": by_rule,
            "structural_roots": int(k),
            "taper_zone_radius_m": None if not dbh_cm else round(float(getattr(self.p, "zrt_radius_per_dbh", 0.0)) * dbh_cm / 100.0, 3),
            "plate_depth_m": round(Dp, 3),
            "plate_max_root_depth_m": round(Dmax, 3),
            "plate_soil_mass_kg": round(float(plate_mass), 1),
            "resistance_soil_weight_knm": round(m_soil, 2),
            "overturning_resistance_min_knm": round(min(per_dir), 2),
            "overturning_resistance_mean_knm": round(float(np.mean(per_dir)), 2),
            "overturning_resistance_by_wind_dir_knm": {f"{d}": round(v, 2) for d, v in zip(range(0, 360, 45), per_dir)},
            "empirical_h_dbh2_knm": None if emp is None else round(emp, 2),
            "empirical_h_dbh2_range_knm": emp_range,
            "stem_fresh_mass_kg": round(stem_mass_kg, 1),
            "critical_turning_moment": self.critical_turning_moment(ap, stem_volume_m3, roots),
            "main_roots": roots,
        }

    def measure(self) -> dict:
        T = self.tree
        n = T.n
        alive = T.death[:n] < 0
        alive[0] = False
        if not alive.any():
            return {"root_length_m": 0.0}
        mid = T.pos[:n] - 0.5 * T.length[:n, None] * T.dir[:n]
        L = T.length[:n][alive]
        depth = -mid[alive, 2]
        horiz = np.hypot(mid[alive, 0], mid[alive, 1])
        tot = float(L.sum())
        order = np.argsort(depth)
        cum = np.cumsum(L[order]) / tot
        d90 = float(depth[order][np.searchsorted(cum, 0.9)])
        oh = np.argsort(horiz)
        ch = np.cumsum(L[oh]) / tot
        r95 = float(horiz[oh][min(np.searchsorted(ch, 0.95), len(oh) - 1)])
        return {
            "root_length_m": round(tot, 2),
            "root_max_depth_m": round(float(depth.max()), 3),
            "root_depth_90pct_m": round(d90, 3),
            "root_share_top_30cm": round(float(L[depth <= 0.3].sum() / tot), 3),
            "root_share_top_50cm": round(float(L[depth <= 0.5].sum() / tot), 3),
            "root_spread_max_m": round(float(horiz.max()), 3),
            "root_spread_95pct_m": round(r95, 3),
            # horizontal distance of the root-length centroid from the stem
            "root_centroid_offset_m": round(float(np.hypot(*((mid[alive, :2] * L[:, None]).sum(0) / tot))), 3),
            "root_axes_by_kind": {k: int(c) for k, c in zip(("taproot", "lateral", "sinker"),
                                                          np.bincount(self.kind[np.unique(T.axis[:n][alive])], minlength=3))},
            "root_uptake_conductance": float(self.uptake_conductance),
        }
