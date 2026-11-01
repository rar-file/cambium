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
