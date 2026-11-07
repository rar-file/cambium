"""Natural regeneration in a plot: seed rain from the living trees,
germination where light and the seedbed allow, and recruitment of the young
seedlings as trees of their own.  From then on a recruit lives or dies by
the model like any other tree: shade through its carbon balance, drought
through its water, moose through leader browsing above 0.3 m, and the plot's
death rules (treegen/plot.py).

Each year, on a ground grid of square cells (``cell_m``):

1. Seed rain.  Every tree at least ``maturity_years`` old with a stem
   diameter sheds ``seeds_ref * (DBH / dbh_ref) ** fecundity_exponent``
   seeds, spread by a 2-D exponential dispersal kernel with mean distance
   ``dispersal_mean_m``.  The plot repeats periodically, so seeds carried
   past its edge come back in from the other side (the seed of the
   surrounding stand).
2. Seedbed.  One-year seedlings per seed on exposed mineral soil and on the
   organic layer, as measured unfenced in full light: these hold germination
   and the first year's losses (drought, seed predation, browsing).  A seed
   that lands on a surface stone is lost.
3. Light.  A germinant whose leaves get less than the light at which birch
   leaves die (``shoot.short_shoot_survival_light``, relative to full light,
   at 0.1 m above the ground) dies in its first season.  On the organic
   layer that light also passes the field layer; bared mineral soil has
   none (it grows back over the recruit with the soil's recovery
   half-life, GrowthModel._herb_factor).
4. Recruitment.  At most one recruit per cell and year, and none in a cell
   where a living tree already stands: more than one seedling per square
   metre adds little because they outcompete each other within a few years.
   The cell recruits with the probability that at least one seedling
   established (Poisson), at a random point of the cell off surface stones.
5. Exposed mineral soil: a share of the ground at the start (the stand grows
   up after a stand-replacing disturbance) and a share newly exposed each
   year (uprooting, animals, frost heave), covered again with the field
   layer's recovery half-life (environment ground_vegetation).
"""
from __future__ import annotations

import math

import numpy as np


class Regeneration:
    def __init__(self, rp, light_survival: float, soil, L: float, seed: int):
        self.p = rp
        self.soil = soil
        self.light_survival = float(light_survival)
        self.L = float(L)
        self.seed = int(seed)
        self.rng = np.random.default_rng([self.seed, 4241])
        self.nc = max(1, int(round(self.L / float(rp.cell_m))))
        self.cs = self.L / self.nc                      # cell side (m)
        c = (np.arange(self.nc) + 0.5) * self.cs - 0.5 * self.L
        self.cx, self.cy = np.meshgrid(c, c, indexing="ij")
        self.mineral = np.full((self.nc, self.nc), float(rp.mineral_initial))
        # share of each cell covered by stones reaching the surface
        k = 8
        sub = (np.arange(k) + 0.5) / k * self.cs - 0.5 * self.cs
        sx, sy = np.meshgrid(sub, sub, indexing="ij")
        pts = np.stack([(self.cx[..., None, None] + sx).ravel(), (self.cy[..., None, None] + sy).ravel(),
                        np.full(self.nc * self.nc * k * k, -0.01)], 1)
        self.surface_stone = soil.is_stone(pts, self.seed).reshape(self.nc, self.nc, k * k).mean(-1)
        self.kernel_ft = np.fft.rfft2(self._kernel())
        self.last = {}

    def _kernel(self) -> np.ndarray:
        """Share of a tree's seed landing in each cell, the source in cell
        (0, 0): the 2-D exponential kernel exp(-r/a) / (2 pi a^2), mean
        distance 2a, summed over the periodic images of the plot and
        normalised (every seed lands somewhere in the repeating plot)."""
        a = 0.5 * float(self.p.dispersal_mean_m)
        reach = int(math.ceil(8.0 * a / self.L)) + 1
        d = np.arange(self.nc) * self.cs
        K = np.zeros((self.nc, self.nc))
        for i in range(-reach, reach + 1):
            for j in range(-reach, reach + 1):
                r = np.hypot(d[:, None] + i * self.L, d[None, :] + j * self.L)
                K += np.exp(-r / a)
        return K / K.sum()

    def _cell(self, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ij = np.floor((xy + 0.5 * self.L) / self.cs).astype(int) % self.nc
        return ij[:, 0], ij[:, 1]

    def seed_rain(self, xy: np.ndarray, seeds: np.ndarray) -> np.ndarray:
        """Seeds landing in each cell from sources at xy (plot coordinates)."""
        src = np.zeros((self.nc, self.nc))
        if len(xy):
            i, j = self._cell(xy)
            np.add.at(src, (i, j), seeds)
        return np.maximum(np.fft.irfft2(np.fft.rfft2(src) * self.kernel_ft, s=src.shape), 0.0)

    def fecundity(self, dbh_m: float, age: int) -> float:
        p = self.p
        if age < int(p.maturity_years) or dbh_m <= 0.0:
            return 0.0
        return float(p.seeds_ref) * (dbh_m / float(p.dbh_ref_m)) ** float(p.fecundity_exponent)

    def step(self, trees_xy: np.ndarray, seeds: np.ndarray, canopy_light: np.ndarray, field_layer: float,
             occupied: np.ndarray):
        """One year: returns this year's recruits as (x, y, on mineral soil).
        canopy_light: relative light at 0.1 m in each cell under the trees;
        field_layer: the share of it left under a full field layer (bared
        mineral soil has none); occupied: cells with a living tree."""
        p = self.p
        rain = self.seed_rain(trees_xy, seeds)
        organic = np.maximum(1.0 - self.mineral - self.surface_stone, 0.0)
        lit_m = canopy_light >= self.light_survival
        lit_o = canopy_light * field_layer >= self.light_survival
        e_m = rain * self.mineral * float(p.establishment_mineral) * lit_m
        e_o = rain * organic * float(p.establishment_organic) * lit_o
        expected = e_m + e_o
        chance = np.where(~occupied, 1.0 - np.exp(-expected), 0.0)
        hit = np.nonzero(self.rng.random(chance.shape) < chance)
        out = []
        for i, j in zip(*hit):
            on_mineral = bool(self.rng.random() * expected[i, j] < e_m[i, j])
            for _ in range(8):                      # a point of the cell off surface stones
                x = self.cx[i, j] + (self.rng.random() - 0.5) * self.cs
                y = self.cy[i, j] + (self.rng.random() - 0.5) * self.cs
                if not self._surface_stone(x, y):
                    out.append((x, y, on_mineral))
                    break
        # the seedbed for next year: bared mineral soil is covered again (the
        # field layer's recovery), new soil is bared
        keep = 0.5 ** (1.0 / self._half_life())
        self.mineral = self.mineral * keep + float(p.mineral_new_per_year) * (1.0 - self.mineral * keep)
        self.last = {"seed_rain_per_m2": float(rain.sum() / self.L ** 2), "lit_share": float(lit_m.mean()),
                     "lit_share_field_layer": float(lit_o.mean()),
                     "expected_per_m2": float(expected.sum() / self.L ** 2), "recruits": len(out),
                     "recruits_on_mineral": sum(1 for r in out if r[2]),
                     "mineral_share": float(self.mineral.mean())}
        return out

    def _half_life(self) -> float:
        """Years for bared mineral soil to be half covered again: the field
        layer's recovery (environment), else regeneration.mineral_half_life_years."""
        hl = float(getattr(self.soil, "herb_recovery_half_life", 0.0) or 0.0)
        return hl if hl > 0.0 else float(self.p.mineral_half_life_years)

    def equilibrium_mineral(self) -> float:
        """Share of exposed mineral soil where new exposure balances cover."""
        keep = 0.5 ** (1.0 / self._half_life())
        new = float(self.p.mineral_new_per_year)
        return new / (1.0 - keep * (1.0 - new))

    def _surface_stone(self, x: float, y: float) -> bool:
        return bool(self.soil.is_stone(np.array([[x, y, -0.01]]), self.seed)[0])


class SpreadRegeneration(Regeneration):
    """Regeneration that can carry a forest across open ground (species block
    ``regeneration.spread``, off by default).  What's different from the class above:

    * The ground can be a long rectangle.  Seed carried past the two ends of x
      is lost, where the plain class brings it back round; the sides repeat, so a
      strip stands for a long forest edge.
    * Each tree throws its seed with a mean distance u = exp(u0 + ut T), T the big
      trees in its 10 m cell, as Liu & Evans 2021 fitted: trees at an open edge throw
      furthest.  The shape is Tiebel et al. 2020's negative exponential in distance,
      most seed nearest the tree, with a small share on a far kernel; Liu & Evans's
      lognormal has a hole at the tree and too thin a tail (``kernel``).
    * Crops differ between years, the same year for every tree: mast years, and a tree
      sheds seed only from a stem diameter on, so a cohort doesn't start all at once.
    * A germinant's chance rises with light between two values, and it needs an opening
      over it: none takes where the leaf area overhead, read over a crown's width, is
      over ``canopy_lai_max``.  The plain class has one cut-off, the light at which birch
      leaves die, and that passes the ground of a closed canopy in this model (it read
      22-34 % on older settings).  The light field alone can't tell a gap from a canopy
      here: its contrast is low (a windthrow plot read 0.42 at the 10th percentile, 0.52
      at the 90th).
    * Open ground starts with the mineral soil of old ground (new exposure balances
      cover), not the share bared by a stand-replacing disturbance.
    * ``max_recruits_per_year``, a limit on memory and not a model value: it keeps
      a random draw of the year's recruits, across the whole ground.
    """

    def __init__(self, rp, light_survival: float, soil, lx: float, ly: float, seed: int):
        self.p = rp
        self.soil = soil
        self.light_survival = float(light_survival)
        self.seed = int(seed)
        self.rng = np.random.default_rng([self.seed, 4243])
        self.lx, self.ly = float(lx), float(ly)
        self.L = self.lx
        cell = float(rp.spread.cell_m)
        self.nx, self.ny = max(1, int(round(self.lx / cell))), max(1, int(round(self.ly / cell)))
        self.csx, self.csy = self.lx / self.nx, self.ly / self.ny
        self.cs = math.sqrt(self.csx * self.csy)
        self.nc = self.nx
        cx = (np.arange(self.nx) + 0.5) * self.csx - 0.5 * self.lx
        cy = (np.arange(self.ny) + 0.5) * self.csy - 0.5 * self.ly
        self.cx, self.cy = np.meshgrid(cx, cy, indexing="ij")
        self.mineral = np.full(self.cx.shape, self.equilibrium_mineral())
        k = 4
        sub = (np.arange(k) + 0.5) / k - 0.5
        sx, sy = np.meshgrid(sub * self.csx, sub * self.csy, indexing="ij")
        pts = np.stack([(self.cx[..., None, None] + sx).ravel(), (self.cy[..., None, None] + sy).ravel(),
                        np.full(self.cx.size * k * k, -0.01)], 1)
        self.surface_stone = soil.is_stone(pts, self.seed).reshape(self.nx, self.ny, k * k).mean(-1)
        # room for seed to run past the end of x and stop, rather than come round
        self.nx_pad = self.nx if bool(rp.spread.repeat_ends) else 2 * self.nx
        self._kernels = {}
        self.trees_in_cell = None
        self.overhead = None
        fx = np.fft.fftfreq(self.nx, self.csx)[:, None]
        fy = np.fft.rfftfreq(self.ny, self.csy)[None, :]
        self._cover_ft = np.exp(-2.0 * (math.pi * float(rp.spread.canopy_radius_m)) ** 2 * (fx ** 2 + fy ** 2))
        self.last = {}

    def _cell(self, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        i = np.floor((xy[:, 0] + 0.5 * self.lx) / self.csx).astype(int)
        j = np.floor((xy[:, 1] + 0.5 * self.ly) / self.csy).astype(int) % self.ny
        return i % self.nx, j

    def read_canopy(self, leaves: np.ndarray | None, leaf_area: np.ndarray | None = None) -> None:
        """Leaf area above 2 m per m2 of ground around each cell (m2 per m2), over a crown's width."""
        grid = np.zeros((self.nx, self.ny))
        if leaves is not None and len(leaves):
            high = leaves[:, 2] >= 2.0
            if high.any():
                i, j = self._cell(leaves[high, :2])
                np.add.at(grid, (i, j), np.ones(int(high.sum())) if leaf_area is None else leaf_area[high])
                grid /= self.csx * self.csy
        self.overhead = np.maximum(np.fft.irfft2(np.fft.rfft2(grid) * self._cover_ft, s=grid.shape), 0.0)

    def count_trees(self, big_xy: np.ndarray) -> None:
        """Big trees in each 10 m cell of the ground, as Liu & Evans counted them."""
        size = float(self.p.spread.density_cell_m)
        self._count_nx, self._count_ny = max(1, int(round(self.lx / size))), max(1, int(round(self.ly / size)))
        grid = np.zeros((self._count_nx, self._count_ny), np.int64)
        if len(big_xy):
            i = np.floor((big_xy[:, 0] + 0.5 * self.lx) / self.lx * self._count_nx).astype(int) % self._count_nx
            j = np.floor((big_xy[:, 1] + 0.5 * self.ly) / self.ly * self._count_ny).astype(int) % self._count_ny
            np.add.at(grid, (i, j), 1)
        # as a count per 10 m x 10 m cell, whatever the ground's width makes of the cell
        self.trees_in_cell = grid * (size * size) / (self.lx / self._count_nx * self.ly / self._count_ny)

    def _kernel_ft(self, t: int) -> np.ndarray:
        """The transform of the seed shadow of a tree with t big trees in its
        cell: share of its seed landing in each cell (Liu & Evans 2021 Eq. 2,
        whose text and Table 1 read u as the mean distance: exp(4.18) = 65 m)."""
        if t in self._kernels:
            return self._kernels[t]
        s = self.p.spread
        u = math.exp(float(s.ln_mean_m) + float(s.ln_mean_per_tree) * t)
        p = math.exp(float(s.ln_shape) + float(s.ln_shape_per_tree) * t)
        mu = math.log(u) - 0.5 * p * p
        mix = str(getattr(s, "kernel", "lognormal")) == "exponential_mix"
        far_share = float(getattr(s, "far_share", 0.0)) if mix else 0.0
        far_mean = float(getattr(s, "far_mean_m", u))
        # the cell at the tree: 1/r averaged over its disc is 1/(R/2), which gives its seed correctly
        r_near = 0.5 * math.sqrt(self.csx * self.csy / math.pi)
        nxp, ny = self.nx_pad, self.ny
        ix = np.arange(nxp)
        dx = np.minimum(ix, nxp - ix) * self.csx
        jy = np.arange(ny)
        dy = np.minimum(jy, ny - jy) * self.csy
        reach = int(math.ceil(float(s.kernel_reach_m) / self.ly)) + 1
        K = np.zeros((nxp, ny))
        images_x = range(-(int(math.ceil(float(s.kernel_reach_m) / self.lx)) + 1),
                         int(math.ceil(float(s.kernel_reach_m) / self.lx)) + 2) if bool(s.repeat_ends) else (0,)
        for m in images_x:
            for n in range(-reach, reach + 1):
                r = np.hypot(dx[:, None] + m * self.lx, dy[None, :] + n * self.ly)
                if mix:
                    r = np.maximum(r, r_near)
                    K += ((1.0 - far_share) * np.exp(-r / u) / u + far_share * np.exp(-r / far_mean) / far_mean) / (2.0 * math.pi * r)
                else:
                    r = np.maximum(r, 0.25 * min(self.csx, self.csy))
                    K += np.exp(-((np.log(r) - mu) ** 2) / (2.0 * p * p)) / ((2.0 * math.pi) ** 1.5 * p * r * r)
        K *= self.csx * self.csy
        if bool(s.repeat_ends):
            K /= K.sum()       # every seed lands somewhere in the repeating ground
        else:
            K = np.minimum(K, 1.0)
        self._kernels[t] = np.fft.rfft2(K)
        return self._kernels[t]

    def seed_rain(self, xy: np.ndarray, seeds: np.ndarray) -> np.ndarray:
        """Seeds landing in each cell, each source on the kernel of its big-tree count."""
        rain = np.zeros((self.nx_pad, self.ny))
        if not len(xy):
            return rain[: self.nx]
        most = int(self.p.spread.max_trees_counted)
        if self.trees_in_cell is None:
            t = np.zeros(len(xy), int)
        else:
            ci = np.floor((xy[:, 0] + 0.5 * self.lx) / self.lx * self._count_nx).astype(int) % self._count_nx
            cj = np.floor((xy[:, 1] + 0.5 * self.ly) / self.ly * self._count_ny).astype(int) % self._count_ny
            t = np.minimum(np.round(self.trees_in_cell[ci, cj]).astype(int), most)
        i, j = self._cell(xy)
        for v in np.unique(t).tolist():
            src = np.zeros((self.nx_pad, self.ny))
            pick = t == v
            np.add.at(src, (i[pick], j[pick]), seeds[pick])
            rain += np.fft.irfft2(np.fft.rfft2(src) * self._kernel_ft(int(v)), s=src.shape)
        return np.maximum(rain[: self.nx], 0.0)

    def bare_circle(self, x: float, y: float, radius: float, share: float) -> None:
        """Uprooting bares mineral soil in a windthrow gap: at least this share of each cell in it."""
        dx = np.abs(self.cx - x)
        dy = np.abs(self.cy - y)
        dx, dy = np.minimum(dx, self.lx - dx), np.minimum(dy, self.ly - dy)
        inside = np.hypot(dx, dy) <= radius
        self.mineral[inside] = np.maximum(self.mineral[inside], share)

    def fecundity(self, dbh_m: float, age: int) -> float:
        """As the plain class, from a stem diameter on as well as an age."""
        least = getattr(self.p.spread, "seed_min_dbh_wood_cm", None)
        if least is not None and dbh_m * 100.0 < float(least):
            return 0.0
        return super().fecundity(dbh_m, age)

    def seed_crop(self) -> float:
        """This year's crop against a poor year's; one draw for the whole ground."""
        share = getattr(self.p.spread, "mast_share", None)
        return float(self.p.spread.mast_factor) if share and self.rng.random() < float(share) else 1.0

    def light_chance(self, light: np.ndarray) -> np.ndarray:
        """Share of germinants that live through the first season, by light at 0.1 m."""
        lo, hi = (float(x) for x in self.p.spread.establishment_light)
        return np.clip((light - lo) / (hi - lo), 0.0, 1.0)

    def step(self, trees_xy: np.ndarray, seeds: np.ndarray, canopy_light: np.ndarray, field_layer: float,
             occupied: np.ndarray):
        """One year, as Regeneration.step, with the light ramp and the kernels."""
        p = self.p
        crop = self.seed_crop()
        rain = self.seed_rain(trees_xy, seeds * crop)
        organic = np.maximum(1.0 - self.mineral - self.surface_stone, 0.0)
        # the organic layer's rate was measured under its field layer in full light, so it
        # already holds that shade: both seedbeds read only the canopy's light here
        chance_light = self.light_chance(canopy_light)
        if self.overhead is not None:
            chance_light = chance_light * (self.overhead < float(p.spread.canopy_lai_max))
        e_m = rain * self.mineral * float(p.establishment_mineral) * chance_light
        e_o = rain * organic * float(p.establishment_organic) * chance_light
        expected = e_m + e_o
        chance = np.where(~occupied, 1.0 - np.exp(-expected), 0.0)
        hit = np.nonzero(self.rng.random(chance.shape) < chance)
        cells = list(zip(*hit))
        limit = getattr(p.spread, "max_recruits_per_year", None)
        if limit is not None and len(cells) > int(limit):
            keep = self.rng.permutation(len(cells))[: int(limit)]
            cells = [cells[n] for n in sorted(keep.tolist())]
        out = []
        for i, j in cells:
            on_mineral = bool(self.rng.random() * expected[i, j] < e_m[i, j])
            for _ in range(8):                      # a point of the cell off surface stones
                x = self.cx[i, j] + (self.rng.random() - 0.5) * self.csx
                y = self.cy[i, j] + (self.rng.random() - 0.5) * self.csy
                if not self._surface_stone(x, y):
                    out.append((x, y, on_mineral))
                    break
        keep_m = 0.5 ** (1.0 / self._half_life())
        self.mineral = self.mineral * keep_m + float(p.mineral_new_per_year) * (1.0 - self.mineral * keep_m)
        area = self.lx * self.ly
        self.last = {"seed_rain_per_m2": float(rain.sum() / area), "seed_crop": crop,
                     "ground_light_mean": float(canopy_light.mean()),
                     "ground_light_p10": float(np.percentile(canopy_light, 10)),
                     "ground_light_p90": float(np.percentile(canopy_light, 90)),
                     "open_share": float((chance_light > 0.0).mean()),
                     "canopy_lai_mean": float(self.overhead.mean()) if self.overhead is not None else None,
                     "canopy_lai_p05": float(np.percentile(self.overhead, 5)) if self.overhead is not None else None,
                     "light_at_thinnest_canopy": float(canopy_light[self.overhead <= np.percentile(self.overhead, 5)].mean()) if self.overhead is not None else None,
                     "expected_per_m2": float(expected.sum() / area), "recruits": len(out),
                     "recruits_on_mineral": sum(1 for r in out if r[2]),
                     "recruits_offered": int(len(hit[0])), "mineral_share": float(self.mineral.mean())}
        return out
